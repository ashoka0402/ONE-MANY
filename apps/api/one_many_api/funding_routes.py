"""Explicit Sandbox participation, idempotent PayPal checkout and verified ledger.

An anonymous AI match is NOT a buyer. Every group member must opt in with
their own independently authenticated, compatible need before any order.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from one_many_api.ai_service import fingerprint
from one_many_api.auth import get_current_user
from one_many_api.channel3 import CatalogMalformed, CatalogUnavailable, Channel3Client, minor_to_display
from one_many_api.database import get_db
from one_many_api.matching import _compatible_dates, features_compatible
from one_many_api.models import (
    FundingGroup, FundingMember, Need, PaymentAttempt, PayPalWebhookEvent, PurchaseProposal, User,
)
from one_many_api.paypal import (
    PAYPAL_CURRENCIES, PayPalInvalid, PayPalSandboxClient, PayPalUnavailable, verify_order,
)
from one_many_api.routes import _owned_need

funding_router = APIRouter(prefix="/api/v1", tags=["paypal-sandbox-funding"])

DISCLAIMER = (
    "SANDBOX ONLY. These are simulated merchant payments, not escrow, legal "
    "co-ownership, automatic retailer purchases, or promised refunds. "
    "Only explicitly joined people can authorize their own share."
)


class JoinIn(BaseModel):
    invite_code: str = Field(min_length=25, max_length=100)
    need_id: UUID


class MemberOut(BaseModel):
    slot: int
    share_minor: int
    share_display: str
    payment_state: str
    is_you: bool


class GroupOut(BaseModel):
    id: UUID
    proposal_id: UUID
    product_title: str
    product_image_url: str | None
    state: str
    currency: str
    total_minor: int
    total_display: str
    captured_minor: int
    captured_display: str
    accepted_count: int
    target_members: int
    expires_at: datetime
    members: list[MemberOut]
    disclaimer: str = DISCLAIMER


class CreatedGroupOut(BaseModel):
    group: GroupOut
    invite_code: str


class GroupsOut(BaseModel):
    groups: list[GroupOut]


class OrderOut(BaseModel):
    paypal_order_id: str
    approval_url: str
    state: str
    amount_minor: int
    currency: str
    disclaimer: str = DISCLAIMER


def _now() -> datetime:
    return datetime.now(UTC)


def _sha(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()

def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _group(db: Session, group_id: UUID, *, lock: bool = False) -> FundingGroup:
    stmt = select(FundingGroup).where(FundingGroup.id == group_id)
    if lock:
        stmt = stmt.with_for_update()
    group = db.scalar(stmt)
    if group is None:
        raise HTTPException(404, "Funding group not found")
    return group


def _members(db: Session, group_id: UUID) -> list[FundingMember]:
    return list(db.scalars(
        select(FundingMember).where(FundingMember.group_id == group_id)
        .order_by(FundingMember.slot_index)
    ).all())


def _assert_member(db: Session, group: FundingGroup, user: User) -> FundingMember:
    member = db.scalar(select(FundingMember).where(
        FundingMember.group_id == group.id,
        FundingMember.user_id == user.id,
    ))
    if member is None:
        raise HTTPException(404, "Funding group not found")
    return member


def _proposal(db: Session, group: FundingGroup) -> PurchaseProposal:
    proposal = db.get(PurchaseProposal, group.proposal_id)
    assert proposal is not None
    return proposal


def _out(db: Session, group: FundingGroup, user: User) -> GroupOut:
    proposal = _proposal(db, group)
    members = _members(db, group.id)
    attempts = {
        attempt.user_id: attempt
        for attempt in db.scalars(
            select(PaymentAttempt).where(PaymentAttempt.group_id == group.id)
        ).all()
    }
    paid = sum(
        attempt.amount_minor for attempt in attempts.values() if attempt.state == "completed"
    )
    return GroupOut(
        id=group.id,
        proposal_id=group.proposal_id,
        product_title=proposal.product_title,
        product_image_url=proposal.product_image_url,
        state=group.state,
        currency=group.currency,
        total_minor=group.total_minor,
        total_display=minor_to_display(group.total_minor, group.currency),
        captured_minor=paid,
        captured_display=minor_to_display(paid, group.currency),
        accepted_count=len(members),
        target_members=group.target_members,
        expires_at=group.expires_at,
        members=[
            MemberOut(
                slot=m.slot_index + 1,
                share_minor=m.share_minor,
                share_display=minor_to_display(m.share_minor, group.currency),
                payment_state=attempts[m.user_id].state if m.user_id in attempts else "not_started",
                is_you=m.user_id == user.id,
            )
            for m in members
        ],
    )


def _valid_need(need: Need, settings) -> None:
    if (
        need.status != "open"
        or not need.discoverable
        or not need.location_key
        or need.intent is None
        or not need.intent.shareable
        or need.intent.source_hash != fingerprint(need.request_text, settings.gemini_model)
    ):
        raise HTTPException(409, "A participant need is no longer open, opted-in or analyzed")
    if need.needed_from is None or need.needed_until is None:
        raise HTTPException(409, "Both usage dates must be supplied before accepting funding")


def _compatibility(own: Need, peer: Need) -> None:
    if own.owner_id == peer.owner_id:
        raise HTTPException(409, "Each participant must be a different account")
    if own.location_key != peer.location_key or own.intent.asset_key != peer.intent.asset_key:
        raise HTTPException(409, "Participant needs do not match the same asset and area")
    if not features_compatible(own.intent, peer.intent):
        raise HTTPException(409, "Participant feature requirements conflict")
    if _compatible_dates(own, peer) != "separate":
        raise HTTPException(409, "Usage windows overlap or are not fully specified")


def _revalidate_members(db: Session, group: FundingGroup, settings) -> list[FundingMember]:
    members = _members(db, group.id)
    if len(members) != group.target_members:
        raise HTTPException(409, "All members must explicitly join before checkout")
    needs = []
    for member in members:
        need = db.get(Need, member.need_id)
        if need is None or need.owner_id != member.user_id:
            raise HTTPException(409, "A member need is unavailable")
        _valid_need(need, settings)
        needs.append(need)
    for index, a in enumerate(needs):
        for b in needs[index + 1:]:
            _compatibility(a, b)
    if sum(member.share_minor for member in members) != group.total_minor:
        raise HTTPException(409, "Group shares no longer add up to the accepted quote")
    return members


def _check_provider_price(db: Session, group: FundingGroup, settings) -> None:
    """Read actual selected offer before first checkout; never use browser prices."""
    proposal = _proposal(db, group)
    need = db.get(Need, proposal.need_id)
    if need is None:
        raise HTTPException(409, "Original need has disappeared")
    _valid_need(need, settings)
    if need.intent.source_hash != proposal.need_source_hash:
        raise HTTPException(409, "Proposal was based on an outdated need")
    try:
        item = Channel3Client(settings).product(
            proposal.channel3_product_id,
            need.intent.required_features,
            need.intent.excluded_features,
        )
    except CatalogUnavailable as exc:
        raise HTTPException(503, str(exc)) from None
    except CatalogMalformed:
        raise HTTPException(502, "Channel3 returned invalid product details") from None
    if item.suitability != "candidate":
        raise HTTPException(409, "Product specifications are no longer eligible")
    if not any(
        offer.url == proposal.merchant_url and
        offer.currency == group.currency and
        offer.price_minor == group.total_minor
        for offer in item.offers
    ):
        raise HTTPException(409, "Selected retailer offer, price or currency changed")


def _mark_captured(db: Session, group: FundingGroup, attempt: PaymentAttempt, capture_id: str):
    if attempt.paypal_capture_id is not None and attempt.paypal_capture_id != capture_id:
        group.state = "needs_review"
        attempt.state = "needs_review"
        db.commit()
        raise HTTPException(409, "Different PayPal capture detected; group requires review")
    attempt.paypal_capture_id = capture_id
    attempt.state = "completed"
    db.flush()
    members = _members(db, group.id)
    completed = list(db.scalars(
        select(PaymentAttempt).where(
            PaymentAttempt.group_id == group.id,
            PaymentAttempt.state == "completed",
        )
    ).all())
    if len(completed) == group.target_members:
        total = sum(a.amount_minor for a in completed)
        if len(members) == group.target_members and total == group.total_minor:
            group.state = "funded"
        else:
            group.state = "needs_review"
    db.commit()


def _verify_attempt_order(
    paypal: PayPalSandboxClient, group: FundingGroup, attempt: PaymentAttempt, settings
):
    if not attempt.paypal_order_id:
        raise HTTPException(409, "No stored PayPal order exists")
    order = paypal.get_order(attempt.paypal_order_id)
    return verify_order(
        order,
        order_id=attempt.paypal_order_id,
        reference_id=str(group.id),
        custom_id=str(attempt.id),
        amount_minor=attempt.amount_minor,
        currency=attempt.currency,
        merchant_id=settings.paypal_merchant_id,
    )


@funding_router.post(
    "/proposals/{proposal_id}/funding-group",
    response_model=CreatedGroupOut,
    status_code=status.HTTP_201_CREATED,
)
def create_group(
    proposal_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal = db.scalar(
        select(PurchaseProposal).where(
            PurchaseProposal.id == proposal_id, PurchaseProposal.owner_id == user.id
        ).with_for_update()
    )
    if proposal is None:
        raise HTTPException(404, "Draft quote not found")
    if proposal.status != "draft" or _aware(proposal.quote_expires_at) <= _now():
        raise HTTPException(409, "Draft quote is no longer fresh")
    if db.scalar(select(FundingGroup).where(FundingGroup.proposal_id == proposal_id)):
        raise HTTPException(409, "Funding group already exists for this proposal")
    if proposal.currency not in PAYPAL_CURRENCIES:
        raise HTTPException(409, "PayPal Sandbox cannot accept this catalog currency")
    if len(proposal.share_amounts_minor) != proposal.prospective_members:
        raise HTTPException(409, "Invalid proposal allocation")
    if sum(proposal.share_amounts_minor) != proposal.price_minor:
        raise HTTPException(409, "Draft quote does not reconcile")

    need = _owned_need(db, user, proposal.need_id)
    _valid_need(need, request.app.state.settings)
    if proposal.need_source_hash != need.intent.source_hash:
        raise HTTPException(409, "Draft quote is for a different or outdated request")
    _check_provider_price_for_proposal(db, proposal, request.app.state.settings)

    code = secrets.token_urlsafe(24)
    group = FundingGroup(
        proposal_id=proposal.id,
        owner_id=user.id,
        invitation_hash=_sha(code),
        total_minor=proposal.price_minor,
        currency=proposal.currency,
        target_members=proposal.prospective_members,
        expires_at=_now() + timedelta(
            hours=request.app.state.settings.funding_group_lifetime_hours
        ),
    )
    db.add(group)
    db.flush()
    db.add(FundingMember(
        group_id=group.id, user_id=user.id, need_id=need.id,
        slot_index=0, share_minor=proposal.share_amounts_minor[0],
    ))
    db.commit()
    return CreatedGroupOut(group=_out(db, group, user), invite_code=code)


def _check_provider_price_for_proposal(db: Session, proposal: PurchaseProposal, settings):
    """Used before creating a funding group; the draft must still be current."""
    need = db.get(Need, proposal.need_id)
    _valid_need(need, settings)
    try:
        item = Channel3Client(settings).product(
            proposal.channel3_product_id,
            need.intent.required_features,
            need.intent.excluded_features,
        )
    except CatalogUnavailable as exc:
        raise HTTPException(503, str(exc)) from None
    except CatalogMalformed:
        raise HTTPException(502, "Channel3 returned invalid product details") from None
    if item.suitability != "candidate" or not any(
        offer.url == proposal.merchant_url
        and offer.price_minor == proposal.price_minor
        and offer.currency == proposal.currency
        for offer in item.offers
    ):
        raise HTTPException(409, "Price or offer changed; refresh the draft first")


@funding_router.post("/funding/join", response_model=GroupOut)
def join_group(
    payload: JoinIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    code_hash = _sha(payload.invite_code)
    group = db.scalar(
        select(FundingGroup).where(FundingGroup.invitation_hash == code_hash).with_for_update()
    )
    if group is None:
        raise HTTPException(404, "Invitation not found")
    if group.state != "recruiting" or _aware(group.expires_at) <= _now():
        raise HTTPException(409, "The invitation is no longer accepting participants")
    if db.scalar(select(FundingMember).where(
        FundingMember.group_id == group.id, FundingMember.user_id == user.id
    )):
        return _out(db, group, user)
    need = _owned_need(db, user, payload.need_id)
    _valid_need(need, request.app.state.settings)
    proposal = _proposal(db, group)
    members = _members(db, group.id)
    if len(members) >= group.target_members:
        raise HTTPException(409, "Funding group is full")
    source_need = db.get(Need, proposal.need_id)
    if source_need is None:
        raise HTTPException(409, "Original request is unavailable")
    _valid_need(source_need, request.app.state.settings)
    if proposal.need_source_hash != source_need.intent.source_hash:
        raise HTTPException(409, "Original request has changed; group requires review")
    for existing in members:
        other = db.get(Need, existing.need_id)
        _valid_need(other, request.app.state.settings)
        _compatibility(other, need)
    slot = len(members)
    db.add(FundingMember(
        group_id=group.id, user_id=user.id, need_id=need.id,
        slot_index=slot, share_minor=proposal.share_amounts_minor[slot],
    ))
    if slot + 1 == group.target_members:
        group.state = "funding"
    db.commit()
    return _out(db, group, user)


@funding_router.post("/funding/groups/{group_id}/rotate-invite", response_model=CreatedGroupOut)
def rotate_invitation(
    group_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _group(db, group_id, lock=True)
    if group.owner_id != user.id:
        raise HTTPException(404, "Funding group not found")
    if group.state != "recruiting":
        raise HTTPException(409, "Invitations are closed after recruitment")
    code = secrets.token_urlsafe(24)
    group.invitation_hash = _sha(code)
    db.commit()
    return CreatedGroupOut(group=_out(db, group, user), invite_code=code)


@funding_router.get("/funding/groups", response_model=GroupsOut)
def groups_for_user(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(FundingGroup).join(FundingMember, FundingMember.group_id == FundingGroup.id)
        .where(FundingMember.user_id == user.id)
        .order_by(FundingGroup.created_at.desc(), FundingGroup.id.desc())
        .limit(50)
    ).all()
    return GroupsOut(groups=[_out(db, row, user) for row in rows])


@funding_router.get("/funding/groups/{group_id}", response_model=GroupOut)
def group_detail(
    group_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _group(db, group_id)
    _assert_member(db, group, user)
    return _out(db, group, user)


@funding_router.post("/funding/groups/{group_id}/paypal-order", response_model=OrderOut)
def make_paypal_order(
    group_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = request.app.state.settings
    group = _group(db, group_id, lock=True)
    member = _assert_member(db, group, user)
    if group.state != "funding" or _aware(group.expires_at) <= _now():
        raise HTTPException(409, "Funding group is not accepting new PayPal orders")
    attempt = db.scalar(select(PaymentAttempt).where(
        PaymentAttempt.group_id == group.id, PaymentAttempt.user_id == user.id
    ))
    if attempt is not None and attempt.state == "awaiting_approval":
        if not attempt.approval_url or not attempt.paypal_order_id:
            raise HTTPException(409, "Order needs reconciliation")
        return OrderOut(
            paypal_order_id=attempt.paypal_order_id,
            approval_url=attempt.approval_url,
            state=attempt.state,
            amount_minor=attempt.amount_minor,
            currency=attempt.currency,
        )
    if attempt is not None and attempt.state != "creating":
        raise HTTPException(409, "Existing order must be reconciled, not recreated")
    _revalidate_members(db, group, settings)
    _check_provider_price(db, group, settings)
    if group.currency not in PAYPAL_CURRENCIES:
        raise HTTPException(409, "Currency is not supported for PayPal Checkout")
    if attempt is None:
        attempt = PaymentAttempt(
            group_id=group.id, user_id=user.id,
            amount_minor=member.share_minor, currency=group.currency,
        )
        db.add(attempt)
        db.commit()  # persist idempotency key BEFORE remote create
        db.refresh(attempt)
    if attempt.amount_minor != member.share_minor or attempt.currency != group.currency:
        raise HTTPException(409, "Stored payment amount does not reconcile")
    client = PayPalSandboxClient(settings)
    try:
        order_id, url = client.create_order(
            group_id=str(group.id),
            attempt_id=str(attempt.id),
            amount_minor=attempt.amount_minor,
            currency=attempt.currency,
            description=_proposal(db, group).product_title,
            request_id=f"om-create-{attempt.id.hex}",
        )
    except (PayPalUnavailable, PayPalInvalid) as exc:
        raise HTTPException(503, str(exc)) from None
    if attempt.paypal_order_id and attempt.paypal_order_id != order_id:
        group.state = "needs_review"
        attempt.state = "needs_review"
        db.commit()
        raise HTTPException(409, "PayPal returned inconsistent order IDs")
    attempt.paypal_order_id = order_id
    attempt.approval_url = url
    attempt.state = "awaiting_approval"
    db.commit()
    return OrderOut(
        paypal_order_id=order_id,
        approval_url=url,
        state=attempt.state,
        amount_minor=attempt.amount_minor,
        currency=attempt.currency,
    )


@funding_router.post("/funding/groups/{group_id}/paypal-capture", response_model=GroupOut)
def capture_my_payment(
    group_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = request.app.state.settings
    group = _group(db, group_id, lock=True)
    _assert_member(db, group, user)
    attempt = db.scalar(select(PaymentAttempt).where(
        PaymentAttempt.group_id == group.id, PaymentAttempt.user_id == user.id
    ))
    if attempt is None:
        raise HTTPException(409, "Create and approve your own PayPal order first")
    if attempt.state == "completed":
        return _out(db, group, user)  # idempotent user refresh
    if group.state != "funding" or attempt.state not in (
        "awaiting_approval", "capture_pending"
    ):
        raise HTTPException(409, "This payment is not eligible for capture")
    paypal = PayPalSandboxClient(settings)
    try:
        state, capture_id = _verify_attempt_order(paypal, group, attempt, settings)
        if state == "APPROVED":
            attempt.state = "capture_pending"
            db.commit()  # an uncertain response must NEVER be treated as failure/no charge
            paypal.capture(attempt.paypal_order_id, f"om-capture-{attempt.id.hex}")
            state, capture_id = _verify_attempt_order(paypal, group, attempt, settings)
        elif state in ("CREATED", "PAYER_ACTION_REQUIRED", "SAVED"):
            raise HTTPException(409, "PayPal order has not been approved by the buyer")
        if state == "COMPLETED" and capture_id:
            _mark_captured(db, group, attempt, capture_id)
        else:
            attempt.state = "capture_pending"
            db.commit()
            return _out(db, group, user)  # Pending is not treated as funded.
    except PayPalUnavailable as exc:
        # Keep capture_pending state for deterministic reconciliation of ambiguous attempts.
        raise HTTPException(503, str(exc)) from None
    except PayPalInvalid as exc:
        group.state = "needs_review"
        attempt.state = "needs_review"
        db.commit()
        raise HTTPException(409, str(exc)) from None
    return _out(db, group, user)


@funding_router.post("/paypal/webhook")
async def webhook_receive(request: Request, db: Session = Depends(get_db)):
    """Always verify provider signature BEFORE trusting event ID, type or references."""
    try:
        event = await request.json()
    except ValueError:
        raise HTTPException(400, "Invalid event JSON") from None
    if not isinstance(event, dict):
        raise HTTPException(400, "Invalid event JSON")
    paypal = PayPalSandboxClient(request.app.state.settings)
    try:
        verified = paypal.verify_webhook(request.headers, event)
    except PayPalUnavailable as exc:
        raise HTTPException(503, str(exc)) from None
    if not verified:
        raise HTTPException(401, "Invalid PayPal webhook signature")
    event_id, event_type = event.get("id"), event.get("event_type")
    if not isinstance(event_id, str) or not (4 <= len(event_id) <= 150):
        raise HTTPException(422, "Invalid webhook event ID")
    if not isinstance(event_type, str) or len(event_type) > 100:
        raise HTTPException(422, "Invalid webhook event type")
    if db.get(PayPalWebhookEvent, event_id):
        return {"received": True, "duplicate": True}
    payload = event.get("resource")
    if not isinstance(payload, dict):
        payload = {}
    capture_id = payload.get("id")
    related = payload.get("supplementary_data", {})
    related = related.get("related_ids", {}) if isinstance(related, dict) else {}
    order_id = related.get("order_id") if isinstance(related, dict) else None
    attempt = None
    if isinstance(order_id, str):
        attempt = db.scalar(
            select(PaymentAttempt).where(PaymentAttempt.paypal_order_id == order_id)
        )
    if attempt is None and isinstance(capture_id, str):
        attempt = db.scalar(
            select(PaymentAttempt).where(PaymentAttempt.paypal_capture_id == capture_id)
        )
    if attempt is not None and event_type in {
        "PAYMENT.CAPTURE.COMPLETED",
        "PAYMENT.CAPTURE.PENDING",
        "PAYMENT.CAPTURE.DENIED",
        "PAYMENT.CAPTURE.REFUNDED",
    }:
        group = _group(db, attempt.group_id, lock=True)
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            try:
                state, verified_id = _verify_attempt_order(
                    paypal, group, attempt, request.app.state.settings
                )
            except (PayPalUnavailable, PayPalInvalid):
                raise HTTPException(503, "PayPal reconciliation unavailable") from None
            if state == "COMPLETED" and verified_id == capture_id:
                if attempt.state not in ("reversed", "needs_review"):
                    _mark_captured(db, group, attempt, verified_id)
        elif event_type == "PAYMENT.CAPTURE.PENDING":
            if attempt.state not in ("completed", "reversed", "needs_review"):
                attempt.state = "capture_pending"
        elif event_type in ("PAYMENT.CAPTURE.DENIED", "PAYMENT.CAPTURE.REFUNDED"):
            # Signed status triggers review; never silently count a refunded capture.
            if capture_id == attempt.paypal_capture_id or order_id == attempt.paypal_order_id:
                attempt.state = (
                    "reversed" if event_type == "PAYMENT.CAPTURE.REFUNDED" else "needs_review"
                )
                group.state = "needs_review"
    db.add(PayPalWebhookEvent(event_id=event_id, event_type=event_type))
    db.commit()
    return {"received": True, "duplicate": False}

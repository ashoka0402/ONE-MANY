"""Member-only funding snapshots + append-only payment-event log.

Read-only GET: cannot create orders, mark captures, fake audit history, or
invoke third-party providers. Only completed captures with a persisted PayPal
capture ID and a reconciled member share contribute to the verified total.
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from one_many_api.auth import get_current_user
from one_many_api.channel3 import minor_to_display
from one_many_api.database import get_db
from one_many_api.funding_routes import _assert_member, _group, _members, _proposal
from one_many_api.models import FundingLedgerEvent, PaymentAttempt, User

ledger_router = APIRouter(prefix="/api/v1", tags=["verified-contribution-ledger"])

LEDGER_NOTICE = (
    "PayPal SANDBOX only. This is a snapshot of server-recorded test-merchant "
    "captures, not bank settlement, escrow, real payment, retailer fulfillment "
    "or a refund guarantee. Audit events begin with Stage 6; historic activity "
    "is not fabricated. Refresh for the latest recorded state."
)


class LedgerMemberOut(BaseModel):
    slot: int
    is_you: bool
    share_minor: int
    share_display: str
    captured_minor: int
    captured_display: str
    payment_state: str
    last_updated_at: datetime | None


class LedgerEventOut(BaseModel):
    id: UUID
    recorded_at: datetime
    event_type: str
    source: str
    member_slot: int | None
    amount_minor: int
    amount_display: str


class LedgerSummaryOut(BaseModel):
    group_id: UUID
    product_title: str
    group_state: str
    currency: str
    total_minor: int
    total_display: str
    captured_minor: int
    captured_display: str
    outstanding_minor: int
    outstanding_display: str
    verified_members: int
    accepted_members: int
    target_members: int
    progress_percent: int
    reconciliation: str
    as_of: datetime
    members: list[LedgerMemberOut]
    events: list[LedgerEventOut]
    has_more_events: bool
    notice: str = LEDGER_NOTICE


@ledger_router.get(
    "/funding/groups/{group_id}/ledger",
    response_model=LedgerSummaryOut,
)
def member_ledger(
    group_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _group(db, group_id)
    _assert_member(db, group, user)
    members = _members(db, group.id)
    attempts = {
        row.user_id: row
        for row in db.scalars(
            select(PaymentAttempt).where(PaymentAttempt.group_id == group.id)
        ).all()
    }
    currency = group.currency
    result: list[LedgerMemberOut] = []
    paid = 0
    verified = 0
    inconsistent = (
        len(attempts) > len(members)
        or any(m.share_minor <= 0 for m in members)
        or (len(members) == group.target_members
            and sum(m.share_minor for m in members) != group.total_minor)
    )
    for member in members:
        attempt = attempts.get(member.user_id)
        matches = (
            attempt is not None
            and attempt.amount_minor == member.share_minor
            and attempt.currency == currency
            and attempt.group_id == group.id
        )
        if attempt is not None and not matches:
            inconsistent = True
        confirmed = (
            matches and attempt.state == "completed"
            and bool(attempt.paypal_capture_id)
        )
        if attempt is not None and attempt.state == "completed" and not confirmed:
            inconsistent = True
        captured = member.share_minor if confirmed else 0
        verified += int(confirmed)
        paid += captured
        result.append(
            LedgerMemberOut(
                slot=member.slot_index + 1,
                is_you=member.user_id == user.id,
                share_minor=member.share_minor,
                share_display=minor_to_display(member.share_minor, currency),
                captured_minor=captured,
                captured_display=minor_to_display(captured, currency),
                payment_state=attempt.state if attempt is not None else "not_started",
                last_updated_at=attempt.updated_at if attempt is not None else None,
            )
        )
    if (
        paid > group.total_minor
        or (group.state == "funded"
            and (verified != group.target_members or paid != group.total_minor))
        or (group.state == "needs_review" and verified == group.target_members)
    ):
        inconsistent = True
    state = (
        "requires_review" if inconsistent or group.state == "needs_review"
        else "reconciled" if (
            group.state == "funded"
            and verified == group.target_members
            and len(members) == group.target_members
            and paid == group.total_minor
        )
        else "in_progress"
    )
    outstanding = max(group.total_minor - paid, 0)
    audit_total = db.scalar(
        select(func.count(FundingLedgerEvent.id)).where(
            FundingLedgerEvent.group_id == group.id
        )
    ) or 0
    history = db.scalars(
        select(FundingLedgerEvent)
        .where(FundingLedgerEvent.group_id == group.id)
        .order_by(FundingLedgerEvent.recorded_at.desc(), FundingLedgerEvent.id.desc())
        .limit(200)
    ).all()
    return LedgerSummaryOut(
        group_id=group.id,
        product_title=_proposal(db, group).product_title,
        group_state=group.state,
        currency=currency,
        total_minor=group.total_minor,
        total_display=minor_to_display(group.total_minor, currency),
        captured_minor=paid,
        captured_display=minor_to_display(paid, currency),
        outstanding_minor=outstanding,
        outstanding_display=minor_to_display(outstanding, currency),
        verified_members=verified,
        accepted_members=len(members),
        target_members=group.target_members,
        progress_percent=min(100, paid * 100 // group.total_minor),
        reconciliation=state,
        as_of=datetime.now(UTC),
        members=result,
        events=[
            LedgerEventOut(
                id=e.id,
                recorded_at=e.recorded_at,
                event_type=e.event_type,
                source=e.source,
                member_slot=e.member_slot,
                amount_minor=e.amount_minor,
                amount_display=minor_to_display(e.amount_minor, currency),
            ) for e in history
        ],
        has_more_events=audit_total > len(history),
    )

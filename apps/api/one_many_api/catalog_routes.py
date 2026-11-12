"""Real Channel3 search and immutable draft quotes; not purchase/payment endpoints."""
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from one_many_api.ai_service import fingerprint
from one_many_api.auth import get_current_user
from one_many_api.channel3 import (
    CatalogMalformed,
    CatalogUnavailable,
    Channel3Client,
    ProductResults,
    minor_to_display,
)
from one_many_api.database import get_db
from one_many_api.matching import find_matches
from one_many_api.models import Need, PurchaseProposal, User
from one_many_api.pricing import equal_shares, hypothetical_savings
from one_many_api.routes import _owned_need

catalog_router = APIRouter(prefix="/api/v1", tags=["catalog-and-draft-proposals"])


class QuoteRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=250)
    offer_url: str = Field(min_length=10, max_length=2048)


class DraftProposalOut(BaseModel):
    id: UUID
    need_id: UUID
    product_id: str
    product_title: str
    product_image_url: str | None
    merchant_domain: str
    merchant_url: str
    currency: str
    price_minor: int
    price_display: str
    prospective_members: int
    member_shares_minor: list[int]
    member_shares_display: list[str]
    hypothetical_savings_minor: int
    hypothetical_savings_display: str
    quote_expires_at: datetime
    created_at: datetime
    status: str
    disclaimer: str = (
        "DRAFT ONLY. These are hypothetical shares based on potential anonymous "
        "matches, not consenting purchasers. Taxes, shipping, fees, fulfillment "
        "and actual availability are not included. No PayPal payment or purchase "
        "has occurred. Reconfirm price, members and conditions before checkout."
    )


class ProposalList(BaseModel):
    proposals: list[DraftProposalOut]


def _eligible_need(need_id: UUID, request: Request, db: Session, owner: User) -> Need:
    need = _owned_need(db, owner, need_id)
    settings = request.app.state.settings
    if need.status != "open" or not need.discoverable or not need.location_key:
        raise HTTPException(409, "Use an open, discoverable need with an area")
    if need.intent is None or not need.intent.shareable:
        raise HTTPException(409, "Analyze a reusable asset first")
    if need.intent.source_hash != fingerprint(need.request_text, settings.gemini_model):
        raise HTTPException(409, "Need was edited or the model changed; analyze again")
    return need


def _serialize(proposal: PurchaseProposal) -> DraftProposalOut:
    price = proposal.price_minor
    currency = proposal.currency
    shares = proposal.share_amounts_minor
    return DraftProposalOut(
        id=proposal.id,
        need_id=proposal.need_id,
        product_id=proposal.channel3_product_id,
        product_title=proposal.product_title,
        product_image_url=proposal.product_image_url,
        merchant_domain=proposal.merchant_domain,
        merchant_url=proposal.merchant_url,
        currency=currency,
        price_minor=price,
        price_display=minor_to_display(price, currency),
        prospective_members=proposal.prospective_members,
        member_shares_minor=shares,
        member_shares_display=[minor_to_display(amount, currency) for amount in shares],
        hypothetical_savings_minor=hypothetical_savings(price, proposal.prospective_members),
        hypothetical_savings_display=minor_to_display(
            hypothetical_savings(price, proposal.prospective_members), currency
        ),
        quote_expires_at=proposal.quote_expires_at,
        created_at=proposal.created_at,
        status=proposal.status,
    )


@catalog_router.post("/needs/{need_id}/products/search", response_model=ProductResults)
def search_products(
    need_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    need = _eligible_need(need_id, request, db, user)
    try:
        return Channel3Client(request.app.state.settings).search(
            need.intent.asset_type,
            need.intent.required_features,
            need.intent.excluded_features,
        )
    except CatalogUnavailable as exc:
        raise HTTPException(503, str(exc)) from None
    except CatalogMalformed:
        raise HTTPException(502, "Channel3 search returned invalid catalog data") from None


@catalog_router.post(
    "/needs/{need_id}/proposals",
    response_model=DraftProposalOut,
    status_code=status.HTTP_201_CREATED,
)
def create_draft(
    need_id: UUID,
    body: QuoteRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    need = _eligible_need(need_id, request, db, user)
    matches = find_matches(db, user, need, request.app.state.settings.match_candidate_limit)
    if matches.potential_members < 1:
        raise HTTPException(409, "No compatible opted-in member currently exists")
    try:
        product = Channel3Client(request.app.state.settings).product(
            body.product_id,
            need.intent.required_features,
            need.intent.excluded_features,
        )
    except CatalogUnavailable as exc:
        raise HTTPException(503, str(exc)) from None
    except CatalogMalformed:
        raise HTTPException(502, "Channel3 product details were invalid") from None
    if product.suitability != "candidate":
        raise HTTPException(409, "Selected catalog item needs manual suitability verification")
    selected = next((offer for offer in product.offers if offer.url == body.offer_url), None)
    if selected is None:
        raise HTTPException(409, "Selected offer is unavailable or changed at the retailer")
    count = min(
        request.app.state.settings.max_proposal_participants,
        matches.potential_members + 1,
    )
    try:
        shares = equal_shares(selected.price_minor, count)
    except ValueError:
        raise HTTPException(409, "Invalid price for the prospective group size") from None
    draft = PurchaseProposal(
        owner_id=user.id,
        need_id=need.id,
        need_source_hash=need.intent.source_hash,
        channel3_product_id=product.id,
        product_title=product.title,
        product_image_url=product.image_url,
        merchant_domain=selected.domain,
        merchant_url=selected.url,
        currency=selected.currency,
        price_minor=selected.price_minor,
        prospective_members=count,
        share_amounts_minor=shares,
        quote_expires_at=datetime.now(UTC) + timedelta(minutes=30),
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return _serialize(draft)


@catalog_router.get("/proposals", response_model=ProposalList)
def list_my_proposals(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(PurchaseProposal)
        .where(PurchaseProposal.owner_id == user.id)
        .order_by(PurchaseProposal.created_at.desc(), PurchaseProposal.id.desc())
        .limit(50)
    ).all()
    return ProposalList(proposals=[_serialize(row) for row in rows])


@catalog_router.get("/proposals/{proposal_id}", response_model=DraftProposalOut)
def get_my_proposal(
    proposal_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.scalar(
        select(PurchaseProposal).where(
            PurchaseProposal.id == proposal_id, PurchaseProposal.owner_id == user.id
        )
    )
    if row is None:
        raise HTTPException(404, "Proposal not found")
    return _serialize(row)

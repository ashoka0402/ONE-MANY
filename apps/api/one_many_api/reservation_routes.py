"""Member-owned, all-day provisional reservations; PostgreSQL enforces no overlaps.

Dates represent inclusive civil calendar days, not UTC timestamps. The backend
owns every mutation; the Bryntum UI is a read-only rendering of confirmed data.
No physical item or real delivery is implied by a reservation.
"""
from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from one_many_api.auth import get_current_user
from one_many_api.database import get_db
from one_many_api.funding_routes import (
    _assert_member,
    _group,
    _members,
    _proposal,
    _revalidate_members,
)
from one_many_api.models import (
    AssetReservation,
    FundingGroup,
    FundingMember,
    Need,
    PaymentAttempt,
    User,
)

reservation_router = APIRouter(prefix="/api/v1", tags=["shared-asset-scheduling"])

NOTICE = (
    "A provisional whole-day shared-use plan, not a physical item reservation, "
    "confirmed handover, legal ownership, or retailer fulfillment. "
    "Each date is a civil calendar day; no time-of-day or timezone is inferred."
)


class ReservationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: date
    end_date: date
    expected_version: int = Field(ge=0)

    @model_validator(mode="after")
    def check_order(self) -> "ReservationIn":
        if self.end_date < self.start_date:
            raise ValueError("End date must not precede start date")
        return self


class ReservationOut(BaseModel):
    id: UUID
    slot: int
    start_date: date
    end_date: date
    version: int
    is_you: bool


class OwnWindow(BaseModel):
    start_date: date
    end_date: date


class ReservationBoardOut(BaseModel):
    group_id: UUID
    product_title: str
    group_state: str
    bookable: bool
    own_version: int
    own_window: OwnWindow | None
    reservations: list[ReservationOut]
    notice: str = NOTICE


def _board(
    db: Session, group: FundingGroup, member: FundingMember, user: User
) -> ReservationBoardOut:
    slots = {row.user_id: row.slot_index + 1 for row in _members(db, group.id)}
    need = db.get(Need, member.need_id)
    own_window = (
        OwnWindow(start_date=need.needed_from, end_date=need.needed_until)
        if need is not None and need.needed_from is not None and need.needed_until is not None
        else None
    )
    rows = db.scalars(
        select(AssetReservation).where(
            AssetReservation.group_id == group.id,
            AssetReservation.status == "active",
        ).order_by(AssetReservation.start_date, AssetReservation.id)
    ).all()
    own_record = db.scalar(
        select(AssetReservation).where(
            AssetReservation.group_id == group.id,
            AssetReservation.user_id == user.id,
        )
    )
    return ReservationBoardOut(
        group_id=group.id,
        product_title=_proposal(db, group).product_title,
        group_state=group.state,
        bookable=group.state == "funded",
        own_version=own_record.version if own_record else 0,
        own_window=own_window,
        reservations=[
            ReservationOut(
                id=row.id,
                slot=slots[row.user_id],
                start_date=row.start_date,
                end_date=row.end_date,
                version=row.version,
                is_you=row.user_id == user.id,
            )
            for row in rows
        ],
    )


def _booking_allowed(db: Session, group: FundingGroup, settings) -> None:
    if group.state != "funded":
        raise HTTPException(409, "A group needs all verified Sandbox captures before scheduling")
    members = _revalidate_members(db, group, settings)
    attempts = db.scalars(
        select(PaymentAttempt).where(PaymentAttempt.group_id == group.id)
    ).all()
    if (
        len(attempts) != len(members)
        or any(item.state != "completed" for item in attempts)
        or {item.user_id for item in attempts} != {item.user_id for item in members}
        or sum(item.amount_minor for item in attempts) != group.total_minor
    ):
        raise HTTPException(409, "Verified contributions no longer reconcile with this group")


@reservation_router.get(
    "/funding/groups/{group_id}/reservations",
    response_model=ReservationBoardOut,
)
def list_reservations(
    group_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _group(db, group_id)
    member = _assert_member(db, group, user)
    return _board(db, group, member, user)


@reservation_router.put(
    "/funding/groups/{group_id}/reservation",
    response_model=ReservationBoardOut,
)
def save_my_reservation(
    group_id: UUID,
    payload: ReservationIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # PostgreSQL serializes all writes on one asset by locking its group.
    # A database GiST exclusion constraint independently rejects overlaps.
    group = _group(db, group_id, lock=True)
    member = _assert_member(db, group, user)
    _booking_allowed(db, group, request.app.state.settings)
    need = db.get(Need, member.need_id)
    if (
        need is None or need.owner_id != user.id
        or need.needed_from is None or need.needed_until is None
        or payload.start_date < need.needed_from
        or payload.end_date > need.needed_until
    ):
        raise HTTPException(409, "Select whole days within your accepted need's date window")

    existing = db.scalar(
        select(AssetReservation).where(
            AssetReservation.group_id == group.id,
            AssetReservation.user_id == user.id,
        )
    )
    # Repeating the exact same PUT is safe even if a previous response was lost.
    if (
        existing is not None and existing.status == "active"
        and existing.start_date == payload.start_date
        and existing.end_date == payload.end_date
    ):
        return _board(db, group, member, user)

    current_version = existing.version if existing else 0
    if payload.expected_version != current_version:
        raise HTTPException(409, "Reservation changed in another request; reload before editing")

    conflict = db.scalar(
        select(AssetReservation.id).where(
            AssetReservation.group_id == group.id,
            AssetReservation.status == "active",
            AssetReservation.user_id != user.id,
            AssetReservation.start_date <= payload.end_date,
            AssetReservation.end_date >= payload.start_date,
        )
    )
    if conflict is not None:
        raise HTTPException(409, "Those days are already reserved for this shared asset")

    if existing is None:
        reservation = AssetReservation(
            group_id=group.id,
            user_id=user.id,
            need_id=member.need_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status="active",
            version=1,
        )
        db.add(reservation)
    else:
        existing.start_date = payload.start_date
        existing.end_date = payload.end_date
        existing.status = "active"
        existing.version += 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Covers the PostgreSQL exclusion constraint under concurrent writes.
        raise HTTPException(409, "Conflicting reservation or outdated version; reload") from None
    return _board(db, group, member, user)


@reservation_router.delete(
    "/funding/groups/{group_id}/reservation",
    response_model=ReservationBoardOut,
)
def cancel_my_reservation(
    group_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _group(db, group_id, lock=True)
    member = _assert_member(db, group, user)
    existing = db.scalar(
        select(AssetReservation).where(
            AssetReservation.group_id == group.id,
            AssetReservation.user_id == user.id,
        )
    )
    if existing is not None and existing.status == "active":
        existing.status = "cancelled"
        existing.version += 1
        db.commit()
    # Cancellation is permitted even while a funding reversal is under review.
    return _board(db, group, member, user)

"""Write-only audit records for server-verified funding transitions.

Call before the surrounding transaction commits. No fabricated backfill is
created for records that existed before Stage 6. Never expose event keys.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from one_many_api.models import FundingLedgerEvent


def record_ledger_event(
    db: Session,
    *,
    group_id: UUID,
    event_key: str,
    event_type: str,
    amount_minor: int,
    currency: str,
    source: str = "application",
    member_slot: int | None = None,
    attempt_id: UUID | None = None,
) -> None:
    if len(event_key) > 210:
        raise ValueError("Audit idempotency key is too long")
    if db.scalar(select(FundingLedgerEvent.id).where(FundingLedgerEvent.event_key == event_key)):
        return
    db.add(FundingLedgerEvent(
        group_id=group_id,
        attempt_id=attempt_id,
        member_slot=member_slot,
        event_type=event_type,
        source=source,
        amount_minor=amount_minor,
        currency=currency,
        event_key=event_key,
    ))

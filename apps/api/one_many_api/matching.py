"""Conservative, explainable compatibility rules; AI never authorizes a match.

Matching uses model-extracted asset labels only as *candidates*, then applies
explicit consent, area, ownership, feature, and scheduling gates.
"""
import re
import unicodedata
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from one_many_api.models import Need, NeedIntent, User


def normalize_area(raw: str | None) -> str | None:
    if not raw:
        return None
    text = unicodedata.normalize("NFKC", raw).casefold()
    normalized = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE).strip()
    return " ".join(normalized.split()) or None


def normalize_asset(raw: str) -> str:
    """Compare canonical product labels conservatively; never infer synonyms in code."""
    return normalize_area(raw) or ""


def feature_key(raw: str) -> str:
    return normalize_area(raw) or ""


def _complete_window(need: Need) -> tuple[date, date] | None:
    if need.needed_from is not None and need.needed_until is not None:
        return need.needed_from, need.needed_until
    return None


def _compatible_dates(a: Need, b: Need) -> Literal["separate", "unconfirmed", "conflict"]:
    aw, bw = _complete_window(a), _complete_window(b)
    if aw is None or bw is None:
        return "unconfirmed"
    if aw[0] <= bw[1] and bw[0] <= aw[1]:
        return "conflict"
    return "separate"


def features_compatible(a: NeedIntent, b: NeedIntent) -> bool:
    a_req = {feature_key(x) for x in a.required_features}
    b_req = {feature_key(x) for x in b.required_features}
    a_forbid = {feature_key(x) for x in a.excluded_features}
    b_forbid = {feature_key(x) for x in b.excluded_features}
    return not (a_req & b_forbid or b_req & a_forbid)


class MatchSummary(BaseModel):
    need_id: str
    asset_type: str
    area: str
    potential_members: int = Field(ge=0)
    non_overlapping_schedules: int = Field(ge=0)
    scheduling_confirmation_required: int = Field(ge=0)
    candidates_limited: bool
    status: Literal["potential_matches", "no_match"]
    explanation: str


def find_matches(
    db: Session,
    user: User,
    own: Need,
    max_candidates: int,
) -> MatchSummary:
    """Only anonymous aggregate results are returned: no peer UUIDs or raw text."""
    own_intent = own.intent
    assert own_intent is not None
    stmt = (
        select(Need, NeedIntent)
        .join(NeedIntent, Need.id == NeedIntent.need_id)
        .where(
            Need.status == "open",
            Need.discoverable.is_(True),
            Need.location_key == own.location_key,
            Need.owner_id != user.id,
            NeedIntent.asset_key == own_intent.asset_key,
            NeedIntent.shareable.is_(True),
        )
        .order_by(Need.created_at.desc())
        .limit(max_candidates + 1)
    )
    rows = db.execute(stmt).all()
    truncated = len(rows) > max_candidates
    by_owner: dict[str, str] = {}
    for peer, intent in rows[:max_candidates]:
        if not features_compatible(own_intent, intent):
            continue
        schedule = _compatible_dates(own, peer)
        if schedule == "conflict":
            continue
        owner = str(peer.owner_id)
        previous = by_owner.get(owner)
        if previous is None or (previous == "unconfirmed" and schedule == "separate"):
            by_owner[owner] = schedule
    confirmed = sum(v == "separate" for v in by_owner.values())
    uncertain = sum(v == "unconfirmed" for v in by_owner.values())
    n = len(by_owner)
    if not n:
        explanation = (
            "No compatible opted-in needs were found in this exact area label. "
            "Product compatibility and inventory have not been verified."
        )
    else:
        explanation = (
            "Members independently requested the same AI-normalized reusable asset in "
            "the same self-reported area. Conflicting dates and explicit feature "
            "exclusions were filtered out. Product specifications, availability "
            "and handover still require verification."
        )
    return MatchSummary(
        need_id=str(own.id),
        asset_type=own_intent.asset_type,
        area=own.location_label or "",
        potential_members=n,
        non_overlapping_schedules=confirmed,
        scheduling_confirmation_required=uncertain,
        candidates_limited=truncated,
        status="potential_matches" if n else "no_match",
        explanation=explanation,
    )

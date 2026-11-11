"""Opt-in intent extraction and owner-only anonymous matching discovery."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from one_many_api.ai_service import AIProviderError, extract_intent, fingerprint
from one_many_api.auth import get_current_user
from one_many_api.database import get_db
from one_many_api.matching import MatchSummary, find_matches, normalize_asset
from one_many_api.models import Need, NeedIntent, User
from one_many_api.routes import _owned_need
from one_many_api.schemas import IntentOut

discovery_router = APIRouter(prefix="/api/v1", tags=["matching"])


@discovery_router.post("/needs/{need_id}/analyze", response_model=IntentOut)
def analyze_need(
    need_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    need = _owned_need(db, user, need_id)
    if need.status != "open":
        raise HTTPException(409, "Archived needs cannot be analyzed")
    settings = request.app.state.settings
    source_hash = fingerprint(need.request_text, settings.gemini_model)
    if need.intent is not None and need.intent.source_hash == source_hash:
        return need.intent  # cached real result; no unnecessary API call

    try:
        extracted = extract_intent(need.request_text, settings)
    except AIProviderError as exc:
        raise HTTPException(503, str(exc)) from None

    # Do not persist a stale output if the source was changed while the provider ran.
    db.refresh(need)
    if fingerprint(need.request_text, settings.gemini_model) != source_hash:
        raise HTTPException(409, "Need changed during analysis; please retry")

    if need.intent is None:
        need.intent = NeedIntent(need_id=need.id)
    intent = need.intent
    intent.asset_type = extracted.asset_type
    intent.asset_key = normalize_asset(extracted.asset_type)
    intent.purpose = extracted.purpose
    intent.required_features = extracted.required_features
    intent.excluded_features = extracted.excluded_features
    intent.shareable = extracted.shareable
    intent.model_name = settings.gemini_model
    intent.source_hash = source_hash
    db.commit()
    db.refresh(intent)
    return intent


@discovery_router.get("/needs/{need_id}/matches", response_model=MatchSummary)
def matches_for_need(
    need_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    need: Need = _owned_need(db, user, need_id)
    if need.status != "open" or not need.discoverable:
        raise HTTPException(409, "Opt in to discovery on an open need first")
    if need.location_key is None:
        raise HTTPException(409, "Add a general neighborhood or area to find matches")
    if need.intent is None:
        raise HTTPException(409, "Analyze this need using AI first")
    settings = request.app.state.settings
    if need.intent.source_hash != fingerprint(need.request_text, settings.gemini_model):
        raise HTTPException(409, "This need must be reanalyzed after edits or model changes")
    if not need.intent.shareable:
        raise HTTPException(409, "This need is not suitable for shared asset ownership")
    return find_matches(db, user, need, settings.match_candidate_limit)

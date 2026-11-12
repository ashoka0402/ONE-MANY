"""Opt-in fictional workspace fixtures. Disabled outside local development.

These are not Gemini inferences, consenting neighbors, catalog offers or PayPal
captures. Never seed funding, payment, ledger or reservation records.
"""

from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from one_many_api.ai_service import fingerprint
from one_many_api.auth import get_current_user, hash_password
from one_many_api.database import get_db
from one_many_api.matching import normalize_area, normalize_asset
from one_many_api.models import Need, NeedIntent, User

demo_router = APIRouter(prefix="/api/v1", tags=["local-demo"])


def _sample_need(
    db: Session, *, owner: User, text: str, area: str,
    asset: str, purpose: str, shareable: bool, opt_in: bool,
    start: int, end: int, model: str,
) -> bool:
    """Create each fixture once per owner, without touching their genuine needs."""
    existing = db.scalar(
        select(Need.id).where(Need.owner_id == owner.id, Need.request_text == text)
    )
    if existing is not None:
        return False
    today = datetime.now(UTC).date()
    need = Need(
        owner_id=owner.id,
        request_text=text,
        location_label=area,
        location_key=normalize_area(area),
        discoverable=opt_in,
        needed_from=today + timedelta(days=start),
        needed_until=today + timedelta(days=end),
        status="open",
    )
    db.add(need)
    db.flush()
    db.add(NeedIntent(
        need_id=need.id,
        asset_type=asset,
        asset_key=normalize_asset(asset),
        purpose=purpose,
        required_features=[],
        excluded_features=[],
        shareable=shareable,
        model_name="demo-fixture",
        source_hash=fingerprint(text, model),
    ))
    return True


@demo_router.post("/demo/seed")
def seed_demo(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, int | str]:
    settings = request.app.state.settings
    if settings.environment != "development":
        raise HTTPException(404, "Demo data is unavailable")
    own = [
        ("[DEMO] I need a pressure washer to clean my driveway this weekend.",
         "Baner, Pune", "pressure washer", "Clean a driveway", True, True, 2, 3),
        ("[DEMO] I need a portable projector for a neighborhood movie night.",
         "Baner, Pune", "portable projector", "Host a movie night", True, True, 5, 6),
        ("[DEMO] I need a power drill to install wall shelves in my apartment.",
         "Hinjawadi, Pune", "power drill", "Install shelving", True, True, 4, 5),
        ("[DEMO] I need disposable paper plates for a house party.",
         "Baner, Pune", "paper plates", "Serve food once", False, False, 8, 8),
    ]
    created_own = 0
    for text, area, asset, purpose, shareable, opt_in, start, end in own:
        created_own += int(_sample_need(
            db, owner=user, text=text, area=area, asset=asset,
            purpose=purpose, shareable=shareable, opt_in=opt_in,
            start=start, end=end, model=settings.gemini_model,
        ))

    # Dedicated inaccessible sample accounts: no password or user details returned.
    # They demonstrate anonymous opt-in matching, not real participants.
    peers = [
        ("[DEMO] Looking for a pressure washer to wash my balcony tiles.",
         "Baner, Pune", "pressure washer", "Wash balcony tiles", 9, 10),
        ("[DEMO] Want a pressure washer to clean the shared courtyard.",
         "Baner, Pune", "pressure washer", "Clean a courtyard", 14, 15),
        ("[DEMO] Need a portable projector for a school presentation.",
         "Baner, Pune", "portable projector", "Show a presentation", 12, 13),
    ]
    created_peer_needs = 0
    for index, (text, area, asset, purpose, start, end) in enumerate(peers, 1):
        email = f"demo-neighbor-{user.id.hex}-{index}@example.invalid"
        neighbor = db.scalar(select(User).where(User.email == email))
        if neighbor is None:
            neighbor = User(
                email=email,
                display_name=f"Fictional Neighbor {index}",
                password_hash=hash_password(token_urlsafe(40)),
            )
            db.add(neighbor)
            db.flush()
        created_peer_needs += int(_sample_need(
            db, owner=neighbor, text=text, area=area, asset=asset,
            purpose=purpose, shareable=True, opt_in=True,
            start=start, end=end, model=settings.gemini_model,
        ))
    db.commit()
    return {
        "created_needs": created_own,
        "created_sample_neighbors": created_peer_needs,
        "message": (
            "Fictional examples added. Match counts are synthetic; "
            "no Gemini calls, catalog offers, funding, reservations or payments were created."
        ),
    }

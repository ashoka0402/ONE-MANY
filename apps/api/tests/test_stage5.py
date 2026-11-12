"""Stage 5: no fabricated reservations; accepted funded members only.

PayPal responses are mocked exclusively in tests. All scheduled dates are
derived from accepted needs, not a hardcoded product calendar.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from one_many_api.ai_service import AIIntent
from one_many_api.channel3 import normalize_product
from one_many_api.config import Settings
from one_many_api.database import get_db
from one_many_api.main import create_app
from one_many_api.models import AssetReservation, Base, FundingGroup, PaymentAttempt

SECRET = "stage-five-test-only-strong-secret-at-least-32-characters"
CATALOG_PRODUCT = {
    "id": "provider-scheduler-projector",
    "title": "Portable meeting projector",
    "offers": [{
        "url": "https://catalog-store.example.com/projector",
        "price": {"currency": "USD", "price": "79.99"},
        "availability": "InStock",
    }],
}


@pytest.fixture
def ctx():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    app = create_app(Settings(
        _env_file=None, environment="test", auth_secret=SECRET,
        channel3_api_key="test-channel3-key",
        paypal_client_id="test-paypal-id",
        paypal_client_secret="test-paypal-secret",
    ))

    def override_db():
        with sessions() as db:
            yield db

    app.app.dependency_overrides[get_db] = override_db
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, sessions
    engine.dispose()


def register(client, label):
    response = client.post("/api/v1/auth/register", json={
        "email": f"stage5-{label}@example.com",
        "display_name": label.title(),
        "password": "not-a-real-password-for-tests-12345",
    })
    assert response.status_code == 201, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def accepted_group(ctx, monkeypatch):
    client, sessions = ctx
    a, b, outsider = [register(client, x) for x in ("organizer", "peer", "other")]
    today = date.today()
    starts = [today + timedelta(days=5), today + timedelta(days=12)]
    ends = [today + timedelta(days=7), today + timedelta(days=14)]
    def extract(text, settings):
        return AIIntent(
            asset_type="portable projector",
            purpose="Display projected presentations",
            required_features=[], excluded_features=[], shareable=True,
        )

    monkeypatch.setattr("one_many_api.discovery_routes.extract_intent", extract)
    ids = []
    for auth, text, start, end in zip(
        (a, b), ("Need a projector for demo presentations", "Need projector for a film club"),
        starts, ends
    ):
        response = client.post("/api/v1/needs", headers=auth, json={
            "request_text": text,
            "location_label": "Baner, Pune",
            "discoverable": True,
            "needed_from": start.isoformat(),
            "needed_until": end.isoformat(),
        })
        assert response.status_code == 201, response.text
        need_id = response.json()["id"]
        ids.append(need_id)
        assert client.post(f"/api/v1/needs/{need_id}/analyze", headers=auth).status_code == 200

    monkeypatch.setattr(
        "one_many_api.catalog_routes.Channel3Client.product",
        lambda self, product, required, excluded:
            normalize_product(CATALOG_PRODUCT, "USD", required, excluded),
    )
    proposal = client.post(
        f"/api/v1/needs/{ids[0]}/proposals",
        headers=a,
        json={"product_id": CATALOG_PRODUCT["id"], "offer_url": CATALOG_PRODUCT["offers"][0]["url"]},
    )
    assert proposal.status_code == 201, proposal.text
    monkeypatch.setattr(
        "one_many_api.funding_routes.Channel3Client.product",
        lambda self, product, required, excluded:
            normalize_product(CATALOG_PRODUCT, "USD", required, excluded),
    )
    opened = client.post(
        f"/api/v1/proposals/{proposal.json()['id']}/funding-group",
        headers=a,
    )
    assert opened.status_code == 201, opened.text
    gid = opened.json()["group"]["id"]
    joined = client.post("/api/v1/funding/join", headers=b, json={
        "invite_code": opened.json()["invite_code"], "need_id": ids[1],
    })
    assert joined.status_code == 200, joined.text
    return client, sessions, (a, b, outsider), ids, gid, starts, ends


def fund_test_group(sessions, gid):
    """A test-only database fixture for confirmed Sandbox capture state."""
    from uuid import UUID
    with sessions.begin() as db:
        group = db.scalar(select(FundingGroup).where(FundingGroup.id == UUID(gid)))
        assert group is not None
        # Read real memberships in the test database instead of faking users.
        from one_many_api.models import FundingMember

        members = db.scalars(
            select(FundingMember).where(FundingMember.group_id == group.id)
            .order_by(FundingMember.slot_index)
        ).all()
        assert len(members) == group.target_members
        for member in members:
            db.add(PaymentAttempt(
                group_id=group.id,
                user_id=member.user_id,
                amount_minor=member.share_minor,
                currency=group.currency,
                state="completed",
                paypal_order_id=f"STAGE5MOCKORDER{member.slot_index}1234567",
                paypal_capture_id=f"STAGE5MOCKCAPTURE{member.slot_index}12345",
            ))
        group.state = "funded"


def test_not_funded_not_authorized_and_invalid_dates(ctx, monkeypatch):
    client, sessions, (a, b, outsider), ids, gid, starts, ends = accepted_group(ctx, monkeypatch)
    uri = f"/api/v1/funding/groups/{gid}/reservation"
    board = client.get(uri + "s", headers=a)
    assert board.status_code == 200
    assert board.json()["bookable"] is False
    assert board.json()["reservations"] == []
    assert client.get(uri + "s", headers=outsider).status_code == 404
    request = {
        "start_date": starts[0].isoformat(),
        "end_date": ends[0].isoformat(),
        "expected_version": 0,
    }
    assert client.put(uri, headers=outsider, json=request).status_code == 404
    assert client.put(uri, headers=a, json=request).status_code == 409
    assert client.put(uri, headers=a, json={**request, "end_date": "1999-01-01"}).status_code == 422
    fund_test_group(sessions, gid)
    assert client.put(
        uri, headers=a, json={**request, "start_date": (starts[0]-timedelta(days=1)).isoformat()}
    ).status_code == 409
    assert client.put(
        uri, headers=a, json={**request, "end_date": (ends[0]+timedelta(days=1)).isoformat()}
    ).status_code == 409
    assert client.put(uri, headers=a, json={**request, "untrusted_amount": 5}).status_code == 422


def test_reservation_lifecycle_versions_anonymity_and_independent_days(ctx, monkeypatch):
    client, sessions, (a, b, outsider), ids, gid, starts, ends = accepted_group(ctx, monkeypatch)
    fund_test_group(sessions, gid)
    url = f"/api/v1/funding/groups/{gid}/reservation"
    first = {
        "start_date": starts[0].isoformat(),
        "end_date": ends[0].isoformat(),
        "expected_version": 0,
    }
    created = client.put(url, headers=a, json=first)
    assert created.status_code == 200, created.text
    mine = created.json()["reservations"][0]
    assert mine["slot"] == 1 and mine["is_you"] is True and mine["version"] == 1
    assert created.json()["bookable"] is True
    duplicate = client.put(url, headers=a, json=first)
    assert duplicate.status_code == 200
    assert duplicate.json()["reservations"][0]["id"] == mine["id"]
    assert duplicate.json()["reservations"][0]["version"] == 1

    changed = client.put(url, headers=a, json={
        **first,
        "end_date": (starts[0] + timedelta(days=1)).isoformat(),
        "expected_version": 1,
    })
    assert changed.status_code == 200, changed.text
    assert changed.json()["reservations"][0]["version"] == 2
    assert client.put(url, headers=a, json={
        **first, "expected_version": 1,
    }).status_code == 409

    peer = client.put(url, headers=b, json={
        "start_date": starts[1].isoformat(), "end_date": ends[1].isoformat(),
        "expected_version": 0,
    })
    assert peer.status_code == 200, peer.text
    assert len(peer.json()["reservations"]) == 2
    assert sorted(x["slot"] for x in peer.json()["reservations"]) == [1, 2]
    assert "stage5-organizer@example.com" not in peer.text
    assert "stage5-peer@example.com" not in peer.text
    assert "Need a projector" not in peer.text
    assert all("user_id" not in x for x in peer.json()["reservations"])

    cancelled = client.delete(url, headers=a)
    assert cancelled.status_code == 200
    assert len(cancelled.json()["reservations"]) == 1
    assert client.delete(url, headers=a).status_code == 200
    restarted = client.put(url, headers=a, json={**first, "expected_version": 3})
    assert restarted.status_code == 200
    assert next(x for x in restarted.json()["reservations"] if x["is_you"])["version"] == 4


def test_existing_conflict_rejected_and_reversal_blocks_changes(ctx, monkeypatch):
    client, sessions, (a, b, outsider), ids, gid, starts, ends = accepted_group(ctx, monkeypatch)
    fund_test_group(sessions, gid)
    url = f"/api/v1/funding/groups/{gid}/reservation"
    # Insert a corrupt cross-member reservation in the test DB only to exercise
    # the API-level overlap guard in addition to PostgreSQL's independent GiST check.
    from uuid import UUID
    from one_many_api.models import FundingMember

    with sessions.begin() as db:
        peer = db.scalar(select(FundingMember).where(
            FundingMember.group_id == UUID(gid),
            FundingMember.slot_index == 1,
        ))
        db.add(AssetReservation(
            group_id=UUID(gid), user_id=peer.user_id, need_id=peer.need_id,
            start_date=starts[0], end_date=starts[0],
            status="active", version=1,
        ))
    conflict = client.put(url, headers=a, json={
        "start_date": starts[0].isoformat(), "end_date": ends[0].isoformat(),
        "expected_version": 0,
    })
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "conflict"

    with sessions.begin() as db:
        group = db.get(FundingGroup, UUID(gid))
        group.state = "needs_review"
    assert client.get(url + "s", headers=a).json()["bookable"] is False
    assert client.put(url, headers=a, json={
        "start_date": starts[0].isoformat(), "end_date": ends[0].isoformat(),
        "expected_version": 0,
    }).status_code == 409
    # Cleanup is allowed despite a payment reversal (but never fabricates a capture).
    assert client.delete(url, headers=b).status_code == 200


def test_absent_group_never_leaks_reservations(ctx):
    client, _ = ctx
    auth = register(client, "unknown")
    target = "f3a186a9-62a1-4e5e-9683-61974e32a517"
    assert client.get(
        f"/api/v1/funding/groups/{target}/reservations", headers=auth,
    ).status_code == 404

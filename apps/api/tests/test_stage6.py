"""Stage 6 read-only ledgers, anonymized snapshot, and append-only audit tests.

The captures are deterministic fixtures INSIDE tests, never production PayPal
responses. Database states are intentionally exercised without live credentials.
"""
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from one_many_api.config import Settings
from one_many_api.database import get_db
from one_many_api.funding_routes import _mark_captured
from one_many_api.main import create_app
from one_many_api.models import (
    Base,
    FundingGroup,
    FundingLedgerEvent,
    FundingMember,
    Need,
    PaymentAttempt,
    PurchaseProposal,
    User,
)
from one_many_api.paypal import PayPalSandboxClient

SECRET = "stage-six-test-only-api-auth-secret-at-least-32-chars"


@pytest.fixture
def context():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    app = create_app(Settings(_env_file=None, environment="test", auth_secret=SECRET))

    def override_db():
        with sessions() as db:
            yield db

    app.app.dependency_overrides[get_db] = override_db
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, sessions
    engine.dispose()


def signup(client, name):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"stage6-{name}@example.com",
            "display_name": name.title(),
            "password": "not-a-real-stored-user-password-1234",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def group_fixture(context):
    """Real persisted ownership rows, but no provider traffic or made-up UI data."""
    client, sessions = context
    owner, peer, outsider = (
        signup(client, "owner"),
        signup(client, "peer"),
        signup(client, "outsider"),
    )
    now = datetime.now(UTC)
    with sessions.begin() as db:
        people = {
            user.email: user
            for user in db.scalars(select(User)).all()
        }
        owner_id = people["stage6-owner@example.com"].id
        peer_id = people["stage6-peer@example.com"].id
        needs = []
        for i, uid in enumerate((owner_id, peer_id)):
            need = Need(
                owner_id=uid,
                request_text=f"Test need of member {i + 1}",
                status="open",
                discoverable=True,
                location_label="Pune",
                location_key="pune",
                needed_from=date(2026, 12, 1 + i * 3),
                needed_until=date(2026, 12, 2 + i * 3),
            )
            db.add(need)
            db.flush()
            needs.append(need)
        proposal = PurchaseProposal(
            owner_id=owner_id,
            need_id=needs[0].id,
            need_source_hash="0" * 64,
            channel3_product_id="fixture-only-item",
            product_title="Test-only durable drill",
            merchant_domain="store.example.com",
            merchant_url="https://store.example.com/test-item",
            currency="USD",
            price_minor=9001,
            prospective_members=2,
            share_amounts_minor=[4501, 4500],
            status="draft",
            quote_expires_at=now + timedelta(minutes=25),
        )
        db.add(proposal)
        db.flush()
        group = FundingGroup(
            proposal_id=proposal.id,
            owner_id=owner_id,
            invitation_hash="a" * 64,
            total_minor=9001,
            currency="USD",
            target_members=2,
            state="funding",
            expires_at=now + timedelta(hours=4),
        )
        db.add(group)
        db.flush()
        gid = group.id
        for i, (user_id, need) in enumerate(zip((owner_id, peer_id), needs)):
            db.add(FundingMember(
                group_id=group.id, user_id=user_id, need_id=need.id,
                slot_index=i, share_minor=[4501, 4500][i],
            ))
        attempt = PaymentAttempt(
            group_id=group.id,
            user_id=owner_id,
            amount_minor=4501,
            currency="USD",
            state="awaiting_approval",
            paypal_order_id="STAGE6TESTORDER12345",
            approval_url="https://www.sandbox.paypal.com/checkoutnow?token=fixture-only",
        )
        db.add(attempt)
    return client, sessions, owner, peer, outsider, gid


def ledger_path(group_id):
    return f"/api/v1/funding/groups/{group_id}/ledger"


def test_member_only_anonymized_read_without_side_effects(context, monkeypatch):
    client, sessions, owner, peer, outsider, gid = group_fixture(context)

    def fail_network(*args, **kwargs):
        raise AssertionError("Ledger GET must never call PayPal")

    monkeypatch.setattr(PayPalSandboxClient, "_call", fail_network)
    assert client.get(ledger_path(gid)).status_code == 401
    assert client.get(ledger_path(gid), headers=outsider).status_code == 404
    response = client.get(ledger_path(gid), headers=peer)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["currency"] == "USD"
    assert result["total_minor"] == 9001
    assert result["total_display"] == "$90.01"
    assert result["captured_minor"] == 0
    assert result["outstanding_minor"] == 9001
    assert result["progress_percent"] == 0
    assert result["accepted_members"] == 2
    assert result["verified_members"] == 0
    assert result["reconciliation"] == "in_progress"
    assert [row["slot"] for row in result["members"]] == [1, 2]
    assert [row["payment_state"] for row in result["members"]] == [
        "awaiting_approval", "not_started",
    ]
    assert [row["is_you"] for row in result["members"]] == [False, True]
    assert result["events"] == []
    assert "audit events begin" in result["notice"].lower()
    forbidden = [
        "stage6-owner@example.com", "stage6-peer@example.com",
        "STAGE6TESTORDER12345", "paypal_order_id", "password_hash",
        "user_id", "approval_url", "merchant_url", "request_text",
    ]
    for secret in forbidden:
        assert secret not in response.text
    # Repeated GET does not change audit history or payment state.
    assert client.get(ledger_path(gid), headers=owner).status_code == 200
    with sessions() as db:
        assert db.scalar(select(func.count(FundingLedgerEvent.id))) == 0
        attempt = db.scalar(select(PaymentAttempt).where(PaymentAttempt.group_id == gid))
        assert attempt.state == "awaiting_approval"


def test_unverified_or_inconsistent_captures_never_count(context):
    client, sessions, owner, peer, outsider, gid = group_fixture(context)
    with sessions.begin() as db:
        group = db.get(FundingGroup, gid)
        group.state = "funded"
        attempt = db.scalar(select(PaymentAttempt).where(PaymentAttempt.group_id == gid))
        attempt.state = "completed"
        attempt.paypal_capture_id = None
    result = client.get(ledger_path(gid), headers=owner)
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["captured_minor"] == 0
    assert body["progress_percent"] == 0
    assert body["reconciliation"] == "requires_review"
    with sessions.begin() as db:
        attempt = db.scalar(select(PaymentAttempt).where(PaymentAttempt.group_id == gid))
        attempt.paypal_capture_id = "TESTCAPTUREFORWRONGAMOUNT"
        attempt.amount_minor = 1
    body = client.get(ledger_path(gid), headers=owner).json()
    assert body["captured_minor"] == 0
    assert body["reconciliation"] == "requires_review"


def test_capture_audit_idempotency_and_fully_funded_snapshot(context):
    client, sessions, owner, peer, outsider, gid = group_fixture(context)
    with sessions() as db:
        group = db.get(FundingGroup, gid)
        a = db.scalar(select(PaymentAttempt).where(PaymentAttempt.group_id == gid))
        _mark_captured(db, group, a, "STAGE6VERIFIEDCAPTUREA123")
        _mark_captured(db, group, a, "STAGE6VERIFIEDCAPTUREA123")
        member = db.scalar(select(FundingMember).where(
            FundingMember.group_id == gid,
            FundingMember.slot_index == 1,
        ))
        second = PaymentAttempt(
            group_id=gid,
            user_id=member.user_id,
            amount_minor=4500,
            currency="USD",
            state="capture_pending",
            paypal_order_id="STAGE6TESTORDERB12345",
        )
        db.add(second)
        db.commit()
        db.refresh(second)
        _mark_captured(db, group, second, "STAGE6VERIFIEDCAPTUREB123")
    response = client.get(ledger_path(gid), headers=peer)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["captured_minor"] == 9001
    assert body["outstanding_minor"] == 0
    assert body["progress_percent"] == 100
    assert body["verified_members"] == 2
    assert body["group_state"] == "funded"
    assert body["reconciliation"] == "reconciled"
    assert len(body["events"]) == 2
    assert all(item["event_type"] == "capture_verified" for item in body["events"])
    assert all(item["source"] == "application" for item in body["events"])
    assert all(item["member_slot"] in (1, 2) for item in body["events"])
    assert "STAGE6VERIFIEDCAPTUREA123" not in response.text


def test_signed_refund_event_logged_once_and_excluded(context, monkeypatch):
    client, sessions, owner, peer, outsider, gid = group_fixture(context)
    with sessions() as db:
        group = db.get(FundingGroup, gid)
        attempt = db.scalar(select(PaymentAttempt).where(PaymentAttempt.group_id == gid))
        _mark_captured(db, group, attempt, "STAGE6CAPTURE789")
    monkeypatch.setattr(
        PayPalSandboxClient, "verify_webhook",
        lambda self, headers, event: True,
    )
    event = {
        "id": "STAGE6REFUNDEVENT1",
        "event_type": "PAYMENT.CAPTURE.REFUNDED",
        "resource": {
            "id": "STAGE6CAPTURE789",
            "supplementary_data": {
                "related_ids": {"order_id": "STAGE6TESTORDER12345"}
            },
        },
    }
    assert client.post("/api/v1/paypal/webhook", json=event).status_code == 200
    repeated = client.post("/api/v1/paypal/webhook", json=event)
    assert repeated.status_code == 200
    assert repeated.json()["duplicate"] is True
    response = client.get(ledger_path(gid), headers=peer)
    assert response.status_code == 200
    body = response.json()
    assert body["captured_minor"] == 0
    assert body["group_state"] == "needs_review"
    assert body["reconciliation"] == "requires_review"
    assert body["members"][0]["payment_state"] == "reversed"
    assert len(body["events"]) == 2
    assert {entry["event_type"] for entry in body["events"]} == {
        "capture_verified", "refund_reported",
    }
    assert next(
        event for event in body["events"] if event["event_type"] == "refund_reported"
    )["source"] == "paypal_verified"
    assert "STAGE6REFUNDEVENT1" not in response.text


def test_unknown_group_is_not_exposed(context):
    client, sessions = context
    person = signup(client, "unrelated")
    missing = uuid4()
    assert client.get(ledger_path(missing), headers=person).status_code == 404

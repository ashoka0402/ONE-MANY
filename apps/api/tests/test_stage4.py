"""Stage 4: sandbox PayPal contract, explicit consent, strict reconciliation.

Network/provider responses below are test fixtures only. Production never fakes a capture.
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from one_many_api.ai_service import AIIntent
from one_many_api.channel3 import normalize_product
from one_many_api.config import Settings
from one_many_api.database import get_db
from one_many_api.main import create_app
from one_many_api.models import Base
from one_many_api.paypal import (
    PayPalInvalid,
    PayPalSandboxClient,
    amount_string,
    approval_link,
    verify_order,
)

TEST_SECRET = "stage-four-test-credentials-not-real-012345678901"
OFFER = "https://shop.example.test/power-drill"
ITEM = {
    "id": "c3-drill-304",
    "title": "Rechargeable Power Drill",
    "description": "Battery-operated power drill for home projects",
    "key_features": ["Battery", "Cordless"],
    "structured_attributes": {"power": ["battery"]},
    "offers": [
        {
            "url": OFFER,
            "domain": "shop.example.test",
            "price": {"currency": "USD", "price": "90.01"},
            "availability": "InStock",
        }
    ],
}


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    app = create_app(
        Settings(
            _env_file=None,
            environment="test",
            auth_secret=TEST_SECRET,
            channel3_api_key="test-channel3-key",
            paypal_client_id="sandbox-client-test",
            paypal_client_secret="sandbox-secret-test",
            paypal_webhook_id="sandbox-hook-test",
        )
    )

    def override_db():
        with sessions() as session:
            yield session

    app.app.dependency_overrides[get_db] = override_db
    with TestClient(app, raise_server_exceptions=False) as http:
        yield http
    engine.dispose()


def account(client, name):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": name + "@example.test",
            "display_name": "Stage Four Member",
            "password": "long-and-unique-test-password",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def create_need(client, auth, description, *, area="Downtown, Pune", start, end, opt=True):
    response = client.post(
        "/api/v1/needs",
        headers=auth,
        json={
            "request_text": description,
            "location_label": area,
            "needed_from": start,
            "needed_until": end,
            "discoverable": opt,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def prepare(client, monkeypatch):
    def extracted(text, settings):
        return AIIntent(
            asset_type="power drill",
            purpose="DIY fixes",
            required_features=["battery"],
            excluded_features=[],
            shareable=True,
        )

    monkeypatch.setattr("one_many_api.discovery_routes.extract_intent", extracted)
    a, b, outsider = (
        account(client, "checkout-owner"),
        account(client, "checkout-peer"),
        account(client, "checkout-stranger"),
    )
    owner_need = create_need(
        client,
        a,
        "Need a drill for my weekend DIY shelves",
        start="2026-11-15",
        end="2026-11-16",
    )
    peer_need = create_need(
        client,
        b,
        "Need a drill to hang curtain rods",
        start="2026-11-20",
        end="2026-11-21",
    )
    for auth, need_id in [(a, owner_need), (b, peer_need)]:
        response = client.post(f"/api/v1/needs/{need_id}/analyze", headers=auth)
        assert response.status_code == 200, response.text

    with patch("one_many_api.catalog_routes.Channel3Client.product") as product:
        product.return_value = normalize_product(ITEM, "USD", ["battery"], [])
        draft = client.post(
            f"/api/v1/needs/{owner_need}/proposals",
            headers=a,
            json={"product_id": ITEM["id"], "offer_url": OFFER},
        )
    assert draft.status_code == 201, draft.text
    draft_id = draft.json()["id"]
    with patch("one_many_api.funding_routes.Channel3Client.product") as item:
        item.return_value = normalize_product(ITEM, "USD", ["battery"], [])
        created = client.post(
            f"/api/v1/proposals/{draft_id}/funding-group",
            headers=a,
        )
    assert created.status_code == 201, created.text
    return a, b, outsider, owner_need, peer_need, created.json()


def joined(client, monkeypatch):
    a, b, outsider, own, peer, created = prepare(client, monkeypatch)
    group_id = created["group"]["id"]
    response = client.post(
        "/api/v1/funding/join",
        headers=b,
        json={"invite_code": created["invite_code"], "need_id": peer},
    )
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "funding"
    return a, b, outsider, own, peer, group_id, created


def paypal_order(group_id, attempt_id, amount, *, state, currency="USD", capture="CAPTURE9876"):
    payment = (
        {
            "captures": [
                {
                    "id": capture,
                    "status": "COMPLETED",
                    "amount": {"value": amount, "currency_code": currency},
                }
            ]
        }
        if state == "COMPLETED"
        else {}
    )
    return {
        "id": "TESTPAYPALORDER123",
        "status": state,
        "purchase_units": [
            {
                "reference_id": group_id,
                "custom_id": attempt_id,
                "amount": {"currency_code": currency, "value": amount},
                "payments": payment,
            }
        ],
    }


def test_paypal_amounts_and_capture_validation():
    assert amount_string(9001, "USD") == "90.01"
    assert amount_string(600, "JPY") == "600"
    with pytest.raises(PayPalInvalid):
        amount_string(9001, "INR")
    with pytest.raises(PayPalInvalid):
        approval_link({"links": [{"rel": "approve", "href": "https://evil.example/capture"}]})
    assert (
        approval_link(
            {
                "links": [
                    {
                        "rel": "approve",
                        "href": "https://www.sandbox.paypal.com/checkoutnow?token=test",
                    }
                ]
            }
        )
        == "https://www.sandbox.paypal.com/checkoutnow?token=test"
    )

    order = paypal_order("g", "a", "45.01", state="COMPLETED")
    assert verify_order(
        order,
        order_id="TESTPAYPALORDER123",
        reference_id="g",
        custom_id="a",
        amount_minor=4501,
        currency="USD",
    ) == ("COMPLETED", "CAPTURE9876")
    with pytest.raises(PayPalInvalid, match="amount"):
        verify_order(
            order,
            order_id="TESTPAYPALORDER123",
            reference_id="g",
            custom_id="a",
            amount_minor=4500,
            currency="USD",
        )
    with pytest.raises(PayPalInvalid, match="reference"):
        verify_order(
            order,
            order_id="TESTPAYPALORDER123",
            reference_id="wrong",
            custom_id="a",
            amount_minor=4501,
            currency="USD",
        )
    with pytest.raises(PayPalInvalid, match="payee"):
        verify_order(
            order,
            order_id="TESTPAYPALORDER123",
            reference_id="g",
            custom_id="a",
            amount_minor=4501,
            currency="USD",
            merchant_id="expected-payee",
        )


def test_paypal_http_endpoints_idempotency_and_sandbox_only(monkeypatch):
    called = []

    def token_post(url, *, data, auth, headers, timeout, follow_redirects):
        called.append(("token", url))
        return httpx.Response(
            200, request=httpx.Request("POST", url), json={"access_token": "test-access"}
        )

    def api_request(method, url, *, headers, json, timeout, follow_redirects):
        called.append((method, url, headers.get("PayPal-Request-Id"), json))
        if method == "POST" and url.endswith("/v2/checkout/orders"):
            return httpx.Response(
                201,
                request=httpx.Request(method, url),
                json={
                    "id": "TESTPAYPALORDER123",
                    "status": "CREATED",
                    "links": [
                        {
                            "rel": "approve",
                            "href": "https://www.sandbox.paypal.com/checkoutnow?token=TESTPAYPALORDER123",
                        }
                    ],
                },
            )
        return httpx.Response(
            200,
            request=httpx.Request(method, url),
            json=paypal_order("g", "a", "45.01", state="APPROVED"),
        )

    monkeypatch.setattr("one_many_api.paypal.httpx.post", token_post)
    monkeypatch.setattr("one_many_api.paypal.httpx.request", api_request)
    settings = Settings(
        _env_file=None,
        paypal_client_id="test-id",
        paypal_client_secret="test-secret",
        public_web_url="http://localhost:3000",
    )
    adapter = PayPalSandboxClient(settings)
    order_id, url = adapter.create_order(
        group_id="g",
        attempt_id="a",
        amount_minor=4501,
        currency="USD",
        description="Drill",
        request_id="unique-create-attempt",
    )
    assert order_id == "TESTPAYPALORDER123"
    assert url.startswith("https://www.sandbox.paypal.com/")
    assert called[1][2] == "unique-create-attempt"
    assert called[1][3]["purchase_units"][0]["amount"]["value"] == "45.01"
    assert called[1][3]["payment_source"]["paypal"]["experience_context"]["return_url"] == (
        "http://localhost:3000/app?paypal_group=g"
    )
    assert all("sandbox.paypal.com" in call[1] for call in called)
    adapter.capture(order_id, request_id="unique-capture-attempt")
    assert called[-1][2] == "unique-capture-attempt"


def test_requires_explicit_acceptance_and_owner_access(client, monkeypatch):
    a, b, outsider, owner_need, peer_need, created = prepare(client, monkeypatch)
    gid = created["group"]["id"]
    assert created["group"]["state"] == "recruiting"
    assert created["group"]["accepted_count"] == 1
    assert client.get(f"/api/v1/funding/groups/{gid}", headers=outsider).status_code == 404
    assert client.post(f"/api/v1/funding/groups/{gid}/paypal-order", headers=a).status_code == 409

    wrong = create_need(
        client,
        outsider,
        "Need a drill for a local library",
        area="Another city",
        start="2026-11-23",
        end="2026-11-24",
    )
    analyzed = client.post(f"/api/v1/needs/{wrong}/analyze", headers=outsider)
    assert analyzed.status_code == 200, analyzed.text
    rejected = client.post(
        "/api/v1/funding/join",
        headers=outsider,
        json={"invite_code": created["invite_code"], "need_id": wrong},
    )
    assert rejected.status_code == 409
    unknown = client.post(
        "/api/v1/funding/join",
        headers=b,
        json={"invite_code": "invalid-code-for-another-fake-group", "need_id": peer_need},
    )
    assert unknown.status_code == 404
    joined = client.post(
        "/api/v1/funding/join",
        headers=b,
        json={"invite_code": created["invite_code"], "need_id": peer_need},
    )
    assert joined.status_code == 200
    assert joined.json()["state"] == "funding"
    assert joined.json()["members"][0]["payment_state"] == "not_started"
    assert joined.json()["members"][1]["payment_state"] == "not_started"
    assert "checkout-peer@example.test" not in joined.text
    assert client.get("/api/v1/funding/groups", headers=b).json()["groups"][0]["id"] == gid


def test_order_capture_reconciliation_and_complete_group(client, monkeypatch):
    a, b, outsider, own, peer, gid, created = joined(client, monkeypatch)
    records: dict[str, tuple[str, str, str, str]] = {}
    completed: set[str] = set()
    creation_requests: list[str] = []
    captures: list[str] = []

    def create_provider(
        self, *, group_id, attempt_id, amount_minor, currency, description, request_id
    ):
        order_id = "ORDER" + attempt_id.replace("-", "")[:22]
        records[order_id] = (group_id, attempt_id, f"{amount_minor / 100:.2f}", currency)
        creation_requests.append(request_id)
        return order_id, "https://www.sandbox.paypal.com/checkoutnow?token=" + order_id

    def retrieve(self, order_id):
        group_id, attempt_id, value, currency = records[order_id]
        state = "COMPLETED" if order_id in completed else "APPROVED"
        order = paypal_order(
            group_id,
            attempt_id,
            value,
            state=state,
            currency=currency,
            capture="CAP" + order_id,
        )
        order["id"] = order_id
        return order

    def capture_provider(self, order_id, request_id):
        completed.add(order_id)
        captures.append(request_id)
        return {"id": order_id, "status": "COMPLETED"}

    monkeypatch.setattr(
        "one_many_api.funding_routes.Channel3Client.product",
        lambda self, pid, req, excl: normalize_product(ITEM, "USD", req, excl),
    )
    monkeypatch.setattr(PayPalSandboxClient, "create_order", create_provider)
    monkeypatch.setattr(PayPalSandboxClient, "get_order", retrieve)
    monkeypatch.setattr(PayPalSandboxClient, "capture", capture_provider)

    first = client.post(f"/api/v1/funding/groups/{gid}/paypal-order", headers=a)
    assert first.status_code == 200, first.text
    duplicated = client.post(f"/api/v1/funding/groups/{gid}/paypal-order", headers=a)
    assert duplicated.status_code == 200
    assert duplicated.json()["paypal_order_id"] == first.json()["paypal_order_id"]
    assert len(creation_requests) == 1
    first_capture = client.post(f"/api/v1/funding/groups/{gid}/paypal-capture", headers=a)
    assert first_capture.status_code == 200, first_capture.text
    assert first_capture.json()["captured_minor"] == 4501
    assert first_capture.json()["state"] == "funding"
    assert len(captures) == 1

    repeated = client.post(f"/api/v1/funding/groups/{gid}/paypal-capture", headers=a)
    assert repeated.status_code == 200
    assert repeated.json()["captured_minor"] == 4501
    assert len(captures) == 1

    second = client.post(f"/api/v1/funding/groups/{gid}/paypal-order", headers=b)
    assert second.status_code == 200
    assert second.json()["amount_minor"] == 4500
    last = client.post(f"/api/v1/funding/groups/{gid}/paypal-capture", headers=b)
    assert last.status_code == 200, last.text
    assert last.json()["state"] == "funded"
    assert last.json()["captured_minor"] == 9001
    assert last.json()["accepted_count"] == 2
    assert (
        client.post(
            f"/api/v1/funding/groups/{gid}/paypal-order",
            headers=b,
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/v1/funding/groups/{gid}/paypal-capture",
            headers=outsider,
        ).status_code
        == 404
    )


def test_mismatched_capture_does_not_count_as_paid(client, monkeypatch):
    a, b, outsider, own, peer, gid, created = joined(client, monkeypatch)
    monkeypatch.setattr(
        "one_many_api.funding_routes.Channel3Client.product",
        lambda self, pid, req, excl: normalize_product(ITEM, "USD", req, excl),
    )
    monkeypatch.setattr(
        PayPalSandboxClient,
        "create_order",
        lambda self, **kwargs: ("TESTPAYPALORDER123", "https://www.sandbox.paypal.com/checkoutnow"),
    )
    created_order = client.post(f"/api/v1/funding/groups/{gid}/paypal-order", headers=a)
    assert created_order.status_code == 200

    def fraudulent(self, order_id):
        group = client.get(f"/api/v1/funding/groups/{gid}", headers=a).json()
        # Simulate an approval/order claiming an incorrect payment amount.
        return paypal_order(gid, "not-the-requested-attempt", "0.01", state="COMPLETED")

    monkeypatch.setattr(PayPalSandboxClient, "get_order", fraudulent)
    refused = client.post(f"/api/v1/funding/groups/{gid}/paypal-capture", headers=a)
    assert refused.status_code == 409, refused.text
    row = client.get(f"/api/v1/funding/groups/{gid}", headers=a).json()
    assert row["captured_minor"] == 0
    assert row["state"] == "needs_review"


def test_verified_webhook_replay_and_refund_never_auto_refunds(client, monkeypatch):
    a, b, _, own, peer, gid, created = joined(client, monkeypatch)
    monkeypatch.setattr(
        "one_many_api.funding_routes.Channel3Client.product",
        lambda self, pid, req, excl: normalize_product(ITEM, "USD", req, excl),
    )
    saved = {}

    def created_order(
        self, *, group_id, attempt_id, amount_minor, currency, description, request_id
    ):
        saved["id"] = attempt_id
        saved["amount"] = f"{amount_minor / 100:.2f}"
        return "TESTPAYPALORDER123", "https://www.sandbox.paypal.com/checkoutnow"

    monkeypatch.setattr(PayPalSandboxClient, "create_order", created_order)
    assert client.post(f"/api/v1/funding/groups/{gid}/paypal-order", headers=a).status_code == 200

    monkeypatch.setattr(PayPalSandboxClient, "verify_webhook", lambda self, headers, event: False)
    event = {
        "id": "EVT-TEST-123",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "CAPTURE9876",
            "supplementary_data": {"related_ids": {"order_id": "TESTPAYPALORDER123"}},
        },
    }
    assert client.post("/api/v1/paypal/webhook", json=event).status_code == 401
    assert client.get(f"/api/v1/funding/groups/{gid}", headers=a).json()["captured_minor"] == 0

    monkeypatch.setattr(PayPalSandboxClient, "verify_webhook", lambda self, headers, event: True)
    monkeypatch.setattr(
        PayPalSandboxClient,
        "get_order",
        lambda self, order_id: paypal_order(gid, saved["id"], saved["amount"], state="COMPLETED"),
    )
    success = client.post("/api/v1/paypal/webhook", json=event)
    assert success.status_code == 200, success.text
    assert success.json()["duplicate"] is False
    again = client.post("/api/v1/paypal/webhook", json=event)
    assert again.status_code == 200
    assert again.json()["duplicate"] is True
    assert client.get(f"/api/v1/funding/groups/{gid}", headers=a).json()["captured_minor"] == 4501

    refunded = {
        "id": "EVT-TEST-REFUNDED",
        "event_type": "PAYMENT.CAPTURE.REFUNDED",
        "resource": event["resource"],
    }
    resp = client.post("/api/v1/paypal/webhook", json=refunded)
    assert resp.status_code == 200, resp.text
    final = client.get(f"/api/v1/funding/groups/{gid}", headers=a).json()
    assert final["captured_minor"] == 0
    assert final["state"] == "needs_review"
    assert final["members"][0]["payment_state"] == "reversed"


def test_consents_can_block_payments_after_join(client, monkeypatch):
    a, b, _, own, peer, gid, created = joined(client, monkeypatch)
    assert (
        client.patch(
            f"/api/v1/needs/{peer}",
            headers=b,
            json={
                "discoverable": False,
            },
        ).status_code
        == 200
    )
    blocked = client.post(f"/api/v1/funding/groups/{gid}/paypal-order", headers=a)
    assert blocked.status_code == 409
    assert client.get(f"/api/v1/funding/groups/{gid}", headers=a).json()["captured_minor"] == 0

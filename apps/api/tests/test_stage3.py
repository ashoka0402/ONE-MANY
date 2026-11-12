"""Stage 3 provider contracts and financial math use isolated test fixtures only."""

from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from one_many_api.ai_service import AIIntent
from one_many_api.channel3 import (
    CatalogMalformed,
    CatalogUnavailable,
    Channel3Client,
    normalize_product,
    price_to_minor,
)
from one_many_api.config import Settings
from one_many_api.database import get_db
from one_many_api.main import create_app
from one_many_api.models import Base
from one_many_api.pricing import equal_shares

TEST_SECRET = "stage-3-test-only-secret-at-least-32-characters"
ITEM_URL = "https://example-retailer.test/cordless-drill"
PRODUCT = {
    "id": "provider-drill-42",
    "title": "Professional Cordless Drill",
    "brands": [{"id": "brand1", "name": "Tool Company"}],
    "description": "A cordless drill with battery and charger",
    "images": [{"url": "https://images.example.test/drill.png"}],
    "key_features": ["Battery-powered", "Variable speed"],
    "structured_attributes": {"power": ["battery"]},
    "offers": [
        {
            "url": ITEM_URL,
            "domain": "example-retailer.test",
            "price": {"price": 90.01, "currency": "USD"},
            "availability": "InStock",
        },
        {
            "url": "https://other-retailer.test/drill",
            "domain": "other-retailer.test",
            "price": {"price": 95, "currency": "USD"},
            "availability": "OutOfStock",
        },
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
            channel3_api_key="provider-key-for-tests-only",
        )
    )

    def db_override():
        with sessions() as db:
            yield db

    app.app.dependency_overrides[get_db] = db_override
    with TestClient(app, raise_server_exceptions=False) as http:
        yield http
    engine.dispose()


def member(client, email):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": "Test Member",
            "password": "long-password-not-a-real-secret",
        },
    )
    assert resp.status_code == 201, resp.text
    return {"Authorization": "Bearer " + resp.json()["access_token"]}


def prepare_need(client, auth, text, start, end):
    res = client.post(
        "/api/v1/needs",
        headers=auth,
        json={
            "request_text": text,
            "location_label": "Downtown, Pune",
            "discoverable": True,
            "needed_from": start,
            "needed_until": end,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def prepare_group(client, monkeypatch):
    def gemini_fixture(text, settings):
        return AIIntent(
            asset_type="cordless drill",
            purpose="Home repairs",
            required_features=["battery"],
            excluded_features=[],
            shareable=True,
        )

    monkeypatch.setattr("one_many_api.discovery_routes.extract_intent", gemini_fixture)
    a, b = member(client, "stage3-a@example.com"), member(client, "stage3-b@example.com")
    own = prepare_need(
        client,
        a,
        "Need a cordless drill to install shelves",
        "2026-11-14",
        "2026-11-15",
    )
    peer = prepare_need(
        client,
        b,
        "Need a cordless drill to attach curtain rods",
        "2026-11-20",
        "2026-11-21",
    )
    for authorization, identifier in [(a, own), (b, peer)]:
        analyzed = client.post(f"/api/v1/needs/{identifier}/analyze", headers=authorization)
        assert analyzed.status_code == 200, analyzed.text
    return a, b, own, peer


def test_money_is_minor_units_and_remainders_are_conserved():
    assert price_to_minor("90.01", "USD") == 9001
    assert price_to_minor(99, "USD") == 9900
    assert price_to_minor(100, "JPY") == 100
    assert equal_shares(9001, 2) == [4501, 4500]
    assert equal_shares(100, 3) == [34, 33, 33]
    assert sum(equal_shares(9001, 7)) == 9001
    with pytest.raises(ValueError):
        price_to_minor("1.005", "USD")
    with pytest.raises(ValueError):
        price_to_minor(Decimal("-10"), "USD")
    with pytest.raises(ValueError):
        price_to_minor("10", "XYZ")
    with pytest.raises(ValueError):
        equal_shares(1, 2)


def test_provider_offer_and_feature_validation():
    product = normalize_product(PRODUCT, "USD", ["battery"], [])
    assert product.id == PRODUCT["id"]
    assert product.suitability == "candidate"
    assert len(product.offers) == 1
    assert product.offers[0].price_minor == 9001
    assert product.brand == "Tool Company"
    assert normalize_product(PRODUCT, "USD", ["corded"], []).suitability == "manual_review"
    assert normalize_product(PRODUCT, "USD", [], ["battery"]).suitability == "blocked"
    without_url = {**PRODUCT, "offers": [{**PRODUCT["offers"][0], "url": "http://unsafe.test"}]}
    assert not normalize_product(without_url, "USD", [], []).offers
    with pytest.raises(CatalogMalformed):
        normalize_product({"title": "No product ID"}, "USD", [], [])


def test_http_contract_search_and_product_recheck(monkeypatch):
    calls = []

    def fake_http(method, url, *, headers, json, timeout, follow_redirects):
        calls.append((method, url, headers, json, follow_redirects))
        payload = {"products": [PRODUCT], "next_page_token": None} if method == "POST" else PRODUCT
        return httpx.Response(200, json=payload, request=httpx.Request(method, url))

    monkeypatch.setattr("one_many_api.channel3.httpx.request", fake_http)
    settings = Settings(_env_file=None, channel3_api_key="test-only")
    client = Channel3Client(settings)
    results = client.search("cordless drill", ["battery"], [])
    assert results.products[0].offers[0].price_display == "$90.01"
    assert calls[0][0] == "POST"
    assert calls[0][1].endswith("/v1/search")
    assert calls[0][2]["x-api-key"] == "test-only"
    assert calls[0][3]["query"] == "cordless drill battery"
    assert calls[0][3]["config"]["country"] == "US"
    assert calls[0][3]["config"]["currency"] == "USD"
    assert calls[0][4] is False

    detail = client.product(PRODUCT["id"], ["battery"], [])
    assert detail.id == PRODUCT["id"]
    assert calls[1][0] == "GET"
    assert "/v1/products/provider-drill-42" in calls[1][1]


def test_missing_or_failed_api_key_never_returns_fake_items(monkeypatch):
    with pytest.raises(CatalogUnavailable, match="not configured"):
        Channel3Client(Settings(_env_file=None, channel3_api_key=None)).search("drill", [], [])

    def blocked(method, url, *, headers, json, timeout, follow_redirects):
        return httpx.Response(401, request=httpx.Request(method, url), json={})

    monkeypatch.setattr("one_many_api.channel3.httpx.request", blocked)
    with pytest.raises(CatalogUnavailable, match="rejected"):
        Channel3Client(Settings(_env_file=None, channel3_api_key="wrong")).search("drill", [], [])


def test_real_workflow_contract_with_fake_provider_only_in_test(client, monkeypatch):
    a, b, own, peer = prepare_group(client, monkeypatch)
    assert client.get(f"/api/v1/needs/{own}/matches", headers=a).json()["potential_members"] == 1

    calls = []

    def fake_http(method, url, *, headers, json, timeout, follow_redirects):
        calls.append((method, url))
        payload = {"products": [PRODUCT]} if method == "POST" else PRODUCT
        return httpx.Response(200, request=httpx.Request(method, url), json=payload)

    monkeypatch.setattr("one_many_api.channel3.httpx.request", fake_http)
    result = client.post(f"/api/v1/needs/{own}/products/search", headers=a)
    assert result.status_code == 200, result.text
    assert result.json()["products"][0]["id"] == PRODUCT["id"]

    malicious = client.post(
        f"/api/v1/needs/{own}/proposals",
        headers=b,
        json={"product_id": PRODUCT["id"], "offer_url": ITEM_URL},
    )
    assert malicious.status_code == 404

    wrong_offer = client.post(
        f"/api/v1/needs/{own}/proposals",
        headers=a,
        json={
            "product_id": PRODUCT["id"],
            "offer_url": "https://different-merchant.test/imaginary-offer",
        },
    )
    assert wrong_offer.status_code == 409

    created = client.post(
        f"/api/v1/needs/{own}/proposals",
        headers=a,
        json={"product_id": PRODUCT["id"], "offer_url": ITEM_URL, "price_minor": 1},
    )
    assert created.status_code == 201, created.text
    quote = created.json()
    assert quote["price_minor"] == 9001
    assert quote["member_shares_minor"] == [4501, 4500]
    assert quote["prospective_members"] == 2
    assert quote["hypothetical_savings_minor"] == 9001
    assert quote["status"] == "draft"
    assert "no PayPal" in quote["disclaimer"] or "No PayPal" in quote["disclaimer"]
    assert client.get("/api/v1/proposals", headers=a).json()["proposals"][0]["id"] == quote["id"]
    assert client.get("/api/v1/proposals", headers=b).json()["proposals"] == []
    assert client.get(f"/api/v1/proposals/{quote['id']}", headers=b).status_code == 404
    assert client.get(f"/api/v1/proposals/{quote['id']}", headers=a).status_code == 200
    assert any(method == "GET" for method, url in calls)

    # Withdrawal of discovery consent stops fresh proposals.
    client.patch(f"/api/v1/needs/{peer}", headers=b, json={"discoverable": False})
    rejected = client.post(
        f"/api/v1/needs/{own}/proposals",
        headers=a,
        json={"product_id": PRODUCT["id"], "offer_url": ITEM_URL},
    )
    assert rejected.status_code == 409


def test_product_search_without_verified_intent_is_rejected(client):
    auth = member(client, "third@example.com")
    need_id = prepare_need(
        client, auth, "Need a power drill to fix the shelves", "2026-11-22", "2026-11-23"
    )
    response = client.post(f"/api/v1/needs/{need_id}/products/search", headers=auth)
    assert response.status_code == 409

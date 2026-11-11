"""Stage 2 contract and privacy tests (model response fixtures, no fake production AI)."""
from collections import Counter

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from one_many_api.ai_service import AIIntent, AIProviderError, extract_intent
from one_many_api.config import Settings
from one_many_api.database import get_db
from one_many_api.main import create_app
from one_many_api.models import Base

SECRET = "stage-two-test-only-secret-of-at-least-32-characters"


@pytest.fixture
def client():
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
    with TestClient(app, raise_server_exceptions=False) as http:
        yield http
    engine.dispose()


def member(client, email: str):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": email.split("@")[0].title(),
            "password": "secure-for-testing-123456",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def add_need(client, auth, *, text, area="Baner, Pune", start=None, end=None, opt=True):
    response = client.post(
        "/api/v1/needs",
        headers=auth,
        json={
            "request_text": text,
            "location_label": area,
            "needed_from": start,
            "needed_until": end,
            "discoverable": opt,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_mocked_provider_transmits_schema_and_validates_payload(monkeypatch):
    requests = []

    def transport(endpoint, *, headers, json, timeout, follow_redirects):
        requests.append((endpoint, headers, json))
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {"parts": [{"text": (
                            '{"asset_type":"pressure washer","purpose":"Clean driveway",'
                            '"required_features":[],"excluded_features":[],"shareable":true}'
                        )}]},
                    }
                ]
            },
            request=httpx.Request("POST", endpoint),
        )

    monkeypatch.setattr("one_many_api.ai_service.httpx.post", transport)
    settings = Settings(
        _env_file=None,
        gemini_api_key="real-looking-test-key-never-sent-to-google",
        gemini_model="gemini-2.5-flash",
    )
    intent = extract_intent("I need to wash my driveway this Saturday", settings)
    assert intent.asset_type == "pressure washer"
    assert intent.shareable is True
    assert len(requests) == 1
    assert requests[0][2]["generationConfig"]["responseMimeType"] == "application/json"
    assert requests[0][2]["contents"][0]["parts"][0]["text"].startswith("I need")
    assert "x-goog-api-key" in requests[0][1]


def test_no_key_or_invalid_provider_output_is_not_faked(monkeypatch):
    settings = Settings(_env_file=None, gemini_api_key=None)
    with pytest.raises(AIProviderError, match="not configured"):
        extract_intent("I need a drill for the weekend", settings)

    def bad_response(endpoint, **kwargs):
        return httpx.Response(
            200, request=httpx.Request("POST", endpoint),
            json={"candidates": [{"content": {"parts": [{"text": "{}"}]}}]},
        )

    monkeypatch.setattr("one_many_api.ai_service.httpx.post", bad_response)
    settings = Settings(_env_file=None, gemini_api_key="test-value")
    with pytest.raises(AIProviderError, match="invalid structured"):
        extract_intent("I need a drill for the weekend", settings)


def test_optin_matching_without_leaking_member_data(client, monkeypatch):
    call_counts = Counter()

    def provider(text, settings):
        call_counts[text] += 1
        return AIIntent(
            asset_type="pressure washer",
            purpose="Clean a home surface",
            required_features=[],
            excluded_features=[],
            shareable=True,
        )

    monkeypatch.setattr("one_many_api.discovery_routes.extract_intent", provider)
    a = member(client, "member-a@example.com")
    b = member(client, "member-b@example.com")
    secret = member(client, "private@example.com")
    other = member(client, "other-area@example.com")
    own_text = "Need a pressure washer to clean our driveway"
    peer_text = "Want a jet washer for cleaning my patio"

    own = add_need(client, a, text=own_text, start="2026-11-15", end="2026-11-16")
    peer = add_need(client, b, text=peer_text, start="2026-11-20", end="2026-11-21")
    hidden = add_need(
        client, secret, text="Need a washer for our apartment courtyard", opt=False
    )
    elsewhere = add_need(
        client, other, text="Need a washer for the garage", area="Hyderabad"
    )

    # Private requests cannot be queried as candidate matches even after analysis.
    assert client.get(f"/api/v1/needs/{own}/matches", headers=a).status_code == 409
    assert client.post(f"/api/v1/needs/{own}/analyze", headers=a).status_code == 200
    assert client.post(f"/api/v1/needs/{own}/analyze", headers=a).status_code == 200
    assert call_counts[own_text] == 1  # cache prevents redundant model spend
    for auth, target in [(b, peer), (secret, hidden), (other, elsewhere)]:
        assert client.post(f"/api/v1/needs/{target}/analyze", headers=auth).status_code == 200

    # Explicit, additional consent required for one's *own* query.
    res = client.patch(f"/api/v1/needs/{own}", headers=a, json={"discoverable": True})
    assert res.status_code == 200

    result = client.get(f"/api/v1/needs/{own}/matches", headers=a)
    assert result.status_code == 200, result.text
    content = result.json()
    assert content["potential_members"] == 1
    assert content["non_overlapping_schedules"] == 1
    assert content["scheduling_confirmation_required"] == 0
    raw = result.text
    assert "member-b@example.com" not in raw
    assert peer_text not in raw
    assert peer not in raw

    # No access to other people's analysis endpoint or match endpoint.
    assert client.post(f"/api/v1/needs/{peer}/analyze", headers=a).status_code == 404
    assert client.get(f"/api/v1/needs/{peer}/matches", headers=a).status_code == 404

    # Editing a text need invalidates cached AI extraction; never silently reuse it.
    assert client.patch(
        f"/api/v1/needs/{own}",
        headers=a,
        json={"request_text": "Need a different camera to film interviews"},
    ).status_code == 200
    assert client.get(f"/api/v1/needs/{own}/matches", headers=a).status_code == 409
    assert client.get(f"/api/v1/needs/{own}", headers=a).json()["intent"] is None


def test_schedule_conflicts_and_exclusions_are_rejected(client, monkeypatch):
    mapping = {
        "Need a cordless drill for a DIY project": (["battery"], []),
        "Need a drill to assemble my patio furniture": ([], ["battery"]),
        "Need a drill for the bathroom shelves": ([], []),
        "Need a drill for next month's repairs": ([], []),
    }

    def extract(text, settings):
        required, excluded = mapping[text]
        return AIIntent(
            asset_type="power drill",
            purpose="Drilling holes",
            required_features=required,
            excluded_features=excluded,
            shareable=True,
        )

    monkeypatch.setattr("one_many_api.discovery_routes.extract_intent", extract)
    a, b, c, d = [member(client, f"m{i}@example.com") for i in range(4)]
    own = add_need(
        client, a, text="Need a cordless drill for a DIY project",
        start="2026-11-18", end="2026-11-19",
    )
    excluded = add_need(
        client, b, text="Need a drill to assemble my patio furniture",
        start="2026-11-22", end="2026-11-23",
    )
    conflict = add_need(
        client, c, text="Need a drill for the bathroom shelves",
        start="2026-11-18", end="2026-11-19",
    )
    unknown = add_need(client, d, text="Need a drill for next month's repairs")
    for user, need in [(a, own), (b, excluded), (c, conflict), (d, unknown)]:
        assert client.post(f"/api/v1/needs/{need}/analyze", headers=user).status_code == 200
    result = client.get(f"/api/v1/needs/{own}/matches", headers=a)
    assert result.status_code == 200, result.text
    assert result.json()["potential_members"] == 1
    assert result.json()["scheduling_confirmation_required"] == 1
    # Archiving removes peer consent and makes it disappear.
    assert client.delete(f"/api/v1/needs/{unknown}", headers=d).status_code == 204
    assert client.get(f"/api/v1/needs/{own}/matches", headers=a).json()["potential_members"] == 0


def test_analysis_failure_does_not_write_fiction(client, monkeypatch):
    auth = member(client, "failure@example.com")
    target = add_need(client, auth, text="Need a portable projector for our lecture")

    def fail(text, settings):
        raise AIProviderError("Gemini is unavailable; try again later")

    monkeypatch.setattr("one_many_api.discovery_routes.extract_intent", fail)
    response = client.post(f"/api/v1/needs/{target}/analyze", headers=auth)
    assert response.status_code == 503
    assert client.get(f"/api/v1/needs/{target}", headers=auth).json()["intent"] is None


def test_no_discovery_when_unshareable(client, monkeypatch):
    auth = member(client, "not-shareable@example.com")
    target = add_need(
        client, auth, text="Need a disposable roll of tissue paper for cleaning"
    )
    monkeypatch.setattr(
        "one_many_api.discovery_routes.extract_intent",
        lambda text, settings: AIIntent(
            asset_type="tissue paper", purpose="Disposable cleaning material",
            required_features=[], excluded_features=[], shareable=False,
        ),
    )
    assert client.post(f"/api/v1/needs/{target}/analyze", headers=auth).status_code == 200
    assert client.get(f"/api/v1/needs/{target}/matches", headers=auth).status_code == 409

"""Stage 1 contract, authentication, validation and ownership regression tests."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from one_many_api.config import Settings
from one_many_api.database import get_db
from one_many_api.main import create_app
from one_many_api.models import Base

TEST_SECRET = "stage-one-test-only-secret-of-at-least-32-characters"


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    wrapped = create_app(
        Settings(
            _env_file=None,
            environment="test",
            auth_secret=TEST_SECRET,
            database_url=None,
        )
    )

    def override_db():
        with sessions() as session:
            yield session

    wrapped.app.dependency_overrides[get_db] = override_db
    with TestClient(wrapped, raise_server_exceptions=False) as test_client:
        yield test_client
    engine.dispose()


def signup(client, email="first@example.com", password="a-very-long-password-123"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": "First Member", "password": password},
    )


def headers(response):
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_registration_login_and_me(client):
    registration = signup(client, "FIRST@EXAMPLE.COM")
    assert registration.status_code == 201, registration.text
    user = registration.json()["user"]
    assert user["email"] == "first@example.com"
    assert "password" not in str(user)
    assert registration.json()["token_type"] == "bearer"
    assert client.get("/api/v1/auth/me", headers=headers(registration)).json()["id"] == user["id"]

    bad = client.post("/api/v1/auth/login", json={"email": "first@example.com", "password": "wrong"})
    assert bad.status_code == 401
    good = client.post(
        "/api/v1/auth/login",
        json={"email": "FIRST@example.com", "password": "a-very-long-password-123"},
    )
    assert good.status_code == 200
    assert good.json()["user"]["id"] == user["id"]


def test_duplicate_registration_and_weak_password(client):
    assert signup(client).status_code == 201
    assert signup(client).status_code == 409
    short = client.post(
        "/api/v1/auth/register",
        json={"email": "second@example.com", "display_name": "S", "password": "123"},
    )
    assert short.status_code == 422


def test_protected_routes_and_invalid_tokens(client):
    assert client.get("/api/v1/needs").status_code == 401
    assert client.get("/api/v1/needs", headers={"Authorization": "Bearer invalid"}).status_code == 401
    past = datetime.now(UTC) - timedelta(minutes=2)
    expired = jwt.encode(
        {
            "sub": str(uuid4()),
            "iss": "one-many-api",
            "aud": "one-many-api",
            "iat": past,
            "exp": past + timedelta(seconds=1),
            "type": "access",
        },
        TEST_SECRET,
        algorithm="HS256",
    )
    assert client.get("/api/v1/needs", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_needs_create_list_update_archive_and_dates(client):
    owner = signup(client)
    auth = headers(owner)
    data = {
        "request_text": "I need a pressure washer on Saturday morning",
        "location_label": "Baner, Pune",
        "needed_from": "2026-11-14",
        "needed_until": "2026-11-15",
    }
    created = client.post("/api/v1/needs", headers=auth, json=data)
    assert created.status_code == 201, created.text
    need = created.json()
    assert need["owner_id"] == owner.json()["user"]["id"]
    assert need["status"] == "open"
    assert need["location_label"] == "Baner, Pune"

    listed = client.get("/api/v1/needs", headers=auth)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == need["id"]

    edited = client.patch(
        f"/api/v1/needs/{need['id']}",
        headers=auth,
        json={"request_text": "I need the pressure washer to clean our driveway"},
    )
    assert edited.status_code == 200
    assert edited.json()["request_text"].endswith("driveway")

    invalid = client.patch(
        f"/api/v1/needs/{need['id']}", headers=auth, json={"needed_until": "2026-11-01"}
    )
    assert invalid.status_code == 422
    assert client.get(f"/api/v1/needs/{need['id']}", headers=auth).json()["needed_until"] == "2026-11-15"

    archived = client.delete(f"/api/v1/needs/{need['id']}", headers=auth)
    assert archived.status_code == 204
    assert client.get("/api/v1/needs?status=open", headers=auth).json()["total"] == 0
    assert client.get("/api/v1/needs?status=archived", headers=auth).json()["total"] == 1

    reopened = client.patch(f"/api/v1/needs/{need['id']}", headers=auth, json={"status": "open"})
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "open"


def test_cross_account_needs_are_not_exposed(client):
    first = headers(signup(client, "first@example.com"))
    second = headers(signup(client, "second@example.com"))
    created = client.post(
        "/api/v1/needs", headers=first, json={"request_text": "Need a camera for a weekend workshop"}
    )
    need_id = created.json()["id"]
    assert client.get("/api/v1/needs", headers=second).json()["total"] == 0
    assert client.get(f"/api/v1/needs/{need_id}", headers=second).status_code == 404
    assert client.patch(
        f"/api/v1/needs/{need_id}", headers=second, json={"status": "archived"}
    ).status_code == 404
    assert client.delete(f"/api/v1/needs/{need_id}", headers=second).status_code == 404
    assert client.get(f"/api/v1/needs/{need_id}", headers=first).status_code == 200


def test_invalid_values_and_pagination(client):
    auth = headers(signup(client))
    assert client.post("/api/v1/needs", headers=auth, json={"request_text": "short"}).status_code == 422
    assert client.post(
        "/api/v1/needs",
        headers=auth,
        json={"request_text": "Looking for a drill for two weekend tasks", "needed_from": "2027-01-10", "needed_until": "2027-01-09"},
    ).status_code == 422
    for i in range(3):
        assert client.post(
            "/api/v1/needs", headers=auth, json={"request_text": f"Projector needed for workshop number {i}"}
        ).status_code == 201
    result = client.get("/api/v1/needs?limit=2&offset=1", headers=auth).json()
    assert result["total"] == 3
    assert len(result["items"]) == 2
    assert client.get("/api/v1/needs?limit=101", headers=auth).status_code == 422
    assert client.get("/api/v1/needs?status=paid", headers=auth).status_code == 422


def test_cors_allows_bearer_write_calls(client):
    response = client.options(
        "/api/v1/needs",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

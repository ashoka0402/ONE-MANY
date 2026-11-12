"""Local demo examples must be fictional, repeatable and production-disabled."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from one_many_api.config import Settings
from one_many_api.database import get_db
from one_many_api.main import create_app
from one_many_api.models import Base

SECRET = "fixture-only-auth-secret-at-least-thirty-two-characters"


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    app = create_app(Settings(
        _env_file=None, environment="development",
        auth_secret=SECRET, database_url=None,
    ))

    def override_db():
        with sessions() as db:
            yield db

    app.app.dependency_overrides[get_db] = override_db
    with TestClient(app, raise_server_exceptions=False) as http:
        yield http
    engine.dispose()


def test_demo_seed_is_authenticated_and_idempotent(client):
    assert client.post("/api/v1/demo/seed").status_code == 401
    account = client.post("/api/v1/auth/register", json={
        "email": "owner@example.com",
        "display_name": "Demo Owner",
        "password": "strong-demo-password-123",
    })
    assert account.status_code == 201, account.text
    auth = {"Authorization": "Bearer " + account.json()["access_token"]}

    first = client.post("/api/v1/demo/seed", headers=auth)
    assert first.status_code == 200, first.text
    assert first.json()["created_needs"] == 4
    assert first.json()["created_sample_neighbors"] == 3
    assert client.post("/api/v1/demo/seed", headers=auth).json() == {
        "created_needs": 0,
        "created_sample_neighbors": 0,
        "message": first.json()["message"],
    }

    needs = client.get("/api/v1/needs", headers=auth).json()
    assert needs["total"] == 4
    assert all(item["request_text"].startswith("[DEMO]") for item in needs["items"])
    assert all(item["intent"]["model_name"] == "demo-fixture" for item in needs["items"])
    assert all(item["owner_id"] == account.json()["user"]["id"] for item in needs["items"])

    washer = next(item for item in needs["items"] if "pressure washer" in item["request_text"])
    matches = client.get(f"/api/v1/needs/{washer['id']}/matches", headers=auth)
    assert matches.status_code == 200, matches.text
    assert matches.json()["potential_members"] == 2
    assert matches.json()["non_overlapping_schedules"] == 2
    assert "demo-neighbor" not in matches.text

    # Sample data never fakes payment captures, retailer offers or ownership.
    assert client.get("/api/v1/funding/groups", headers=auth).json()["groups"] == []
    assert client.get("/api/v1/proposals", headers=auth).json()["proposals"] == []


def test_demo_seed_not_available_in_test_or_production():
    test_app = create_app(Settings(_env_file=None, environment="test", auth_secret=SECRET))
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with sessions() as db:
            yield db

    test_app.app.dependency_overrides[get_db] = override_db
    with TestClient(test_app, raise_server_exceptions=False) as client:
        account = client.post("/api/v1/auth/register", json={
            "email": "tester@example.com",
            "display_name": "Tester",
            "password": "strong-password-123456",
        })
        token = account.json()["access_token"]
        result = client.post("/api/v1/demo/seed", headers={"Authorization": f"Bearer {token}"})
        assert result.status_code == 404
    engine.dispose()

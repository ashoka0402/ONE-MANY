"""Stage 7 deployment safety: schema readiness, CORS and Render database URLs."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from one_many_api.config import Settings
from one_many_api.main import create_app
from one_many_api.models import Base

TEST_SECRET = "stage-seven-smoke-auth-secret-that-is-not-real-12345"


def test_render_postgres_native_url_is_normalized_to_psycopg():
    for original in (
        "postgresql://demo:private@db.internal:5432/one_many",
        "postgres://demo:private@db.internal:5432/one_many",
    ):
        config = Settings(_env_file=None, database_url=original)
        uri = config.database_url.get_secret_value()
        assert uri.startswith("postgresql+psycopg://")
        assert uri.endswith("/one_many")
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="sqlite:///tmp/fake.db")


def test_production_configuration_requires_https_public_site():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None, environment="production",
            auth_secret=TEST_SECRET,
            database_url="postgresql://demo:pass@db.internal:5432/one_many",
            public_web_url="http://demo.example.com",
        )
    settings = Settings(
        _env_file=None, environment="production",
        auth_secret=TEST_SECRET,
        database_url="postgresql://demo:pass@db.internal:5432/one_many",
        public_web_url="https://demo.example.com",
        cors_origins=["https://demo.example.com"],
    )
    assert settings.database_url.get_secret_value().startswith("postgresql+psycopg://")


def test_readiness_checks_migration_and_browser_put_preflight():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app = create_app(Settings(_env_file=None, environment="test", auth_secret=TEST_SECRET))
    app.app.dependency_overrides.clear()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/ready")
        assert response.status_code == 503
        assert client.get("/api/v1/health").json()["status"] == "ok"
        preflight = client.options(
            "/api/v1/funding/groups/00000000-0000-4000-8000-000000000000/reservation",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "PUT",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert preflight.status_code == 200, preflight.text
        assert preflight.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert "PUT" in preflight.headers["access-control-allow-methods"]
        assert preflight.headers["access-control-allow-headers"]
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["x-content-type-options"] == "nosniff"

        app.app.state.db_session_factory = session_factory
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
            conn.execute(text("INSERT INTO alembic_version VALUES ('20261112_05')"))
        assert client.get("/api/v1/ready").status_code == 503
        with engine.begin() as conn:
            conn.execute(text("UPDATE alembic_version SET version_num = '20261112_06'"))
        ready = client.get("/api/v1/ready")
        assert ready.status_code == 200, ready.text
        assert ready.json()["status"] == "ready"
    engine.dispose()

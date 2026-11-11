import json
import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from one_many_api.config import Settings
from one_many_api.logging import JsonFormatter
from one_many_api.main import create_app


@pytest.fixture
def client():
    app = create_app(Settings(_env_file=None, environment="test", database_url=None))
    api = app.app

    @api.get("/test/validate")
    async def validate(count: int):
        return {"count": count}

    @api.get("/test/error")
    async def error():
        raise RuntimeError("private database credentials")

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "one-many-api", "version": "0.1.0"}


def test_not_found(client):
    response = client.get("/missing")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "http_404", "message": "Not Found"}}


def test_method_not_allowed(client):
    response = client.post("/api/v1/health")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "http_405"


def test_validation_does_not_echo_input(client):
    response = client.get("/test/validate?count=private-value")
    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "validation_error", "message": "Request validation failed"}
    }
    assert "private-value" not in response.text


def test_unexpected_error_is_safe_and_has_cors(client):
    response = client.get("/test/error", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Internal server error"}
    }
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_allowed_origin(client):
    response = client.options(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-credentials" not in response.headers


def test_untrusted_origin(client):
    response = client.get("/api/v1/health", headers={"Origin": "https://untrusted.example"})
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("origin", ["*", "https://*.example", "https://example.com/path"])
def test_settings_reject_wildcards_and_paths(origin):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, cors_origins=[origin])


def test_settings_read_environment(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://one-many.example"]')
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:private@localhost/one_many")
    monkeypatch.setenv("AUTH_SECRET", "not-a-real-credential-just-long-enough-for-tests")
    settings = Settings(_env_file=None)
    assert settings.environment == "production"
    assert settings.cors_origins == ["https://one-many.example"]
    assert "private" not in repr(settings)


def test_settings_reject_wrong_database_driver():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="sqlite:///test.db")


def test_json_logging_excludes_exception_text():
    record = logging.LogRecord(
        "one_many_api", logging.ERROR, "", 0, "unhandled_exception", (), None
    )
    record.error_type = "RuntimeError"
    result = json.loads(JsonFormatter().format(record))
    assert result["event"] == "unhandled_exception"
    assert result["level"] == "ERROR"
    assert result["error_type"] == "RuntimeError"
    assert result["timestamp"]


def test_invalid_database_does_not_expose_password():
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, database_url="mysql://user:private-password@localhost/database")
    assert "private-password" not in str(error.value)


def test_json_logging_redacts_server_exception_traceback():
    exception = RuntimeError("private-password")
    record = logging.LogRecord(
        "uvicorn.error",
        logging.ERROR,
        "",
        0,
        "Exception in ASGI application",
        (),
        (RuntimeError, exception, None),
    )
    formatted = JsonFormatter().format(record)
    assert "private-password" not in formatted
    assert json.loads(formatted)["error_type"] == "RuntimeError"

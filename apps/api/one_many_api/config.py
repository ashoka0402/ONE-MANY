from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", hide_input_in_errors=True
    )

    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: SecretStr | None = None
    auth_secret: SecretStr | None = None
    access_token_minutes: int = Field(default=60, ge=5, le=1440)
    gemini_api_key: SecretStr | None = None
    gemini_model: str = Field(default="gemini-2.5-flash", pattern=r"^gemini-[a-zA-Z0-9._-]+$")
    gemini_timeout_seconds: float = Field(default=12.0, ge=2, le=30)
    match_candidate_limit: int = Field(default=300, ge=10, le=2000)
    channel3_api_key: SecretStr | None = None
    channel3_country: str = Field(default="US", pattern=r"^[A-Z]{2}$")
    channel3_currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    channel3_timeout_seconds: float = Field(default=12.0, ge=3, le=30)
    max_proposal_participants: int = Field(default=8, ge=2, le=30)

    @model_validator(mode="after")
    def credentials_for_production(self) -> "Settings":
        if self.auth_secret is not None and len(self.auth_secret.get_secret_value()) < 32:
            raise ValueError("AUTH_SECRET must contain at least 32 characters")
        if self.environment == "production":
            if self.auth_secret is None or self.database_url is None:
                raise ValueError("Production requires AUTH_SECRET and DATABASE_URL")
        return self

    @field_validator("cors_origins")
    @classmethod
    def explicit_origins(cls, origins: list[str]) -> list[str]:
        for origin in origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
                or "*" in origin
            ):
                raise ValueError("CORS origins must be explicit HTTP(S) origins without paths")
        return origins

    @field_validator("database_url")
    @classmethod
    def postgres_url(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            try:
                url = make_url(value.get_secret_value())
                if url.drivername != "postgresql+psycopg" or not url.host or not url.database:
                    raise ValueError(
                        "DATABASE_URL must use postgresql+psycopg with host and database"
                    )
            except ArgumentError:
                raise ValueError("DATABASE_URL must be a valid PostgreSQL connection URL") from None
        return value

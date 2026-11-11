"""Session management is separate from migrations and API handlers."""

from collections.abc import Generator
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from one_many_api.config import Settings


def build_session_factory(settings: Settings) -> tuple[sessionmaker[Session], Any] | None:
    if settings.database_url is None:
        return None
    engine = create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_recycle=1800,
    )
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False), engine


def get_db(request: Request) -> Generator[Session, None, None]:
    factory = getattr(request.app.state, "db_session_factory", None)
    if factory is None:
        raise HTTPException(503, "Database is not configured")
    with factory() as session:
        yield session

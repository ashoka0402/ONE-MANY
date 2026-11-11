"""Alembic migration environment; schema is not created implicitly."""
from alembic import context
from sqlalchemy import create_engine

from one_many_api.config import Settings
from one_many_api.models import Base

target_metadata = Base.metadata


def database_url() -> str:
    settings = Settings()
    if settings.database_url is None:
        raise RuntimeError("DATABASE_URL is required for migrations")
    return settings.database_url.get_secret_value()


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url(), pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

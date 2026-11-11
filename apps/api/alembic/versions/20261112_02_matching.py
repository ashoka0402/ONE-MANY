"""Opt-in discovery fields and AI need extraction cache.

Revision ID: 20261112_02
Revises: 20261112_01
"""
import re
import unicodedata

import sqlalchemy as sa
from alembic import op

revision = "20261112_02"
down_revision = "20261112_01"
branch_labels = None
depends_on = None


def _normalized_area(label: str | None) -> str | None:
    if not label:
        return None
    text = unicodedata.normalize("NFKC", label).casefold()
    key = re.sub(r"[\W_]+", " ", text).strip()
    return " ".join(key.split()) or None


def upgrade() -> None:
    op.add_column("needs", sa.Column("location_key", sa.String(120), nullable=True))
    op.add_column(
        "needs",
        sa.Column("discoverable", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    conn = op.get_bind()
    # Backfill *existing* Stage 1 location data, without turning on consent.
    for row in conn.execute(
        sa.text("SELECT id, location_label FROM needs WHERE location_label IS NOT NULL")
    ).mappings():
        conn.execute(
            sa.text("UPDATE needs SET location_key = :area WHERE id = :id"),
            {"id": row["id"], "area": _normalized_area(row["location_label"])},
        )
    op.create_index(
        "ix_needs_discoverable_area",
        "needs",
        ["status", "discoverable", "location_key"],
    )
    op.create_table(
        "need_intents",
        sa.Column(
            "need_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("needs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("asset_type", sa.String(120), nullable=False),
        sa.Column("asset_key", sa.String(120), nullable=False),
        sa.Column("purpose", sa.String(240), nullable=False),
        sa.Column("required_features", sa.JSON(), nullable=False),
        sa.Column("excluded_features", sa.JSON(), nullable=False),
        sa.Column("shareable", sa.Boolean(), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column(
            "analyzed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_need_intents_asset_key", "need_intents", ["asset_key"])


def downgrade() -> None:
    op.drop_index("ix_need_intents_asset_key", table_name="need_intents")
    op.drop_table("need_intents")
    op.drop_index("ix_needs_discoverable_area", table_name="needs")
    op.drop_column("needs", "discoverable")
    op.drop_column("needs", "location_key")

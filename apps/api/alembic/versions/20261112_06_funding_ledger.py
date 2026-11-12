"""Append-only funding observations, never a second mutable money balance.

Revision ID: 20261112_06
Revises: 20261112_05
"""
import sqlalchemy as sa

from alembic import op

revision = "20261112_06"
down_revision = "20261112_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "funding_ledger_events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "group_id", sa.Uuid(as_uuid=True),
            sa.ForeignKey("funding_groups.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "attempt_id", sa.Uuid(as_uuid=True),
            sa.ForeignKey("payment_attempts.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("member_slot", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(48), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("event_key", sa.String(210), nullable=False, unique=True),
        sa.Column(
            "recorded_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "amount_minor >= 0", name="ck_funding_events_nonnegative",
        ),
        sa.CheckConstraint(
            "member_slot IS NULL OR member_slot >= 1", name="ck_funding_events_slot",
        ),
        sa.CheckConstraint(
            "source IN ('application', 'paypal_verified')",
            name="ck_funding_events_source",
        ),
    )
    op.create_index(
        "ix_funding_events_group_recorded", "funding_ledger_events",
        ["group_id", "recorded_at"],
    )


def downgrade() -> None:
    op.drop_table("funding_ledger_events")

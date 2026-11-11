"""Users and owned needs (Stage 1).

Revision ID: 20261112_01
Revises:
"""

import sqlalchemy as sa

from alembic import op

revision = "20261112_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "needs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("request_text", sa.Text(), nullable=False),
        sa.Column("location_label", sa.String(120), nullable=True),
        sa.Column("needed_from", sa.Date(), nullable=True),
        sa.Column("needed_until", sa.Date(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("status IN ('open', 'archived')", name="ck_needs_status"),
        sa.CheckConstraint(
            "needed_from IS NULL OR needed_until IS NULL OR needed_until >= needed_from",
            name="ck_needs_dates",
        ),
    )
    op.create_index("ix_needs_owner_created", "needs", ["owner_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_needs_owner_created", table_name="needs")
    op.drop_table("needs")
    op.drop_table("users")

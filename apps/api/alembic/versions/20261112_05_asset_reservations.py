"""Provisional date-only booking with a database-enforced no-overlap invariant.

Revision ID: 20261112_05
Revises: 20261112_04
"""
import sqlalchemy as sa

from alembic import op

revision = "20261112_05"
down_revision = "20261112_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asset_reservations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "group_id", sa.Uuid(as_uuid=True),
            sa.ForeignKey("funding_groups.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column(
            "user_id", sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column(
            "need_id", sa.Uuid(as_uuid=True),
            sa.ForeignKey("needs.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.CheckConstraint("status IN ('active', 'cancelled')", name="ck_reservations_status"),
        sa.CheckConstraint("end_date >= start_date", name="ck_reservations_dates"),
    )
    op.create_index(
        "ix_reservations_group_member",
        "asset_reservations", ["group_id", "user_id"], unique=True,
    )
    op.create_index(
        "ix_reservations_group_dates",
        "asset_reservations", ["group_id", "status", "start_date"],
    )
    # The group row is locked by the API, but exclusion also guarantees safety
    # against application bugs and simultaneous non-API writes.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        "ALTER TABLE asset_reservations ADD CONSTRAINT ex_reservations_no_overlap "
        "EXCLUDE USING gist (group_id WITH =, "
        "daterange(start_date, end_date + 1, '[)') WITH &&) "
        "WHERE (status = 'active')"
    )


def downgrade() -> None:
    op.drop_table("asset_reservations")

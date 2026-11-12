"""Persist non-payable price snapshots for potential collective purchases.

Revision ID: 20261112_03
Revises: 20261112_02
"""
import sqlalchemy as sa
from alembic import op

revision = "20261112_03"
down_revision = "20261112_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_proposals",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "need_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("needs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("need_source_hash", sa.String(64), nullable=False),
        sa.Column("channel3_product_id", sa.String(250), nullable=False),
        sa.Column("product_title", sa.String(500), nullable=False),
        sa.Column("product_image_url", sa.Text(), nullable=True),
        sa.Column("merchant_domain", sa.String(255), nullable=False),
        sa.Column("merchant_url", sa.Text(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("prospective_members", sa.Integer(), nullable=False),
        sa.Column("share_amounts_minor", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="draft"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("quote_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("price_minor > 0", name="ck_proposals_positive_price"),
        sa.CheckConstraint("prospective_members >= 2", name="ck_proposals_min_members"),
        sa.CheckConstraint(
            "status IN ('draft', 'cancelled')", name="ck_proposals_status"
        ),
    )
    op.create_index("ix_proposals_owner_created", "purchase_proposals", ["owner_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_proposals_owner_created", table_name="purchase_proposals")
    op.drop_table("purchase_proposals")

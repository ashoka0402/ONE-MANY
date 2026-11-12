"""Explicit group acceptance and idempotent PayPal Sandbox ledger.

Revision ID: 20261112_04
Revises: 20261112_03
"""

import sqlalchemy as sa

from alembic import op

revision = "20261112_04"
down_revision = "20261112_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "funding_groups",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "proposal_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("purchase_proposals.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "owner_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("invitation_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("state", sa.String(16), nullable=False, server_default="recruiting"),
        sa.Column("total_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("target_members", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "state IN ('recruiting', 'funding', 'funded', 'needs_review', 'cancelled')",
            name="ck_funding_group_state",
        ),
        sa.CheckConstraint("target_members >= 2", name="ck_funding_group_members"),
        sa.CheckConstraint("total_minor > 0", name="ck_funding_group_amount"),
    )
    op.create_index("ix_funding_groups_owner_created", "funding_groups", ["owner_id", "created_at"])
    op.create_table(
        "funding_members",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "group_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("funding_groups.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
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
        sa.Column("slot_index", sa.Integer(), nullable=False),
        sa.Column("share_minor", sa.Integer(), nullable=False),
        sa.Column(
            "accepted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("share_minor > 0", name="ck_funding_member_amount"),
        sa.CheckConstraint("slot_index >= 0", name="ck_funding_member_slot"),
    )
    op.create_index(
        "ix_funding_members_group_user", "funding_members", ["group_id", "user_id"], unique=True
    )
    op.create_index(
        "ix_funding_members_group_need", "funding_members", ["group_id", "need_id"], unique=True
    )
    op.create_index(
        "ix_funding_members_group_slot", "funding_members", ["group_id", "slot_index"], unique=True
    )
    op.create_table(
        "payment_attempts",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "group_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("funding_groups.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("state", sa.String(20), nullable=False, server_default="creating"),
        sa.Column("paypal_order_id", sa.String(100), nullable=True, unique=True),
        sa.Column("paypal_capture_id", sa.String(100), nullable=True, unique=True),
        sa.Column("approval_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "state IN ('creating', 'awaiting_approval', 'capture_pending', "
            "'completed', 'needs_review', 'reversed')",
            name="ck_payment_attempt_state",
        ),
        sa.CheckConstraint("amount_minor > 0", name="ck_payment_attempt_amount"),
    )
    op.create_index(
        "ix_payment_attempt_group_user",
        "payment_attempts",
        ["group_id", "user_id"],
        unique=True,
    )
    op.create_table(
        "paypal_webhook_events",
        sa.Column("event_id", sa.String(150), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column(
            "received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("paypal_webhook_events")
    op.drop_index("ix_payment_attempt_group_user", table_name="payment_attempts")
    op.drop_table("payment_attempts")
    op.drop_index("ix_funding_members_group_slot", table_name="funding_members")
    op.drop_index("ix_funding_members_group_need", table_name="funding_members")
    op.drop_index("ix_funding_members_group_user", table_name="funding_members")
    op.drop_table("funding_members")
    op.drop_index("ix_funding_groups_owner_created", table_name="funding_groups")
    op.drop_table("funding_groups")

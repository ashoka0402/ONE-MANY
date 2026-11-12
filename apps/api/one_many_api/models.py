"""Database tables for authenticated users and independently managed needs."""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    needs: Mapped[list["Need"]] = relationship(back_populates="owner")


class Need(Base):
    __tablename__ = "needs"
    __table_args__ = (
        CheckConstraint("status IN ('open', 'archived')", name="ck_needs_status"),
        CheckConstraint(
            "needed_from IS NULL OR needed_until IS NULL OR needed_until >= needed_from",
            name="ck_needs_dates",
        ),
        Index("ix_needs_owner_created", "owner_id", "created_at"),
        Index("ix_needs_discoverable_area", "status", "discoverable", "location_key"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    request_text: Mapped[str] = mapped_column(Text, nullable=False)
    location_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    discoverable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    needed_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    needed_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="open", server_default="open"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    owner: Mapped[User] = relationship(back_populates="needs")
    intent: Mapped["NeedIntent | None"] = relationship(
        back_populates="need", uselist=False, cascade="all, delete-orphan"
    )


class NeedIntent(Base):
    """A cached, strictly validated real provider extraction for one owned need."""

    __tablename__ = "need_intents"
    __table_args__ = (Index("ix_need_intents_asset_key", "asset_key"),)

    need_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("needs.id", ondelete="CASCADE"), primary_key=True
    )
    asset_type: Mapped[str] = mapped_column(String(120), nullable=False)
    asset_key: Mapped[str] = mapped_column(String(120), nullable=False)
    purpose: Mapped[str] = mapped_column(String(240), nullable=False)
    required_features: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    excluded_features: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    shareable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    need: Mapped[Need] = relationship(back_populates="intent")


class PurchaseProposal(Base):
    """Immutable, unapproved catalog quote snapshot; no participant is charged."""

    __tablename__ = "purchase_proposals"
    __table_args__ = (
        CheckConstraint("price_minor > 0", name="ck_proposals_positive_price"),
        CheckConstraint("prospective_members >= 2", name="ck_proposals_min_members"),
        CheckConstraint("status IN ('draft', 'cancelled')", name="ck_proposals_status"),
        Index("ix_proposals_owner_created", "owner_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    need_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("needs.id", ondelete="RESTRICT"), nullable=False
    )
    need_source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    channel3_product_id: Mapped[str] = mapped_column(String(250), nullable=False)
    product_title: Mapped[str] = mapped_column(String(500), nullable=False)
    product_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    merchant_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    merchant_url: Mapped[str] = mapped_column(Text, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    price_minor: Mapped[int] = mapped_column(nullable=False)
    prospective_members: Mapped[int] = mapped_column(nullable=False)
    share_amounts_minor: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="draft", server_default="draft"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    quote_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FundingGroup(Base):
    """Time-limited, member-approved sandbox-only funding pool."""

    __tablename__ = "funding_groups"
    __table_args__ = (
        CheckConstraint(
            "state IN ('recruiting', 'funding', 'funded', 'needs_review', 'cancelled')",
            name="ck_funding_group_state",
        ),
        CheckConstraint("target_members >= 2", name="ck_funding_group_members"),
        CheckConstraint("total_minor > 0", name="ck_funding_group_amount"),
        Index("ix_funding_groups_owner_created", "owner_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    proposal_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("purchase_proposals.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    owner_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    invitation_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="recruiting")
    total_minor: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_members: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FundingMember(Base):
    """Explicit opt-in by authenticated owners of compatible needs."""

    __tablename__ = "funding_members"
    __table_args__ = (
        Index("ix_funding_members_group_user", "group_id", "user_id", unique=True),
        Index("ix_funding_members_group_need", "group_id", "need_id", unique=True),
        Index("ix_funding_members_group_slot", "group_id", "slot_index", unique=True),
        CheckConstraint("share_minor > 0", name="ck_funding_member_amount"),
        CheckConstraint("slot_index >= 0", name="ck_funding_member_slot"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    group_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("funding_groups.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    need_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("needs.id", ondelete="RESTRICT"), nullable=False
    )
    slot_index: Mapped[int] = mapped_column(nullable=False)
    share_minor: Mapped[int] = mapped_column(nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PaymentAttempt(Base):
    """Exactly one PayPal order per accepted member per group, idempotently retried."""

    __tablename__ = "payment_attempts"
    __table_args__ = (
        Index("ix_payment_attempt_group_user", "group_id", "user_id", unique=True),
        CheckConstraint(
            "state IN ('creating', 'awaiting_approval', 'capture_pending', "
            "'completed', 'needs_review', 'reversed')",
            name="ck_payment_attempt_state",
        ),
        CheckConstraint("amount_minor > 0", name="ck_payment_attempt_amount"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    group_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("funding_groups.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    amount_minor: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="creating")
    paypal_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    paypal_capture_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    approval_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class PayPalWebhookEvent(Base):
    """Verified PayPal event IDs prevent replay-driven ledger changes."""

    __tablename__ = "paypal_webhook_events"
    event_id: Mapped[str] = mapped_column(String(150), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

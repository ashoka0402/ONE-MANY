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

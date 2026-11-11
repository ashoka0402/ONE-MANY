"""Database tables for authenticated users and independently managed needs."""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text, Uuid, func
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

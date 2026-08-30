"""SQLAlchemy models mirroring the authoritative database schema."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


Category = Enum(
    "groceries",
    "dining",
    "coffee",
    "transport",
    "fuel",
    "utilities",
    "rent_mortgage",
    "subscriptions",
    "shopping",
    "health",
    "entertainment",
    "income",
    "other",
    name="category_enum",
    native_enum=True,
    create_type=False,
)
CategorySource = Enum(
    "model",
    "rule",
    "user",
    name="category_source_enum",
    native_enum=True,
    create_type=False,
)
Cadence = Enum(
    "weekly",
    "biweekly",
    "monthly",
    "quarterly",
    "annual",
    name="cadence_enum",
    native_enum=True,
    create_type=False,
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("now()"),
    )


class Import(Base):
    __tablename__ = "imports"
    __table_args__ = (
        Index("ix_imports_user", "user_id", text("imported_at DESC")),
        CheckConstraint("row_count >= 0"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("now()"),
    )
    date_min: Mapped[Optional[date]] = mapped_column(Date)
    date_max: Mapped[Optional[date]] = mapped_column(Date)


class RecurringGroup(Base):
    __tablename__ = "recurring_groups"
    __table_args__ = (
        Index("ix_recurring_user", "user_id"),
        UniqueConstraint("user_id", "merchant", "cadence"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    merchant: Mapped[str] = mapped_column(Text, nullable=False)
    cadence: Mapped[str] = mapped_column(Cadence, nullable=False)
    avg_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount_stddev: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        server_default=text("0"),
    )
    first_seen: Mapped[date] = mapped_column(Date, nullable=False)
    last_seen: Mapped[date] = mapped_column(Date, nullable=False)
    next_expected: Mapped[date] = mapped_column(Date, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("now()"),
    )


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_txn_user_date", "user_id", "txn_date"),
        Index("ix_txn_user_merchant", "user_id", "merchant"),
        Index("ix_txn_user_category", "user_id", "category"),
        CheckConstraint("category_confidence BETWEEN 0 AND 1"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    import_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("imports.id", ondelete="CASCADE"),
        nullable=False,
    )
    txn_date: Mapped[date] = mapped_column(Date, nullable=False)
    description_raw: Mapped[str] = mapped_column(Text, nullable=False)
    merchant: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str] = mapped_column(Category, nullable=False, server_default=text("'other'"))
    category_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default=text("0"),
    )
    category_source: Mapped[str] = mapped_column(
        CategorySource,
        nullable=False,
        server_default=text("'model'"),
    )
    is_recurring: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    recurring_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recurring_groups.id", ondelete="SET NULL"),
    )
    is_anomaly: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    anomaly_reason: Mapped[Optional[str]] = mapped_column(Text)
    dedupe_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("now()"),
    )


class CategoryCorrection(Base):
    __tablename__ = "category_corrections"
    __table_args__ = (Index("ix_corrections_user", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    old_category: Mapped[str] = mapped_column(Category, nullable=False)
    new_category: Mapped[str] = mapped_column(Category, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("now()"),
    )


ImportRecord = Import

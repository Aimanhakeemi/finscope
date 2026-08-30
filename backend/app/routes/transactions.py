"""Transaction listing and category-correction endpoints."""
from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.categorize import TAXONOMY
from app.db import get_session
from app.models import CategoryCorrection, Transaction
from app.seed import seed_demo_user

router = APIRouter(prefix="/api/transactions", tags=["transactions"])
CategoryName = Literal[
    "groceries", "dining", "coffee", "transport", "fuel", "utilities",
    "rent_mortgage", "subscriptions", "shopping", "health", "entertainment",
    "income", "other",
]


class CategoryUpdate(BaseModel):
    category: CategoryName


class TransactionResponse(BaseModel):
    id: str
    txn_date: date
    description_raw: str
    merchant: str
    amount: float
    category: str
    category_confidence: float
    category_source: str
    is_recurring: bool
    recurring_group_id: Optional[str]
    is_anomaly: bool
    anomaly_reason: Optional[str]


class TransactionListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    transactions: list[TransactionResponse]


def serialize_transaction(transaction: Transaction) -> dict[str, Any]:
    return {
        "id": str(transaction.id),
        "txn_date": transaction.txn_date,
        "description_raw": transaction.description_raw,
        "merchant": transaction.merchant,
        "amount": float(transaction.amount),
        "category": str(transaction.category),
        "category_confidence": float(transaction.category_confidence),
        "category_source": str(transaction.category_source),
        "is_recurring": transaction.is_recurring,
        "recurring_group_id": (
            str(transaction.recurring_group_id) if transaction.recurring_group_id else None
        ),
        "is_anomaly": transaction.is_anomaly,
        "anomaly_reason": transaction.anomaly_reason,
    }


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    from_date: Optional[date] = Query(None, alias="from"),  # noqa: B008
    to_date: Optional[date] = Query(None, alias="to"),  # noqa: B008
    category: Optional[str] = None,
    merchant: Optional[str] = None,
    is_recurring: Optional[bool] = None,
    is_anomaly: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),  # noqa: B008
    offset: int = Query(0, ge=0),  # noqa: B008
    sort: str = Query("-date", pattern=r"^-?(date|amount)$"),  # noqa: B008
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, Any]:
    user = seed_demo_user(session)
    if category is not None and category not in TAXONOMY:
        raise HTTPException(422, "unknown category")
    if from_date and to_date and from_date > to_date:
        raise HTTPException(400, "from must be before or equal to to")

    filters = [Transaction.user_id == user.id]
    if from_date:
        filters.append(Transaction.txn_date >= from_date)
    if to_date:
        filters.append(Transaction.txn_date <= to_date)
    if category:
        filters.append(Transaction.category == category)
    if merchant:
        filters.append(Transaction.merchant.ilike(f"%{merchant}%"))
    if is_recurring is not None:
        filters.append(Transaction.is_recurring == is_recurring)
    if is_anomaly is not None:
        filters.append(Transaction.is_anomaly == is_anomaly)

    sort_name = sort.lstrip("-")
    sort_column = Transaction.txn_date if sort_name == "date" else Transaction.amount
    order = sort_column.desc() if sort.startswith("-") else sort_column.asc()
    query = select(Transaction).where(*filters).order_by(order, Transaction.id)
    total = session.scalar(select(func.count()).select_from(Transaction).where(*filters)) or 0
    transactions = session.scalars(query.offset(offset).limit(limit)).all()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "transactions": [serialize_transaction(transaction) for transaction in transactions],
    }


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: UUID,
    update: CategoryUpdate,
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, Any]:
    user = seed_demo_user(session)
    transaction = session.scalar(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user.id,
        )
    )
    if transaction is None:
        raise HTTPException(404, "transaction not found")

    correction = CategoryCorrection(
        user_id=user.id,
        transaction_id=transaction.id,
        old_category=transaction.category,
        new_category=update.category,
    )
    transaction.category = update.category
    transaction.category_confidence = 1.0
    transaction.category_source = "user"
    session.add(correction)
    session.commit()
    session.refresh(transaction)
    return serialize_transaction(transaction)

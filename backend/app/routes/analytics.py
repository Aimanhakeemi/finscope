"""Dashboard analytics endpoints."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Transaction
from app.seed import seed_demo_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class CategoryTotal(BaseModel):
    category: str
    total: float
    txn_count: int


class MonthlyTotal(BaseModel):
    month: str
    spend: float
    income: float


class MerchantTotal(BaseModel):
    merchant: str
    total: float
    txn_count: int


class SummaryResponse(BaseModel):
    range: list[Optional[date]]
    totals: dict[str, float]
    by_category: list[CategoryTotal]
    monthly: list[MonthlyTotal]
    top_merchants: list[MerchantTotal]


@router.get("/summary", response_model=SummaryResponse)
def summary(
    from_date: Optional[date] = Query(None, alias="from"),  # noqa: B008
    to_date: Optional[date] = Query(None, alias="to"),  # noqa: B008
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, Any]:
    user = seed_demo_user(session)
    if from_date and to_date and from_date > to_date:
        raise HTTPException(400, "from must be before or equal to to")

    filters = [Transaction.user_id == user.id]
    if from_date:
        filters.append(Transaction.txn_date >= from_date)
    if to_date:
        filters.append(Transaction.txn_date <= to_date)
    transactions = session.scalars(
        select(Transaction).where(*filters).order_by(Transaction.txn_date, Transaction.id)
    ).all()

    category_totals: dict[str, list[float | int]] = defaultdict(lambda: [0.0, 0])
    merchant_totals: dict[str, list[float | int]] = defaultdict(lambda: [0.0, 0])
    monthly: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    spend = 0.0
    income = 0.0
    for transaction in transactions:
        amount = float(transaction.amount)
        category = str(transaction.category)
        merchant = transaction.merchant
        category_totals[category][0] += amount
        category_totals[category][1] += 1
        merchant_totals[merchant][0] += amount
        merchant_totals[merchant][1] += 1
        month = transaction.txn_date.strftime("%Y-%m")
        if amount < 0:
            spend += amount
            monthly[month][0] += amount
        else:
            income += amount
            monthly[month][1] += amount

    categories = sorted(
        category_totals.items(), key=lambda item: (-abs(float(item[1][0])), item[0])
    )
    merchants = sorted(
        merchant_totals.items(), key=lambda item: (-abs(float(item[1][0])), item[0])
    )[:10]
    dates = [transaction.txn_date for transaction in transactions]
    return {
        "range": [
            from_date or (min(dates) if dates else None),
            to_date or (max(dates) if dates else None),
        ],
        "totals": {
            "spend": round(spend, 2),
            "income": round(income, 2),
            "net": round(spend + income, 2),
        },
        "by_category": [
            {
                "category": category,
                "total": round(float(values[0]), 2),
                "txn_count": int(values[1]),
            }
            for category, values in categories
        ],
        "monthly": [
            {
                "month": month,
                "spend": round(values[0], 2),
                "income": round(values[1], 2),
            }
            for month, values in sorted(monthly.items())
        ],
        "top_merchants": [
            {
                "merchant": merchant,
                "total": round(float(values[0]), 2),
                "txn_count": int(values[1]),
            }
            for merchant, values in merchants
        ],
    }

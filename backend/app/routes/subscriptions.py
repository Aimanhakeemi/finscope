"""Recurring charge endpoints."""
from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import RecurringGroup, Transaction
from app.recurring import CADENCES
from app.seed import seed_demo_user

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


class SubscriptionResponse(BaseModel):
    recurring_group_id: str
    merchant: str
    cadence: str
    avg_amount: float
    amount_stddev: float
    monthly_cost: float
    first_seen: date
    last_seen: date
    next_expected: date
    occurrences: int
    active: bool
    price_changed: bool


class SubscriptionListResponse(BaseModel):
    subscriptions: list[SubscriptionResponse]
    total_monthly_cost: float
    total_annual_cost: float


def _price_changed(transactions: Sequence[Transaction]) -> bool:
    if len(transactions) < 2 or not transactions[0].amount:
        return False
    first = abs(float(transactions[0].amount))
    last = abs(float(transactions[-1].amount))
    return abs(last - first) / first > 0.05


@router.get("", response_model=SubscriptionListResponse)
def list_subscriptions(
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, Any]:
    user = seed_demo_user(session)
    groups = session.scalars(
        select(RecurringGroup)
        .where(RecurringGroup.user_id == user.id, RecurringGroup.avg_amount < 0)
        .order_by(RecurringGroup.merchant)
    ).all()
    subscriptions: list[dict[str, Any]] = []
    for group in groups:
        transactions = session.scalars(
            select(Transaction)
            .where(Transaction.recurring_group_id == group.id)
            .order_by(Transaction.txn_date, Transaction.id)
        ).all()
        cadence_days = CADENCES[str(group.cadence)][0]
        monthly_cost = abs(float(group.avg_amount)) * 30 / cadence_days
        subscriptions.append(
            {
                "recurring_group_id": str(group.id),
                "merchant": group.merchant,
                "cadence": str(group.cadence),
                "avg_amount": float(group.avg_amount),
                "amount_stddev": float(group.amount_stddev),
                "monthly_cost": round(monthly_cost, 2),
                "first_seen": group.first_seen,
                "last_seen": group.last_seen,
                "next_expected": group.next_expected,
                "occurrences": len(transactions),
                "active": group.active,
                "price_changed": _price_changed(transactions),
            }
        )
    subscriptions.sort(key=lambda item: (-item["monthly_cost"], item["merchant"]))
    monthly = sum(item["monthly_cost"] for item in subscriptions)
    return {
        "subscriptions": subscriptions,
        "total_monthly_cost": round(monthly, 2),
        "total_annual_cost": round(monthly * 12, 2),
    }

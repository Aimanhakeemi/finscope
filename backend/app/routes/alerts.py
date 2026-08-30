"""Anomaly alert endpoints."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Transaction
from app.seed import seed_demo_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertResponse(BaseModel):
    transaction_id: str
    txn_date: date
    description_raw: str
    amount: float
    category: str
    reason: str
    signals: list[str]


class AlertListResponse(BaseModel):
    alerts: list[AlertResponse]


def _signals(reason: str) -> list[str]:
    signals: list[str] = []
    if "statistical outlier" in reason:
        signals.append("robust_z")
    if "IQR fence" in reason:
        signals.append("iqr")
    if "first charge" in reason:
        signals.append("new_large_merchant")
    return signals


@router.get("", response_model=AlertListResponse)
def list_alerts(
    from_date: Optional[date] = Query(None, alias="from"),  # noqa: B008
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, list[dict[str, Any]]]:
    user = seed_demo_user(session)
    start = from_date or (date.today() - timedelta(days=60))
    transactions = session.scalars(
        select(Transaction)
        .where(
            Transaction.user_id == user.id,
            Transaction.is_anomaly.is_(True),
            Transaction.txn_date >= start,
        )
        .order_by(Transaction.txn_date.desc(), Transaction.id)
    ).all()
    return {
        "alerts": [
            {
                "transaction_id": str(transaction.id),
                "txn_date": transaction.txn_date,
                "description_raw": transaction.description_raw,
                "amount": float(transaction.amount),
                "category": str(transaction.category),
                "reason": transaction.anomaly_reason or "Anomalous transaction",
                "signals": _signals(transaction.anomaly_reason or ""),
            }
            for transaction in transactions
        ]
    }

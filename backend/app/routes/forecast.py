"""Spending forecast endpoint."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.forecast import build_forecast
from app.models import Transaction
from app.seed import seed_demo_user

router = APIRouter(prefix="/api", tags=["forecast"])


class ForecastValueResponse(BaseModel):
    point: float
    low: float
    high: float


class CategoryForecastResponse(BaseModel):
    category: str
    point: float
    low: float
    high: float


class ForecastResponse(BaseModel):
    as_of: date
    method: str
    next_month: str
    total_spend: ForecastValueResponse
    by_category: list[CategoryForecastResponse]


@router.get("/forecast", response_model=ForecastResponse)
def get_forecast(
    session: Session = Depends(get_session),  # noqa: B008
) -> ForecastResponse:
    user = seed_demo_user(session)
    transactions = session.scalars(
        select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.txn_date)
    ).all()
    result = build_forecast(transactions)
    return ForecastResponse(
        as_of=result.as_of,
        method=result.method,
        next_month=result.next_month,
        total_spend=ForecastValueResponse(
            point=round(result.total_spend.point, 2),
            low=round(result.total_spend.low, 2),
            high=round(result.total_spend.high, 2),
        ),
        by_category=[
            CategoryForecastResponse(
                category=item.category,
                point=round(item.value.point, 2),
                low=round(item.value.low, 2),
                high=round(item.value.high, 2),
            )
            for item in result.by_category
        ],
    )

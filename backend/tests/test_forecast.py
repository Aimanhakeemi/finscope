from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from app.forecast import build_forecast
from fastapi.testclient import TestClient


def _transactions(months: int):
    return [
        SimpleNamespace(
            txn_date=date(2026, month, 1),
            amount=-float(100 + month),
            category="groceries",
        )
        for month in range(1, months + 1)
    ]


def test_short_history_uses_trailing_median():
    result = build_forecast(_transactions(5))
    assert result.method == "trailing_median"
    assert result.next_month == "2026-06"
    assert result.total_spend.point == -104.0


def test_long_history_uses_ets_and_forecasts_categories():
    result = build_forecast(_transactions(6))
    assert result.method == "ets"
    assert result.next_month == "2026-07"
    assert result.total_spend.low <= result.total_spend.point <= result.total_spend.high
    assert result.by_category[0].category == "groceries"


def test_category_history_uses_seasonal_naive_shape():
    result = build_forecast(_transactions(12))
    assert result.method == "ets"
    assert result.by_category[0].value.point == -101.0


def test_forecast_endpoint_matches_contract(client: TestClient):
    response = client.post(
        "/api/imports",
        files={
            "file": (
                "statement.csv",
                b"date,description,amount\n2026-01-01,COFFEE,-5\n",
                "text/csv",
            )
        },
    )
    assert response.status_code == 201
    response = client.get("/api/forecast")
    assert response.status_code == 200
    assert set(response.json()) == {"as_of", "method", "next_month", "total_spend", "by_category"}

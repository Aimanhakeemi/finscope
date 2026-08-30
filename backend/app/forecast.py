"""Local next-month spending forecasts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np

Z80 = 1.2815515655446004


@dataclass(frozen=True)
class ForecastValue:
    point: float
    low: float
    high: float


@dataclass(frozen=True)
class CategoryForecast:
    category: str
    value: ForecastValue


@dataclass(frozen=True)
class ForecastResult:
    as_of: date
    method: str
    next_month: str
    total_spend: ForecastValue
    by_category: list[CategoryForecast]


def _mad(values: np.ndarray) -> float:
    median = float(np.median(values))
    return float(np.median(np.abs(values - median)))


def _with_interval(point: float, spread: float) -> ForecastValue:
    spread = max(0.0, spread)
    return ForecastValue(point, point - spread, point + spread)


def _trailing_median(values: np.ndarray) -> ForecastValue:
    recent = values[-3:]
    return _with_interval(float(np.median(recent)), 1.5 * _mad(recent))


def _seasonal_naive(values: np.ndarray) -> ForecastValue:
    lag = 12 if len(values) >= 12 else 1
    point = float(values[-lag])
    differences = values[lag:] - values[:-lag]
    spread = Z80 * float(np.std(differences)) if len(differences) > 1 else 1.5 * _mad(values)
    return _with_interval(point, spread)


def _ets(values: np.ndarray) -> ForecastValue:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    fitted = ExponentialSmoothing(
        values,
        trend="add",
        seasonal=None,
        initialization_method="estimated",
    ).fit()
    point = float(fitted.forecast(1)[0])
    residuals = np.asarray(fitted.resid, dtype=float)
    spread = Z80 * float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0
    if not np.isfinite(spread):
        spread = 1.5 * _mad(values)
    return _with_interval(point, spread)


def _forecast_series(values: Sequence[float], use_ets: bool) -> tuple[ForecastValue, str]:
    series = np.asarray(values, dtype=float)
    if len(series) < 6:
        return _trailing_median(series), "trailing_median"
    if not use_ets:
        return _seasonal_naive(series), "seasonal_naive"
    try:
        return _ets(series), "ets"
    except (ValueError, RuntimeError, np.linalg.LinAlgError):
        return _trailing_median(series), "trailing_median"


def _field(item: Any, name: str) -> Any:
    if isinstance(item, Mapping):
        return item[name]
    return getattr(item, name)


def _next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def build_forecast(transactions: Sequence[Any]) -> ForecastResult:
    rows: list[tuple[date, float, str]] = [
        (_field(item, "txn_date"), float(_field(item, "amount")), str(_field(item, "category")))
        for item in transactions
        if float(_field(item, "amount")) < 0
    ]
    if not rows:
        today = date.today()
        zero = ForecastValue(0.0, 0.0, 0.0)
        return ForecastResult(
            today, "trailing_median", _next_month(today).strftime("%Y-%m"), zero, []
        )

    first_month = min(row[0] for row in rows).replace(day=1)
    last_date = max(row[0] for row in rows)
    last_month = last_date.replace(day=1)
    months: list[date] = []
    current = first_month
    while current <= last_month:
        months.append(current)
        current = _next_month(current)

    totals = {month: 0.0 for month in months}
    categories = sorted({row[2] for row in rows})
    by_category = {category: {month: 0.0 for month in months} for category in categories}
    for txn_date, amount, category in rows:
        month = txn_date.replace(day=1)
        totals[month] += amount
        by_category[category][month] += amount

    total_value, method = _forecast_series([totals[month] for month in months], use_ets=True)
    category_forecasts = []
    for category in categories:
        values = [by_category[category][month] for month in months]
        value, _ = _forecast_series(values, use_ets=False)
        category_forecasts.append(CategoryForecast(category, value))
    category_forecasts.sort(key=lambda item: (-abs(item.value.point), item.category))
    return ForecastResult(
        as_of=last_date,
        method=method,
        next_month=_next_month(last_month).strftime("%Y-%m"),
        total_spend=total_value,
        by_category=category_forecasts,
    )

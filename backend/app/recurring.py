"""Recurring-payment detection.

Rule-based and fully explainable: a merchant is "recurring" when its charges
arrive on a regular cadence AND the amount is stable.

This module has no framework dependencies so it is trivial to unit-test.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import date, timedelta

# cadence label -> (nominal days, tolerance in days)
CADENCES: dict[str, tuple[int, int]] = {
    "weekly": (7, 2),
    "biweekly": (14, 3),
    "monthly": (30, 5),
    "quarterly": (91, 10),
    "annual": (365, 20),
}

MIN_OCCURRENCES = 3
MAX_AMOUNT_CV = 0.25  # stddev / mean


@dataclass(frozen=True)
class Transaction:
    merchant: str
    txn_date: date
    amount: float  # negative = outflow


@dataclass(frozen=True)
class RecurringGroup:
    merchant: str
    cadence: str
    avg_amount: float
    amount_stddev: float
    first_seen: date
    last_seen: date
    next_expected: date
    occurrences: int

    @property
    def monthly_cost(self) -> float:
        nominal, _ = CADENCES[self.cadence]
        return abs(self.avg_amount) * (30.0 / nominal)


def _match_cadence(median_gap: float) -> str | None:
    for label, (nominal, tol) in CADENCES.items():
        if abs(median_gap - nominal) <= tol:
            return label
    return None


def detect_recurring(
    transactions: list[Transaction], today: date | None = None
) -> list[RecurringGroup]:
    """Return the recurring groups found in ``transactions``."""
    today = today or date.today()

    by_merchant: dict[str, list[Transaction]] = {}
    for t in transactions:
        by_merchant.setdefault(t.merchant, []).append(t)

    groups: list[RecurringGroup] = []
    for merchant, txns in by_merchant.items():
        if len(txns) < MIN_OCCURRENCES:
            continue

        txns = sorted(txns, key=lambda t: t.txn_date)
        gaps = [
            (b.txn_date - a.txn_date).days
            for a, b in zip(txns, txns[1:])  # noqa: B905
            if b.txn_date != a.txn_date
        ]
        if len(gaps) < MIN_OCCURRENCES - 1:
            continue

        median_gap = statistics.median(gaps)
        cadence = _match_cadence(median_gap)
        if cadence is None:
            continue

        amounts = [abs(t.amount) for t in txns]
        mean_amt = statistics.fmean(amounts)
        stdev_amt = statistics.pstdev(amounts) if len(amounts) > 1 else 0.0
        if mean_amt == 0 or (stdev_amt / mean_amt) > MAX_AMOUNT_CV:
            continue

        nominal, _ = CADENCES[cadence]
        last_seen = txns[-1].txn_date
        groups.append(
            RecurringGroup(
                merchant=merchant,
                cadence=cadence,
                avg_amount=round(statistics.fmean([t.amount for t in txns]), 2),
                amount_stddev=round(stdev_amt, 2),
                first_seen=txns[0].txn_date,
                last_seen=last_seen,
                next_expected=last_seen + timedelta(days=nominal),
                occurrences=len(txns),
            )
        )

    return sorted(groups, key=lambda g: g.monthly_cost, reverse=True)


def is_active(group: RecurringGroup, today: date | None = None) -> bool:
    today = today or date.today()
    nominal, _ = CADENCES[group.cadence]
    return (today - group.last_seen).days <= nominal * 1.5

"""Anomaly detection over outflows, per category.

A transaction is flagged when >= 2 independent signals fire, which keeps the
false-positive rate low (see docs/EVALUATION.md).
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass

ROBUST_Z_CUTOFF = 3.5
IQR_K = 1.5
NEW_MERCHANT_PERCENTILE = 0.90


@dataclass(frozen=True)
class Flag:
    index: int
    reason: str
    signals: tuple[str, ...] = ()


def _robust_z(x: float, values: list[float]) -> float:
    med = statistics.median(values)
    mad = statistics.median([abs(v - med) for v in values]) or 1e-9
    return 0.6745 * (x - med) / mad


def _iqr_bounds(values: list[float]) -> tuple[float, float]:
    s = sorted(values)
    q1 = s[len(s) // 4]
    q3 = s[(3 * len(s)) // 4]
    iqr = q3 - q1
    return q1 - IQR_K * iqr, q3 + IQR_K * iqr


def detect_anomalies(
    amounts: list[float],
    categories: list[str],
    merchants: list[str],
) -> list[Flag]:
    """`amounts` are signed; only outflows (negative) are considered."""
    outflow_idx = [i for i, a in enumerate(amounts) if a < 0]
    all_outflows = sorted(abs(amounts[i]) for i in outflow_idx)
    if not all_outflows:
        return []
    big_cut = all_outflows[int(len(all_outflows) * NEW_MERCHANT_PERCENTILE) - 1]

    by_cat: dict[str, list[float]] = {}
    for i in outflow_idx:
        by_cat.setdefault(categories[i], []).append(abs(amounts[i]))

    seen_merchants: set[str] = set()
    flags: list[Flag] = []
    for i in outflow_idx:
        amt = abs(amounts[i])
        cat_values = by_cat[categories[i]]
        # ponytail: sparse categories borrow the global baseline; use hierarchical
        # statistics if anomaly volume or category count later makes this too coarse.
        reference_values = cat_values if len(cat_values) >= 4 else all_outflows
        signals: list[str] = []

        if len(reference_values) >= 4:
            if abs(_robust_z(amt, reference_values)) > ROBUST_Z_CUTOFF:
                signals.append(f"{amt:.0f} is a statistical outlier for {categories[i]}")
            _lo, hi = _iqr_bounds(reference_values)
            if amt > hi:
                signals.append(f"{amt:.0f} exceeds the IQR fence for {categories[i]}")

        if merchants[i] not in seen_merchants and amt >= big_cut:
            signals.append("first charge from this merchant, and a large amount")

        seen_merchants.add(merchants[i])

        if len(signals) >= 2:
            signal_names = tuple(
                name
                for name, condition in (
                    ("robust_z", "statistical outlier" in " ".join(signals)),
                    ("iqr", "IQR fence" in " ".join(signals)),
                    ("new_large_merchant", "first charge" in " ".join(signals)),
                )
                if condition
            )
            flags.append(Flag(i, "; ".join(signals), signal_names))

    return flags

"""Generate a deterministic synthetic bank statement + ground-truth labels.

Usage:
    python data/generate_synthetic.py --months 12 --seed 42 \
        --out data/sample_statement.csv

Also writes <out stem>.labels.csv with the true category and recurring flag for
every row, for use by the evaluation harness.
"""
from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

# (merchant, category, typical_amount, jitter)
ONE_OFF_MERCHANTS = [
    ("TARGET STORE 1123", "shopping", -60, 40),
    ("AMZN MKTP US*2X4B1", "shopping", -35, 30),
    ("SHELL OIL 574112", "fuel", -48, 12),
    ("CHEVRON 220481", "fuel", -45, 12),
    ("UBER *TRIP", "transport", -18, 10),
    ("LYFT *RIDE", "transport", -16, 9),
    ("CVS/PHARMACY #4471", "health", -24, 18),
    ("MCDONALD'S F1123", "dining", -12, 6),
    ("CHIPOTLE 2231", "dining", -14, 5),
    ("STARBUCKS STORE 119", "coffee", -6, 2),
    ("BLUE BOTTLE COFFEE", "coffee", -7, 2),
    ("TRADER JOE'S #201", "groceries", -55, 25),
    ("WHOLE FOODS MKT", "groceries", -70, 30),
]

RECURRING_MERCHANTS = [
    # (merchant, category, amount, cadence_days)
    ("NETFLIX.COM", "subscriptions", -15.49, 30),
    ("SPOTIFY USA", "subscriptions", -10.99, 30),
    ("ICLOUD+ STORAGE", "subscriptions", -2.99, 30),
    ("PLANET FITNESS", "health", -24.99, 30),
    ("THE NEW YORK TIMES", "subscriptions", -4.25, 7),
    ("STATE FARM INSURANCE", "utilities", -120.00, 30),
    ("CITY WATER & POWER", "utilities", -85.00, 30),
]

RENT = ("GREENFIELD APARTMENTS", "rent_mortgage", -1850.00, 30)
SALARY = ("ACME CORP PAYROLL", "income", 3200.00, 14)


def daterange_months(start: date, months: int):
    d = start
    for _ in range(months * 31):
        yield d
        d += timedelta(days=1)
        if (d - start).days > months * 30:
            return


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=12)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=Path("data/sample_statement.csv"))
    args = ap.parse_args()

    rng = random.Random(args.seed)
    end = date(2026, 8, 1)
    start = end - timedelta(days=args.months * 30)

    rows: list[dict] = []

    def add(d: date, merchant: str, category: str, amount: float, recurring: bool):
        rows.append(
            {
                "date": d.isoformat(),
                "description": merchant,
                "amount": f"{amount:.2f}",
                "_category": category,
                "_recurring": "1" if recurring else "0",
            }
        )

    # Salary every 14 days
    d = start
    while d <= end:
        add(d, SALARY[0], SALARY[1], SALARY[2] + rng.uniform(-50, 50), True)
        d += timedelta(days=SALARY[3])

    # Rent monthly on the 1st
    d = start.replace(day=1)
    while d <= end:
        add(d, RENT[0], RENT[1], RENT[2], True)
        # advance one month
        d = (d.replace(day=28) + timedelta(days=7)).replace(day=1)

    # Recurring subscriptions
    for merchant, cat, amt, cadence in RECURRING_MERCHANTS:
        d = start + timedelta(days=rng.randint(0, cadence))
        price = amt
        while d <= end:
            # inject a price hike on Netflix halfway through
            if merchant == "NETFLIX.COM" and (d - start).days > args.months * 15:
                price = -17.99
            add(d, merchant, cat, price, True)
            d += timedelta(days=cadence + rng.randint(-1, 1))

    # Weekly groceries + frequent coffee/dining
    for d in daterange_months(start, args.months):
        if d > end:
            break
        if d.weekday() == 5:  # Saturday grocery run
            m, cat, base, jit = rng.choice(
                [x for x in ONE_OFF_MERCHANTS if x[1] == "groceries"]
            )
            add(d, m, cat, base + rng.uniform(-jit, jit), False)
        if rng.random() < 0.5:  # coffee
            m, cat, base, jit = rng.choice(
                [x for x in ONE_OFF_MERCHANTS if x[1] == "coffee"]
            )
            add(d, m, cat, base + rng.uniform(-jit, jit), False)
        if rng.random() < 0.35:  # dining / misc
            m, cat, base, jit = rng.choice(
                [x for x in ONE_OFF_MERCHANTS if x[1] not in ("coffee", "groceries")]
            )
            add(d, m, cat, base + rng.uniform(-jit, jit), False)

    # Deliberate anomalies
    mid = start + timedelta(days=args.months * 15)
    add(mid, "BIG APPLIANCE WAREHOUSE", "shopping", -1240.00, False)          # large one-off
    add(mid + timedelta(days=2), "AMZN MKTP US*2X4B1", "shopping", -35.00, False)
    add(mid + timedelta(days=2), "AMZN MKTP US*2X4B1", "shopping", -35.00, False)  # dup-looking
    add(end - timedelta(days=5), "OVERSEAS ATM WITHDRAWAL", "other", -600.00, False)

    rows.sort(key=lambda r: r["date"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "description", "amount"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in ("date", "description", "amount")})

    labels = args.out.with_suffix(".labels.csv")
    with labels.open("w", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=["date", "description", "amount", "category", "recurring"]
        )
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    "date": r["date"],
                    "description": r["description"],
                    "amount": r["amount"],
                    "category": r["_category"],
                    "recurring": r["_recurring"],
                }
            )

    print(f"Wrote {len(rows)} transactions -> {args.out}")
    print(f"Wrote labels -> {labels}")


if __name__ == "__main__":
    main()

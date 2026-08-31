"""Generate a deterministic synthetic bank statement + ground-truth labels.

Usage:
    python data/generate_synthetic.py --months 12 --seed 42 \
        --split all --out data/sample_statement.csv

Also writes <out stem>.labels.csv with the true category and recurring flag for
every row, for use by the evaluation harness.
"""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass(frozen=True)
class MerchantProfile:
    variants: tuple[str, ...]
    category: str
    typical_amount: float
    jitter: float


def merchant(
    variants: tuple[str, ...], category: str, typical_amount: float, jitter: float
) -> MerchantProfile:
    if not 3 <= len(variants) <= 6:
        raise ValueError("merchant profiles need 3-6 variants")
    return MerchantProfile(variants, category, typical_amount, jitter)


ONE_OFF_MERCHANTS = (
    merchant(
        (
            "TARGET RETAIL STORE 1123",
            "TARGET #1123",
            "TGT SOUTH LAKE UNION",
            "TARGET RETAIL SEATTLE",
        ),
        "shopping",
        -60,
        40,
    ),
    merchant(
        (
            "AMZN MKTP US*2X4B1",
            "AMAZON MARKETPLACE",
            "AMZN ONLINE ORDER 84731",
            "AMZN MKTPLACE SEATTLE",
        ),
        "shopping",
        -35,
        30,
    ),
    merchant(
        ("SHELL GAS FUEL 574112", "SHELL #574112", "SHELL FUEL TACOMA", "SH OIL 574112"),
        "fuel",
        -48,
        12,
    ),
    merchant(
        ("CHEVRON 220481", "CHEVRON #220481", "CHEV FUEL BELLEVUE", "CHEVRON SERVICE 220481"),
        "fuel",
        -45,
        12,
    ),
    merchant(
        ("UBER *TRIP", "UBER TRANSIT RIDE", "UBR RIDE SEATTLE", "UBER *EATS RIDE"),
        "transport",
        -18,
        10,
    ),
    merchant(
        ("LYFT *RIDE", "LYFT RIDE", "LYFT MOBILITY 771", "LYFT SEATTLE WA"),
        "transport",
        -16,
        9,
    ),
    merchant(
        ("CVS HEALTH 4471", "CVS/PHARMACY #4471", "CVS PHARMACY", "CVS STORE SEATTLE"),
        "health",
        -24,
        18,
    ),
    merchant(
        (
            "MCDONALD'S RESTAURANT F1123",
            "MCDONALDS DINING #1123",
            "MCD F1123 SEATTLE",
            "MCDONALDS RESTAURANT",
        ),
        "dining",
        -12,
        6,
    ),
    merchant(
        (
            "CHIPOTLE RESTAURANT 2231",
            "CHIPOTLE #2231",
            "CHIPOTLE MEXICAN GRILL",
            "CHIPOTLE SEATTLE",
        ),
        "dining",
        -14,
        5,
    ),
    merchant(
        ("STARBUCKS STORE 119", "STARBUCKS #119", "SBUX 4471 SEATTLE WA", "STARBUCKS PIKE PLACE"),
        "coffee",
        -6,
        2,
    ),
    merchant(
        ("BLUE BOTTLE COFFEE", "BLUE BOTTLE #12", "BLUE BOTTLE OAKLAND", "BBC COFFEE HOUSE"),
        "coffee",
        -7,
        2,
    ),
    merchant(
        ("TRADER JOE'S #201", "TRADER JOES 201", "TRADER JOES CAPITOL HILL", "TJ GROCERY 201"),
        "groceries",
        -55,
        25,
    ),
    merchant(
        ("WHOLE FOODS MKT", "WHOLE FOODS #104", "WHOLE FDS MARKET SEATTLE", "WHOLE FOODS GROCERY"),
        "groceries",
        -70,
        30,
    ),
    merchant(
        ("AMC THEATRES LIVE SHOW 14", "AMC MOVIE #14", "AMC MOVIE SEATTLE", "AMC CINEMA 14"),
        "entertainment",
        -25,
        15,
    ),
    merchant(
        (
            "USPS POST OFFICE SERVICE FEE",
            "US POSTAL SERVICE",
            "POST OFFICE SEATTLE",
            "USPS RETAIL 441",
        ),
        "other",
        -15,
        4,
    ),
    merchant(
        (
            "RENTAL PROPERTY SERVICE",
            "RENTAL HOUSING FEE",
            "LEASE PAYMENT SERVICE",
            "HOUSING RENTAL FEE",
        ),
        "rent_mortgage",
        -1800,
        80,
    ),
    merchant(
        ("PAYPAL CASHOUT", "PAYPAL SELLER CREDIT", "PAYPAL PAYOUT", "ONLINE PAYMENT DEPOSIT"),
        "income",
        250,
        100,
    ),
    merchant(
        ("ADOBE CREATIVE CLOUD", "ADOBE DIGITAL PLAN", "CREATIVE CLOUD #2", "ADOBE SOFTWARE"),
        "subscriptions",
        -24,
        6,
    ),
    merchant(
        ("COMCAST INTERNET BILL", "COMCAST HOME INTERNET", "CABLE INTERNET BILL", "CMST INTERNET"),
        "utilities",
        -78,
        14,
    ),
    merchant(
        ("FERRY TRANSIT PASS", "FERRY COMMUTE", "FERRY TRANSIT #4", "HARBOR TRANSIT"),
        "transport",
        -14,
        6,
    ),
    merchant(
        ("CONCERT TICKETS", "LIVE MUSIC TICKETS", "CONCERT VENUE #3", "LIVE SHOW TICKETS"),
        "entertainment",
        -45,
        20,
    ),
)

RECURRING_MERCHANTS = (
    merchant(
        ("NETFLIX.COM", "netflix.com", "POS * NETFLIX.COM", "NETFLIX.COM #001"),
        "subscriptions",
        -15.49,
        0,
    ),
    merchant(
        ("SPOTIFY USA", "spotify usa", "POS * SPOTIFY USA", "SPOTIFY USA #001"),
        "subscriptions",
        -10.99,
        0,
    ),
    merchant(
        (
            "ICLOUD+ STORAGE, DIGITAL, WA",
            "icloud+ storage",
            "POS * ICLOUD+ STORAGE",
            "ICLOUD+ STORAGE #001",
        ),
        "subscriptions",
        -2.99,
        0,
    ),
    merchant(
        ("PLANET FITNESS", "planet fitness", "POS * PLANET FITNESS", "PLANET FITNESS #001"),
        "health",
        -24.99,
        0,
    ),
    merchant(
        (
            "THE NEW YORK TIMES",
            "the new york times",
            "POS * THE NEW YORK TIMES",
            "THE NEW YORK TIMES #001",
        ),
        "subscriptions",
        -4.25,
        0,
    ),
    merchant(
        (
            "STATE FARM INSURANCE, UTILITY, WA",
            "state farm insurance",
            "POS * STATE FARM INSURANCE",
            "STATE FARM INSURANCE #001",
        ),
        "utilities",
        -120.00,
        0,
    ),
    merchant(
        (
            "CITY WATER & POWER, UTILITY, WA",
            "city water & power",
            "POS * CITY WATER & POWER",
            "CITY WATER & POWER #001",
        ),
        "utilities",
        -85.00,
        0,
    ),
)

LONG_TAIL_MERCHANTS: dict[str, tuple[MerchantProfile, ...]] = {
    "groceries": (
        merchant(
            (
                "FREMONT FARMERS MARKET",
                "FREMONT FARMERS MKT",
                "FARMERS MKT FREMONT",
                "FFM MARKET 88",
            ),
            "groceries",
            -42,
            22,
        ),
        merchant(
            ("MARTIN'S GROCERY", "MARTINS MARKET 44", "MARTIN GROCERY TACOMA", "MARTINS FOOD HALL"),
            "groceries",
            -64,
            28,
        ),
        merchant(
            ("RAINIER CO-OP", "RAINIER FOOD COOP", "RAINIER COOP #8", "RNR FOOD MARKET"),
            "groceries",
            -38,
            18,
        ),
    ),
    "dining": (
        merchant(
            ("TAMARIND KITCHEN", "TAMARIND KITCHEN #4", "TAMARIND RESTAURANT", "TMRD DINER"),
            "dining",
            -18,
            7,
        ),
        merchant(
            ("PIKE STREET NOODLES", "PIKE ST NOODLES", "PIKE NOODLES RESTAURANT", "PSN DINER"),
            "dining",
            -16,
            6,
        ),
        merchant(
            ("NORTHWEST TACOS", "NW TACOS SEATTLE", "NORTHWEST TACO RESTAURANT", "NWT FOOD TRUCK"),
            "dining",
            -14,
            5,
        ),
    ),
    "coffee": (
        merchant(
            ("JUNIPER ROASTERS", "JUNIPER COFFEE", "JUNIPER ROAST #7", "JNR COFFEE"),
            "coffee",
            -7,
            2,
        ),
        merchant(
            ("HARBOR BEAN CO", "HARBOR BEAN CAFE", "HARBOR BEAN #2", "HBC COFFEE"), "coffee", -7, 2
        ),
        merchant(
            ("CEDAR CUP", "CEDAR CUP CAFE", "CEDAR CUP #6", "CDC COFFEE BAR"), "coffee", -6, 2
        ),
    ),
    "transport": (
        merchant(
            ("SEATTLE TAXI UNION", "SEA TAXI UNION", "SEATTLE TRANSIT TAXI #21", "STU CAB FARE"),
            "transport",
            -20,
            8,
        ),
        merchant(
            ("SOUND TRANSIT", "SOUND TRANSIT ORCA", "SND TRANSIT #7", "SOUND BUS FARE"),
            "transport",
            -5,
            3,
        ),
        merchant(
            ("HARBOR FERRY", "HARBOR FERRY PASS", "HARBOR FERRY #3", "HFRY TICKET"),
            "transport",
            -14,
            7,
        ),
    ),
    "fuel": (
        merchant(
            ("ARCO FUEL 778", "ARCO #778", "ARCO GAS TACOMA", "ARCO STATION 778"), "fuel", -46, 12
        ),
        merchant(
            ("76 STATION", "76 GAS #44", "76 FUEL BELLEVUE", "SEVENTY SIX STATION"), "fuel", -43, 11
        ),
        merchant(
            ("COSTCO FUEL", "COSTCO GAS #6", "COSTCO FUEL SEATTLE", "CST FUEL CENTER"),
            "fuel",
            -51,
            14,
        ),
    ),
    "utilities": (
        merchant(
            ("COMCAST CABLE", "COMCAST INTERNET", "COMCAST #22", "CMST HOME NET"),
            "utilities",
            -78,
            14,
        ),
        merchant(
            ("PUGET ELECTRIC", "PUGET ELEC CO", "PUGET POWER #5", "PUGET ELECTRIC BILL"),
            "utilities",
            -92,
            8,
        ),
        merchant(
            ("NORTHWEST MOBILE", "NW MOBILE BILL", "NORTHWEST CELL #3", "NWM UTILITY BILL"),
            "utilities",
            -84,
            14,
        ),
    ),
    "rent_mortgage": (
        merchant(
            (
                "PARKVIEW PROPERTY MGMT",
                "PARKVIEW PROP MGMT",
                "PARKVIEW RENT #4",
                "PV PROPERTY RENT",
            ),
            "rent_mortgage",
            -1780,
            65,
        ),
        merchant(
            (
                "LAKE UNION LOFTS",
                "LAKE UNION LOFT RENT",
                "LAKE UNION LEASE #2",
                "LUL PROPERTY RENT",
            ),
            "rent_mortgage",
            -1820,
            65,
        ),
        merchant(
            ("EVERGREEN MORTGAGE", "EVERGREEN HOME LOAN", "EVERGREEN MTG #7", "EG HOME FINANCE"),
            "rent_mortgage",
            -1760,
            65,
        ),
    ),
    "subscriptions": (
        merchant(
            ("HULU STREAMING", "HULU STREAM #7", "HULU DIGITAL", "HULU MEDIA"),
            "subscriptions",
            -18,
            4,
        ),
        merchant(
            ("DISNEY PLUS", "DISNEY+ DIGITAL", "DISNEY PLUS #9", "DISNEY STREAM"),
            "subscriptions",
            -14,
            4,
        ),
        merchant(
            ("ADOBE CREATIVE CLOUD", "ADOBE CC PLAN", "ADOBE CLOUD #2", "ADOBE DIGITAL"),
            "subscriptions",
            -24,
            6,
        ),
    ),
    "shopping": (
        merchant(
            ("NORDSTROM RACK", "NORDSTROM RACK #4", "NORD RACK SEATTLE", "NORDSTROM CLEARANCE"),
            "shopping",
            -88,
            45,
        ),
        merchant(
            ("REI CO-OP", "REI OUTDOOR #9", "REI SEATTLE", "REI MEMBER STORE"), "shopping", -74, 38
        ),
        merchant(
            ("HOME DEPOT", "HOME DEPOT #12", "HOME DEPOT SEATTLE", "HD HARDWARE STORE"),
            "shopping",
            -96,
            50,
        ),
    ),
    "health": (
        merchant(
            ("WALGREENS PHARMACY", "WALGREENS #71", "WALGREENS HEALTH", "WGN PHARMACY"),
            "health",
            -29,
            12,
        ),
        merchant(
            ("GREENLAKE DENTAL", "GREENLAKE DENTAL #2", "GREENLAKE DENTAL CARE", "GL DENTAL"),
            "health",
            -34,
            14,
        ),
        merchant(
            ("MOTION PHYSICAL THERAPY", "MOTION PT CLINIC", "MOTION THERAPY #3", "MPT HEALTH"),
            "health",
            -32,
            14,
        ),
    ),
    "entertainment": (
        merchant(
            ("PARAMOUNT THEATRE", "PARAMOUNT THEATER #4", "PARAMOUNT LIVE SHOW", "PMT LIVE SHOW"),
            "entertainment",
            -38,
            18,
        ),
        merchant(
            ("SEATTLE AQUARIUM", "SEA AQUARIUM #2", "SEATTLE AQUARIUM TICKETS", "SAQ ADMISSION"),
            "entertainment",
            -34,
            16,
        ),
        merchant(
            ("NORTHWEST MUSIC HALL", "NW MUSIC HALL #8", "NORTHWEST LIVE MUSIC", "NWMH TICKETS"),
            "entertainment",
            -36,
            17,
        ),
    ),
    "income": (
        merchant(
            (
                "FREELANCE DESIGN DEPOSIT",
                "FREELANCE DESIGN PAY",
                "DESIGN PROJECT PAY #4",
                "FREELANCE INVOICE",
            ),
            "income",
            650,
            180,
        ),
        merchant(
            (
                "MARKETPLACE SELLER PAY",
                "MARKETPLACE PAYOUT",
                "SELLER PAYOUT #8",
                "ONLINE SALES DEPOSIT",
            ),
            "income",
            280,
            120,
        ),
        merchant(
            ("CASHBACK REWARD", "CARD CASHBACK", "CASHBACK REWARD #3", "REWARD CREDIT"),
            "income",
            42,
            18,
        ),
    ),
    "other": (
        merchant(
            ("CITY PERMIT OFFICE", "CITY PERMIT FEE", "CITY PERMIT #4", "MUNICIPAL PERMIT"),
            "other",
            -15,
            4,
        ),
        merchant(
            (
                "POSTAL MONEY ORDER",
                "POSTAL MONEY ORDER #2",
                "POSTAL MONEY ORDER FEE",
                "USPS MONEY ORDER",
            ),
            "other",
            -15,
            4,
        ),
        merchant(
            (
                "MISCELLANEOUS SERVICE FEE",
                "MISC SERVICE FEE #6",
                "ACCOUNT SERVICE FEE",
                "MISC BANK FEE",
            ),
            "other",
            -12,
            4,
        ),
    ),
}

AMBIGUOUS_MERCHANTS = (
    merchant(
        (
            "COSTCO WHOLESALE GAS & MARKET",
            "COSTCO WAREHOUSE FUEL",
            "COSTCO MARKET & GAS",
            "CST WHOLESALE GAS",
        ),
        "groceries",
        -96,
        24,
    ),
    merchant(
        (
            "WALMART SUPERCENTER GROCERY & GAS",
            "WALMART MARKET FUEL",
            "WALMART SUPERSTORE #8",
            "WMT GROCERY GAS",
        ),
        "groceries",
        -82,
        28,
    ),
    merchant(
        (
            "AIRPORT HOTEL PARKING",
            "AIRPORT HOTEL & GARAGE",
            "HOTEL SHUTTLE PARKING",
            "SEA HOTEL PARKING",
        ),
        "transport",
        -22,
        8,
    ),
    merchant(
        (
            "DOWNTOWN HOTEL SHOW",
            "HOTEL LOUNGE EVENT",
            "HOTEL BALLROOM TICKETS",
            "CITY HOTEL ENTERTAINMENT",
        ),
        "entertainment",
        -48,
        20,
    ),
)

SALARY = merchant(
    (
        "ACME CORP PAYROLL, DIRECT DEPOSIT, WA",
        "acme corp payroll",
        "POS * ACME CORP PAYROLL",
        "ACME CORP PAYROLL #001",
    ),
    "income",
    3200.00,
    0,
)
RENT = merchant(
    (
        "GREENFIELD APARTMENTS, PROPERTY RENT, WA",
        "greenfield apartments",
        "POS * GREENFIELD APARTMENTS",
        "GREENFIELD APARTMENTS #001",
    ),
    "rent_mortgage",
    -1850.00,
    0,
)


def daterange_months(start: date, months: int):
    d = start
    for _ in range(months):
        next_month = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
        while d < next_month:
            yield d
            d += timedelta(days=1)


def _variant(profile: MerchantProfile, rng: random.Random, split: str) -> str:
    if split == "all":
        variants = profile.variants
    else:
        midpoint = len(profile.variants) // 2
        variants = profile.variants[:midpoint] if split == "train" else profile.variants[midpoint:]
    return rng.choice(variants)


def _amount(profile: MerchantProfile, rng: random.Random) -> float:
    return profile.typical_amount + rng.uniform(-profile.jitter, profile.jitter)


def _recurring_amount(amount: float, rng: random.Random) -> float:
    return amount * (1 + rng.uniform(-0.025, 0.025))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=12)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--split", choices=("all", "train", "eval"), default="all")
    ap.add_argument("--out", type=Path, default=Path("data/sample_statement.csv"))
    args = ap.parse_args()
    if args.months < 1:
        ap.error("--months must be positive")

    rng = random.Random(args.seed)
    end = date(2026, 7, 31)
    month_index = end.year * 12 + end.month - 1 - (args.months - 1)
    start_year, start_month = divmod(month_index, 12)
    start = date(start_year, start_month + 1, 1)
    span_days = (end - start).days
    midpoint = start + timedelta(days=span_days // 2)

    rows: list[dict[str, str]] = []

    def add(d: date, profile: MerchantProfile, amount: float, recurring: bool) -> None:
        rows.append(
            {
                "date": d.isoformat(),
                "description": _variant(profile, rng, args.split),
                "amount": f"{amount:.2f}",
                "category": profile.category,
                "recurring": "1" if recurring else "0",
            }
        )

    # Salary every 14 days and rent monthly on the 1st.
    d = start
    while d <= end:
        add(d, SALARY, _recurring_amount(SALARY.typical_amount, rng), True)
        d += timedelta(days=14)

    d = start.replace(day=1)
    while d <= end:
        add(d, RENT, _recurring_amount(RENT.typical_amount, rng), True)
        d = (d.replace(day=28) + timedelta(days=7)).replace(day=1)

    # Recurring subscriptions and bills. Their punctuation/casing variants
    # normalize to one merchant, so amount noise does not erase the pattern.
    for profile, cadence in zip(  # noqa: B905
        RECURRING_MERCHANTS, (30, 30, 30, 30, 7, 30, 30)
    ):
        d = start + timedelta(days=rng.randint(0, cadence))
        price = profile.typical_amount
        while d <= end:
            if profile.variants[0] == "NETFLIX.COM" and d > midpoint:
                price = -17.99
            add(d, profile, _recurring_amount(price, rng), True)
            d += timedelta(days=cadence + rng.randint(-1, 1))

    # Frequent everyday spending.
    for d in daterange_months(start, args.months):
        if d > end:
            break
        if d.weekday() == 5:
            profile = rng.choice(tuple(p for p in ONE_OFF_MERCHANTS if p.category == "groceries"))
            add(d, profile, _amount(profile, rng), False)
        if rng.random() < 0.5:
            profile = rng.choice(tuple(p for p in ONE_OFF_MERCHANTS if p.category == "coffee"))
            add(d, profile, _amount(profile, rng), False)
        if rng.random() < 0.35:
            profile = rng.choice(
                tuple(p for p in ONE_OFF_MERCHANTS if p.category not in ("coffee", "groceries"))
            )
            add(d, profile, _amount(profile, rng), False)

    # Long-tail merchants are absent from train and rare in eval.
    if args.split != "train":
        for profiles in LONG_TAIL_MERCHANTS.values():
            for profile in profiles:
                for _ in range(rng.randint(2, 4)):
                    d = start + timedelta(days=rng.randint(0, span_days))
                    add(d, profile, _amount(profile, rng), False)

        # About 1.5% of the eval rows use a deliberately ambiguous merchant.
        ambiguous_count = max(1, round(len(rows) * 0.015))
        for _ in range(ambiguous_count):
            profile = rng.choice(AMBIGUOUS_MERCHANTS)
            d = start + timedelta(days=rng.randint(0, span_days))
            add(d, profile, _amount(profile, rng), False)

    # Stable anomaly identities: the fixture intentionally references these.
    mid = midpoint
    rows.extend(
        [
            {
                "date": mid.isoformat(),
                "description": "BIG APPLIANCE WAREHOUSE",
                "amount": "-1240.00",
                "category": "shopping",
                "recurring": "0",
            },
            {
                "date": (mid + timedelta(days=2)).isoformat(),
                "description": "AMZN MKTP US*2X4B1",
                "amount": "-35.00",
                "category": "shopping",
                "recurring": "0",
            },
            {
                "date": (mid + timedelta(days=2)).isoformat(),
                "description": "AMZN MKTP US*2X4B1",
                "amount": "-35.00",
                "category": "shopping",
                "recurring": "0",
            },
            {
                "date": (end - timedelta(days=5)).isoformat(),
                "description": "OVERSEAS ATM WITHDRAWAL",
                "amount": "-600.00",
                "category": "other",
                "recurring": "0",
            },
        ]
    )

    rows.sort(key=lambda row: row["date"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "description", "amount"])
        w.writeheader()
        for row in rows:
            w.writerow({key: row[key] for key in ("date", "description", "amount")})

    labels = args.out.with_suffix(".labels.csv")
    with labels.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "description", "amount", "category", "recurring"])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} transactions -> {args.out}")
    print(f"Wrote labels -> {labels}")


if __name__ == "__main__":
    main()

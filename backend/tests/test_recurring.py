from datetime import date, timedelta

from app.recurring import Transaction, detect_recurring, is_active


def _series(merchant: str, start: date, cadence_days: int, n: int, amount: float):
    return [
        Transaction(merchant, start + timedelta(days=cadence_days * i), amount)
        for i in range(n)
    ]


def test_detects_monthly_subscription():
    txns = _series("NETFLIX.COM", date(2026, 1, 3), 30, 8, -15.49)
    groups = detect_recurring(txns, today=date(2026, 8, 29))

    assert len(groups) == 1
    g = groups[0]
    assert g.merchant == "NETFLIX.COM"
    assert g.cadence == "monthly"
    assert round(g.monthly_cost, 2) == 15.49


def test_ignores_irregular_merchant():
    txns = [
        Transaction("CORNER STORE", date(2026, 1, 1), -5),
        Transaction("CORNER STORE", date(2026, 1, 9), -22),
        Transaction("CORNER STORE", date(2026, 3, 2), -8),
        Transaction("CORNER STORE", date(2026, 6, 20), -40),
    ]
    assert detect_recurring(txns, today=date(2026, 8, 29)) == []


def test_rejects_unstable_amounts():
    # regular cadence but wildly varying amounts -> not a subscription
    txns = [
        Transaction("VARIABLE LLC", date(2026, 1, 1) + timedelta(days=30 * i), amt)
        for i, amt in enumerate([-10, -80, -15, -120, -12])
    ]
    assert detect_recurring(txns, today=date(2026, 8, 29)) == []


def test_active_flag():
    txns = _series("SPOTIFY USA", date(2025, 1, 5), 30, 6, -10.99)
    g = detect_recurring(txns, today=date(2026, 8, 29))[0]
    assert is_active(g, today=date(2025, 7, 10)) is True
    assert is_active(g, today=date(2026, 8, 29)) is False

from __future__ import annotations

from datetime import date

import pytest
from app.etl import ETLError, normalize


def test_normalize_cleans_merchants_and_deduplicates():
    raw = (
        b"date,description,amount\n"
        b"2026-01-02,SQ * COFFEE SHOP 123,-4.50\n"
        b"2026-01-02,SQ * COFFEE SHOP 123,-4.50\n"
        b"2026-01-03,WHOLE FOODS, -70.00\n"
    )
    frame = normalize(raw)
    assert frame["txn_date"].tolist() == [date(2026, 1, 2), date(2026, 1, 3)]
    assert frame["merchant"].tolist() == ["coffee shop", "whole foods"]
    assert frame["amount"].tolist() == [-4.5, -70.0]
    assert frame.attrs["rows_received"] == 3
    assert frame.attrs["rows_deduped"] == 1


def test_normalize_supports_dmy_and_debit_credit_columns():
    raw = (
        b"When,Details,Withdrawal,Deposit\n"
        b"02/01/2026,MARKET,12.00,\n"
        b"03/01/2026,PAYROLL,,3200.00\n"
    )
    frame = normalize(
        raw,
        {
            "date": "When",
            "description": "Details",
            "debit": "Withdrawal",
            "credit": "Deposit",
            "date_format": "DMY",
        },
    )
    assert [str(value) for value in frame["txn_date"]] == ["2026-01-02", "2026-01-03"]
    assert frame["amount"].tolist() == [-12.0, 3200.0]


def test_normalize_rejects_missing_required_columns():
    with pytest.raises(ETLError, match="missing columns"):
        normalize(b"date,description\n2026-01-01,missing amount\n")

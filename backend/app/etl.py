"""CSV normalization for statement imports."""
from __future__ import annotations

import io
import re
from collections.abc import Mapping

import pandas as pd

DATE_FORMATS = {
    "YMD": "%Y-%m-%d",
    "MDY": "%m/%d/%Y",
    "DMY": "%d/%m/%Y",
}


class ETLError(ValueError):
    pass


def clean_merchant(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = text.lower().strip()
    text = re.sub(r"^(?:sq|tst|pos)\s*\*\s*", "", text)
    text = re.sub(r"[*#]", " ", text)
    text = re.sub(r"\b\d{3,}\b", "", text)
    text = re.sub(r"\s*,\s*[a-z .'-]+,\s*[a-z]{2}$", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _column_name(frame: pd.DataFrame, mapping: Mapping[str, str], field: str) -> str | None:
    requested = mapping.get(field, field)
    requested_key = str(requested).strip().casefold()
    for column in frame.columns:
        if str(column).strip().casefold() == requested_key:
            return column
    return None


def _numbers(values: pd.Series) -> pd.Series:
    cleaned = (
        values.astype("string")
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace(r"^\((.*)\)$", r"-\1", regex=True)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


def normalize(raw_bytes: bytes, mapping: Mapping[str, str] | None = None) -> pd.DataFrame:
    """Return clean transactions with normalized dates, merchants and amounts."""
    mapping = mapping or {}
    try:
        raw = pd.read_csv(io.BytesIO(raw_bytes))
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise ETLError(f"could not parse CSV: {exc}") from exc

    date_column = _column_name(raw, mapping, "date")
    description_column = _column_name(raw, mapping, "description")
    amount_column = _column_name(raw, mapping, "amount")
    debit_column = _column_name(raw, mapping, "debit")
    credit_column = _column_name(raw, mapping, "credit")

    missing = [
        field for field, column in (("date", date_column), ("description", description_column))
        if column is None
    ]
    if amount_column is None and (debit_column is None or credit_column is None):
        missing.append("amount or debit/credit")
    if missing:
        raise ETLError(f"CSV missing columns: {missing}")

    date_format = str(mapping.get("date_format", "YMD")).upper()
    if date_format not in DATE_FORMATS:
        raise ETLError(f"date_format must be one of {sorted(DATE_FORMATS)}")

    dates = pd.to_datetime(raw[date_column], format=DATE_FORMATS[date_format], errors="coerce")
    if amount_column is not None:
        amounts = _numbers(raw[amount_column])
    else:
        debits = _numbers(raw[debit_column]).fillna(0)
        credits = _numbers(raw[credit_column]).fillna(0)
        amounts = credits - debits

    descriptions = raw[description_column].astype("string").str.strip()
    clean = pd.DataFrame(
        {
            "txn_date": dates.dt.date,
            "description_raw": descriptions,
            "amount": amounts,
        }
    )
    valid = (
        clean["txn_date"].notna()
        & clean["description_raw"].notna()
        & clean["description_raw"].ne("")
        & clean["amount"].notna()
    )
    clean = clean.loc[valid].copy()
    clean["merchant"] = clean["description_raw"].map(clean_merchant)
    clean = clean.loc[clean["merchant"].ne("")].copy()
    duplicate_mask = clean.duplicated(subset=["txn_date", "merchant", "amount"])
    clean = clean.loc[~duplicate_mask].reset_index(drop=True)

    clean.attrs["rows_received"] = len(raw)
    clean.attrs["rows_valid"] = len(clean) + int(duplicate_mask.sum())
    clean.attrs["rows_deduped"] = int(duplicate_mask.sum())
    return clean

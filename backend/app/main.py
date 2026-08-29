"""FinScope API — FastAPI entrypoint.

This is a skeleton wiring the analytic modules to HTTP routes. Persistence
(SQLAlchemy models + Alembic) is added in milestone M1; see docs/ROADMAP.md.
"""
from __future__ import annotations

import io

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile

from app.anomaly import detect_anomalies
from app.recurring import Transaction, detect_recurring

app = FastAPI(title="FinScope API", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: c.strip().lower() for c in df.columns})
    missing = {"date", "description", "amount"} - set(df.columns)
    if missing:
        raise HTTPException(400, f"CSV missing columns: {sorted(missing)}")
    df["txn_date"] = pd.to_datetime(df["date"]).dt.date
    df["amount"] = pd.to_numeric(df["amount"])
    df["merchant"] = (
        df["description"].str.lower()
        .str.replace(r"[*#]", " ", regex=True)
        .str.replace(r"\b\d{3,}\b", "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    df = df.drop_duplicates(subset=["txn_date", "merchant", "amount"])
    return df


@app.post("/api/imports")
async def create_import(file: UploadFile = File(...)) -> dict:
    raw = await file.read()
    try:
        df = _normalize(pd.read_csv(io.BytesIO(raw)))
    except pd.errors.ParserError as e:
        raise HTTPException(400, f"could not parse CSV: {e}") from e

    # categorization is wired in M1; placeholder keeps the endpoint runnable
    df["category"] = "other"

    txns = [
        Transaction(r.merchant, r.txn_date, float(r.amount)) for r in df.itertuples()
    ]
    recurring = detect_recurring(txns)

    # Recurring charges are "expected", so exclude them from anomaly detection —
    # otherwise rent and utilities dominate the outlier list.
    recurring_merchants = {g.merchant for g in recurring}
    mask = ~df["merchant"].isin(recurring_merchants)
    flags = detect_anomalies(
        df.loc[mask, "amount"].tolist(),
        df.loc[mask, "category"].tolist(),
        df.loc[mask, "merchant"].tolist(),
    )
    flag_rows = df.loc[mask].reset_index(drop=True)

    return {
        "filename": file.filename,
        "rows": len(df),
        "date_range": [str(df["txn_date"].min()), str(df["txn_date"].max())],
        "recurring_groups": [
            {
                "merchant": g.merchant,
                "cadence": g.cadence,
                "avg_amount": g.avg_amount,
                "monthly_cost": round(g.monthly_cost, 2),
                "next_expected": str(g.next_expected),
            }
            for g in recurring
        ],
        "anomalies": [
            {
                "date": str(flag_rows.iloc[f.index]["txn_date"]),
                "description": flag_rows.iloc[f.index]["description"],
                "amount": float(flag_rows.iloc[f.index]["amount"]),
                "reason": f.reason,
            }
            for f in flags
        ],
    }

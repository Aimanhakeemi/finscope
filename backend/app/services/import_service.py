"""Import orchestration: normalize, categorize, deduplicate, and persist."""
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.categorize import TAXONOMY, Categorizer
from app.etl import ETLError, normalize
from app.models import Import, Transaction


def make_dedupe_key(txn_date: date, merchant: str, amount: Decimal) -> str:
    value = f"{txn_date.isoformat()}|{merchant}|{amount:.2f}"
    return hashlib.sha1(value.encode(), usedforsecurity=False).hexdigest()


def import_statement(
    session: Session,
    user_id: UUID,
    filename: str,
    raw_bytes: bytes,
    mapping: Mapping[str, str] | None = None,
    categorizer: Categorizer | None = None,
) -> dict[str, Any]:
    frame = normalize(raw_bytes, mapping)
    if frame.empty:
        raise ETLError("CSV has 0 valid rows")

    existing_keys = set(
        session.scalars(select(Transaction.dedupe_key).where(Transaction.user_id == user_id)).all()
    )
    imported = Import(
        user_id=user_id,
        filename=filename,
        row_count=0,
        date_min=frame["txn_date"].min(),
        date_max=frame["txn_date"].max(),
    )
    session.add(imported)
    session.flush()

    categorizer = categorizer or Categorizer()
    breakdown = {category: 0 for category in TAXONOMY}
    llm_fallback_count = 0
    rows_deduped = int(frame.attrs.get("rows_deduped", 0))
    accepted_dates: list[date] = []

    for row in frame.itertuples(index=False):
        amount = Decimal(str(float(row.amount))).quantize(Decimal("0.01"))
        txn_date = row.txn_date
        key = make_dedupe_key(txn_date, row.merchant, amount)
        if key in existing_keys:
            rows_deduped += 1
            continue
        prediction = categorizer.predict_one(row.merchant, float(amount))
        transaction = Transaction(
            user_id=user_id,
            import_id=imported.id,
            txn_date=txn_date,
            description_raw=str(row.description_raw),
            merchant=str(row.merchant),
            amount=amount,
            category=prediction.category,
            category_confidence=prediction.confidence,
            category_source=prediction.source,
            dedupe_key=key,
        )
        session.add(transaction)
        existing_keys.add(key)
        breakdown[prediction.category] += 1
        llm_fallback_count += prediction.source == "llm"
        accepted_dates.append(txn_date)

    imported.row_count = len(accepted_dates)
    session.commit()
    dates = accepted_dates or frame["txn_date"].tolist()
    return {
        "import_id": str(imported.id),
        "filename": filename,
        "rows_received": int(frame.attrs.get("rows_received", len(frame))),
        "rows_accepted": len(accepted_dates),
        "rows_deduped": rows_deduped,
        "date_range": [str(min(dates)), str(max(dates))],
        "category_breakdown": breakdown,
        "llm_fallback_count": llm_fallback_count,
    }

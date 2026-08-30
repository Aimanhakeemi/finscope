"""Train the local transaction categorizer from synthetic labels and corrections."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.categorize import DEFAULT_MODEL_PATH, Categorizer
from app.config import settings
from app.etl import clean_merchant
from app.models import CategoryCorrection, Transaction

DEFAULT_LABELS = Path(__file__).resolve().parents[2] / "data" / "sample_statement.labels.csv"


def _load_corrections(database_url: str) -> pd.DataFrame:
    try:
        with Session(create_engine(database_url)) as session:
            rows = session.execute(
                select(Transaction.merchant, CategoryCorrection.new_category)
                .join(CategoryCorrection, CategoryCorrection.transaction_id == Transaction.id)
            ).all()
    except SQLAlchemyError:
        return pd.DataFrame(columns=["merchant", "category"])
    return pd.DataFrame(rows, columns=["merchant", "category"])


def train(labels_path: Path, output_path: Path, database_url: str | None = None) -> Path:
    labels = pd.read_csv(labels_path)
    required = {"description", "category"}
    missing = required - set(labels.columns)
    if missing:
        raise ValueError(f"labels missing columns: {sorted(missing)}")
    training = pd.DataFrame(
        {
            "merchant": labels["description"].map(clean_merchant),
            "category": labels["category"].astype(str),
        }
    )
    if database_url:
        training = pd.concat(
            [training, _load_corrections(database_url)], ignore_index=True,
        )
    categorizer = Categorizer(output_path)
    categorizer.train(training)
    sidecar = output_path.with_suffix(".json")
    sidecar.write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "trained_at": datetime.now(timezone.utc).isoformat(),
                "rows": len(training),
                "classes": sorted(training["category"].unique().tolist()),
            },
            indent=2,
        )
        + "\n"
    )
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--database-url", default=settings.database_url)
    args = parser.parse_args()
    train(args.labels, args.output, args.database_url)
    print(f"Wrote categorizer -> {args.output}")


if __name__ == "__main__":
    main()

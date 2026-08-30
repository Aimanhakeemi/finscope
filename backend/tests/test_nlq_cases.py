from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from app import nlq
from app.models import Import, Transaction
from app.seed import seed_demo_user
from sqlalchemy import text
from sqlalchemy.orm import Session


def _seed_query_data(session: Session) -> None:
    user = seed_demo_user(session)
    imported = Import(user_id=user.id, filename="nlq.csv", row_count=13)
    session.add(imported)
    session.flush()
    rows = [
        ("2026-01-05", "STARBUCKS", -5, "coffee", False),
        ("2026-01-10", "WHOLE FOODS", -20, "groceries", False),
        ("2026-02-05", "STARBUCKS", -6, "coffee", False),
        ("2026-02-10", "NETFLIX", -16, "subscriptions", True),
        ("2026-03-05", "STARBUCKS", -7, "coffee", False),
        ("2026-03-10", "RENT", -1000, "rent_mortgage", True),
        ("2026-04-10", "WHOLE FOODS", -25, "groceries", False),
        ("2026-05-05", "STARBUCKS", -8, "coffee", False),
        ("2026-06-10", "TARGET", -50, "shopping", False),
        ("2026-06-15", "SALARY", 3000, "income", False),
        ("2026-07-10", "NETFLIX", -18, "subscriptions", True),
        ("2026-08-05", "STARBUCKS", -9, "coffee", False),
        ("2026-08-15", "SALARY", 3000, "income", False),
    ]
    session.add_all(
        [
            Transaction(
                user_id=user.id,
                import_id=imported.id,
                txn_date=date.fromisoformat(txn_date),
                description_raw=merchant,
                merchant=merchant,
                amount=Decimal(str(amount)),
                category=category,
                category_confidence=1.0,
                category_source="model",
                is_recurring=recurring,
                dedupe_key=f"nlq-{index}",
            )
            for index, (txn_date, merchant, amount, category, recurring) in enumerate(rows)
        ]
    )
    session.commit()
    session.execute(
        text(
            "CREATE VIEW v_readonly_transactions AS "
            "SELECT txn_date, merchant, amount, category, is_recurring FROM transactions"
        )
    )


def test_fixture_queries_meet_execution_accuracy(db_session: Session, monkeypatch):
    _seed_query_data(db_session)
    fixture = Path(__file__).parent / "fixtures" / "nlq_cases.yaml"
    cases: list[dict[str, Any]] = yaml.safe_load(fixture.read_text())
    assert len(cases) == 25
    correct = 0

    for case in cases:
        monkeypatch.setattr(nlq, "generate_sql", lambda _question, sql=case["gold_sql"]: sql)

        def run_query(sql: str) -> tuple[list[str], list[dict[str, Any]]]:
            result = db_session.execute(text(sql))
            return list(result.keys()), [dict(row._mapping) for row in result]

        result = nlq.ask(case["question"], run_query)
        if result.rows == case["gold_result"]:
            correct += 1

    assert correct / len(cases) >= 0.80

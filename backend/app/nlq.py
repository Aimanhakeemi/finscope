"""Natural-language question -> read-only SQL over v_readonly_transactions.

Guardrails (see docs/ARCHITECTURE.md #6):
  * exactly one SELECT statement
  * references only v_readonly_transactions
  * LIMIT forced to <= MAX_ROWS
  * executed as the finscope_readonly Postgres role with a statement timeout
"""
from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

ALLOWED_RELATION = "v_readonly_transactions"
MAX_ROWS = 500

SCHEMA_PROMPT = f"""
You translate questions about personal spending into a single PostgreSQL SELECT.
Only this view exists:

  {ALLOWED_RELATION}(txn_date date, merchant text, amount numeric,
                     category text, is_recurring boolean)

Rules:
- amount is negative for money spent, positive for money received.
- Return ONLY the SQL, no prose, no markdown fences.
- One SELECT statement. No CTE that writes. No other tables.

Examples:
Q: how much did I spend on coffee since June 2026?
A: SELECT -SUM(amount) AS spent FROM {ALLOWED_RELATION}
   WHERE category = 'coffee' AND amount < 0 AND txn_date >= '2026-06-01';

Q: top 5 merchants by total spend
A: SELECT merchant, -SUM(amount) AS spent FROM {ALLOWED_RELATION}
   WHERE amount < 0 GROUP BY merchant ORDER BY spent DESC LIMIT 5;
""".strip()


@dataclass(frozen=True)
class AskResult:
    sql: str
    rows: list[dict[str, Any]]
    columns: list[str]


class GuardrailError(ValueError):
    pass


def generate_sql(question: str) -> str:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise GuardrailError("LLM features disabled (no ANTHROPIC_API_KEY)")

    from anthropic import Anthropic
    from anthropic.types import TextBlock

    client = Anthropic()
    msg = client.messages.create(
        model=os.getenv("FINSCOPE_LLM_MODEL", "claude-sonnet-5"),
        max_tokens=300,
        temperature=0,
        system=SCHEMA_PROMPT,
        messages=[{"role": "user", "content": question}],
    )
    block = msg.content[0] if msg.content else None
    if not isinstance(block, TextBlock):
        raise GuardrailError("unexpected non-text response from the model")
    return block.text.strip().rstrip(";")


def validate_sql(sql: str) -> str:
    """Parse with sqlglot; raise GuardrailError on anything unsafe. Returns safe SQL."""
    import sqlglot
    from sqlglot import exp

    try:
        statements = sqlglot.parse(sql, read="postgres")
    except Exception as e:  # noqa: BLE001
        raise GuardrailError(f"unparseable SQL: {e}") from e

    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise GuardrailError("only a single SELECT statement is allowed")

    tree = statements[0]
    for table in tree.find_all(exp.Table):
        if table.name.lower() != ALLOWED_RELATION or table.db or table.catalog:
            raise GuardrailError(f"disallowed relation: {table.name}")

    for function in tree.find_all(exp.Anonymous):
        if function.name.lower() == "pg_sleep":
            raise GuardrailError("disallowed function: pg_sleep")

    limit = tree.args.get("limit")
    if limit is None:
        tree.set("limit", exp.Limit(expression=exp.Literal.number(MAX_ROWS)))
    else:
        expression = limit.expression
        if not isinstance(expression, exp.Literal) or not expression.is_int:
            raise GuardrailError("LIMIT must be an integer")
        try:
            requested = int(expression.this)
        except (TypeError, ValueError) as exc:
            raise GuardrailError("LIMIT must be an integer") from exc
        if requested < 0 or requested > MAX_ROWS:
            tree.set("limit", exp.Limit(expression=exp.Literal.number(MAX_ROWS)))

    return tree.sql(dialect="postgres")


def run_readonly(sql: str) -> tuple[list[str], list[dict[str, Any]]]:
    """Execute validated SQL with the restricted database engine."""
    from app.db import create_readonly_engine

    readonly_engine = create_readonly_engine()
    try:
        with readonly_engine.connect() as connection:
            result = connection.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(row._mapping) for row in result]
            return columns, rows
    finally:
        readonly_engine.dispose()


def ask(
    question: str,
    run_query: Callable[[str], tuple[list[str], list[dict[str, Any]]]],
) -> AskResult:
    """`run_query(sql) -> (columns, rows)` executes as the read-only role."""
    sql = validate_sql(generate_sql(question))
    columns, rows = run_query(sql)
    return AskResult(sql=sql, rows=rows, columns=columns)

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from anthropic.types import TextBlock
from app.nlq import ALLOWED_RELATION, MAX_ROWS, GuardrailError, generate_sql, validate_sql


def test_generate_sql_uses_mocked_anthropic_client(monkeypatch):
    response = SimpleNamespace(
        content=[TextBlock(type="text", text=f"SELECT * FROM {ALLOWED_RELATION}")]
    )
    client = Mock()
    client.messages.create.return_value = response
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr("anthropic.Anthropic", lambda: client)

    assert generate_sql("show my transactions") == f"SELECT * FROM {ALLOWED_RELATION}"
    client.messages.create.assert_called_once()


def test_missing_limit_is_added():
    safe = validate_sql(f"SELECT merchant FROM {ALLOWED_RELATION}")
    assert safe.endswith(f"LIMIT {MAX_ROWS}")


def test_existing_limit_is_preserved():
    safe = validate_sql(f"SELECT merchant FROM {ALLOWED_RELATION} LIMIT 5")
    assert safe.endswith("LIMIT 5")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; SELECT 2",
        "UPDATE transactions SET amount = 0",
        "SELECT * FROM transactions",
        f"SELECT pg_sleep(1) FROM {ALLOWED_RELATION}",
        f"SELECT * FROM public.{ALLOWED_RELATION}",
    ],
)
def test_unsafe_queries_are_rejected(sql: str):
    with pytest.raises(GuardrailError):
        validate_sql(sql)

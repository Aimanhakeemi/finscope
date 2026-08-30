from __future__ import annotations

from app.nlq import AskResult
from fastapi.testclient import TestClient


def test_ask_requires_anthropic_key(client: TestClient, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client.post("/api/ask", json={"question": "How much did I spend?"})
    assert response.status_code == 503
    assert response.json() == {
        "detail": "The Ask feature needs an ANTHROPIC_API_KEY. See .env.example."
    }


def test_ask_returns_sql_and_rows(client: TestClient, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.routes.ask.ask",
        lambda question, run_query: AskResult(
            sql="SELECT 1 LIMIT 500",
            columns=["answer"],
            rows=[{"answer": 1}],
        ),
    )
    response = client.post("/api/ask", json={"question": "How much did I spend?"})
    assert response.status_code == 200
    assert response.json() == {
        "question": "How much did I spend?",
        "sql": "SELECT 1 LIMIT 500",
        "columns": ["answer"],
        "rows": [{"answer": 1}],
        "truncated": False,
    }

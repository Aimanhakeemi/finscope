from __future__ import annotations

from fastapi.testclient import TestClient
from test_imports_api import upload


def test_summary_matches_api_shape_and_signed_totals(client: TestClient):
    assert upload(client).status_code == 201
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"range", "totals", "by_category", "monthly", "top_merchants"}
    assert body["range"] == ["2026-01-01", "2026-01-03"]
    assert body["totals"] == {"spend": -76.0, "income": 3200.0, "net": 3124.0}
    assert body["monthly"] == [{"month": "2026-01", "spend": -76.0, "income": 3200.0}]
    assert body["by_category"][0]["category"] == "income"
    assert body["top_merchants"][0]["merchant"] == "acme corp payroll"


def test_summary_rejects_reversed_date_range(client: TestClient):
    response = client.get(
        "/api/analytics/summary",
        params={"from": "2026-02-01", "to": "2026-01-01"},
    )
    assert response.status_code == 400

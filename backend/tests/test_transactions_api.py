from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from test_imports_api import CSV, upload


def test_list_and_correct_transaction(client: TestClient):
    assert upload(client).status_code == 201
    response = client.get("/api/transactions", params={"category": "coffee"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    transaction = body["transactions"][0]
    assert transaction["merchant"] == "starbucks store"

    corrected = client.patch(
        f"/api/transactions/{transaction['id']}",
        json={"category": "dining"},
    )
    assert corrected.status_code == 200
    assert corrected.json()["category"] == "dining"
    assert corrected.json()["category_source"] == "user"
    assert corrected.json()["category_confidence"] == 1.0


def test_transaction_correction_rejects_bad_input_and_unknown_id(client: TestClient):
    assert upload(client, CSV).status_code == 201
    invalid = client.patch(f"/api/transactions/{uuid4()}", json={"category": "not-real"})
    assert invalid.status_code == 422
    unknown = client.patch(f"/api/transactions/{uuid4()}", json={"category": "dining"})
    assert unknown.status_code == 404

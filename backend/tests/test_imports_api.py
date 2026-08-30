from __future__ import annotations

from fastapi.testclient import TestClient

CSV = (
    b"date,description,amount\n"
    b"2026-01-01,STARBUCKS STORE 119,-6.00\n"
    b"2026-01-02,ACME CORP PAYROLL,3200.00\n"
    b"2026-01-03,WHOLE FOODS MKT,-70.00\n"
    b"2026-01-03,WHOLE FOODS MKT,-70.00\n"
)


def upload(client: TestClient, content: bytes = CSV):
    return client.post(
        "/api/imports",
        files={"file": ("statement.csv", content, "text/csv")},
    )


def test_create_and_list_imports(client: TestClient):
    response = upload(client)
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "statement.csv"
    assert body["rows_received"] == 4
    assert body["rows_accepted"] == 3
    assert body["rows_deduped"] == 1
    assert body["date_range"] == ["2026-01-01", "2026-01-03"]
    assert body["category_breakdown"]["coffee"] == 1
    assert body["category_breakdown"]["income"] == 1
    assert body["llm_fallback_count"] == 0

    imports = client.get("/api/imports")
    assert imports.status_code == 200
    assert imports.json()["imports"][0]["import_id"] == body["import_id"]
    assert imports.json()["imports"][0]["rows_accepted"] == 3


def test_create_import_rejects_bad_csv(client: TestClient):
    response = upload(client, b"date,description\n2026-01-01,no amount\n")
    assert response.status_code == 400
    assert "missing columns" in response.json()["detail"]


def test_create_import_accepts_column_mapping(client: TestClient):
    content = b"When,Details,Withdrawal,Deposit\n02/01/2026,MARKET,12.00,\n"
    response = client.post(
        "/api/imports",
        data={
            "mapping": (
                '{"date":"When","description":"Details",'
                '"debit":"Withdrawal","credit":"Deposit","date_format":"DMY"}'
            )
        },
        files={"file": ("mapped.csv", content, "text/csv")},
    )
    assert response.status_code == 201
    assert response.json()["rows_accepted"] == 1

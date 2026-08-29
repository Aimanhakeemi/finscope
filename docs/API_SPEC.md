# FinScope — API Specification

Base URL (dev): `http://localhost:8000`
All request/response bodies are JSON unless noted. All timestamps are ISO 8601.
Errors use this shape:

```json
{ "detail": "human readable message" }
```

Standard status codes: `200` OK, `201` Created, `400` bad input, `404` not found,
`422` validation error (FastAPI default), `500` server error, `503` LLM feature
requested but disabled.

For M0–M4 there is a single implicit demo user (seeded on startup). Auth
(`Authorization: Bearer …`) is a stretch item; endpoints are written so a `user_id`
can be threaded through later without shape changes.

---

## GET /healthz

Liveness. No auth.

**200**
```json
{ "status": "ok", "version": "0.1.0", "llm_enabled": false }
```

---

## POST /api/imports

Upload a statement CSV. `multipart/form-data`.

| field | type | required | notes |
| --- | --- | --- | --- |
| `file` | file | yes | CSV, ≤ 5 MB |
| `mapping` | JSON string | no | column overrides, see below |

`mapping` (when the CSV headers aren't `date,description,amount`):
```json
{ "date": "Transaction Date", "description": "Details", "amount": "Amount",
  "date_format": "DMY" }
```
`date_format` ∈ `"YMD" | "MDY" | "DMY"` (default `"YMD"`). If the CSV has separate
`debit`/`credit` columns, pass `{ "debit": "Withdrawal", "credit": "Deposit" }`
instead of `amount`.

**201**
```json
{
  "import_id": "b1f2…",
  "filename": "statement.csv",
  "rows_received": 540,
  "rows_accepted": 518,
  "rows_deduped": 22,
  "date_range": ["2025-09-01", "2026-08-01"],
  "category_breakdown": { "groceries": 61, "coffee": 88, "…": 0 },
  "llm_fallback_count": 12
}
```

**400** — missing required columns, unparseable CSV, file too large, 0 valid rows.

---

## GET /api/imports

List past imports, newest first.

**200**
```json
{ "imports": [
  { "import_id": "b1f2…", "filename": "statement.csv", "rows_accepted": 518,
    "imported_at": "2026-08-29T10:04:00Z", "date_range": ["2025-09-01","2026-08-01"] }
] }
```

---

## GET /api/transactions

Query params (all optional): `from` (date), `to` (date), `category`, `merchant`,
`is_recurring` (bool), `is_anomaly` (bool), `limit` (default 100, max 1000),
`offset` (default 0), `sort` (`date` | `amount`, prefix `-` for desc; default `-date`).

**200**
```json
{
  "total": 518,
  "limit": 100,
  "offset": 0,
  "transactions": [
    {
      "id": "t_001",
      "txn_date": "2026-08-01",
      "description_raw": "GREENFIELD APARTMENTS",
      "merchant": "greenfield apartments",
      "amount": -1850.00,
      "category": "rent_mortgage",
      "category_confidence": 1.0,
      "category_source": "rule",
      "is_recurring": true,
      "recurring_group_id": "rg_01",
      "is_anomaly": false,
      "anomaly_reason": null
    }
  ]
}
```

---

## PATCH /api/transactions/{id}

Correct a transaction's category. Persists a row in `category_corrections`.

**Request**
```json
{ "category": "dining" }
```
`category` must be in the taxonomy (see DATA_DICTIONARY). Otherwise **422**.

**200** — returns the updated transaction (same shape as above, with
`category_source: "user"`, `category_confidence: 1.0`).

**404** — unknown id.

---

## GET /api/analytics/summary

Query params: `from` (date, default = earliest txn), `to` (date, default = latest).

**200**
```json
{
  "range": ["2025-09-01", "2026-08-01"],
  "totals": { "spend": -18234.55, "income": 41600.00, "net": 23365.45 },
  "by_category": [
    { "category": "rent_mortgage", "total": -22200.00, "txn_count": 12 },
    { "category": "groceries", "total": -3421.19, "txn_count": 61 }
  ],
  "monthly": [
    { "month": "2025-09", "spend": -2980.11, "income": 3200.00 },
    { "month": "2025-10", "spend": -3110.44, "income": 3200.00 }
  ],
  "top_merchants": [
    { "merchant": "greenfield apartments", "total": -22200.00, "txn_count": 12 }
  ]
}
```
All `total`/`spend` values are signed (negative = outflow). `by_category` sorted by
`abs(total)` desc. `monthly` sorted ascending. `top_merchants` top 10 by `abs(total)`.

---

## GET /api/subscriptions

Detected recurring charges.

**200**
```json
{
  "subscriptions": [
    {
      "recurring_group_id": "rg_01",
      "merchant": "netflix.com",
      "cadence": "monthly",
      "avg_amount": -16.24,
      "amount_stddev": 1.31,
      "monthly_cost": 16.24,
      "first_seen": "2025-09-04",
      "last_seen": "2026-07-31",
      "next_expected": "2026-08-30",
      "occurrences": 11,
      "active": true,
      "price_changed": true
    }
  ],
  "total_monthly_cost": 41.71,
  "total_annual_cost": 500.52
}
```
Sorted by `monthly_cost` desc. `price_changed` = true when the last amount differs
from the first by > 5%.

---

## GET /api/alerts

Anomalous transactions for a period. Query param: `from` (date, default = last 60 days).

**200**
```json
{
  "alerts": [
    {
      "transaction_id": "t_402",
      "txn_date": "2026-02-02",
      "description_raw": "BIG APPLIANCE WAREHOUSE",
      "amount": -1240.00,
      "category": "shopping",
      "reason": "1240 is a statistical outlier for shopping; first charge from this merchant, and a large amount",
      "signals": ["robust_z", "iqr", "new_large_merchant"]
    }
  ]
}
```
Recurring-group transactions are excluded before detection.

---

## POST /api/ask

Natural-language question → generated SQL + result.

**Request**
```json
{ "question": "how much did I spend on coffee since June?" }
```

**200**
```json
{
  "question": "how much did I spend on coffee since June?",
  "sql": "SELECT -SUM(amount) AS spent FROM v_readonly_transactions WHERE category = 'coffee' AND amount < 0 AND txn_date >= '2026-06-01' LIMIT 500",
  "columns": ["spent"],
  "rows": [ { "spent": 173.40 } ],
  "truncated": false
}
```

**503** — `ANTHROPIC_API_KEY` not set:
```json
{ "detail": "The Ask feature needs an ANTHROPIC_API_KEY. See .env.example." }
```

**400** — guardrail rejected the generated SQL:
```json
{ "detail": "Generated query was not a safe single SELECT over the allowed view." }
```

---

## GET /api/forecast

Next-month projection.

**200**
```json
{
  "as_of": "2026-08-01",
  "method": "ets",
  "next_month": "2026-09",
  "total_spend": { "point": -3050.00, "low": -3480.00, "high": -2620.00 },
  "by_category": [
    { "category": "groceries", "point": -305.00, "low": -360.00, "high": -250.00 }
  ]
}
```
`method` ∈ `"ets" | "seasonal_naive" | "trailing_median"`. Interval is 80%.
Falls back to `trailing_median` when < 6 months of history.

---

## OpenAPI

FastAPI serves the live spec at `/openapi.json` and Swagger UI at `/docs`. This
document is the source of truth; `/openapi.json` must match it.

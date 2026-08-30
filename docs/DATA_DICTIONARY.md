# FinScope — Data Dictionary

## Category taxonomy (fixed, 12 classes)

`groceries`, `dining`, `coffee`, `transport`, `fuel`, `utilities`, `rent_mortgage`,
`subscriptions`, `shopping`, `health`, `entertainment`, `income`, `other`

Rationale: small enough to categorize reliably and to label by hand; covers the
majority of consumer statement volume.

## Table: `users`
| column | type | notes |
| --- | --- | --- |
| id | uuid PK | |
| email | text unique | demo user seeded on first run |
| created_at | timestamptz | |

## Table: `imports`
| column | type | notes |
| --- | --- | --- |
| id | uuid PK | |
| user_id | uuid FK → users | |
| filename | text | original upload name |
| row_count | int | rows accepted after dedupe |
| imported_at | timestamptz | |
| date_min / date_max | date | statement coverage window |

## Table: `transactions`
| column | type | notes |
| --- | --- | --- |
| id | uuid PK | |
| user_id | uuid FK | |
| import_id | uuid FK | |
| txn_date | date | parsed from source |
| description_raw | text | original description string |
| merchant | text | cleaned merchant name (noise stripped, lower-case) |
| amount | numeric(12,2) | negative = money out, positive = money in |
| category | text | one of the taxonomy values |
| category_confidence | real | 0–1; model probability or 1.0 for rule/user |
| category_source | text | `model` \| `rule` \| `user` |
| is_recurring | bool | set by `recurring.py` |
| recurring_group_id | uuid FK → recurring_groups, null | |
| is_anomaly | bool | set by `anomaly.py` |
| anomaly_reason | text null | e.g. `amount 4.1x category median`, `new merchant, large` |
| dedupe_key | text | `sha1(txn_date | merchant | amount)` |
| created_at | timestamptz | |

Indexes: `(user_id, txn_date)`, `(user_id, merchant)`, unique `(user_id, dedupe_key)`.

## Table: `recurring_groups`
| column | type | notes |
| --- | --- | --- |
| id | uuid PK | |
| user_id | uuid FK | |
| merchant | text | |
| cadence | text | `weekly` \| `biweekly` \| `monthly` \| `quarterly` \| `annual` |
| avg_amount | numeric(12,2) | |
| amount_stddev | numeric(12,2) | |
| first_seen / last_seen | date | |
| next_expected | date | last_seen + cadence interval |
| active | bool | false if no charge within 1.5× cadence of today |

## Table: `category_corrections`
| column | type | notes |
| --- | --- | --- |
| id | uuid PK | |
| user_id | uuid FK | |
| transaction_id | uuid FK | |
| old_category / new_category | text | |
| created_at | timestamptz | used as training labels on next model rebuild |

## Views

### `v_monthly_category_spend`
`user_id, month (date_trunc), category, total_amount, txn_count`

### `v_merchant_totals`
`user_id, merchant, total_amount, txn_count, first_seen, last_seen`

### `v_readonly_transactions` (ONLY object exposed to NL→SQL)
`txn_date, merchant, amount, category, is_recurring` — no ids, no raw description.

## Input CSV contract

Minimum required (after column mapping):

| field | accepted formats |
| --- | --- |
| date | `YYYY-MM-DD`, `MM/DD/YYYY`, `DD/MM/YYYY` (mapping step disambiguates) |
| description | free text |
| amount | `-12.34`, `12.34`, or separate `debit`/`credit` columns |

## Synthetic data generator

`data/generate_synthetic.py`:
- Seeded RNG (`--seed`, default 42) → reproducible.
- Emits: monthly salary (income), rent (monthly recurring), 4–6 subscriptions with
  realistic cadences, weekly groceries, frequent coffee/dining, occasional shopping,
  utilities, 2–3 deliberate anomalies (a large one-off, a duplicated-looking charge,
  a price jump on one subscription).
- Also writes `data/sample_statement.labels.csv` with the true category + recurring
  flags for evaluation.

# FinScope — Database Schema (authoritative DDL)

Target: PostgreSQL 16. Managed with Alembic; the migration chain should produce
exactly this. UUIDs via `gen_random_uuid()` (`pgcrypto`), enable it in the migration.

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ─────────────────────────────────────────────────────────────
CREATE TABLE users (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email       text NOT NULL UNIQUE,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────
CREATE TABLE imports (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename     text NOT NULL,
    row_count    integer NOT NULL CHECK (row_count >= 0),
    imported_at  timestamptz NOT NULL DEFAULT now(),
    date_min     date,
    date_max     date
);
CREATE INDEX ix_imports_user ON imports(user_id, imported_at DESC);

-- ─────────────────────────────────────────────────────────────
CREATE TYPE category_enum AS ENUM (
    'groceries','dining','coffee','transport','fuel','utilities',
    'rent_mortgage','subscriptions','shopping','health','entertainment',
    'income','other'
);
CREATE TYPE category_source_enum AS ENUM ('model','rule','user');
CREATE TYPE cadence_enum AS ENUM ('weekly','biweekly','monthly','quarterly','annual');

-- ─────────────────────────────────────────────────────────────
CREATE TABLE recurring_groups (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    merchant       text NOT NULL,
    cadence        cadence_enum NOT NULL,
    avg_amount     numeric(12,2) NOT NULL,
    amount_stddev  numeric(12,2) NOT NULL DEFAULT 0,
    first_seen     date NOT NULL,
    last_seen      date NOT NULL,
    next_expected  date NOT NULL,
    active         boolean NOT NULL DEFAULT true,
    created_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, merchant, cadence)
);
CREATE INDEX ix_recurring_user ON recurring_groups(user_id);

-- ─────────────────────────────────────────────────────────────
CREATE TABLE transactions (
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id               uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    import_id             uuid NOT NULL REFERENCES imports(id) ON DELETE CASCADE,
    txn_date              date NOT NULL,
    description_raw       text NOT NULL,
    merchant              text NOT NULL,
    amount                numeric(12,2) NOT NULL,      -- negative = outflow
    category              category_enum NOT NULL DEFAULT 'other',
    category_confidence   real NOT NULL DEFAULT 0 CHECK (category_confidence BETWEEN 0 AND 1),
    category_source       category_source_enum NOT NULL DEFAULT 'model',
    is_recurring          boolean NOT NULL DEFAULT false,
    recurring_group_id    uuid REFERENCES recurring_groups(id) ON DELETE SET NULL,
    is_anomaly            boolean NOT NULL DEFAULT false,
    anomaly_reason        text,
    dedupe_key            text NOT NULL,               -- sha1(txn_date|merchant|amount)
    created_at            timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, dedupe_key)
);
CREATE INDEX ix_txn_user_date     ON transactions(user_id, txn_date);
CREATE INDEX ix_txn_user_merchant ON transactions(user_id, merchant);
CREATE INDEX ix_txn_user_category ON transactions(user_id, category);

-- ─────────────────────────────────────────────────────────────
CREATE TABLE category_corrections (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transaction_id  uuid NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    old_category    category_enum NOT NULL,
    new_category    category_enum NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_corrections_user ON category_corrections(user_id, created_at);

-- ─────────────────────────────────────────────────────────────
-- Analytics views
CREATE VIEW v_monthly_category_spend AS
SELECT user_id,
       date_trunc('month', txn_date)::date AS month,
       category,
       SUM(amount)   AS total_amount,
       COUNT(*)      AS txn_count
FROM transactions
GROUP BY user_id, date_trunc('month', txn_date), category;

CREATE VIEW v_merchant_totals AS
SELECT user_id, merchant,
       SUM(amount) AS total_amount,
       COUNT(*)    AS txn_count,
       MIN(txn_date) AS first_seen,
       MAX(txn_date) AS last_seen
FROM transactions
GROUP BY user_id, merchant;

-- The ONLY object exposed to natural-language SQL. No ids, no raw description.
CREATE VIEW v_readonly_transactions AS
SELECT txn_date, merchant, amount, category, is_recurring
FROM transactions;

-- ─────────────────────────────────────────────────────────────
-- Least-privilege role for the NL→SQL feature.
-- Password comes from env (FINSCOPE_READONLY_PASSWORD); migration reads it or the
-- app creates the role on startup if absent.
CREATE ROLE finscope_readonly LOGIN PASSWORD 'change-me';
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM finscope_readonly;
GRANT USAGE ON SCHEMA public TO finscope_readonly;
GRANT SELECT ON v_readonly_transactions TO finscope_readonly;
ALTER ROLE finscope_readonly SET statement_timeout = '3s';
```

## Notes for the implementer

- The app's main connection uses the `finscope` superuser-ish role; the `/api/ask`
  path opens a **separate** connection/pool as `finscope_readonly`.
- `is_recurring` / `recurring_group_id` / `is_anomaly` / `anomaly_reason` are set by a
  post-import job that runs `recurring.detect_recurring` then `anomaly.detect_anomalies`
  over the user's full history (not just the new import) and updates rows in place.
- `dedupe_key = sha1(f"{txn_date.isoformat()}|{merchant}|{amount:.2f}")`. Collisions
  across imports are intended (same charge re-uploaded → skipped).
- SQLAlchemy models mirror this file; if they drift, this file wins and the migration
  is regenerated.

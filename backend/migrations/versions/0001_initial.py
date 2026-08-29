"""Create the complete FinScope schema from DB_SCHEMA.md."""

from __future__ import annotations

import os

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def upgrade() -> None:
    password = os.getenv("FINSCOPE_READONLY_PASSWORD", "change-me")

    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute(
        """
        CREATE TABLE users (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            email text NOT NULL UNIQUE,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE imports (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            filename text NOT NULL,
            row_count integer NOT NULL CHECK (row_count >= 0),
            imported_at timestamptz NOT NULL DEFAULT now(),
            date_min date,
            date_max date
        )
        """
    )
    op.execute("CREATE INDEX ix_imports_user ON imports(user_id, imported_at DESC)")
    op.execute(
        """
        CREATE TYPE category_enum AS ENUM (
            'groceries','dining','coffee','transport','fuel','utilities',
            'rent_mortgage','subscriptions','shopping','health','entertainment',
            'income','other'
        )
        """
    )
    op.execute("CREATE TYPE category_source_enum AS ENUM ('model','llm','rule','user')")
    op.execute(
        "CREATE TYPE cadence_enum AS ENUM ('weekly','biweekly','monthly','quarterly','annual')"
    )
    op.execute(
        """
        CREATE TABLE recurring_groups (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            merchant text NOT NULL,
            cadence cadence_enum NOT NULL,
            avg_amount numeric(12,2) NOT NULL,
            amount_stddev numeric(12,2) NOT NULL DEFAULT 0,
            first_seen date NOT NULL,
            last_seen date NOT NULL,
            next_expected date NOT NULL,
            active boolean NOT NULL DEFAULT true,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (user_id, merchant, cadence)
        )
        """
    )
    op.execute("CREATE INDEX ix_recurring_user ON recurring_groups(user_id)")
    op.execute(
        """
        CREATE TABLE transactions (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            import_id uuid NOT NULL REFERENCES imports(id) ON DELETE CASCADE,
            txn_date date NOT NULL,
            description_raw text NOT NULL,
            merchant text NOT NULL,
            amount numeric(12,2) NOT NULL,
            category category_enum NOT NULL DEFAULT 'other',
            category_confidence real NOT NULL DEFAULT 0 CHECK (category_confidence BETWEEN 0 AND 1),
            category_source category_source_enum NOT NULL DEFAULT 'model',
            is_recurring boolean NOT NULL DEFAULT false,
            recurring_group_id uuid REFERENCES recurring_groups(id) ON DELETE SET NULL,
            is_anomaly boolean NOT NULL DEFAULT false,
            anomaly_reason text,
            dedupe_key text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (user_id, dedupe_key)
        )
        """
    )
    op.execute("CREATE INDEX ix_txn_user_date ON transactions(user_id, txn_date)")
    op.execute("CREATE INDEX ix_txn_user_merchant ON transactions(user_id, merchant)")
    op.execute("CREATE INDEX ix_txn_user_category ON transactions(user_id, category)")
    op.execute(
        """
        CREATE TABLE category_corrections (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            transaction_id uuid NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
            old_category category_enum NOT NULL,
            new_category category_enum NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_corrections_user ON category_corrections(user_id, created_at)")
    op.execute(
        """
        CREATE VIEW v_monthly_category_spend AS
        SELECT user_id,
               date_trunc('month', txn_date)::date AS month,
               category,
               SUM(amount) AS total_amount,
               COUNT(*) AS txn_count
        FROM transactions
        GROUP BY user_id, date_trunc('month', txn_date), category
        """
    )
    op.execute(
        """
        CREATE VIEW v_merchant_totals AS
        SELECT user_id, merchant,
               SUM(amount) AS total_amount,
               COUNT(*) AS txn_count,
               MIN(txn_date) AS first_seen,
               MAX(txn_date) AS last_seen
        FROM transactions
        GROUP BY user_id, merchant
        """
    )
    op.execute(
        """
        CREATE VIEW v_readonly_transactions AS
        SELECT txn_date, merchant, amount, category, is_recurring
        FROM transactions
        """
    )
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'finscope_readonly') THEN
                CREATE ROLE finscope_readonly LOGIN PASSWORD {_literal(password)};
            ELSE
                ALTER ROLE finscope_readonly LOGIN PASSWORD {_literal(password)};
            END IF;
        END
        $$
        """
    )
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM finscope_readonly")
    op.execute("GRANT USAGE ON SCHEMA public TO finscope_readonly")
    op.execute("GRANT SELECT ON v_readonly_transactions TO finscope_readonly")
    op.execute("ALTER ROLE finscope_readonly SET statement_timeout = '3s'")


def downgrade() -> None:
    op.execute("REVOKE ALL ON v_readonly_transactions FROM finscope_readonly")
    op.execute("DROP VIEW IF EXISTS v_readonly_transactions")
    op.execute("DROP VIEW IF EXISTS v_merchant_totals")
    op.execute("DROP VIEW IF EXISTS v_monthly_category_spend")
    op.execute("DROP TABLE IF EXISTS category_corrections")
    op.execute("DROP TABLE IF EXISTS transactions")
    op.execute("DROP TABLE IF EXISTS recurring_groups")
    op.execute("DROP TABLE IF EXISTS imports")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TYPE IF EXISTS cadence_enum")
    op.execute("DROP TYPE IF EXISTS category_source_enum")
    op.execute("DROP TYPE IF EXISTS category_enum")
    op.execute("DROP ROLE IF EXISTS finscope_readonly")

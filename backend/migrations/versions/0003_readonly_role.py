"""Ensure the restricted natural-language SQL surface is configured."""

from __future__ import annotations

import os

from alembic import op

revision = "0003_readonly_role"
down_revision = "0002_drop_llm_category_source"
branch_labels = None
depends_on = None


def _literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def upgrade() -> None:
    password = os.getenv("FINSCOPE_READONLY_PASSWORD", "change-me")
    op.execute(
        """
        CREATE OR REPLACE VIEW v_readonly_transactions AS
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
    # The view and role are part of the base schema, so the prior migration owns them.
    pass

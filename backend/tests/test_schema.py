from __future__ import annotations

from sqlalchemy import text


def test_postgres_schema_dump_matches_contract(postgres_connection):
    tables = set(
        postgres_connection.execute(
            text(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                  AND table_name <> 'alembic_version'
                """
            )
        ).scalars()
    )
    assert tables == {
        "users",
        "imports",
        "recurring_groups",
        "transactions",
        "category_corrections",
    }

    views = set(
        postgres_connection.execute(
            text("SELECT viewname FROM pg_views WHERE schemaname = 'public'")
        ).scalars()
    )
    assert views == {"v_monthly_category_spend", "v_merchant_totals", "v_readonly_transactions"}

    enum_values = postgres_connection.execute(
        text(
            """
            SELECT t.typname, array_agg(e.enumlabel ORDER BY e.enumsortorder)
            FROM pg_type t
            JOIN pg_enum e ON e.enumtypid = t.oid
            WHERE t.typname IN ('category_enum', 'category_source_enum', 'cadence_enum')
            GROUP BY t.typname
            """
        )
    ).all()
    assert dict(enum_values) == {
        "category_enum": [
            "groceries",
            "dining",
            "coffee",
            "transport",
            "fuel",
            "utilities",
            "rent_mortgage",
            "subscriptions",
            "shopping",
            "health",
            "entertainment",
            "income",
            "other",
        ],
        "category_source_enum": ["model", "llm", "rule", "user"],
        "cadence_enum": ["weekly", "biweekly", "monthly", "quarterly", "annual"],
    }

    column_rows = postgres_connection.execute(
        text(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN (
                  'users', 'imports', 'recurring_groups', 'transactions', 'category_corrections'
              )
            """
        )
    ).all()
    columns: dict[str, set[str]] = {}
    for table_name, column_name in column_rows:
        columns.setdefault(table_name, set()).add(column_name)
    assert columns == {
        "users": {"id", "email", "created_at"},
        "imports": {
            "id",
            "user_id",
            "filename",
            "row_count",
            "imported_at",
            "date_min",
            "date_max",
        },
        "recurring_groups": {
            "id",
            "user_id",
            "merchant",
            "cadence",
            "avg_amount",
            "amount_stddev",
            "first_seen",
            "last_seen",
            "next_expected",
            "active",
            "created_at",
        },
        "transactions": {
            "id",
            "user_id",
            "import_id",
            "txn_date",
            "description_raw",
            "merchant",
            "amount",
            "category",
            "category_confidence",
            "category_source",
            "is_recurring",
            "recurring_group_id",
            "is_anomaly",
            "anomaly_reason",
            "dedupe_key",
            "created_at",
        },
        "category_corrections": {
            "id",
            "user_id",
            "transaction_id",
            "old_category",
            "new_category",
            "created_at",
        },
    }

    role = postgres_connection.execute(
        text("SELECT rolname FROM pg_roles WHERE rolname = 'finscope_readonly'")
    ).scalar_one_or_none()
    assert role == "finscope_readonly"

    grant = postgres_connection.execute(
        text(
            """
            SELECT has_table_privilege(
                'finscope_readonly', 'public.v_readonly_transactions', 'SELECT'
            )
            """
        )
    ).scalar_one()
    assert grant is True

"""Remove LLM as a transaction category source."""

from __future__ import annotations

from alembic import op

revision = "0002_drop_llm_category_source"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE transactions ALTER COLUMN category_source DROP DEFAULT")
    op.execute(
        "ALTER TABLE transactions ALTER COLUMN category_source "
        "TYPE text USING category_source::text"
    )
    op.execute(
        "UPDATE transactions SET category_source = 'model' "
        "WHERE category_source = 'llm'"
    )
    op.execute("DROP TYPE category_source_enum")
    op.execute("CREATE TYPE category_source_enum AS ENUM ('model','rule','user')")
    op.execute(
        "ALTER TABLE transactions ALTER COLUMN category_source "
        "TYPE category_source_enum USING category_source::category_source_enum"
    )
    op.execute(
        "ALTER TABLE transactions ALTER COLUMN category_source SET DEFAULT 'model'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE transactions ALTER COLUMN category_source DROP DEFAULT")
    op.execute(
        "ALTER TABLE transactions ALTER COLUMN category_source "
        "TYPE text USING category_source::text"
    )
    op.execute("DROP TYPE category_source_enum")
    op.execute("CREATE TYPE category_source_enum AS ENUM ('model','llm','rule','user')")
    op.execute(
        "ALTER TABLE transactions ALTER COLUMN category_source "
        "TYPE category_source_enum USING category_source::category_source_enum"
    )
    op.execute(
        "ALTER TABLE transactions ALTER COLUMN category_source SET DEFAULT 'model'"
    )

"""Shared deterministic test fixtures."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

os.environ.pop("ANTHROPIC_API_KEY", None)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE users (
                id CHAR(32) PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture
def postgres_connection():
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url.startswith("postgresql"):
        pytest.skip("PostgreSQL schema test requires DATABASE_URL")
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            yield connection
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"PostgreSQL is unavailable: {exc}")
    finally:
        engine.dispose()

"""Shared deterministic test fixtures."""

from __future__ import annotations

import os
from collections.abc import Generator

os.environ.pop("ANTHROPIC_API_KEY", None)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    from app.models import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    server_defaults = {
        column: column.server_default
        for table in Base.metadata.tables.values()
        for column in table.columns
    }
    for column in server_defaults:
        column.server_default = None
    Base.metadata.create_all(engine)
    for column, server_default in server_defaults.items():
        column.server_default = server_default
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture
def client(
    db_session: Session, monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    from app import main
    from app.db import get_session
    from app.seed import seed_demo_user

    monkeypatch.setattr(main, "SessionLocal", lambda: db_session)
    seed_demo_user(db_session)

    def override_session() -> Generator[Session, None, None]:
        yield db_session

    main.app.dependency_overrides[get_session] = override_session
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


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

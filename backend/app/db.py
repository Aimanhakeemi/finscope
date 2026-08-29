"""Database engines and FastAPI session dependencies."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_readonly_engine(database_url: str | None = None) -> Engine:
    """Create a separate engine authenticated as the restricted SQL role."""
    url = make_url(database_url or settings.database_url).set(
        username="finscope_readonly",
        password=settings.finscope_readonly_password,
    )
    return create_engine(url, pool_pre_ping=True)

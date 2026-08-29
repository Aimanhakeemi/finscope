from __future__ import annotations

from app.config import settings
from app.db import create_readonly_engine
from app.seed import DEMO_USER_EMAIL, seed_demo_user


def test_readonly_engine_uses_restricted_role(monkeypatch):
    monkeypatch.setattr(settings, "finscope_readonly_password", "secret")
    engine = create_readonly_engine("postgresql+psycopg://main:pass@localhost:5432/db")
    assert engine.url.username == "finscope_readonly"
    assert engine.url.password == "secret"
    engine.dispose()


def test_seed_inserts_demo_user_once(db_session):
    first = seed_demo_user(db_session)
    second = seed_demo_user(db_session)
    assert first.email == DEMO_USER_EMAIL
    assert second.id == first.id

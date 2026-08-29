"""Startup seed for the single implicit demo user."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User

DEMO_USER_EMAIL = "demo@finscope.local"


def seed_demo_user(session: Session) -> User:
    user = session.scalar(select(User).where(User.email == DEMO_USER_EMAIL))
    if user is None:
        user = User(email=DEMO_USER_EMAIL)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

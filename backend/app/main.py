"""FinScope API entrypoint."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.db import SessionLocal
from app.seed import seed_demo_user

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    try:
        with SessionLocal() as session:
            seed_demo_user(session)
    except SQLAlchemyError:
        logger.warning("Demo user seed skipped because the database is unavailable")
    yield


app = FastAPI(title="FinScope API", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {
        "status": "ok",
        "version": settings.app_version,
        "llm_enabled": bool(settings.anthropic_api_key),
    }

"""FinScope API entrypoint."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.db import SessionLocal
from app.routes.alerts import router as alerts_router
from app.routes.analytics import router as analytics_router
from app.routes.imports import router as imports_router
from app.routes.subscriptions import router as subscriptions_router
from app.routes.transactions import router as transactions_router
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(imports_router)
app.include_router(transactions_router)
app.include_router(analytics_router)
app.include_router(subscriptions_router)
app.include_router(alerts_router)


@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {
        "status": "ok",
        "version": settings.app_version,
        "llm_enabled": bool(settings.anthropic_api_key),
    }

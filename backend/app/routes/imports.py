"""Statement import endpoints."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.etl import ETLError
from app.models import Import
from app.seed import seed_demo_user
from app.services.import_service import import_statement

router = APIRouter(prefix="/api/imports", tags=["imports"])
MAX_FILE_BYTES = 5 * 1024 * 1024


class ImportSummary(BaseModel):
    import_id: str
    filename: str
    rows_received: int
    rows_accepted: int
    rows_deduped: int
    date_range: list[str]
    category_breakdown: dict[str, int]
    llm_fallback_count: int


class ImportListItem(BaseModel):
    import_id: str
    filename: str
    rows_accepted: int
    imported_at: datetime
    date_range: list[str]


class ImportListResponse(BaseModel):
    imports: list[ImportListItem]


def _mapping(value: Optional[str]) -> dict[str, str]:
    if not value:
        return {}
    try:
        parsed: Any = json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "mapping must be valid JSON") from exc
    if not isinstance(parsed, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in parsed.items()
    ):
        raise HTTPException(400, "mapping must be a JSON object of strings")
    return parsed


@router.post("", response_model=ImportSummary, status_code=201)
async def create_import(
    file: UploadFile = File(...),  # noqa: B008
    mapping: Optional[str] = Form(None),
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, Any]:
    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_FILE_BYTES:
        raise HTTPException(400, "file too large (maximum 5 MB)")
    try:
        result = import_statement(
            session,
            seed_demo_user(session).id,
            file.filename or "statement.csv",
            raw_bytes,
            _mapping(mapping),
        )
    except ETLError as exc:
        raise HTTPException(400, str(exc)) from exc
    return result


@router.get("", response_model=ImportListResponse)
def list_imports(
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, list[dict[str, Any]]]:
    user = seed_demo_user(session)
    records = session.scalars(
        select(Import).where(Import.user_id == user.id).order_by(Import.imported_at.desc())
    ).all()
    return {
        "imports": [
            {
                "import_id": str(record.id),
                "filename": record.filename,
                "rows_accepted": record.row_count,
                "imported_at": record.imported_at,
                "date_range": [str(record.date_min), str(record.date_max)],
            }
            for record in records
        ]
    }

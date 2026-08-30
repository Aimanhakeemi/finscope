"""Natural-language query endpoint."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.nlq import MAX_ROWS, AskResult, GuardrailError, ask, run_readonly

router = APIRouter(prefix="/api", tags=["ask"])
ASK_DISABLED = "The Ask feature needs an ANTHROPIC_API_KEY. See .env.example."
UNSAFE_QUERY = "Generated query was not a safe single SELECT over the allowed view."


class AskRequest(BaseModel):
    question: str = Field(min_length=1)


class AskResponse(BaseModel):
    question: str
    sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    truncated: bool


@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest) -> AskResponse:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=503, detail=ASK_DISABLED)
    try:
        result: AskResult = ask(request.question, run_readonly)
    except GuardrailError as exc:
        raise HTTPException(status_code=400, detail=UNSAFE_QUERY) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Ask feature failed.") from exc
    return AskResponse(
        question=request.question,
        sql=result.sql,
        columns=result.columns,
        rows=result.rows,
        truncated=len(result.rows) >= MAX_ROWS,
    )

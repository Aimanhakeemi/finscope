"""Application settings loaded from environment variables and ``.env``."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    app_version: str = "0.1.0"
    database_url: str = "postgresql+psycopg://finscope:finscope@localhost:5432/finscope"
    anthropic_api_key: Optional[str] = None
    finscope_llm_model: str = "claude-sonnet-5"
    finscope_readonly_password: str = "change-me"

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")


settings = Settings()

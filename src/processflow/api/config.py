"""Application settings — loaded from environment variables with PROCESSFLOW_ prefix."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_db_url() -> str:
    data_dir = Path(os.getenv("PROCESSFLOW_DATA_DIR", "data"))
    return f"sqlite+aiosqlite:///{data_dir / 'processflow.db'}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PROCESSFLOW_")

    database_url: str = _default_db_url()
    artifacts_dir: Path = Path("data/artifacts")
    cors_origins: list[str] = ["http://localhost:3000"]
    anthropic_api_key: str | None = None
    openrouter_api_key: str | None = None
    llm_provider: str = "anthropic"  # "anthropic" or "openrouter"
    llm_model: str = "claude-sonnet-4-20250514"  # default model for the selected provider
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    def get_api_key(self) -> str:
        """Get the appropriate API key based on configured provider."""
        if self.llm_provider == "openrouter":
            key = self.openrouter_api_key or os.environ.get("OPENROUTER_API_KEY")
            if not key:
                raise RuntimeError(
                    "OpenRouter provider selected but PROCESSFLOW_OPENROUTER_API_KEY not set"
                )
            return key
        else:  # anthropic
            key = self.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not key:
                raise RuntimeError(
                    "Anthropic provider selected but PROCESSFLOW_ANTHROPIC_API_KEY not set"
                )
            return key


settings = Settings()

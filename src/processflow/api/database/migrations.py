"""Simple table creation for MVP — no Alembic needed yet."""

from __future__ import annotations

from processflow.api.database.engine import async_engine
from processflow.api.database.models import Base


async def create_tables() -> None:
    """Create all tables if they don't exist."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

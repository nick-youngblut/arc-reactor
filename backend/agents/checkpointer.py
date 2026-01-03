from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import AsyncIterator

from sqlalchemy import text

from backend.services.database import DatabaseService, _build_database_url

try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
except ImportError as exc:  # pragma: no cover - optional dependency until installed
    AsyncPostgresSaver = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def _ensure_available() -> None:
    if _IMPORT_ERROR is not None:
        raise RuntimeError("LangGraph checkpointing is not available") from _IMPORT_ERROR


def _build_postgres_connection_string(settings: object) -> str:
    """Build a PostgreSQL connection string compatible with psycopg (not SQLAlchemy format)."""
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        # If DATABASE_URL is set, convert from SQLAlchemy format to psycopg format
        if env_url.startswith("postgresql+asyncpg://"):
            return env_url.replace("postgresql+asyncpg://", "postgresql://")
        return env_url

    user = os.getenv("DB_USER") or getattr(settings, "db_user", None)
    password = os.getenv("DB_PASSWORD") or getattr(settings, "db_password", "")
    database = os.getenv("DB_NAME") or getattr(settings, "db_name", None)
    host = os.getenv("DB_HOST") or getattr(settings, "db_host", None)
    port = os.getenv("DB_PORT") or getattr(settings, "db_port", 5432)

    if user and database and host:
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    raise ValueError("Database configuration is missing for PostgreSQL checkpointer")


@asynccontextmanager
async def checkpointer_session(settings: object) -> AsyncIterator["AsyncPostgresSaver"]:
    _ensure_available()
    database_url = _build_postgres_connection_string(settings)
    async with AsyncPostgresSaver.from_conn_string(database_url) as saver:
        await saver.setup()  # Ensure LangGraph tables exist
        yield saver


async def cleanup_old_threads(database: DatabaseService, max_age_days: int = 30) -> None:
    cutoff = f"NOW() - INTERVAL '{max_age_days} days'"
    query = text(f"DELETE FROM checkpoints WHERE created_at < {cutoff}")
    async with database.engine.begin() as conn:
        await conn.execute(query)

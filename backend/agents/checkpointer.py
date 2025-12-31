from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import timedelta
from typing import AsyncIterator

from sqlalchemy import text

from backend.services.database import DatabaseService, _build_database_url

try:
    from langgraph.checkpoint.base import JsonPlusSerializer
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
except ImportError as exc:  # pragma: no cover - optional dependency until installed
    AsyncPostgresSaver = None  # type: ignore[assignment]
    JsonPlusSerializer = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def _ensure_available() -> None:
    if _IMPORT_ERROR is not None:
        raise RuntimeError("LangGraph checkpointing is not available") from _IMPORT_ERROR


def _build_serializer():
    if JsonPlusSerializer is None:
        return None
    return JsonPlusSerializer()


@asynccontextmanager
async def checkpointer_session(settings: object) -> AsyncIterator["AsyncPostgresSaver"]:
    _ensure_available()
    database_url = _build_database_url(settings)
    serializer = _build_serializer()
    async with AsyncPostgresSaver.from_conn_string(database_url, serializer=serializer) as saver:
        yield saver


async def cleanup_old_threads(database: DatabaseService, max_age_days: int = 30) -> None:
    cutoff = f"NOW() - INTERVAL '{max_age_days} days'"
    query = text(f"DELETE FROM checkpoints WHERE created_at < {cutoff}")
    async with database.engine.begin() as conn:
        await conn.execute(query)

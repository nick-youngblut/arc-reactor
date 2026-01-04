from __future__ import annotations

from sqlalchemy import text

from backend.services.database import DatabaseService


async def cleanup_old_threads(database: DatabaseService, max_age_days: int = 30) -> None:
    cutoff = f"NOW() - INTERVAL '{max_age_days} days'"
    query = text(f"DELETE FROM checkpoints WHERE created_at < {cutoff}")
    async with database.engine.begin() as conn:
        await conn.execute(query)

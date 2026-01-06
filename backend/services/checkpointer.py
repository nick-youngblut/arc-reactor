from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

if TYPE_CHECKING:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

logger = logging.getLogger(__name__)


@dataclass
class CheckpointerService:
    """Application-level checkpointer with connection pooling."""

    pool: AsyncConnectionPool
    checkpointer: "AsyncPostgresSaver"

    @classmethod
    async def create(cls, settings: object) -> "CheckpointerService":
        """Create service with initialized pool and checkpointer."""
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        except ImportError as exc:
            raise RuntimeError("LangGraph checkpointing is not available") from exc

        conn_string = _build_checkpointer_connection_string(settings)

        pool = AsyncConnectionPool(
            conninfo=conn_string,
            min_size=getattr(settings, "checkpointer_pool_min_size", 5),
            max_size=getattr(settings, "checkpointer_pool_max_size", 50),
            timeout=getattr(settings, "checkpointer_pool_timeout", 30.0),
            max_idle=getattr(settings, "checkpointer_pool_max_idle", 300.0),
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
                "row_factory": dict_row,
            },
        )

        await pool.open()

        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()

        logger.info(
            "Checkpointer service initialized (pool: %d-%d connections)",
            pool.min_size,
            pool.max_size,
        )

        return cls(pool=pool, checkpointer=checkpointer)

    async def health_check(self) -> bool:
        """Check pool health for readiness endpoint."""
        try:
            async with self.pool.connection() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close pool during shutdown."""
        logger.info("Closing checkpointer connection pool")
        await self.pool.close()


def _build_checkpointer_connection_string(settings: object) -> str:
    """Build PostgreSQL connection string for psycopg3 (not SQLAlchemy format)."""
    env_url = os.getenv("DATABASE_URL")
    if env_url:
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

    raise ValueError("Database configuration is missing for checkpointer")

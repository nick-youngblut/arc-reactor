from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from ..utils.circuit_breaker import Breakers


def _build_benchling_url(settings: object) -> str:
    host = getattr(settings, "benchling_warehouse_host", None)
    db = getattr(settings, "benchling_warehouse_db", None)
    user = os.getenv("BENCHLING_WAREHOUSE_USER") or getattr(
        settings, "benchling_warehouse_user", "benchling_reader"
    )
    password = os.getenv("BENCHLING_WAREHOUSE_PASSWORD") or getattr(
        settings, "benchling_warehouse_password", ""
    )

    if not host or not db:
        raise ValueError("Benchling warehouse host and database must be configured")

    return f"postgresql+asyncpg://{user}:{password}@{host}:5432/{db}?sslmode=require"


@dataclass
class BenchlingService:
    engine: AsyncEngine
    breaker: object

    @classmethod
    def create(cls, settings: object, breakers: Breakers) -> "BenchlingService":
        warehouse_url = _build_benchling_url(settings)
        engine = create_async_engine(
            warehouse_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )
        return cls(engine=engine, breaker=breakers.benchling)

    async def query(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return await self._execute(sql, params or {})

    async def _execute(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        @self.breaker
        async def _run() -> list[dict[str, Any]]:
            async with self.engine.begin() as conn:
                result = await conn.execute(text(sql), params)
                return [dict(row) for row in result.mappings().all()]

        return await _run()

    async def health_check(self) -> bool:
        try:
            await self._execute("SELECT 1", {})
            return True
        except Exception:
            return False

    async def close(self) -> None:
        await self.engine.dispose()

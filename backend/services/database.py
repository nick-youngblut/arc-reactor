from __future__ import annotations

import os
from dataclasses import dataclass
from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def _build_database_url(settings: object) -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    user = os.getenv("DB_USER") or getattr(settings, "db_user", None)
    password = os.getenv("DB_PASSWORD") or getattr(settings, "db_password", "")
    database = os.getenv("DB_NAME") or getattr(settings, "db_name", None)
    host = os.getenv("DB_HOST") or getattr(settings, "db_host", None)
    port = os.getenv("DB_PORT") or getattr(settings, "db_port", 5432)
    connection_name = os.getenv("DB_CONNECTION_NAME") or getattr(
        settings, "cloudsql_connection_name", None
    )

    if user and database and connection_name and not host:
        return (
            f"postgresql+asyncpg://{user}:{password}@/{database}?host=/cloudsql/{connection_name}"
        )

    if user and database and host:
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

    raise ValueError("Database configuration is missing")


@dataclass
class DatabaseService:
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]

    @classmethod
    def create(cls, settings: object) -> "DatabaseService":
        database_url = _build_database_url(settings)
        engine = create_async_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        return cls(engine=engine, session_factory=session_factory)

    async def health_check(self) -> bool:
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def get_session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            yield session

    async def close(self) -> None:
        await self.engine.dispose()

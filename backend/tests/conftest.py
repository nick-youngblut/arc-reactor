"""Shared pytest fixtures for backend tests."""

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import Base
from backend.models.runs import Run
from backend.models.tasks import Task


@pytest.fixture
async def session() -> AsyncSession:
    """Create an in-memory SQLite database session for testing."""
    handle, path = tempfile.mkstemp(suffix=".db")
    os.close(handle)
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()
    os.unlink(path)

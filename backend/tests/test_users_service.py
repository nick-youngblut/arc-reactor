from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import Base
from backend.services.users import DEFAULT_PREFERENCES, DEFAULT_STATS, UserService


@pytest.fixture
async def session() -> AsyncSession:
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


@pytest.mark.asyncio
async def test_get_or_create_user(session: AsyncSession) -> None:
    service = UserService(session=session)
    user = await service.get_or_create_user("user@arc.org", "Arc User")
    assert user.email == "user@arc.org"
    assert user.display_name == "Arc User"
    assert user.preferences == DEFAULT_PREFERENCES
    assert user.stats == DEFAULT_STATS

    updated = await service.get_or_create_user("user@arc.org", "Arc User")
    assert updated.last_login_at >= user.last_login_at


@pytest.mark.asyncio
async def test_update_preferences(session: AsyncSession) -> None:
    service = UserService(session=session)
    await service.get_or_create_user("user@arc.org", "Arc User")

    user = await service.update_preferences(
        "user@arc.org", {"default_pipeline": "nf-core/scrnaseq"}
    )
    assert user is not None
    assert user.preferences["default_pipeline"] == "nf-core/scrnaseq"
    assert user.preferences["notifications_enabled"] is False


@pytest.mark.asyncio
async def test_update_stats(session: AsyncSession) -> None:
    service = UserService(session=session)
    await service.get_or_create_user("user@arc.org", "Arc User")

    user = await service.update_stats("user@arc.org", sample_count=10, successful=True)
    assert user is not None
    assert user.stats["total_runs"] == 1
    assert user.stats["successful_runs"] == 1
    assert user.stats["total_samples_processed"] == 10

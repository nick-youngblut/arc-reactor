from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import Base
from backend.models.runs import Run
from backend.models.tasks import Task
from backend.models.weblog_event_log import WeblogEventLog


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


async def _create_run(session: AsyncSession) -> Run:
    run = Run(
        run_id="run-123",
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        status="pending",
        user_email="user@arc.org",
        user_name="Arc User",
        gcs_path="gs://arc-reactor-runs/runs/run-123",
        params={},
        sample_count=1,
    )
    session.add(run)
    await session.commit()
    return run


@pytest.mark.asyncio
async def test_task_unique_constraint(session: AsyncSession) -> None:
    await _create_run(session)

    task = Task(
        id=uuid4(),
        run_id="run-123",
        task_id=1,
        hash="abcd1234efgh5678ijkl9012mnop3456",
        name="process task",
        process="ALIGN",
        status="COMPLETED",
        attempt=1,
    )
    session.add(task)
    await session.commit()

    duplicate = Task(
        id=uuid4(),
        run_id="run-123",
        task_id=1,
        hash="abcd1234efgh5678ijkl9012mnop3456",
        name="process task",
        process="ALIGN",
        status="COMPLETED",
        attempt=1,
    )
    session.add(duplicate)

    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.asyncio
async def test_weblog_event_log_unique_constraint(session: AsyncSession) -> None:
    event = WeblogEventLog(
        id=uuid4(),
        run_id="run-123",
        event_type="process_submitted",
        task_id=1,
        attempt=1,
        event_timestamp=datetime.now(timezone.utc),
    )
    session.add(event)
    await session.commit()

    duplicate = WeblogEventLog(
        id=uuid4(),
        run_id="run-123",
        event_type="process_submitted",
        task_id=1,
        attempt=1,
        event_timestamp=datetime.now(timezone.utc),
    )
    session.add(duplicate)

    with pytest.raises(IntegrityError):
        await session.commit()

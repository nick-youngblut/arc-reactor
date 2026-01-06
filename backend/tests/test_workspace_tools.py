from __future__ import annotations

import json
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.tools.workspace_tools import (
    get_current_config,
    get_current_samplesheet,
    get_workspace_status,
)
from backend.models.workspace_api import WorkspaceCreateRequest
from backend.services.workspace import WorkspaceService


def _make_runtime(session: AsyncSession, *, thread_id: str, user_email: str) -> SimpleNamespace:
    @asynccontextmanager
    async def _factory():
        yield WorkspaceService(session=session)

    return SimpleNamespace(
        config={
            "configurable": {
                "thread_id": thread_id,
                "user_email": user_email,
                "workspace_service_factory": _factory,
            }
        }
    )


@pytest.mark.asyncio
async def test_get_current_samplesheet_and_config(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    request = WorkspaceCreateRequest(
        thread_id="thread-1",
        samplesheet="sample-data",
        config="config-data",
    )
    await service.create("user@arc.org", request)

    runtime = _make_runtime(session, thread_id="thread-1", user_email="user@arc.org")

    samplesheet = await get_current_samplesheet.ainvoke({"runtime": runtime})
    config = await get_current_config.ainvoke({"runtime": runtime})

    assert samplesheet == "sample-data"
    assert config == "config-data"


@pytest.mark.asyncio
async def test_get_workspace_status(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    request = WorkspaceCreateRequest(
        thread_id="thread-2",
        pipeline="nf-core/scrnaseq",
        version="2.0",
        samplesheet="samples",
    )
    created = await service.create("user@arc.org", request)

    runtime = _make_runtime(session, thread_id="thread-2", user_email="user@arc.org")
    status = await get_workspace_status.ainvoke({"runtime": runtime})

    payload = json.loads(status)
    assert payload["workspace_id"] == str(created.id)
    assert payload["pipeline"] == "nf-core/scrnaseq"
    assert payload["samplesheet"]["present"] is True
    assert payload["config"]["present"] is False

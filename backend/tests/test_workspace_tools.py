from __future__ import annotations

import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.tools.workspace_tools import (
    get_current_config,
    get_current_samplesheet,
    get_workspace_status,
    update_config,
    update_samplesheet,
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


@pytest.mark.asyncio
async def test_update_samplesheet_success(monkeypatch) -> None:
    mock_service = AsyncMock()
    mock_service.get_or_create_for_thread.return_value = MagicMock(id="ws-123")
    mock_service.update_samplesheet.return_value = MagicMock()

    mock_context = MagicMock()
    mock_context.service = mock_service
    mock_context.thread_id = "thread-1"
    mock_context.user_email = "user@arc.org"
    mock_context.close = None

    async def mock_get_workspace_context(_runtime):
        return mock_context

    monkeypatch.setattr(
        "backend.agents.tools.workspace_tools.get_workspace_context",
        mock_get_workspace_context,
    )

    result = await update_samplesheet.ainvoke({"content": "sample,fastq_1\nA,gs://bucket/a.fq"})

    assert result == "Samplesheet updated successfully."
    mock_service.update_samplesheet.assert_called_once()
    _, kwargs = mock_service.update_samplesheet.call_args
    assert kwargs.get("force") is True


@pytest.mark.asyncio
async def test_update_samplesheet_overwrites_user_edits(monkeypatch) -> None:
    mock_service = AsyncMock()
    mock_service.get_or_create_for_thread.return_value = MagicMock(id="ws-123")
    mock_service.update_samplesheet.return_value = MagicMock()

    mock_context = MagicMock()
    mock_context.service = mock_service
    mock_context.thread_id = "thread-1"
    mock_context.user_email = "user@arc.org"
    mock_context.close = None

    async def mock_get_workspace_context(_runtime):
        return mock_context

    monkeypatch.setattr(
        "backend.agents.tools.workspace_tools.get_workspace_context",
        mock_get_workspace_context,
    )

    await update_samplesheet.ainvoke({"content": "new content"})

    _, kwargs = mock_service.update_samplesheet.call_args
    assert kwargs.get("force") is True


@pytest.mark.asyncio
async def test_update_samplesheet_error_no_thread(monkeypatch) -> None:
    mock_context = MagicMock()
    mock_context.service = MagicMock()
    mock_context.thread_id = None
    mock_context.user_email = "user@arc.org"
    mock_context.close = None

    async def mock_get_workspace_context(_runtime):
        return mock_context

    monkeypatch.setattr(
        "backend.agents.tools.workspace_tools.get_workspace_context",
        mock_get_workspace_context,
    )

    result = await update_samplesheet.ainvoke({"content": "test"})

    assert result == "Error: thread_id is required."


@pytest.mark.asyncio
async def test_update_config_success(monkeypatch) -> None:
    mock_service = AsyncMock()
    mock_service.get_or_create_for_thread.return_value = MagicMock(id="ws-123")
    mock_service.update_config.return_value = MagicMock()

    mock_context = MagicMock()
    mock_context.service = mock_service
    mock_context.thread_id = "thread-1"
    mock_context.user_email = "user@arc.org"
    mock_context.close = None

    async def mock_get_workspace_context(_runtime):
        return mock_context

    monkeypatch.setattr(
        "backend.agents.tools.workspace_tools.get_workspace_context",
        mock_get_workspace_context,
    )

    result = await update_config.ainvoke({"content": "params { genome = 'GRCh38' }"})

    assert result == "Config updated successfully."
    mock_service.update_config.assert_called_once()
    _, kwargs = mock_service.update_config.call_args
    assert kwargs.get("force") is True


@pytest.mark.asyncio
async def test_update_config_overwrites_user_edits(monkeypatch) -> None:
    mock_service = AsyncMock()
    mock_service.get_or_create_for_thread.return_value = MagicMock(id="ws-123")
    mock_service.update_config.return_value = MagicMock()

    mock_context = MagicMock()
    mock_context.service = mock_service
    mock_context.thread_id = "thread-1"
    mock_context.user_email = "user@arc.org"
    mock_context.close = None

    async def mock_get_workspace_context(_runtime):
        return mock_context

    monkeypatch.setattr(
        "backend.agents.tools.workspace_tools.get_workspace_context",
        mock_get_workspace_context,
    )

    await update_config.ainvoke({"content": "params { foo = 'bar' }"})

    _, kwargs = mock_service.update_config.call_args
    assert kwargs.get("force") is True


@pytest.mark.asyncio
async def test_update_config_error_no_thread(monkeypatch) -> None:
    mock_context = MagicMock()
    mock_context.service = MagicMock()
    mock_context.thread_id = None
    mock_context.user_email = "user@arc.org"
    mock_context.close = None

    async def mock_get_workspace_context(_runtime):
        return mock_context

    monkeypatch.setattr(
        "backend.agents.tools.workspace_tools.get_workspace_context",
        mock_get_workspace_context,
    )

    result = await update_config.ainvoke({"content": "test"})

    assert result == "Error: thread_id is required."

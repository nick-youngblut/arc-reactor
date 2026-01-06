from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.workspace_api import WorkspaceCreateRequest
from backend.services.workspace import WorkspaceService


@pytest.mark.asyncio
async def test_create_and_get_workspace(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    request = WorkspaceCreateRequest(
        thread_id="thread-1",
        pipeline="nf-core/rnaseq",
        version="1.0",
        samplesheet="sample-data",
        config="config-data",
    )

    created = await service.create("user@arc.org", request)
    assert created.user_email == "user@arc.org"
    assert created.thread_id == "thread-1"
    assert created.samplesheet.content == "sample-data"
    assert created.samplesheet.modified_by == "user"
    assert created.samplesheet.modified_at is not None
    assert created.config.content == "config-data"
    assert created.config.modified_by == "user"
    assert created.config.modified_at is not None

    fetched = await service.get(created.id, "user@arc.org")
    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_get_by_thread_and_draft(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    draft = await service.create("user@arc.org", WorkspaceCreateRequest())
    threaded = await service.create("user@arc.org", WorkspaceCreateRequest(thread_id="thread-2"))

    fetched_draft = await service.get_draft("user@arc.org")
    assert fetched_draft is not None
    assert fetched_draft.id == draft.id

    fetched_thread = await service.get_by_thread("user@arc.org", "thread-2")
    assert fetched_thread is not None
    assert fetched_thread.id == threaded.id


@pytest.mark.asyncio
async def test_get_or_create_for_thread(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    created = await service.get_or_create_for_thread("user@arc.org", "thread-3")
    again = await service.get_or_create_for_thread("user@arc.org", "thread-3")
    assert created.id == again.id


@pytest.mark.asyncio
async def test_list_by_user_filters_and_orders(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    await service.create("user@arc.org", WorkspaceCreateRequest(thread_id="thread-a"))
    await service.create("other@arc.org", WorkspaceCreateRequest(thread_id="thread-b"))

    workspaces = await service.list_by_user("user@arc.org")
    assert len(workspaces) == 1
    assert workspaces[0].thread_id == "thread-a"


@pytest.mark.asyncio
async def test_update_samplesheet_protects_user_edits(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    created = await service.create("user@arc.org", WorkspaceCreateRequest(samplesheet="initial"))

    with pytest.raises(ValueError):
        await service.update_samplesheet(
            created.id,
            "user@arc.org",
            "agent-update",
            "agent",
        )

    updated = await service.update_samplesheet(
        created.id,
        "user@arc.org",
        "agent-update",
        "agent",
        force=True,
    )
    assert updated is not None
    assert updated.samplesheet.content == "agent-update"
    assert updated.samplesheet.modified_by == "agent"


@pytest.mark.asyncio
async def test_update_config_protects_user_edits(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    created = await service.create("user@arc.org", WorkspaceCreateRequest(config="init"))

    with pytest.raises(ValueError):
        await service.update_config(
            created.id,
            "user@arc.org",
            "agent-config",
            "agent",
        )

    updated = await service.update_config(
        created.id,
        "user@arc.org",
        "agent-config",
        "agent",
        force=True,
    )
    assert updated is not None
    assert updated.config.content == "agent-config"
    assert updated.config.modified_by == "agent"


@pytest.mark.asyncio
async def test_update_pipeline_and_associate_thread(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    created = await service.create("user@arc.org", WorkspaceCreateRequest())

    updated = await service.update_pipeline(
        created.id,
        "user@arc.org",
        "nf-core/scrnaseq",
        "2.0",
    )
    assert updated is not None
    assert updated.pipeline == "nf-core/scrnaseq"
    assert updated.version == "2.0"

    associated = await service.associate_thread(
        created.id,
        "user@arc.org",
        "thread-4",
    )
    assert associated is not None
    assert associated.thread_id == "thread-4"


@pytest.mark.asyncio
async def test_delete_workspace(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    created = await service.create("user@arc.org", WorkspaceCreateRequest())

    deleted = await service.delete(created.id, "user@arc.org")
    assert deleted is True

    missing = await service.get(created.id, "user@arc.org")
    assert missing is None

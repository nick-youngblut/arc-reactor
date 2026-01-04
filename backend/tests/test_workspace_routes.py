from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.routes.workspaces import (
    associate_workspace_thread,
    create_workspace,
    delete_workspace,
    get_draft_workspace,
    get_workspace,
    get_workspace_by_thread,
    list_workspaces,
    update_config,
    update_pipeline,
    update_samplesheet,
    update_workspace,
)
from backend.models.workspace_api import (
    AssociateThreadRequest,
    FileUpdateRequest,
    PipelineUpdateRequest,
    WorkspaceCreateRequest,
    WorkspaceUpdateRequest,
)
from backend.services.workspace import WorkspaceService
from backend.utils.auth import UserContext
from backend.utils.errors import NotFoundError, ValidationError


@pytest.mark.asyncio
async def test_workspace_routes_create_and_get(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    user = UserContext(email="user@arc.org", name="Arc User")

    created = await create_workspace(
        WorkspaceCreateRequest(thread_id="thread-1", samplesheet="samples"),
        user=user,
        service=service,
    )

    fetched = await get_workspace(created.id, user=user, service=service)
    assert fetched.id == created.id
    assert fetched.samplesheet.content == "samples"


@pytest.mark.asyncio
async def test_workspace_routes_list_and_draft(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    user = UserContext(email="user@arc.org", name="Arc User")

    threaded = await create_workspace(
        WorkspaceCreateRequest(thread_id="thread-1"),
        user=user,
        service=service,
    )
    draft = await create_workspace(WorkspaceCreateRequest(), user=user, service=service)

    workspaces = await list_workspaces(user=user, service=service)
    assert len(workspaces) == 2
    assert {workspace.id for workspace in workspaces} == {threaded.id, draft.id}

    fetched_draft = await get_draft_workspace(user=user, service=service)
    assert fetched_draft is not None
    assert fetched_draft.id == draft.id


@pytest.mark.asyncio
async def test_workspace_routes_get_by_thread_not_found(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    user = UserContext(email="user@arc.org", name="Arc User")

    with pytest.raises(NotFoundError):
        await get_workspace_by_thread("missing-thread", user=user, service=service)


@pytest.mark.asyncio
async def test_workspace_routes_update_files(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    user = UserContext(email="user@arc.org", name="Arc User")

    created = await create_workspace(WorkspaceCreateRequest(), user=user, service=service)

    updated_samplesheet = await update_samplesheet(
        created.id,
        FileUpdateRequest(content="new-samples"),
        user=user,
        service=service,
    )
    assert updated_samplesheet.samplesheet.content == "new-samples"
    assert updated_samplesheet.samplesheet.modified_by == "user"

    updated_config = await update_config(
        created.id,
        FileUpdateRequest(content="new-config"),
        user=user,
        service=service,
    )
    assert updated_config.config.content == "new-config"
    assert updated_config.config.modified_by == "user"


@pytest.mark.asyncio
async def test_workspace_routes_update_pipeline_and_put(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    user = UserContext(email="user@arc.org", name="Arc User")

    created = await create_workspace(WorkspaceCreateRequest(), user=user, service=service)

    updated_pipeline = await update_pipeline(
        created.id,
        PipelineUpdateRequest(pipeline="nf-core/rnaseq", version="3.0"),
        user=user,
        service=service,
    )
    assert updated_pipeline.pipeline == "nf-core/rnaseq"
    assert updated_pipeline.version == "3.0"

    updated = await update_workspace(
        created.id,
        WorkspaceUpdateRequest(
            pipeline="nf-core/scrnaseq",
            version="2.0",
            samplesheet="samples",
            config="config",
        ),
        user=user,
        service=service,
    )
    assert updated.pipeline == "nf-core/scrnaseq"
    assert updated.samplesheet.content == "samples"
    assert updated.config.content == "config"


@pytest.mark.asyncio
async def test_workspace_routes_put_requires_pipeline_for_version(
    session: AsyncSession,
) -> None:
    service = WorkspaceService(session=session)
    user = UserContext(email="user@arc.org", name="Arc User")

    created = await create_workspace(WorkspaceCreateRequest(), user=user, service=service)

    with pytest.raises(ValidationError):
        await update_workspace(
            created.id,
            WorkspaceUpdateRequest(version="2.0"),
            user=user,
            service=service,
        )


@pytest.mark.asyncio
async def test_workspace_routes_associate_and_delete(session: AsyncSession) -> None:
    service = WorkspaceService(session=session)
    user = UserContext(email="user@arc.org", name="Arc User")

    draft = await create_workspace(WorkspaceCreateRequest(), user=user, service=service)

    associated = await associate_workspace_thread(
        draft.id,
        AssociateThreadRequest(thread_id="thread-9"),
        user=user,
        service=service,
    )
    assert associated.thread_id == "thread-9"

    deleted = await delete_workspace(draft.id, user=user, service=service)
    assert deleted is True

    with pytest.raises(NotFoundError):
        await get_workspace(draft.id, user=user, service=service)

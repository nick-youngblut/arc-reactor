from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.dependencies import get_current_user_context, get_workspace_service
from backend.models.workspace_api import (
    AssociateThreadRequest,
    FileUpdateRequest,
    PipelineUpdateRequest,
    WorkspaceCreateRequest,
    WorkspaceResponse,
    WorkspaceUpdateRequest,
)
from backend.services.workspace import WorkspaceService
from backend.utils.auth import UserContext
from backend.utils.errors import NotFoundError, ValidationError

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    user: UserContext = Depends(get_current_user_context),
    service: WorkspaceService = Depends(get_workspace_service),
) -> list[WorkspaceResponse]:
    """List all workspaces for the current user."""
    return await service.list_by_user(user.email)


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    request: WorkspaceCreateRequest,
    user: UserContext = Depends(get_current_user_context),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Create a new workspace (draft if no thread_id provided)."""
    return await service.create(user.email, request)


@router.get("/draft", response_model=WorkspaceResponse | None)
async def get_draft_workspace(
    user: UserContext = Depends(get_current_user_context),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse | None:
    """Get the user's draft workspace (not associated with a thread)."""
    return await service.get_draft(user.email)


@router.get("/by-thread/{thread_id}", response_model=WorkspaceResponse)
async def get_workspace_by_thread(
    thread_id: str,
    user: UserContext = Depends(get_current_user_context),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Get workspace by thread ID."""
    workspace = await service.get_by_thread(user.email, thread_id)
    if not workspace:
        raise NotFoundError("Workspace not found", detail=f"No workspace for thread {thread_id}")
    return workspace


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    user: UserContext = Depends(get_current_user_context),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Get workspace by ID."""
    workspace = await service.get(workspace_id, user.email)
    if not workspace:
        raise NotFoundError("Workspace not found", detail=f"No workspace with ID {workspace_id}")
    return workspace


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    request: WorkspaceUpdateRequest,
    user: UserContext = Depends(get_current_user_context),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Update entire workspace."""
    workspace = await service.get(workspace_id, user.email)
    if not workspace:
        raise NotFoundError("Workspace not found", detail=f"No workspace with ID {workspace_id}")

    if request.version is not None and request.pipeline is None:
        raise ValidationError("pipeline is required when providing version")

    if request.pipeline is not None:
        await service.update_pipeline(
            workspace_id,
            user.email,
            request.pipeline,
            request.version,
        )

    if request.samplesheet is not None:
        try:
            await service.update_samplesheet(
                workspace_id,
                user.email,
                request.samplesheet,
                "user",
            )
        except ValueError as exc:
            raise ValidationError("Cannot update samplesheet", detail=str(exc)) from exc

    if request.config is not None:
        try:
            await service.update_config(
                workspace_id,
                user.email,
                request.config,
                "user",
            )
        except ValueError as exc:
            raise ValidationError("Cannot update config", detail=str(exc)) from exc

    if (
        request.pipeline is None
        and request.samplesheet is None
        and request.config is None
        and request.version is None
    ):
        return workspace

    updated = await service.get(workspace_id, user.email)
    if not updated:
        raise NotFoundError("Workspace not found", detail=f"No workspace with ID {workspace_id}")
    return updated


@router.patch("/{workspace_id}/samplesheet", response_model=WorkspaceResponse)
async def update_samplesheet(
    workspace_id: UUID,
    request: FileUpdateRequest,
    user: UserContext = Depends(get_current_user_context),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Update samplesheet only."""
    try:
        workspace = await service.update_samplesheet(
            workspace_id,
            user.email,
            request.content,
            "user",
        )
    except ValueError as exc:
        raise ValidationError("Cannot update samplesheet", detail=str(exc)) from exc

    if not workspace:
        raise NotFoundError("Workspace not found", detail=f"No workspace with ID {workspace_id}")
    return workspace


@router.patch("/{workspace_id}/config", response_model=WorkspaceResponse)
async def update_config(
    workspace_id: UUID,
    request: FileUpdateRequest,
    user: UserContext = Depends(get_current_user_context),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Update config only."""
    try:
        workspace = await service.update_config(
            workspace_id,
            user.email,
            request.content,
            "user",
        )
    except ValueError as exc:
        raise ValidationError("Cannot update config", detail=str(exc)) from exc

    if not workspace:
        raise NotFoundError("Workspace not found", detail=f"No workspace with ID {workspace_id}")
    return workspace


@router.patch("/{workspace_id}/pipeline", response_model=WorkspaceResponse)
async def update_pipeline(
    workspace_id: UUID,
    request: PipelineUpdateRequest,
    user: UserContext = Depends(get_current_user_context),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Update pipeline selection."""
    workspace = await service.update_pipeline(
        workspace_id,
        user.email,
        request.pipeline,
        request.version,
    )
    if not workspace:
        raise NotFoundError("Workspace not found", detail=f"No workspace with ID {workspace_id}")
    return workspace


@router.post("/{workspace_id}/associate", response_model=WorkspaceResponse)
async def associate_workspace_thread(
    workspace_id: UUID,
    request: AssociateThreadRequest,
    user: UserContext = Depends(get_current_user_context),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """Associate draft workspace with thread."""
    workspace = await service.associate_thread(
        workspace_id,
        user.email,
        request.thread_id,
    )
    if not workspace:
        raise NotFoundError("Workspace not found", detail=f"No draft workspace {workspace_id}")
    return workspace


@router.delete("/{workspace_id}", response_model=bool)
async def delete_workspace(
    workspace_id: UUID,
    user: UserContext = Depends(get_current_user_context),
    service: WorkspaceService = Depends(get_workspace_service),
) -> bool:
    """Delete workspace."""
    deleted = await service.delete(workspace_id, user.email)
    if not deleted:
        raise NotFoundError("Workspace not found", detail=f"No workspace with ID {workspace_id}")
    return True

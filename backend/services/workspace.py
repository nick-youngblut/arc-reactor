from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.workspace import WorkspaceState
from backend.models.workspace_api import FileState, WorkspaceCreateRequest, WorkspaceResponse

ModifierType = Literal["agent", "user"]


@dataclass
class WorkspaceService:
    """Service for workspace state persistence."""

    session: AsyncSession

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    async def get(self, workspace_id: UUID, user_email: str) -> WorkspaceResponse | None:
        result = await self.session.execute(
            select(WorkspaceState).where(
                WorkspaceState.id == workspace_id,
                WorkspaceState.user_email == user_email,
            )
        )
        workspace = result.scalar_one_or_none()
        return self._to_response(workspace) if workspace else None

    async def get_by_thread(self, user_email: str, thread_id: str) -> WorkspaceResponse | None:
        result = await self.session.execute(
            select(WorkspaceState).where(
                WorkspaceState.user_email == user_email,
                WorkspaceState.thread_id == thread_id,
            )
        )
        workspace = result.scalar_one_or_none()
        return self._to_response(workspace) if workspace else None

    async def get_draft(self, user_email: str) -> WorkspaceResponse | None:
        result = await self.session.execute(
            select(WorkspaceState).where(
                WorkspaceState.user_email == user_email,
                WorkspaceState.thread_id.is_(None),
            )
        )
        workspace = result.scalar_one_or_none()
        return self._to_response(workspace) if workspace else None

    async def get_or_create_for_thread(
        self,
        user_email: str,
        thread_id: str,
    ) -> WorkspaceResponse:
        existing = await self.get_by_thread(user_email, thread_id)
        if existing:
            return existing

        workspace = WorkspaceState(
            user_email=user_email,
            thread_id=thread_id,
        )
        self.session.add(workspace)
        await self.session.commit()
        await self.session.refresh(workspace)
        return self._to_response(workspace)

    async def list_by_user(self, user_email: str) -> list[WorkspaceResponse]:
        result = await self.session.execute(
            select(WorkspaceState)
            .where(WorkspaceState.user_email == user_email)
            .order_by(WorkspaceState.updated_at.desc())
        )
        workspaces = result.scalars().all()
        return [self._to_response(workspace) for workspace in workspaces]

    async def create(self, user_email: str, request: WorkspaceCreateRequest) -> WorkspaceResponse:
        now = self._now()
        workspace = WorkspaceState(
            user_email=user_email,
            thread_id=request.thread_id,
            pipeline=request.pipeline,
            version=request.version,
            samplesheet=request.samplesheet,
            samplesheet_modified_by="user" if request.samplesheet else None,
            samplesheet_modified_at=now if request.samplesheet else None,
            config=request.config,
            config_modified_by="user" if request.config else None,
            config_modified_at=now if request.config else None,
        )
        self.session.add(workspace)
        await self.session.commit()
        await self.session.refresh(workspace)
        return self._to_response(workspace)

    async def update_samplesheet(
        self,
        workspace_id: UUID,
        user_email: str,
        content: str,
        modifier: ModifierType,
        *,
        force: bool = False,
    ) -> WorkspaceResponse | None:
        result = await self.session.execute(
            select(WorkspaceState).where(
                WorkspaceState.id == workspace_id,
                WorkspaceState.user_email == user_email,
            )
        )
        workspace = result.scalar_one_or_none()
        if not workspace:
            return None

        if (
            modifier == "agent"
            and workspace.samplesheet_modified_by == "user"
            and not force
        ):
            raise ValueError(
                "Cannot overwrite user-edited samplesheet. "
                "Use get_current_samplesheet to read current state."
            )

        workspace.samplesheet = content
        workspace.samplesheet_modified_by = modifier
        workspace.samplesheet_modified_at = self._now()

        await self.session.commit()
        await self.session.refresh(workspace)
        return self._to_response(workspace)

    async def update_config(
        self,
        workspace_id: UUID,
        user_email: str,
        content: str,
        modifier: ModifierType,
        *,
        force: bool = False,
    ) -> WorkspaceResponse | None:
        result = await self.session.execute(
            select(WorkspaceState).where(
                WorkspaceState.id == workspace_id,
                WorkspaceState.user_email == user_email,
            )
        )
        workspace = result.scalar_one_or_none()
        if not workspace:
            return None

        if modifier == "agent" and workspace.config_modified_by == "user" and not force:
            raise ValueError(
                "Cannot overwrite user-edited config. "
                "Use get_current_config to read current state."
            )

        workspace.config = content
        workspace.config_modified_by = modifier
        workspace.config_modified_at = self._now()

        await self.session.commit()
        await self.session.refresh(workspace)
        return self._to_response(workspace)

    async def update_pipeline(
        self,
        workspace_id: UUID,
        user_email: str,
        pipeline: str,
        version: str | None,
    ) -> WorkspaceResponse | None:
        result = await self.session.execute(
            select(WorkspaceState).where(
                WorkspaceState.id == workspace_id,
                WorkspaceState.user_email == user_email,
            )
        )
        workspace = result.scalar_one_or_none()
        if not workspace:
            return None

        workspace.pipeline = pipeline
        workspace.version = version

        await self.session.commit()
        await self.session.refresh(workspace)
        return self._to_response(workspace)

    async def associate_thread(
        self,
        workspace_id: UUID,
        user_email: str,
        thread_id: str,
    ) -> WorkspaceResponse | None:
        result = await self.session.execute(
            select(WorkspaceState).where(
                WorkspaceState.id == workspace_id,
                WorkspaceState.user_email == user_email,
                WorkspaceState.thread_id.is_(None),
            )
        )
        workspace = result.scalar_one_or_none()
        if not workspace:
            return None

        workspace.thread_id = thread_id

        await self.session.commit()
        await self.session.refresh(workspace)
        return self._to_response(workspace)

    async def delete(self, workspace_id: UUID, user_email: str) -> bool:
        result = await self.session.execute(
            select(WorkspaceState).where(
                WorkspaceState.id == workspace_id,
                WorkspaceState.user_email == user_email,
            )
        )
        workspace = result.scalar_one_or_none()
        if not workspace:
            return False

        await self.session.delete(workspace)
        await self.session.commit()
        return True

    def _to_response(self, workspace: WorkspaceState) -> WorkspaceResponse:
        return WorkspaceResponse(
            id=workspace.id,
            user_email=workspace.user_email,
            thread_id=workspace.thread_id,
            pipeline=workspace.pipeline,
            version=workspace.version,
            samplesheet=FileState(
                content=workspace.samplesheet,
                modified_by=workspace.samplesheet_modified_by,
                modified_at=workspace.samplesheet_modified_at,
            ),
            config=FileState(
                content=workspace.config,
                modified_by=workspace.config_modified_by,
                modified_at=workspace.config_modified_at,
            ),
            validation_result=workspace.validation_result,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )

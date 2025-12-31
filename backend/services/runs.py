from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.runs import Run
from backend.models.schemas.runs import RunListResponse, RunResponse, RunStatus


_STATUS_FIELD_MAP: dict[RunStatus, str] = {
    RunStatus.SUBMITTED: "submitted_at",
    RunStatus.RUNNING: "started_at",
    RunStatus.COMPLETED: "completed_at",
    RunStatus.FAILED: "failed_at",
    RunStatus.CANCELLED: "cancelled_at",
}

_STATUS_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.PENDING: {RunStatus.SUBMITTED, RunStatus.CANCELLED},
    RunStatus.SUBMITTED: {RunStatus.RUNNING, RunStatus.CANCELLED},
    RunStatus.RUNNING: {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED},
    RunStatus.COMPLETED: set(),
    RunStatus.FAILED: set(),
    RunStatus.CANCELLED: set(),
}


@dataclass
class RunStoreService:
    session: AsyncSession
    bucket_name: str

    @classmethod
    def create(cls, session: AsyncSession, settings: object) -> "RunStoreService":
        bucket_name = getattr(settings, "nextflow_bucket", None)
        if not bucket_name:
            raise ValueError("nextflow_bucket must be configured")
        return cls(session=session, bucket_name=bucket_name)

    def _gcs_path(self, run_id: str) -> str:
        return f"gs://{self.bucket_name}/runs/{run_id}"

    def _work_dir(self, run_id: str) -> str:
        return f"gs://{self.bucket_name}/runs/{run_id}/work/"

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _normalize_status(status: RunStatus | str) -> RunStatus:
        if isinstance(status, RunStatus):
            return status
        return RunStatus(status)

    @staticmethod
    def _to_response(run: Run) -> RunResponse:
        return RunResponse(
            run_id=run.run_id,
            pipeline=run.pipeline,
            pipeline_version=run.pipeline_version,
            status=RunStatus(run.status),
            user_email=run.user_email,
            user_name=run.user_name,
            created_at=run.created_at,
            updated_at=run.updated_at,
            submitted_at=run.submitted_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            failed_at=run.failed_at,
            cancelled_at=run.cancelled_at,
            gcs_path=run.gcs_path,
            batch_job_name=run.batch_job_name,
            params=run.params,
            sample_count=run.sample_count,
            source_ngs_runs=run.source_ngs_runs,
            source_project=run.source_project,
            parent_run_id=run.parent_run_id,
            is_recovery=run.is_recovery,
            recovery_notes=run.recovery_notes,
            reused_work_dir=run.reused_work_dir,
            exit_code=run.exit_code,
            error_message=run.error_message,
            error_task=run.error_task,
            metrics=run.metrics,
        )

    async def create_run(
        self,
        *,
        pipeline: str,
        pipeline_version: str,
        user_email: str,
        user_name: str | None,
        params: dict[str, Any],
        sample_count: int,
        source_ngs_runs: list[str] | None = None,
        source_project: str | None = None,
    ) -> str:
        run_id = f"run-{uuid4().hex[:8]}"
        now = self._now()
        run = Run(
            run_id=run_id,
            pipeline=pipeline,
            pipeline_version=pipeline_version,
            status=RunStatus.PENDING.value,
            user_email=user_email,
            user_name=user_name,
            created_at=now,
            updated_at=now,
            gcs_path=self._gcs_path(run_id),
            params=params,
            sample_count=sample_count,
            source_ngs_runs=source_ngs_runs,
            source_project=source_project,
            is_recovery=False,
        )
        self.session.add(run)
        await self.session.commit()
        return run_id

    async def get_run(self, run_id: str) -> RunResponse | None:
        run = await self.session.get(Run, run_id)
        if not run:
            return None
        return self._to_response(run)

    async def list_runs(
        self,
        *,
        user_email: str | None = None,
        status: RunStatus | str | None = None,
        pipeline: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> RunListResponse:
        filters = []
        if user_email:
            filters.append(Run.user_email == user_email)
        if status:
            filters.append(Run.status == self._normalize_status(status).value)
        if pipeline:
            filters.append(Run.pipeline == pipeline)

        total_query = select(func.count()).select_from(Run)
        if filters:
            total_query = total_query.where(*filters)
        total = (await self.session.execute(total_query)).scalar_one()

        query = select(Run)
        if filters:
            query = query.where(*filters)
        query = query.order_by(Run.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(query)
        runs = [self._to_response(run) for run in result.scalars().all()]

        return RunListResponse(
            runs=runs,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_run_status(
        self,
        *,
        run_id: str,
        status: RunStatus | str,
        timestamp: datetime | None = None,
        batch_job_name: str | None = None,
        exit_code: int | None = None,
        error_message: str | None = None,
        error_task: str | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> bool:
        run = await self.session.get(Run, run_id)
        if not run:
            return False

        next_status = self._normalize_status(status)
        current_status = RunStatus(run.status)
        if next_status != current_status:
            allowed = _STATUS_TRANSITIONS.get(current_status, set())
            if next_status not in allowed:
                raise ValueError(
                    f"Invalid status transition: {current_status.value} -> {next_status.value}"
                )
            run.status = next_status.value

        now = timestamp or self._now()
        run.updated_at = now

        if next_status in _STATUS_FIELD_MAP:
            setattr(run, _STATUS_FIELD_MAP[next_status], now)

        if batch_job_name is not None:
            run.batch_job_name = batch_job_name
        if exit_code is not None:
            run.exit_code = exit_code
        if error_message is not None:
            run.error_message = error_message
        if error_task is not None:
            run.error_task = error_task
        if metrics is not None:
            run.metrics = metrics

        await self.session.commit()
        return True

    async def create_recovery_run(
        self,
        *,
        parent_run_id: str,
        user_email: str,
        user_name: str | None,
        notes: str | None = None,
        override_params: dict[str, Any] | None = None,
        reused_work_dir: str | None = None,
    ) -> str | None:
        parent = await self.session.get(Run, parent_run_id)
        if not parent:
            return None

        run_id = f"run-{uuid4().hex[:8]}"
        now = self._now()
        run = Run(
            run_id=run_id,
            pipeline=parent.pipeline,
            pipeline_version=parent.pipeline_version,
            status=RunStatus.PENDING.value,
            user_email=user_email,
            user_name=user_name,
            created_at=now,
            updated_at=now,
            gcs_path=self._gcs_path(run_id),
            params=override_params if override_params is not None else parent.params,
            sample_count=parent.sample_count,
            source_ngs_runs=parent.source_ngs_runs,
            source_project=parent.source_project,
            parent_run_id=parent.run_id,
            is_recovery=True,
            recovery_notes=notes,
            reused_work_dir=reused_work_dir or self._work_dir(parent.run_id),
        )
        self.session.add(run)
        await self.session.commit()
        return run_id

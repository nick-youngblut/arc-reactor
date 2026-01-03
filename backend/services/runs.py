from __future__ import annotations

import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.runs import Run
from backend.models.schemas.runs import RunListResponse, RunResponse, RunStatus
from backend.services.batch import BatchService
from backend.services.storage import StorageService
from backend.utils.errors import BatchError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


_STATUS_FIELD_MAP: dict[RunStatus, str] = {
    RunStatus.SUBMITTED: "submitted_at",
    RunStatus.RUNNING: "started_at",
    RunStatus.COMPLETED: "completed_at",
    RunStatus.FAILED: "failed_at",
    RunStatus.CANCELLED: "cancelled_at",
}

_STATUS_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.PENDING: {RunStatus.SUBMITTED, RunStatus.CANCELLED, RunStatus.FAILED},
    RunStatus.SUBMITTED: {RunStatus.RUNNING, RunStatus.CANCELLED, RunStatus.FAILED},
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
    def _render_params_yaml(params: dict[str, Any]) -> str:
        lines = []
        for key, value in params.items():
            if isinstance(value, bool):
                rendered = "true" if value else "false"
            elif isinstance(value, (int, float)):
                rendered = str(value)
            else:
                rendered = f"\"{value}\""
            lines.append(f"{key}: {rendered}")
        return "\n".join(lines)

    @staticmethod
    def _format_error_message(exc: Exception) -> str:
        detail = getattr(exc, "detail", None)
        if detail:
            return str(detail)
        return str(exc)

    @staticmethod
    def _emit_metric(name: str, value: int | float, **tags: Any) -> None:
        logger.info("metric %s=%s %s", name, value, tags)

    @staticmethod
    def _generate_weblog_secret() -> tuple[str, str]:
        weblog_secret = secrets.token_urlsafe(24)
        weblog_secret_hash = hashlib.sha256(weblog_secret.encode()).hexdigest()
        return weblog_secret, weblog_secret_hash

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
    ) -> tuple[str, str]:
        run_id = f"run-{uuid4().hex[:12]}"
        now = self._now()
        weblog_secret, weblog_secret_hash = self._generate_weblog_secret()
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
            weblog_secret_hash=weblog_secret_hash,
        )
        self.session.add(run)
        await self.session.commit()
        return run_id, weblog_secret

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
                logger.warning(
                    "Invalid run status transition",
                    extra={
                        "run_id": run_id,
                        "current_status": current_status.value,
                        "next_status": next_status.value,
                    },
                )
                raise ValueError(
                    f"Invalid status transition: {current_status.value} -> {next_status.value}"
                )
            run.status = next_status.value
            logger.info(
                "Run status updated",
                extra={
                    "run_id": run_id,
                    "current_status": current_status.value,
                    "next_status": next_status.value,
                },
            )
            self._emit_metric(
                "run_status_transition",
                1,
                run_id=run_id,
                from_status=current_status.value,
                to_status=next_status.value,
            )

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
            logger.error(
                "Run error recorded",
                extra={"run_id": run_id, "status": next_status.value, "error_message": error_message},
            )
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
    ) -> tuple[str, str] | None:
        parent = await self.session.get(Run, parent_run_id)
        if not parent:
            return None

        run_id = f"run-{uuid4().hex[:12]}"
        now = self._now()
        weblog_secret, weblog_secret_hash = self._generate_weblog_secret()
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
            weblog_secret_hash=weblog_secret_hash,
        )
        self.session.add(run)
        await self.session.commit()
        return run_id, weblog_secret

    async def submit_run(
        self,
        *,
        payload: object,
        user_email: str,
        user_name: str | None,
        sample_count: int,
        storage: StorageService,
        batch: BatchService,
    ) -> str:
        samplesheet_csv = getattr(payload, "samplesheet_csv", None)
        config_content = getattr(payload, "config_content", None)
        params = getattr(payload, "params", None)
        pipeline = getattr(payload, "pipeline", None)
        pipeline_version = getattr(payload, "pipeline_version", None)

        if not all([samplesheet_csv, config_content, params is not None, pipeline, pipeline_version]):
            raise ValidationError("Missing required submission inputs")

        run_id, weblog_secret = await self.create_run(
            pipeline=pipeline,
            pipeline_version=pipeline_version,
            user_email=user_email,
            user_name=user_name,
            params=params,
            sample_count=sample_count,
        )

        logger.info(
            "Submitting run",
            extra={"run_id": run_id, "pipeline": pipeline, "pipeline_version": pipeline_version},
        )

        try:
            params_yaml = self._render_params_yaml(params)
            storage.upload_run_files(
                run_id,
                {
                    "samplesheet.csv": samplesheet_csv,
                    "nextflow.config": config_content,
                    "params.yaml": params_yaml,
                },
                user_email,
            )

            config_gcs_path = (
                f"gs://{storage.bucket_name}/runs/{run_id}/inputs/nextflow.config"
            )
            params_gcs_path = f"gs://{storage.bucket_name}/runs/{run_id}/inputs/params.yaml"
            work_dir = f"gs://{storage.bucket_name}/runs/{run_id}/work/"

            batch_job_name = batch.submit_orchestrator_job(
                run_id=run_id,
                pipeline=pipeline,
                pipeline_version=pipeline_version,
                config_gcs_path=config_gcs_path,
                params_gcs_path=params_gcs_path,
                work_dir=work_dir,
                is_recovery=False,
                weblog_secret=weblog_secret,
                user_email=user_email,
            )

            await self.update_run_status(
                run_id=run_id,
                status=RunStatus.SUBMITTED,
                batch_job_name=batch_job_name,
            )
            self._emit_metric("run_submitted", 1, run_id=run_id, pipeline=pipeline)
            return run_id
        except Exception as exc:
            logger.exception("Run submission failed", extra={"run_id": run_id})
            try:
                await self.update_run_status(
                    run_id=run_id,
                    status=RunStatus.FAILED,
                    error_message=self._format_error_message(exc),
                )
                self._emit_metric("run_submission_failed", 1, run_id=run_id)
            except Exception:
                logger.exception("Failed to mark run as failed", extra={"run_id": run_id})
            if isinstance(exc, BatchError):
                raise
            raise BatchError("Run submission failed", detail=self._format_error_message(exc))

    async def submit_recovery_run(
        self,
        *,
        parent_run_id: str,
        user_email: str,
        user_name: str | None,
        storage: StorageService,
        batch: BatchService,
        notes: str | None = None,
        override_params: dict[str, Any] | None = None,
        override_config: str | None = None,
        reuse_work_dir: bool = True,
    ) -> str:
        parent = await self.get_run(parent_run_id)
        if not parent:
            raise NotFoundError("Run not found", detail=f"No run exists with ID {parent_run_id}")

        if parent.status not in {RunStatus.FAILED, RunStatus.CANCELLED}:
            raise ValidationError(
                "Only failed or cancelled runs can be recovered",
                detail=parent.status.value,
            )

        if reuse_work_dir and not storage.check_work_dir_exists(parent_run_id):
            raise ValidationError("Recovery unavailable: work directory not found")

        reused_work_dir = f"gs://{storage.bucket_name}/runs/{parent_run_id}/work/"
        recovery = await self.create_recovery_run(
            parent_run_id=parent_run_id,
            user_email=user_email,
            user_name=user_name,
            notes=notes,
            override_params=override_params,
            reused_work_dir=reused_work_dir if reuse_work_dir else None,
        )
        if not recovery:
            raise NotFoundError("Run not found", detail=f"No run exists with ID {parent_run_id}")
        run_id, weblog_secret = recovery

        logger.info(
            "Submitting recovery run",
            extra={
                "run_id": run_id,
                "parent_run_id": parent_run_id,
                "reuse_work_dir": reuse_work_dir,
            },
        )

        try:
            samplesheet = storage.get_file_content(
                f"gs://{storage.bucket_name}/runs/{parent_run_id}/inputs/samplesheet.csv",
                text=True,
            )
            config_content = (
                override_config
                if override_config is not None
                else storage.get_file_content(
                    f"gs://{storage.bucket_name}/runs/{parent_run_id}/inputs/nextflow.config",
                    text=True,
                )
            )
            if override_params is not None:
                params_yaml = self._render_params_yaml(override_params)
            else:
                params_yaml = storage.get_file_content(
                    f"gs://{storage.bucket_name}/runs/{parent_run_id}/inputs/params.yaml",
                    text=True,
                )

            storage.upload_run_files(
                run_id,
                {
                    "samplesheet.csv": samplesheet,
                    "nextflow.config": config_content,
                    "params.yaml": params_yaml,
                },
                user_email,
            )

            config_gcs_path = (
                f"gs://{storage.bucket_name}/runs/{run_id}/inputs/nextflow.config"
            )
            params_gcs_path = f"gs://{storage.bucket_name}/runs/{run_id}/inputs/params.yaml"
            work_dir = reused_work_dir if reuse_work_dir else f"{self._work_dir(run_id)}"

            batch_job_name = batch.submit_orchestrator_job(
                run_id=run_id,
                pipeline=parent.pipeline,
                pipeline_version=parent.pipeline_version,
                config_gcs_path=config_gcs_path,
                params_gcs_path=params_gcs_path,
                work_dir=work_dir,
                is_recovery=True,
                weblog_secret=weblog_secret,
                user_email=user_email,
            )

            await self.update_run_status(
                run_id=run_id,
                status=RunStatus.SUBMITTED,
                batch_job_name=batch_job_name,
            )
            self._emit_metric("run_recovery_submitted", 1, run_id=run_id)
            return run_id
        except Exception as exc:
            logger.exception("Recovery submission failed", extra={"run_id": run_id})
            try:
                await self.update_run_status(
                    run_id=run_id,
                    status=RunStatus.FAILED,
                    error_message=self._format_error_message(exc),
                )
                self._emit_metric("run_recovery_failed", 1, run_id=run_id)
            except Exception:
                logger.exception("Failed to mark recovery run as failed", extra={"run_id": run_id})
            if isinstance(exc, BatchError):
                raise
            raise BatchError("Recovery submission failed", detail=self._format_error_message(exc))

    async def reconcile_stale_runs(
        self,
        *,
        batch: BatchService,
        min_age_seconds: float = 900.0,
    ) -> int:
        cutoff = self._now().timestamp() - min_age_seconds
        query = select(Run).where(Run.status.in_([RunStatus.SUBMITTED.value, RunStatus.RUNNING.value]))
        result = await self.session.execute(query)
        stale_runs = [run for run in result.scalars().all() if run.updated_at.timestamp() < cutoff]

        reconciled = 0
        for run in stale_runs:
            if not run.batch_job_name:
                continue
            try:
                status = batch.get_job_status(run.batch_job_name)
            except Exception as exc:
                logger.warning(
                    "Failed to fetch Batch status for run",
                    extra={"run_id": run.run_id, "error": str(exc)},
                )
                continue
            run_status = status.get("run_status")
            if not run_status:
                continue
            next_status = RunStatus(run_status)
            if next_status == RunStatus.FAILED:
                message = None
                events = status.get("status_events") or []
                if events:
                    message = str(events[-1].get("description"))
                await self.update_run_status(
                    run_id=run.run_id,
                    status=next_status,
                    error_message=message,
                )
                reconciled += 1
            elif next_status in {RunStatus.COMPLETED, RunStatus.CANCELLED}:
                await self.update_run_status(run_id=run.run_id, status=next_status)
                reconciled += 1

        if reconciled:
            logger.info("Reconciled stale runs", extra={"count": reconciled})
        return reconciled

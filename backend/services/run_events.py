from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.schemas.runs import RunStatus
from backend.services.runs import RunStoreService


@dataclass
class RunEvent:
    event: str
    status: RunStatus
    timestamp: datetime
    progress: float | None = None


@dataclass
class RunEventService:
    session: AsyncSession
    settings: object

    @staticmethod
    def _status_timestamp(run) -> datetime:
        if run.status == RunStatus.SUBMITTED and run.submitted_at:
            return run.submitted_at
        if run.status == RunStatus.RUNNING and run.started_at:
            return run.started_at
        if run.status == RunStatus.COMPLETED and run.completed_at:
            return run.completed_at
        if run.status == RunStatus.FAILED and run.failed_at:
            return run.failed_at
        if run.status == RunStatus.CANCELLED and run.cancelled_at:
            return run.cancelled_at
        return run.updated_at or datetime.now(timezone.utc)

    @staticmethod
    def _progress_from_metrics(metrics: dict[str, object] | None) -> float | None:
        if not metrics:
            return None
        raw_progress = metrics.get("progress")
        if isinstance(raw_progress, (int, float)):
            return float(raw_progress)
        completed = metrics.get("tasks_completed")
        total = metrics.get("tasks_total")
        if isinstance(completed, (int, float)) and isinstance(total, (int, float)) and total:
            return float(completed) / float(total)
        return None

    async def stream_run_events(
        self,
        run_id: str,
        *,
        poll_interval: float = 2.0,
    ) -> AsyncIterator[RunEvent]:
        service = RunStoreService.create(self.session, settings=self.settings)
        run = await service.get_run(run_id)
        if not run:
            return
        last_status = run.status
        yield RunEvent(
            event="status",
            status=last_status,
            timestamp=self._status_timestamp(run),
            progress=self._progress_from_metrics(run.metrics),
        )

        while True:
            current = await service.get_run(run_id)
            if not current:
                yield RunEvent(
                    event="done", status=last_status, timestamp=datetime.now(timezone.utc)
                )
                break
            if current.status != last_status:
                last_status = current.status
                yield RunEvent(
                    event="status",
                    status=last_status,
                    timestamp=self._status_timestamp(current),
                    progress=self._progress_from_metrics(current.metrics),
                )
                if last_status in {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}:
                    yield RunEvent(
                        event="done", status=last_status, timestamp=datetime.now(timezone.utc)
                    )
                    break
            await asyncio.sleep(poll_interval)

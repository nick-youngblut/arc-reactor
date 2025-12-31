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


@dataclass
class RunEventService:
    session: AsyncSession
    settings: object

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
        yield RunEvent(event="status", status=last_status, timestamp=datetime.now(timezone.utc))

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
                    event="status", status=last_status, timestamp=datetime.now(timezone.utc)
                )
                if last_status in {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}:
                    yield RunEvent(
                        event="done", status=last_status, timestamp=datetime.now(timezone.utc)
                    )
                    break
            await asyncio.sleep(poll_interval)

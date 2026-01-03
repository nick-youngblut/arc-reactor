from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from google.cloud import batch_v1
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db_session
from backend.models.runs import Run
from backend.utils.auth import ServiceContext, get_service_context

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/reconcile-runs")
async def reconcile_stale_runs(
    service: ServiceContext = Depends(get_service_context),
    session: AsyncSession = Depends(get_db_session),
):
    stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=10)
    orphan_threshold = datetime.now(timezone.utc) - timedelta(hours=24)

    result = await session.execute(
        select(Run).where(
            Run.status.in_(["submitted", "running"]),
            Run.updated_at < stale_threshold,
        )
    )
    stale_runs = result.scalars().all()

    batch_client = batch_v1.BatchServiceClient()
    reconciled = []

    for run in stale_runs:
        if not run.batch_job_name:
            continue

        try:
            job = batch_client.get_job(name=run.batch_job_name)
            batch_state = job.status.state.name

            if batch_state in ("SUCCEEDED", "FAILED") and run.status == "running":
                new_status = "completed" if batch_state == "SUCCEEDED" else "failed"

                await session.execute(
                    update(Run)
                    .where(Run.run_id == run.run_id)
                    .values(
                        status=new_status,
                        completed_at=datetime.now(timezone.utc)
                        if new_status == "completed"
                        else None,
                        failed_at=datetime.now(timezone.utc)
                        if new_status == "failed"
                        else None,
                        error_message="Status recovered from Batch API (original event lost)",
                        updated_at=datetime.now(timezone.utc),
                    )
                )
                reconciled.append(
                    {"run_id": run.run_id, "action": f"updated to {new_status}"}
                )

        except Exception:
            if run.created_at < orphan_threshold:
                await session.execute(
                    update(Run)
                    .where(Run.run_id == run.run_id)
                    .values(
                        status="failed",
                        failed_at=datetime.now(timezone.utc),
                        error_message="Run orphaned: Batch job not found after 24 hours",
                        updated_at=datetime.now(timezone.utc),
                    )
                )
                reconciled.append(
                    {"run_id": run.run_id, "action": "marked as failed (orphaned)"}
                )

    await session.commit()

    return {
        "checked": len(stale_runs),
        "reconciled": reconciled,
    }

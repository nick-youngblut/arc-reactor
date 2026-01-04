from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class TaskResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    run_id: str
    task_id: int
    hash: str
    name: str
    process: str
    status: str
    exit_code: int | None = None
    submit_time: int | None = None
    start_time: int | None = None
    complete_time: int | None = None
    duration_ms: int | None = None
    realtime_ms: int | None = None
    cpu_percent: float | None = None
    peak_rss: int | None = None
    peak_vmem: int | None = None
    workdir: str | None = None
    container: str | None = None
    attempt: int
    error_message: str | None = None


class TaskSummaryResponse(BaseModel):
    total: int
    completed: int
    running: int
    submitted: int
    failed: int
    cached: int

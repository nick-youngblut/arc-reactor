from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunCreateRequest(BaseModel):
    pipeline: str = Field(..., pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
    pipeline_version: str = Field(..., pattern=r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")
    samplesheet_csv: str = Field(..., max_length=10 * 1024 * 1024)
    config_content: str = Field(..., max_length=100 * 1024)
    params: dict[str, Any] = Field(default_factory=dict)


class RunResponse(BaseModel):
    run_id: str
    pipeline: str
    pipeline_version: str
    status: RunStatus
    user_email: str
    user_name: str | None = None
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    cancelled_at: datetime | None = None
    gcs_path: str
    batch_job_name: str | None = None
    params: dict[str, Any]
    sample_count: int
    source_ngs_runs: list[str] | None = None
    source_project: str | None = None
    parent_run_id: str | None = None
    is_recovery: bool = False
    recovery_notes: str | None = None
    reused_work_dir: str | None = None
    exit_code: int | None = None
    error_message: str | None = None
    error_task: str | None = None
    metrics: dict[str, Any] | None = None


class RunListResponse(BaseModel):
    runs: list[RunResponse]
    total: int
    page: int
    page_size: int


class RunRecoverRequest(BaseModel):
    reuse_work_dir: bool = True
    notes: str | None = None
    override_params: dict[str, Any] | None = None
    override_config: str | None = None

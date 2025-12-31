from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class LogEntry(BaseModel):
    timestamp: datetime
    source: Literal["nextflow", "task", "batch"]
    message: str
    task_name: str | None = None
    stream: Literal["stdout", "stderr"] | None = None


class TaskInfo(BaseModel):
    task_id: str
    name: str
    process: str
    status: str
    exit_code: int | None = None
    duration: str | None = None
    cpu_percent: str | None = None
    memory_peak: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    work_dir: str | None = None
    has_logs: bool


class TaskLogs(BaseModel):
    task_id: str
    stdout: str
    stderr: str

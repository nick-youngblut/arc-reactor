from __future__ import annotations

import asyncio
import csv
import io
import logging
import re
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator

from backend.models.schemas.logs import LogEntry, TaskInfo, TaskLogs
from backend.services.storage import StorageService
from backend.utils.errors import BatchError

logger = logging.getLogger(__name__)

_TRACE_CACHE: dict[str, dict[str, Any]] = {}
_TRACE_TTL = timedelta(minutes=5)

_TIMESTAMP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)(Z)?")


@dataclass
class LogService:
    storage: StorageService
    project_id: str | None

    @classmethod
    def create(cls, storage: StorageService, settings: object) -> "LogService":
        project_id = getattr(settings, "gcp_project", None)
        return cls(storage=storage, project_id=project_id)

    def _log_path(self, run_id: str, filename: str) -> str:
        return f"gs://{self.storage.bucket_name}/runs/{run_id}/logs/{filename}"

    def _parse_line(self, line: str, source: str) -> LogEntry:
        timestamp = datetime.now(timezone.utc)
        match = _TIMESTAMP_RE.match(line)
        if match:
            value = match.group(1)
            if match.group(2):
                value = f"{value}+00:00"
            try:
                timestamp = datetime.fromisoformat(value)
            except ValueError:
                timestamp = datetime.now(timezone.utc)
        message = line.strip()
        return LogEntry(timestamp=timestamp, source=source, message=message)

    async def get_workflow_log(
        self,
        run_id: str,
        *,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[LogEntry]:
        path = self._log_path(run_id, "nextflow.log")
        try:
            content = self.storage.get_file_content(path, text=True)
        except Exception:
            return []

        lines = content.splitlines()
        if offset < 0:
            offset = 0
        sliced = lines[offset : (offset + limit) if limit else None]
        return [self._parse_line(line, "nextflow") for line in sliced]

    async def stream_workflow_log(
        self,
        run_id: str,
        *,
        poll_interval: float = 2.0,
    ) -> AsyncIterator[LogEntry]:
        path = self._log_path(run_id, "nextflow.log")
        offset = 0
        while True:
            try:
                content = self.storage.get_file_content(path, text=True)
            except Exception:
                await asyncio.sleep(poll_interval)
                continue
            if offset >= len(content):
                await asyncio.sleep(poll_interval)
                continue
            chunk = content[offset:]
            offset = len(content)
            for line in chunk.splitlines():
                yield self._parse_line(line, "nextflow")
            await asyncio.sleep(poll_interval)

    async def list_tasks(self, run_id: str) -> list[TaskInfo]:
        now = datetime.now(timezone.utc)
        cached = _TRACE_CACHE.get(run_id)
        if cached and cached["expires_at"] > now:
            return cached["data"]

        path = self._log_path(run_id, "trace.txt")
        try:
            content = self.storage.get_file_content(path, text=True)
        except Exception:
            return []

        reader = csv.DictReader(io.StringIO(content), delimiter="\t")
        tasks: list[TaskInfo] = []
        for row in reader:
            if not row:
                continue
            tasks.append(
                TaskInfo(
                    task_id=_get_value(row, ["task_id", "id", "hash"]) or "",
                    name=_get_value(row, ["name", "tag"]) or "",
                    process=_get_value(row, ["process"]) or "",
                    status=_get_value(row, ["status"]) or "",
                    exit_code=_to_int(_get_value(row, ["exit", "exit_code"])),
                    duration=_get_value(row, ["duration"]),
                    cpu_percent=_get_value(row, ["cpu", "cpu%", "%cpu"]),
                    memory_peak=_get_value(row, ["memory", "memory%", "mem"]),
                    start_time=_get_value(row, ["start", "start_time"]),
                    end_time=_get_value(row, ["complete", "end", "end_time"]),
                    work_dir=_get_value(row, ["workdir", "work_dir"]),
                    has_logs=bool(_get_value(row, ["task_id", "id", "hash"])),
                )
            )

        _TRACE_CACHE[run_id] = {"data": tasks, "expires_at": now + _TRACE_TTL}
        return tasks

    async def get_task_logs(self, run_id: str, task_id: str) -> TaskLogs:
        client = self._logging_client()
        stdout = self._query_logs(client, run_id, task_id, "stdout")
        stderr = self._query_logs(client, run_id, task_id, "stderr")
        return TaskLogs(task_id=task_id, stdout=stdout, stderr=stderr)

    async def stream_task_logs(
        self,
        run_id: str,
        task_id: str,
        *,
        poll_interval: float = 2.0,
    ) -> AsyncIterator[LogEntry]:
        last_stdout = ""
        last_stderr = ""
        while True:
            logs = await self.get_task_logs(run_id, task_id)
            if logs.stdout and logs.stdout != last_stdout:
                delta = logs.stdout[len(last_stdout) :]
                last_stdout = logs.stdout
                for line in delta.splitlines():
                    yield LogEntry(
                        timestamp=datetime.now(timezone.utc),
                        source="task",
                        message=line,
                        task_name=task_id,
                        stream="stdout",
                    )
            if logs.stderr and logs.stderr != last_stderr:
                delta = logs.stderr[len(last_stderr) :]
                last_stderr = logs.stderr
                for line in delta.splitlines():
                    yield LogEntry(
                        timestamp=datetime.now(timezone.utc),
                        source="task",
                        message=line,
                        task_name=task_id,
                        stream="stderr",
                    )
            await asyncio.sleep(poll_interval)

    async def create_log_archive(self, run_id: str) -> bytes:
        filenames = ["nextflow.log", "trace.txt", "timeline.html", "report.html"]
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as tmp:
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
                for filename in filenames:
                    path = self._log_path(run_id, filename)
                    try:
                        content = self.storage.get_file_content(path, text=False)
                    except Exception:
                        continue
                    zf.writestr(filename, content)
            tmp.seek(0)
            return tmp.read()

    def _logging_client(self):
        try:
            from google.cloud import logging_v2

            return logging_v2.Client(project=self.project_id)
        except Exception as exc:
            raise BatchError("Cloud Logging client unavailable", detail=str(exc)) from exc

    def _query_logs(self, client, run_id: str, task_id: str, stream: str) -> str:
        filter_ = (
            f'labels.run_id="{run_id}" AND '
            f'labels.task_name="{task_id}" AND '
            f'labels.stream="{stream}"'
        )
        try:
            entries = client.list_entries(order_by="timestamp desc", filter_=filter_)
            messages: list[str] = []
            for entry in entries:
                payload = entry.payload
                messages.append(str(payload))
            return "\n".join(reversed(messages))
        except Exception as exc:
            raise BatchError("Cloud Logging query failed", detail=str(exc)) from exc


def _get_value(row: dict[str, str], keys: list[str]) -> str | None:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None

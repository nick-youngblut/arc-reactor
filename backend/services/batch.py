from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Callable

from backend.models.schemas.runs import RunStatus
from backend.utils.errors import BatchError

try:  # optional dependency
    from google.cloud import batch_v1
    from google.api_core import exceptions as gcp_exceptions
except Exception:  # pragma: no cover - handled at runtime
    batch_v1 = None  # type: ignore
    gcp_exceptions = None  # type: ignore


logger = logging.getLogger(__name__)

_LABEL_ALLOWED_RE = re.compile(r"[^a-z0-9_-]")


@dataclass
class BatchQuotaExceededError(BatchError):
    code: str = "BATCH_QUOTA_EXCEEDED"


@dataclass
class BatchJobCreationError(BatchError):
    code: str = "BATCH_JOB_CREATION_FAILED"


@dataclass
class BatchJobNotFoundError(BatchError):
    code: str = "BATCH_JOB_NOT_FOUND"


_STATE_TO_RUN_STATUS: dict[str, RunStatus] = {
    "QUEUED": RunStatus.SUBMITTED,
    "SCHEDULED": RunStatus.SUBMITTED,
    "RUNNING": RunStatus.RUNNING,
    "SUCCEEDED": RunStatus.COMPLETED,
    "FAILED": RunStatus.FAILED,
    "CANCELLED": RunStatus.CANCELLED,
    "DELETION_IN_PROGRESS": RunStatus.CANCELLED,
}


def _sanitize_label_value(value: str, *, max_length: int = 63) -> str:
    normalized = value.lower()
    normalized = _LABEL_ALLOWED_RE.sub("-", normalized)
    normalized = normalized.strip("-_")
    if not normalized:
        normalized = "unknown"
    if not normalized[0].isalpha():
        normalized = f"x{normalized}"
    return normalized[:max_length]


def _is_instance(exc: Exception, candidate: Any) -> bool:
    if candidate is None:
        return False
    try:
        return isinstance(exc, candidate)
    except TypeError:
        return False


@dataclass
class BatchService:
    client: Any
    project: str
    region: str
    orchestrator_image: str
    service_account: str | None
    weblog_receiver_url: str

    @classmethod
    def create(cls, settings: object) -> "BatchService":
        if batch_v1 is None:
            raise BatchError("GCP Batch client unavailable")

        project = getattr(settings, "gcp_project", None)
        region = getattr(settings, "gcp_region", None)
        orchestrator_image = getattr(settings, "orchestrator_image", None)
        service_account = getattr(settings, "nextflow_service_account", None)
        weblog_receiver_url = getattr(settings, "weblog_receiver_url", None)

        missing = [
            name
            for name, value in (
                ("gcp_project", project),
                ("gcp_region", region),
                ("orchestrator_image", orchestrator_image),
                ("weblog_receiver_url", weblog_receiver_url),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Missing Batch settings: {', '.join(missing)}")

        client = batch_v1.BatchServiceClient()
        return cls(
            client=client,
            project=project,
            region=region,
            orchestrator_image=orchestrator_image,
            service_account=service_account,
            weblog_receiver_url=weblog_receiver_url,
        )

    def _parent(self) -> str:
        return f"projects/{self.project}/locations/{self.region}"

    def _build_labels(self, run_id: str, pipeline: str, user_email: str | None) -> dict[str, str]:
        # Batch labels must be lowercase, <=63 chars, start with a letter, and use
        # only [a-z0-9_-]; we sanitize inputs so labels remain queryable in Cloud Logging.
        labels = {
            "run-id": _sanitize_label_value(run_id),
            "app": "arc-reactor",
            "pipeline": _sanitize_label_value(pipeline),
        }
        if user_email:
            labels["user-email"] = _sanitize_label_value(user_email)
        return labels

    def _call_with_retry(
        self,
        operation: Callable[..., Any],
        *args: Any,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        **kwargs: Any,
    ) -> Any:
        last_exc: Exception | None = None
        for attempt in range(max_attempts):
            try:
                return operation(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                if _is_instance(exc, getattr(gcp_exceptions, "ResourceExhausted", None)):
                    raise BatchQuotaExceededError("GCP Batch quota exceeded", detail=str(exc))
                if _is_instance(exc, getattr(gcp_exceptions, "PermissionDenied", None)):
                    logger.error("GCP Batch permission denied: %s", exc)
                    raise BatchJobCreationError("Permission denied for Batch job", detail=str(exc))

                retryable = _is_instance(exc, getattr(gcp_exceptions, "ServiceUnavailable", None))
                retryable = retryable or _is_instance(
                    exc, getattr(gcp_exceptions, "DeadlineExceeded", None)
                )
                retryable = retryable or _is_instance(
                    exc, getattr(gcp_exceptions, "TooManyRequests", None)
                )
                retryable = retryable or _is_instance(
                    exc, getattr(gcp_exceptions, "GoogleAPICallError", None)
                )

                if retryable and attempt < max_attempts - 1:
                    time.sleep(base_delay * (2**attempt))
                    continue

                raise BatchJobCreationError("Batch job creation failed", detail=str(exc))
        if last_exc:
            raise BatchJobCreationError("Batch job creation failed", detail=str(last_exc))
        raise BatchJobCreationError("Batch job creation failed")

    def submit_orchestrator_job(
        self,
        *,
        run_id: str,
        pipeline: str,
        pipeline_version: str,
        config_gcs_path: str,
        params_gcs_path: str,
        work_dir: str,
        is_recovery: bool,
        weblog_secret: str,
        user_email: str | None = None,
    ) -> str:
        if batch_v1 is None:
            raise BatchError("GCP Batch client unavailable")

        env = {
            "RUN_ID": run_id,
            "PIPELINE": pipeline,
            "PIPELINE_VERSION": pipeline_version,
            "CONFIG_GCS_PATH": config_gcs_path,
            "PARAMS_GCS_PATH": params_gcs_path,
            "WORK_DIR": work_dir,
            "IS_RECOVERY": "true" if is_recovery else "false",
            "WEBLOG_URL": self.weblog_receiver_url,
            "WEBLOG_SECRET": weblog_secret,
        }

        runnable = batch_v1.Runnable(
            container=batch_v1.Runnable.Container(
                image_uri=self.orchestrator_image,
            )
        )

        task_spec = batch_v1.TaskSpec(
            runnables=[runnable],
            compute_resource=batch_v1.ComputeResource(cpu_milli=2000, memory_mib=4096),
            max_run_duration="604800s",
            max_retry_count=2,
            environment=batch_v1.Environment(variables=env),
        )

        task_group = batch_v1.TaskGroup(task_spec=task_spec, task_count=1)

        allocation_policy = batch_v1.AllocationPolicy(
            instances=[
                batch_v1.AllocationPolicy.InstancePolicyOrTemplate(
                    policy=batch_v1.AllocationPolicy.InstancePolicy(
                        machine_type="e2-standard-2",
                        provisioning_model=batch_v1.AllocationPolicy.ProvisioningModel.SPOT,
                    )
                )
            ],
        )
        if self.service_account:
            allocation_policy.service_account = batch_v1.ServiceAccount(email=self.service_account)

        job = batch_v1.Job(
            task_groups=[task_group],
            allocation_policy=allocation_policy,
            logs_policy=batch_v1.LogsPolicy(
                destination=batch_v1.LogsPolicy.Destination.CLOUD_LOGGING
            ),
            labels=self._build_labels(run_id, pipeline, user_email),
        )

        request = batch_v1.CreateJobRequest(
            parent=self._parent(),
            job_id=f"nf-{run_id}",
            job=job,
        )
        response = self._call_with_retry(self.client.create_job, request=request)
        return response.name

    def get_job_status(self, job_name: str) -> dict[str, Any]:
        if batch_v1 is None:
            raise BatchError("GCP Batch client unavailable")

        try:
            request = batch_v1.GetJobRequest(name=job_name)
            job = self.client.get_job(request=request)
        except Exception as exc:
            if _is_instance(exc, getattr(gcp_exceptions, "NotFound", None)):
                raise BatchJobNotFoundError("Batch job not found", detail=str(exc))
            raise BatchError("Failed to fetch Batch job status", detail=str(exc))

        state = getattr(getattr(job.status, "state", None), "name", None)
        events = []
        for event in getattr(job.status, "status_events", []) or []:
            events.append(
                {
                    "type": getattr(event, "type_", None),
                    "description": getattr(event, "description", None),
                }
            )

        run_status = _STATE_TO_RUN_STATUS.get(state) if state else None
        return {
            "state": state,
            "status_events": events,
            "run_status": run_status.value if run_status else None,
        }

    def poll_job_until_terminal(
        self,
        job_name: str,
        *,
        poll_interval: float = 10.0,
        timeout_seconds: float = 3600.0,
    ) -> dict[str, Any]:
        terminal_states = {"SUCCEEDED", "FAILED", "CANCELLED"}
        start = time.monotonic()
        while True:
            status = self.get_job_status(job_name)
            if status.get("state") in terminal_states:
                return status
            if time.monotonic() - start > timeout_seconds:
                raise BatchError("Batch job polling timed out", detail=job_name)
            time.sleep(poll_interval)

    def cancel_job(self, job_name: str) -> bool:
        if batch_v1 is None:
            raise BatchError("GCP Batch client unavailable")

        try:
            request = batch_v1.DeleteJobRequest(name=job_name)
            self.client.delete_job(request=request)
            return True
        except Exception as exc:
            if _is_instance(exc, getattr(gcp_exceptions, "NotFound", None)):
                return False
            raise BatchError("Failed to cancel Batch job", detail=str(exc))

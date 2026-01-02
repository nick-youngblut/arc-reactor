from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.services import batch as batch_service
from backend.services.batch import (
    BatchJobCreationError,
    BatchJobNotFoundError,
    BatchQuotaExceededError,
    BatchService,
)


class _Exceptions:
    class ResourceExhausted(Exception):
        pass

    class PermissionDenied(Exception):
        pass

    class NotFound(Exception):
        pass

    class ServiceUnavailable(Exception):
        pass

    class DeadlineExceeded(Exception):
        pass

    class TooManyRequests(Exception):
        pass

    class GoogleAPICallError(Exception):
        pass


class _Runnable:
    class Container:
        def __init__(self, image_uri: str) -> None:
            self.image_uri = image_uri

    def __init__(self, container: "_Runnable.Container") -> None:
        self.container = container


class _ComputeResource:
    def __init__(self, cpu_milli: int, memory_mib: int) -> None:
        self.cpu_milli = cpu_milli
        self.memory_mib = memory_mib


class _Environment:
    def __init__(self, variables: dict[str, str]) -> None:
        self.variables = variables


class _TaskSpec:
    def __init__(
        self,
        *,
        runnables: list[_Runnable],
        compute_resource: _ComputeResource,
        max_run_duration: str,
        max_retry_count: int,
        environment: _Environment,
    ) -> None:
        self.runnables = runnables
        self.compute_resource = compute_resource
        self.max_run_duration = max_run_duration
        self.max_retry_count = max_retry_count
        self.environment = environment


class _TaskGroup:
    def __init__(self, *, task_spec: _TaskSpec, task_count: int) -> None:
        self.task_spec = task_spec
        self.task_count = task_count


class _AllocationPolicy:
    class ProvisioningModel:
        SPOT = "SPOT"

    class InstancePolicy:
        def __init__(self, machine_type: str, provisioning_model: str) -> None:
            self.machine_type = machine_type
            self.provisioning_model = provisioning_model

    class InstancePolicyOrTemplate:
        def __init__(self, policy: "_AllocationPolicy.InstancePolicy") -> None:
            self.policy = policy

    def __init__(self, instances: list["_AllocationPolicy.InstancePolicyOrTemplate"]) -> None:
        self.instances = instances
        self.service_account = None


class _ServiceAccount:
    def __init__(self, email: str) -> None:
        self.email = email


class _LogsPolicy:
    class Destination:
        CLOUD_LOGGING = "CLOUD_LOGGING"

    def __init__(self, destination: str) -> None:
        self.destination = destination


class _Job:
    def __init__(self, *, task_groups, allocation_policy, logs_policy, labels) -> None:
        self.task_groups = task_groups
        self.allocation_policy = allocation_policy
        self.logs_policy = logs_policy
        self.labels = labels
        self.name = ""
        self.status = None


class _JobStatusState:
    def __init__(self, name: str) -> None:
        self.name = name


class _StatusEvent:
    def __init__(self, type_: str, description: str) -> None:
        self.type_ = type_
        self.description = description


class _JobStatus:
    def __init__(self, state: str, events: list[_StatusEvent] | None = None) -> None:
        self.state = _JobStatusState(state)
        self.status_events = events or []


class _Client:
    def __init__(self) -> None:
        self.created_jobs: list[tuple[str, _Job, str]] = []
        self.jobs: dict[str, _Job] = {}
        self.create_side_effects: list[Exception] = []

    def create_job(self, *, request=None, parent: str | None = None, job=None, job_id=None) -> _Job:
        if request is not None:
            parent = request.parent
            job = request.job
            job_id = request.job_id
        if self.create_side_effects:
            raise self.create_side_effects.pop(0)
        job.name = f"{parent}/jobs/{job_id}"
        self.created_jobs.append((parent, job, job_id))
        self.jobs[job.name] = job
        return job

    def get_job(self, *, request=None, name: str | None = None):
        job_name = request.name if request is not None else name
        if job_name not in self.jobs:
            raise _Exceptions.NotFound("missing")
        return self.jobs[job_name]

    def delete_job(self, *, request=None, name: str | None = None):
        job_name = request.name if request is not None else name
        if job_name not in self.jobs:
            raise _Exceptions.NotFound("missing")
        del self.jobs[job_name]
        return True


class _BatchV1:
    BatchServiceClient = _Client
    Runnable = _Runnable
    TaskSpec = _TaskSpec
    ComputeResource = _ComputeResource
    Environment = _Environment
    TaskGroup = _TaskGroup
    AllocationPolicy = _AllocationPolicy
    LogsPolicy = _LogsPolicy
    Job = _Job
    ServiceAccount = _ServiceAccount
    CreateJobRequest = SimpleNamespace
    GetJobRequest = SimpleNamespace
    DeleteJobRequest = SimpleNamespace


def _service(client: _Client) -> BatchService:
    return BatchService(
        client=client,
        project="proj",
        region="us-west1",
        orchestrator_image="gcr.io/proj/orchestrator:latest",
        service_account="svc@proj.iam.gserviceaccount.com",
        database_url="postgresql+asyncpg://user:pass@10.0.0.1:5432/db",
    )


def test_submit_orchestrator_job_builds_job(monkeypatch) -> None:
    monkeypatch.setattr(batch_service, "batch_v1", _BatchV1)
    monkeypatch.setattr(batch_service, "gcp_exceptions", _Exceptions)

    client = _Client()
    service = _service(client)

    job_name = service.submit_orchestrator_job(
        run_id="run-123",
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        config_gcs_path="gs://bucket/runs/run-123/inputs/nextflow.config",
        params_gcs_path="gs://bucket/runs/run-123/inputs/params.yaml",
        work_dir="gs://bucket/runs/run-123/work/",
        is_recovery=False,
        user_email="dev@arc.org",
    )

    assert job_name.endswith("/jobs/nf-run-123")
    assert client.created_jobs

    _, job, job_id = client.created_jobs[0]
    assert job_id == "nf-run-123"
    assert job.labels["app"] == "arc-reactor"
    assert job.labels["pipeline"] == "nf-core-scrnaseq"
    assert job.labels["user-email"].startswith("dev-arc")

    env = job.task_groups[0].task_spec.environment.variables
    assert env["RUN_ID"] == "run-123"
    assert env["PIPELINE"] == "nf-core/scrnaseq"
    assert env["PIPELINE_VERSION"] == "2.7.1"
    assert env["IS_RECOVERY"] == "false"
    assert env["DATABASE_URL"].startswith("postgresql+asyncpg://")


def test_get_job_status_maps_state(monkeypatch) -> None:
    monkeypatch.setattr(batch_service, "batch_v1", _BatchV1)
    monkeypatch.setattr(batch_service, "gcp_exceptions", _Exceptions)

    client = _Client()
    service = _service(client)

    job = _Job(task_groups=[], allocation_policy=None, logs_policy=None, labels={})
    job.status = _JobStatus("RUNNING", [_StatusEvent("INFO", "Started")])
    job_name = "projects/proj/locations/us-west1/jobs/nf-run-123"
    client.jobs[job_name] = job

    status = service.get_job_status(job_name)
    assert status["state"] == "RUNNING"
    assert status["run_status"] == "running"
    assert status["status_events"][0]["description"] == "Started"


def test_cancel_job_handles_missing(monkeypatch) -> None:
    monkeypatch.setattr(batch_service, "batch_v1", _BatchV1)
    monkeypatch.setattr(batch_service, "gcp_exceptions", _Exceptions)

    client = _Client()
    service = _service(client)

    job = _Job(task_groups=[], allocation_policy=None, logs_policy=None, labels={})
    job_name = "projects/proj/locations/us-west1/jobs/nf-run-123"
    client.jobs[job_name] = job

    assert service.cancel_job(job_name) is True
    assert service.cancel_job(job_name) is False


def test_submit_orchestrator_job_error_handling(monkeypatch) -> None:
    monkeypatch.setattr(batch_service, "batch_v1", _BatchV1)
    monkeypatch.setattr(batch_service, "gcp_exceptions", _Exceptions)
    monkeypatch.setattr(batch_service.time, "sleep", lambda *_: None)

    client = _Client()
    service = _service(client)

    client.create_side_effects = [_Exceptions.ServiceUnavailable("try again"), None]
    job_name = service.submit_orchestrator_job(
        run_id="run-456",
        pipeline="nf-core/scrnaseq",
        pipeline_version="2.7.1",
        config_gcs_path="gs://bucket/runs/run-456/inputs/nextflow.config",
        params_gcs_path="gs://bucket/runs/run-456/inputs/params.yaml",
        work_dir="gs://bucket/runs/run-456/work/",
        is_recovery=True,
    )
    assert job_name.endswith("/jobs/nf-run-456")

    client.create_side_effects = [_Exceptions.ResourceExhausted("quota")]
    with pytest.raises(BatchQuotaExceededError):
        service.submit_orchestrator_job(
            run_id="run-789",
            pipeline="nf-core/scrnaseq",
            pipeline_version="2.7.1",
            config_gcs_path="gs://bucket/runs/run-789/inputs/nextflow.config",
            params_gcs_path="gs://bucket/runs/run-789/inputs/params.yaml",
            work_dir="gs://bucket/runs/run-789/work/",
            is_recovery=False,
        )

    client.create_side_effects = [_Exceptions.PermissionDenied("denied")]
    with pytest.raises(BatchJobCreationError):
        service.submit_orchestrator_job(
            run_id="run-790",
            pipeline="nf-core/scrnaseq",
            pipeline_version="2.7.1",
            config_gcs_path="gs://bucket/runs/run-790/inputs/nextflow.config",
            params_gcs_path="gs://bucket/runs/run-790/inputs/params.yaml",
            work_dir="gs://bucket/runs/run-790/work/",
            is_recovery=False,
        )


def test_get_job_status_not_found(monkeypatch) -> None:
    monkeypatch.setattr(batch_service, "batch_v1", _BatchV1)
    monkeypatch.setattr(batch_service, "gcp_exceptions", _Exceptions)

    client = _Client()
    service = _service(client)

    with pytest.raises(BatchJobNotFoundError):
        service.get_job_status("projects/proj/locations/us-west1/jobs/missing")

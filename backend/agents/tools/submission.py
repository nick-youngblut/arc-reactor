from __future__ import annotations

import csv
import io
import json
from typing import Any

from langchain_core.tools import tool

from backend.agents.tools.base import get_tool_context, tool_error_handler
from backend.config import settings
from backend.models.schemas.runs import RunStatus
from backend.services.database import DatabaseService
from backend.services.pipelines import PipelineRegistry
from backend.services.runs import RunStoreService

try:  # optional dependency
    from google.cloud import batch_v1
except Exception:  # pragma: no cover - handled at runtime
    batch_v1 = None  # type: ignore


def _runtime_config(runtime: Any | None) -> dict[str, Any]:
    if runtime is None:
        return {}
    config = getattr(runtime, "config", None)
    return config if isinstance(config, dict) else {}


def _runtime_configurable(runtime: Any | None) -> dict[str, Any]:
    config = _runtime_config(runtime)
    configurable = config.get("configurable")
    return configurable if isinstance(configurable, dict) else {}


def _count_samples(samplesheet_csv: str) -> int:
    reader = csv.reader(io.StringIO(samplesheet_csv))
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        return 0
    return max(len(rows) - 1, 0)


def _extract_params_from_config(config_content: str) -> dict[str, Any]:
    params: dict[str, Any] = {}
    in_params = False
    for raw_line in config_content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//") or line.startswith("#"):
            continue
        if line.startswith("params"):
            if "{" in line:
                in_params = True
            continue
        if in_params and line.startswith("}"):
            in_params = False
            continue
        if not in_params or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().rstrip(",")
        if value.lower() in {"true", "false"}:
            params[key] = value.lower() == "true"
        elif value.startswith(("\"", "'")) and value.endswith(("\"", "'")):
            params[key] = value[1:-1]
        else:
            try:
                params[key] = int(value)
            except ValueError:
                params[key] = value
    return params


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


def _estimate_runtime(sample_count: int) -> str:
    if sample_count <= 8:
        return "2-4 hours"
    if sample_count <= 24:
        return "4-6 hours"
    if sample_count <= 48:
        return "6-10 hours"
    return "10-16 hours"


def _submit_orchestrator_job(
    *,
    run_id: str,
    pipeline: str,
    pipeline_version: str,
    config_uri: str,
    params_uri: str,
    work_dir: str,
) -> str | None:
    if batch_v1 is None:
        return None
    try:
        project = settings.get("gcp_project")
        region = settings.get("gcp_region")
        service_account = settings.get("nextflow_service_account")
        orchestrator_image = settings.get("orchestrator_image")

        env = {
            "RUN_ID": run_id,
            "PIPELINE": pipeline,
            "PIPELINE_VERSION": pipeline_version,
            "CONFIG_GCS_PATH": config_uri,
            "PARAMS_GCS_PATH": params_uri,
            "WORK_DIR": work_dir,
        }

        runnable = batch_v1.Runnable(
            container=batch_v1.Runnable.Container(
                image_uri=orchestrator_image,
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
        if service_account:
            allocation_policy.service_account = batch_v1.ServiceAccount(email=service_account)

        job = batch_v1.Job(
            task_groups=[task_group],
            allocation_policy=allocation_policy,
            logs_policy=batch_v1.LogsPolicy(
                destination=batch_v1.LogsPolicy.Destination.CLOUD_LOGGING
            ),
            labels={"run_id": run_id},
        )

        client = batch_v1.BatchServiceClient()
        parent = f"projects/{project}/locations/{region}"
        response = client.create_job(parent=parent, job=job, job_id=f"nf-{run_id}")
        return response.name
    except Exception:
        return None


async def _get_run_store(runtime: Any | None) -> tuple[RunStoreService, Any]:
    configurable = _runtime_configurable(runtime)
    run_store = configurable.get("run_store_service")
    if run_store is not None and all(
        hasattr(run_store, attr) for attr in ("create_run", "get_run", "update_run_status")
    ):
        return run_store, None

    database_service = configurable.get("database_service")
    if database_service is None:
        database_service = DatabaseService.create(settings)

    session = await anext(database_service.get_session())
    return RunStoreService.create(session, settings), session


async def _close_session(session) -> None:
    if session is None:
        return
    await session.close()


@tool
@tool_error_handler
async def submit_run(
    samplesheet_csv: str,
    config_content: str,
    pipeline: str,
    pipeline_version: str,
    runtime: Any | None = None,
) -> str:
    """Submit a validated pipeline run to GCP Batch."""
    if not samplesheet_csv or not config_content:
        return "Error: samplesheet_csv and config_content are required."

    registry = PipelineRegistry.create()
    pipeline_schema = registry.get_pipeline(pipeline)
    if not pipeline_schema:
        return "Error: Pipeline not found."
    if pipeline_version not in pipeline_schema.versions:
        return "Error: Pipeline version not available."

    sample_count = _count_samples(samplesheet_csv)
    if sample_count <= 0:
        return "Error: samplesheet_csv must include at least one sample."

    params = _extract_params_from_config(config_content)

    context = get_tool_context(runtime)
    storage = context.storage
    if storage is None:
        return "Error: Storage service unavailable."

    run_store, session = await _get_run_store(runtime)
    try:
        run_id = await run_store.create_run(
            pipeline=pipeline,
            pipeline_version=pipeline_version,
            user_email=context.user_email or "unknown",
            user_name=context.user_name,
            params=params,
            sample_count=sample_count,
        )

        params_yaml = _render_params_yaml(params)
        uploaded = storage.upload_run_files(
            run_id,
            {
                "samplesheet.csv": samplesheet_csv,
                "nextflow.config": config_content,
                "params.yaml": params_yaml,
            },
            context.user_email or "unknown",
        )

        config_uri = next((uri for uri in uploaded if uri.endswith("nextflow.config")), "")
        params_uri = next((uri for uri in uploaded if uri.endswith("params.yaml")), "")
        work_dir = f"gs://{storage.bucket_name}/runs/{run_id}/work/"

        batch_job_name = _submit_orchestrator_job(
            run_id=run_id,
            pipeline=pipeline,
            pipeline_version=pipeline_version,
            config_uri=config_uri,
            params_uri=params_uri,
            work_dir=work_dir,
        )

        await run_store.update_run_status(
            run_id=run_id,
            status=RunStatus.SUBMITTED,
            batch_job_name=batch_job_name,
        )

        return json.dumps(
            {
                "run_id": run_id,
                "status": RunStatus.SUBMITTED.value,
                "gcs_path": f"gs://{storage.bucket_name}/runs/{run_id}",
                "estimated_runtime": _estimate_runtime(sample_count),
                "message": "Pipeline run submitted successfully. You can track progress in the Runs tab.",
            },
            indent=2,
        )
    finally:
        await _close_session(session)


@tool
@tool_error_handler
async def cancel_run(run_id: str, runtime: Any | None = None) -> str:
    """Cancel a running pipeline job."""
    if not run_id:
        return "Error: run_id is required."

    run_store, session = await _get_run_store(runtime)
    try:
        run = await run_store.get_run(run_id)
        if not run:
            return "Error: Run not found."

        context = get_tool_context(runtime)
        if context.user_email and run.user_email != context.user_email:
            return "Error: Access denied."

        if run.status in {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}:
            return f"Error: Run is already in terminal state ({run.status.value})."

        if batch_v1 is not None and run.batch_job_name:
            client = batch_v1.BatchServiceClient()
            client.delete_job(name=run.batch_job_name)

        await run_store.update_run_status(run_id=run_id, status=RunStatus.CANCELLED)
        return json.dumps(
            {
                "run_id": run_id,
                "status": RunStatus.CANCELLED.value,
                "message": "Run cancelled successfully.",
            },
            indent=2,
        )
    finally:
        await _close_session(session)


@tool
@tool_error_handler
async def delete_file(run_id: str, file_path: str, runtime: Any | None = None) -> str:
    """Delete a run file from GCS."""
    if not run_id or not file_path:
        return "Error: run_id and file_path are required."

    run_store, session = await _get_run_store(runtime)
    try:
        run = await run_store.get_run(run_id)
        if not run:
            return "Error: Run not found."

        context = get_tool_context(runtime)
        if context.user_email and run.user_email != context.user_email:
            return "Error: Access denied."

        storage = context.storage
        if storage is None:
            return "Error: Storage service unavailable."

        deleted = storage.delete_run_file(run_id, file_path)
        if not deleted:
            return "Error: File not found."

        return json.dumps(
            {"run_id": run_id, "file_path": file_path, "message": "File deleted."},
            indent=2,
        )
    finally:
        await _close_session(session)


@tool
@tool_error_handler
async def clear_samplesheet(confirm: bool, runtime: Any | None = None) -> str:
    """Clear samplesheet from agent state."""
    if not confirm:
        return "Error: confirm must be true to clear samplesheet."

    configurable = _runtime_configurable(runtime)
    generated = configurable.get("generated_files")
    if isinstance(generated, dict):
        generated.pop("samplesheet.csv", None)

    return "Samplesheet cleared from agent state."

from __future__ import annotations

import csv
import io
import json
from typing import Any

from langchain_core.tools import tool

from backend.agents.tools.base import (
    ensure_limit,
    format_table,
    get_tool_context,
    parse_semicolon_delimited,
    tool_error_handler,
)
from backend.config import settings
from backend.services.pipelines import PipelineRegistry


def _store_generated_file(
    runtime: Any | None,
    *,
    filename: str,
    content: str,
    metadata: dict[str, Any],
) -> None:
    if runtime is None:
        return
    config = getattr(runtime, "config", None)
    if not isinstance(config, dict):
        return
    configurable = config.setdefault("configurable", {})
    if not isinstance(configurable, dict):
        return
    generated = configurable.setdefault("generated_files", {})
    if not isinstance(generated, dict):
        generated = {}
        configurable["generated_files"] = generated
    generated[filename] = {"content": content, "metadata": metadata}


def _pipeline_expected_cells_default(registry: PipelineRegistry, pipeline: str) -> int | None:
    schema = registry.get_pipeline(pipeline)
    if not schema:
        return None
    for param in schema.optional_params:
        if param.name == "expected_cells" and isinstance(param.default, int):
            return param.default
    return None


def _format_missing_paths(missing: list[str]) -> str:
    preview = ", ".join(missing[:5])
    suffix = "..." if len(missing) > 5 else ""
    return f"Missing FASTQ files: {preview}{suffix}"


def _extract_params(config_content: str) -> dict[str, Any]:
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
        if not in_params:
            continue
        if "=" not in line:
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


def _estimate_runtime(sample_count: int) -> str:
    if sample_count <= 8:
        return "2-4 hours"
    if sample_count <= 24:
        return "4-6 hours"
    if sample_count <= 48:
        return "6-10 hours"
    return "10-16 hours"


@tool
@tool_error_handler
async def generate_samplesheet(
    ngs_run: str | None = None,
    pooled_sample: str | None = None,
    sample_ids: str | None = None,
    pipeline: str | None = None,
    expected_cells: int | None = None,
    runtime: Any | None = None,
) -> str:
    """Generate a samplesheet CSV for a pipeline."""
    if not pipeline:
        return "Error: pipeline is required."
    if not ngs_run and not pooled_sample:
        return "Error: Provide either ngs_run or pooled_sample."

    registry = PipelineRegistry.create()
    pipeline_schema = registry.get_pipeline(pipeline)
    if not pipeline_schema:
        return "Error: Pipeline not found."

    context = get_tool_context(runtime)
    benchling = context.benchling
    storage = context.storage

    if ngs_run:
        run_filter = 'nr."name$" = :ngs_run'
        params: dict[str, Any] = {"ngs_run": ngs_run}
    else:
        run_filter = 'ps."name$" = :pooled_sample'
        params = {"pooled_sample": pooled_sample}

    sample_list = parse_semicolon_delimited(sample_ids)
    sample_filter = ""
    if sample_list:
        placeholders = ", ".join(f":sample_{i}" for i in range(len(sample_list)))
        params.update({f"sample_{i}": sample for i, sample in enumerate(sample_list)})
        sample_filter = (
            f"AND (lps.sample_id IN ({placeholders}) OR lps.\"name$\" IN ({placeholders}))"
        )

    sql = f"""
    SELECT DISTINCT
        nr."name$" AS ngs_run,
        ps."name$" AS pooled_sample,
        lps.sample_id,
        lps."name$" AS sample_name,
        nros_r1.link_to_fastq_file AS fastq_1,
        nros_r2.link_to_fastq_file AS fastq_2
    FROM ngs_run$raw nr
    INNER JOIN ngs_run_pooling_v2$raw nrp ON nr.id = nrp.ngs_run
    INNER JOIN pooled_sample$raw ps ON nrp.ngs_library_pool = ps.id
    INNER JOIN ngs_library_pooling_v2$raw nlp ON ps.id = nlp.destination
    INNER JOIN library_prep_sample$raw lps ON nlp.source = lps.id
    LEFT JOIN ngs_run_output_sample$raw nros_r1
        ON nr.id = nros_r1.ngs_run
        AND lps.id = nros_r1.ngs_library
        AND nros_r1.read = 'R1'
        AND nros_r1."archived$" = FALSE
    LEFT JOIN ngs_run_output_sample$raw nros_r2
        ON nr.id = nros_r2.ngs_run
        AND lps.id = nros_r2.ngs_library
        AND nros_r2.read = 'R2'
        AND nros_r2."archived$" = FALSE
    WHERE {run_filter}
        AND nr."archived$" = FALSE
        AND lps."archived$" = FALSE
        AND (ps."archived$" = FALSE OR ps."archived$" IS NULL)
        {sample_filter}
    ORDER BY lps.sample_id
    LIMIT :limit
    """

    params["limit"] = ensure_limit(None, default=500)
    rows = await benchling.query(sql, params)
    if not rows:
        return "No samples found for the requested run."

    missing_fastq = [
        row.get("sample_id")
        for row in rows
        if not row.get("fastq_1") or not row.get("fastq_2")
    ]
    if missing_fastq:
        preview = ", ".join(str(sample) for sample in missing_fastq[:5])
        suffix = "..." if len(missing_fastq) > 5 else ""
        return f"Error: Missing FASTQ paths for samples: {preview}{suffix}"

    paths = [row["fastq_1"] for row in rows if row.get("fastq_1")]
    paths += [row["fastq_2"] for row in rows if row.get("fastq_2")]

    if storage is not None:
        existence = storage.files_exist(paths)
        missing = [path for path, ok in existence.items() if not ok]
        if missing:
            return f"Error: {_format_missing_paths(missing)}"

    samplesheet_columns = [column.name for column in pipeline_schema.samplesheet_columns]
    expected_cells_value = expected_cells or _pipeline_expected_cells_default(registry, pipeline)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=samplesheet_columns)
    writer.writeheader()

    for row in rows:
        sample_name = row.get("sample_name") or row.get("sample_id")
        record: dict[str, Any] = {}
        for column in samplesheet_columns:
            if column == "sample":
                record[column] = sample_name
            elif column == "fastq_1":
                record[column] = row.get("fastq_1") or ""
            elif column == "fastq_2":
                record[column] = row.get("fastq_2") or ""
            elif column == "expected_cells":
                record[column] = expected_cells_value or ""
            else:
                record[column] = row.get(column, "")
        writer.writerow(record)

    csv_content = buffer.getvalue().strip()
    _store_generated_file(
        runtime,
        filename="samplesheet.csv",
        content=csv_content,
        metadata={
            "pipeline": pipeline,
            "ngs_run": ngs_run,
            "pooled_sample": pooled_sample,
            "sample_count": len(rows),
        },
    )

    table_preview = format_table(rows[:5])
    preview_note = "\n\nSample preview (first 5 rows):\n" + table_preview if rows else ""
    return (
        f"Generated samplesheet for {pipeline}:\n\n{csv_content}\n\n"
        f"{len(rows)} samples ready. Review in the samplesheet panel and proceed with "
        f"configuration.{preview_note}"
    )


@tool
@tool_error_handler
async def generate_config(
    pipeline: str | None = None,
    params: dict[str, Any] | None = None,
    profile: str | None = None,
    runtime: Any | None = None,
) -> str:
    """Generate a Nextflow config for a pipeline."""
    if not pipeline:
        return "Error: pipeline is required."

    registry = PipelineRegistry.create()
    pipeline_schema = registry.get_pipeline(pipeline)
    if not pipeline_schema:
        return "Error: Pipeline not found."

    params = params or {}
    errors = registry.validate_params(pipeline, params)
    if errors:
        return "Error: " + "; ".join(errors)

    defaults: dict[str, Any] = {}
    for param in pipeline_schema.optional_params:
        if param.default is not None:
            defaults[param.name] = param.default

    rendered_params = {**defaults, **params}
    params_block = registry.render_config(pipeline, rendered_params)

    profile_name = (profile or "gcp_batch").strip()
    gcp_project = settings.get("gcp_project")
    gcp_region = settings.get("gcp_region")
    service_account = settings.get("nextflow_service_account")

    config_content = "\n".join(
        [
            "// Nextflow configuration",
            params_block,
            "",
            f"profiles {{",
            f"  {profile_name} {{",
            "    process {",
            "      executor = \"google-batch\"",
            "      errorStrategy = \"retry\"",
            "      maxRetries = 3",
            "      scratch = true",
            "    }",
            "    google {",
            f"      project = \"{gcp_project}\"",
            f"      location = \"{gcp_region}\"",
            "      batch {",
            f"        serviceAccountEmail = \"{service_account}\"",
            "        spot = true",
            "        maxSpotAttempts = 3",
            "      }",
            "    }",
            "  }",
            "}",
        ]
    )

    _store_generated_file(
        runtime,
        filename="nextflow.config",
        content=config_content,
        metadata={
            "pipeline": pipeline,
            "profile": profile_name,
        },
    )

    return f"Generated config for {pipeline}:\n\n{config_content}"


@tool
@tool_error_handler
async def validate_inputs(
    samplesheet_csv: str,
    config_content: str,
    pipeline: str,
    runtime: Any | None = None,
) -> str:
    """Validate samplesheet and config contents."""
    registry = PipelineRegistry.create()
    pipeline_schema = registry.get_pipeline(pipeline)
    if not pipeline_schema:
        return json.dumps({"valid": False, "errors": [{"type": "PIPELINE_NOT_FOUND"}]}, indent=2)

    errors: list[dict[str, Any]] = []
    warnings: list[str] = []

    reader = csv.DictReader(io.StringIO(samplesheet_csv))
    rows = [row for row in reader if any(value for value in row.values())]
    if not rows:
        errors.append({"type": "EMPTY_SAMPLESHEET", "message": "No samples found."})
        return json.dumps({"valid": False, "errors": errors}, indent=2)

    required_columns = [col.name for col in pipeline_schema.samplesheet_columns if col.required]
    missing_columns = [col for col in required_columns if col not in reader.fieldnames or []]
    if missing_columns:
        errors.append(
            {
                "type": "MISSING_COLUMNS",
                "message": f"Missing required columns: {', '.join(missing_columns)}",
            }
        )
        return json.dumps({"valid": False, "errors": errors}, indent=2)

    fastq_paths: list[str] = []
    for row in rows:
        sample_name = row.get("sample") or row.get("sample_id") or "unknown"
        for column in required_columns:
            if not row.get(column):
                errors.append(
                    {
                        "type": "MISSING_FIELD",
                        "sample": sample_name,
                        "field": column,
                        "message": f"Missing required field {column}",
                    }
                )
        for fastq_field in ("fastq_1", "fastq_2"):
            value = row.get(fastq_field)
            if value:
                if not value.startswith("gs://"):
                    errors.append(
                        {
                            "type": "INVALID_PATH",
                            "sample": sample_name,
                            "field": fastq_field,
                            "message": f"Invalid FASTQ path: {value}",
                        }
                    )
                else:
                    fastq_paths.append(value)

        expected_cells_value = row.get("expected_cells")
        if expected_cells_value:
            try:
                cells = int(expected_cells_value)
                if cells < 5000:
                    warnings.append(
                        f"Sample {sample_name} has expected_cells below 5000 ({cells})."
                    )
            except ValueError:
                errors.append(
                    {
                        "type": "INVALID_FIELD",
                        "sample": sample_name,
                        "field": "expected_cells",
                        "message": f"expected_cells must be an integer: {expected_cells_value}",
                    }
                )

    context = get_tool_context(runtime)
    storage = context.storage
    verified_count = 0
    if storage is not None and fastq_paths:
        existence = storage.files_exist(fastq_paths)
        verified_count = sum(1 for ok in existence.values() if ok)
        for path, ok in existence.items():
            if not ok:
                errors.append(
                    {
                        "type": "MISSING_FILE",
                        "message": f"File not found: {path}",
                    }
                )
    elif fastq_paths:
        warnings.append("File existence not verified (storage unavailable).")

    params = _extract_params(config_content)
    if not params:
        errors.append({"type": "MISSING_PARAMS", "message": "No params block found."})
    else:
        param_errors = registry.validate_params(pipeline, params)
        for error in param_errors:
            error_type = "MISSING_PARAM" if error.startswith("Missing") else "INVALID_PARAM"
            errors.append({"type": error_type, "message": error})

    valid = len(errors) == 0
    response: dict[str, Any] = {"valid": valid}
    if errors:
        response["errors"] = errors
    if warnings:
        response["warnings"] = warnings
    if valid:
        response["summary"] = {
            "sample_count": len(rows),
            "files_verified": verified_count,
            "estimated_runtime": _estimate_runtime(len(rows)),
        }

    return json.dumps(response, indent=2)

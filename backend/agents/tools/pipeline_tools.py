from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from backend.agents.tools.base import format_table, tool_error_handler
from backend.services.pipelines import PipelineRegistry

_PIPELINE_CATEGORIES = {
    "nf-core/scrnaseq": "scRNA-seq",
}


@tool
@tool_error_handler
async def list_pipelines(category: str | None = None, runtime: Any | None = None) -> str:
    """List available pipelines in the registry."""
    registry = PipelineRegistry.create()
    rows = []
    category_filter = (category or "").strip().lower()

    for pipeline in registry.list_pipelines():
        pipeline_category = _PIPELINE_CATEGORIES.get(pipeline.name, "unknown")
        if category_filter and category_filter not in pipeline_category.lower():
            continue
        rows.append(
            {
                "pipeline": pipeline.name,
                "version": pipeline.default_version,
                "description": pipeline.description,
                "category": pipeline_category,
            }
        )

    if not rows:
        suffix = f" for category '{category}'" if category else ""
        return f"No pipelines found{suffix}."

    table = format_table(rows)
    return (
        "Available pipelines:\n\n"
        f"{table}\n\n"
        "Use get_pipeline_schema for detailed parameter information."
    )


def _format_param_line(name: str, description: str, param_type: str, options, default) -> str:
    details = []
    if param_type:
        details.append(param_type)
    if options:
        details.append(f"options: {', '.join(options)}")
    if default is not None:
        details.append(f"default: {default}")
    details_text = f" ({'; '.join(details)})" if details else ""
    return f"  - {name}: {description}{details_text}"


@tool
@tool_error_handler
async def get_pipeline_schema(
    pipeline: str,
    version: str | None = None,
    runtime: Any | None = None,
) -> str:
    """Get schema details for a pipeline."""
    if not pipeline:
        return "Error: pipeline is required."

    registry = PipelineRegistry.create()
    pipeline_schema = registry.get_pipeline(pipeline)
    if not pipeline_schema:
        return "Error: Pipeline not found."

    selected_version = version or pipeline_schema.default_version
    if selected_version not in pipeline_schema.versions:
        return (
            "Error: Unknown pipeline version. "
            f"Available versions: {', '.join(pipeline_schema.versions)}"
        )

    lines = [f"Pipeline: {pipeline_schema.name} (v{selected_version})", ""]
    lines.append("Samplesheet Columns:")
    for column in pipeline_schema.samplesheet_columns:
        required = "required" if column.required else "optional"
        line = f"  - {column.name} ({required}, {column.type}): {column.description}"
        lines.append(line)

    lines.append("")
    lines.append("Required Parameters:")
    if pipeline_schema.required_params:
        for param in pipeline_schema.required_params:
            lines.append(
                _format_param_line(
                    param.name,
                    param.description,
                    param.type,
                    param.options,
                    param.default,
                )
            )
    else:
        lines.append("  - None")

    lines.append("")
    lines.append("Optional Parameters:")
    if pipeline_schema.optional_params:
        for param in pipeline_schema.optional_params:
            lines.append(
                _format_param_line(
                    param.name,
                    param.description,
                    param.type,
                    param.options,
                    param.default,
                )
            )
    else:
        lines.append("  - None")

    return "\n".join(lines)

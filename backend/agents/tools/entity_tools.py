from __future__ import annotations

from typing import Any

import pandas as pd
from langchain_core.tools import tool

from backend.agents.tools.base import format_table, get_tool_context, tool_error_handler




def _rows_from_frame(frame: pd.DataFrame | dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(frame, pd.DataFrame):
        return frame.to_dict(orient="records")
    if isinstance(frame, dict):
        return [frame]
    return []



@tool
@tool_error_handler
async def trace_sample_lineage(
    entity_id: str,
    relationship_field: str,
    max_depth: int | None = 10,
    include_path: bool = True,
    runtime: Any | None = None,
) -> str:
    """Trace parent lineage for an entity through a relationship field."""
    if not entity_id:
        return "Error: entity_id is required."
    if not relationship_field:
        return "Error: relationship_field is required."

    context = get_tool_context(runtime)
    benchling = context.benchling

    result = await benchling.get_ancestors(
        entity_id=entity_id,
        relationship_field=relationship_field,
        max_depth=max_depth or 10,
        include_path=include_path,
        return_format="dataframe",
    )
    rows = _rows_from_frame(result)
    if not rows:
        return f"No ancestors found for {entity_id}."
    return f"Lineage for {entity_id}:\n\n{format_table(rows)}"


@tool
@tool_error_handler
async def find_sample_descendants(
    entity_id: str,
    relationship_field: str | None = None,
    max_depth: int | None = 10,
    include_path: bool = True,
    runtime: Any | None = None,
) -> str:
    """Find descendant entities from a starting entity."""
    if not entity_id:
        return "Error: entity_id is required."

    context = get_tool_context(runtime)
    benchling = context.benchling

    result = await benchling.get_descendants(
        entity_id=entity_id,
        relationship_field=relationship_field or "parent_sample",
        max_depth=max_depth or 10,
        include_path=include_path,
        return_format="dataframe",
    )
    rows = _rows_from_frame(result)
    if not rows:
        return f"No descendants found for {entity_id}."
    return f"Descendants for {entity_id}:\n\n{format_table(rows)}"


@tool
@tool_error_handler
async def get_entity_relationships(
    entity_id: str,
    relationship_field: str | None = None,
    runtime: Any | None = None,
) -> str:
    """Get entity_link relationships for a specific entity."""
    if not entity_id:
        return "Error: entity_id is required."

    context = get_tool_context(runtime)
    benchling = context.benchling

    result = await benchling.get_related_entities(
        entity_id=entity_id,
        relationship_field=relationship_field,
        return_format="dict",
    )
    if not isinstance(result, dict):
        return f"No relationships found for {entity_id}."

    source = result.get("source") or {}
    relationships = result.get("relationships") or {}
    if not relationships:
        return f"No relationships found for {entity_id}."

    source_name = source.get("name") or entity_id
    lines = [f"Relationships for {source_name}:"]
    for field_name, linked in relationships.items():
        if not linked:
            continue
        names = [item.get("name") or item.get("id") for item in linked if isinstance(item, dict)]
        preview = ", ".join(name for name in names if name)
        count = len(names)
        if preview:
            lines.append(f"{field_name} ({count}): {preview}")
        else:
            lines.append(f"{field_name} ({count})")

    return "\n".join(lines)

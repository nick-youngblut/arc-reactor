from __future__ import annotations

import json
from typing import Any, Iterable

from langchain_core.tools import tool

from backend.agents.tools.base import (
    ensure_limit,
    format_table,
    get_tool_context,
    parse_semicolon_delimited,
    tool_error_handler,
)


_ALLOWED_ENTITY_FIELDS: dict[str, str] = {
    "entity_id": "entity.id",
    "entity_name": "entity.name",
    "schema_name": "schema.name",
    "schema_system_name": "schema.system_name",
    "project_name": "project.name",
    "folder_name": "folder.name",
    "entity_type": "entity.type",
    "entity_url": "entity.url",
    "created_at": "entity.created_at",
    "modified_at": "entity.modified_at",
    "creator_name": "creator.name",
}

_CONTENT_COLUMNS = (
    "content",
    "markdown",
    "plain_text",
    "text",
    "rich_text",
    "html",
)


def _normalize_pattern(pattern: str) -> str:
    if not any(ch in pattern for ch in ("%", "_", "*", "?")):
        pattern = f"%{pattern}%"
    return pattern.replace("*", "%").replace("?", "_")


def _build_in_clause(prefix: str, values: Iterable[str]) -> tuple[str, dict[str, Any]]:
    params: dict[str, Any] = {}
    placeholders: list[str] = []
    for index, value in enumerate(values):
        key = f"{prefix}_{index}"
        placeholders.append(f":{key}")
        params[key] = value
    return ", ".join(placeholders), params


def _build_like_clause(
    column: str,
    values: Iterable[str],
    prefix: str,
) -> tuple[str, dict[str, Any]]:
    params: dict[str, Any] = {}
    clauses: list[str] = []
    for index, value in enumerate(values):
        key = f"{prefix}_{index}"
        clauses.append(f"{column} LIKE :{key}")
        params[key] = _normalize_pattern(value)
    if not clauses:
        return "", {}
    return "(" + " OR ".join(clauses) + ")", params


def _ensure_safe_identifier(identifier: str) -> str:
    if not identifier:
        raise ValueError("Identifier must be a non-empty string")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$")
    if not set(identifier) <= allowed:
        raise ValueError(f"Unsafe identifier detected: {identifier}")
    return identifier


def _format_yaml_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if value == "" or any(ch in value for ch in [":", "-", "#", "\n", "\r", "\t"]):
            return json.dumps(value)
        return value
    return json.dumps(value)


def _to_yaml(value: Any, indent: int = 0) -> list[str]:
    spacer = "  " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, val in value.items():
            if isinstance(val, (dict, list)):
                lines.append(f"{spacer}{key}:")
                lines.extend(_to_yaml(val, indent + 1))
            else:
                lines.append(f"{spacer}{key}: {_format_yaml_value(val)}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{spacer}-")
                lines.extend(_to_yaml(item, indent + 1))
            else:
                lines.append(f"{spacer}- {_format_yaml_value(item)}")
        return lines
    return [f"{spacer}{_format_yaml_value(value)}"]


async def _get_table_columns(benchling, table_name: str) -> set[str]:
    sql = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = :table_name
    """
    rows = await benchling.query(sql, {"table_name": table_name})
    return {row["column_name"] for row in rows if row.get("column_name")}


def _format_relationships_tree(
    root_entity: dict[str, Any],
    relationships: list[dict[str, Any]],
) -> str:
    header = f"{root_entity['entity_name']} ({root_entity['schema_name']})"
    if not relationships:
        return "\n".join([header, "└── (no relationships found)"])

    by_depth: dict[int, list[dict[str, Any]]] = {}
    for rel in relationships:
        depth = rel.get("depth", 1)
        by_depth.setdefault(depth, []).append(rel)

    lines = [header]
    for depth in sorted(by_depth.keys()):
        level_rels = sorted(
            by_depth[depth],
            key=lambda rel: (
                rel.get("source_entity_name") or "",
                rel.get("link_direction") or "",
                rel.get("link_field") or "",
                rel.get("linked_entity_name") or rel.get("linked_entity_id") or "",
            ),
        )
        for index, rel in enumerate(level_rels):
            branch = "└──" if index == len(level_rels) - 1 else "├──"
            direction = "→" if rel.get("link_direction") == "forward" else "←"
            indent = "    " * max(depth - 1, 0)
            linked_name = rel.get("linked_entity_name") or rel.get("linked_entity_id")
            linked_schema = rel.get("linked_schema_name") or "Unknown schema"
            field_name = rel.get("link_field") or "(unknown field)"
            lines.append(
                f"{indent}{branch} {direction} {field_name}: {linked_name} ({linked_schema})"
            )
    return "\n".join(lines)


async def _resolve_entities(
    benchling,
    entity_name: str,
    schema_name: str | None = None,
) -> list[dict[str, Any]]:
    if not entity_name or not entity_name.strip():
        raise ValueError("entity_name must be a non-empty string")

    sql = """
        SELECT
            e.id AS entity_id,
            e.name AS entity_name,
            e.schema_id AS schema_id,
            s.name AS schema_name,
            s.system_name AS schema_system_name
        FROM entity$raw e
        INNER JOIN schema$raw s ON e.schema_id = s.id
        WHERE e."archived$" = false
          AND s."archived$" = false
          AND e.name = :entity_name
    """
    params: dict[str, Any] = {"entity_name": entity_name.strip()}
    if schema_name:
        sql += " AND s.name = :schema_name"
        params["schema_name"] = schema_name
    sql += " ORDER BY s.name, e.name"

    return await benchling.query(sql, params)


async def _get_entity_link_fields(
    benchling,
    schema_id: str,
    field_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    sql = """
        SELECT
            sf.display_name AS field_display_name,
            sf.system_name AS field_system_name,
            sf.is_multi AS is_multi,
            sf.target_schema_id AS target_schema_id,
            target.name AS target_schema_name,
            target.system_name AS target_schema_system_name
        FROM schema_field$raw sf
        LEFT JOIN schema$raw target ON sf.target_schema_id = target.id
        WHERE sf.schema_id = :schema_id
          AND sf."archived$" = false
          AND sf.type IN ('entity_link', 'custom_entity_link')
    """
    params: dict[str, Any] = {"schema_id": schema_id}
    if field_filter:
        clause, clause_params = _build_in_clause("field_filter", field_filter)
        sql += f" AND sf.display_name IN ({clause})"
        params.update(clause_params)
    sql += " ORDER BY sf.display_name"

    return await benchling.query(sql, params)


async def _fetch_entity_info_map(
    benchling,
    entity_ids: Iterable[str],
) -> dict[str, dict[str, Any]]:
    ids = list({entity_id for entity_id in entity_ids if entity_id})
    if not ids:
        return {}
    clause, params = _build_in_clause("entity_id", ids)
    sql = f"""
        SELECT
            e.id AS entity_id,
            e.name AS entity_name,
            e.schema_id AS schema_id,
            s.name AS schema_name,
            s.system_name AS schema_system_name
        FROM entity$raw e
        INNER JOIN schema$raw s ON e.schema_id = s.id
        WHERE e."archived$" = false
          AND s."archived$" = false
          AND e.id IN ({clause})
    """
    rows = await benchling.query(sql, params)
    return {row["entity_id"]: row for row in rows if row.get("entity_id")}


async def _get_forward_links(
    benchling,
    source_entity: dict[str, Any],
    link_fields: list[dict[str, Any]],
    field_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    if not link_fields:
        return []

    filtered = link_fields
    if field_filter:
        filtered = [row for row in link_fields if row.get("field_display_name") in field_filter]
        if not filtered:
            return []

    table_name = _ensure_safe_identifier(f"{source_entity['schema_system_name']}$raw")
    entity_id = source_entity["entity_id"]

    raw_links: list[tuple[str, str, str, str]] = []
    for field in filtered:
        display_name = field["field_display_name"]
        system_name = _ensure_safe_identifier(field["field_system_name"])
        is_multi = bool(field.get("is_multi"))

        if is_multi:
            sql = f"""
                SELECT
                    :link_field AS link_field,
                    elements.linked_entity_id
                FROM {table_name}
                CROSS JOIN LATERAL jsonb_array_elements_text(
                    to_jsonb("{system_name}")
                ) AS elements(linked_entity_id)
                WHERE id = :entity_id
                  AND "{system_name}" IS NOT NULL
            """
        else:
            sql = f"""
                SELECT
                    :link_field AS link_field,
                    "{system_name}" AS linked_entity_id
                FROM {table_name}
                WHERE id = :entity_id
                  AND "{system_name}" IS NOT NULL
            """

        results = await benchling.query(sql, {"entity_id": entity_id, "link_field": display_name})
        for row in results:
            linked_id = row.get("linked_entity_id")
            if linked_id:
                raw_links.append((display_name, system_name, str(linked_id), "forward"))

    if not raw_links:
        return []

    linked_info = await _fetch_entity_info_map(benchling, [link[2] for link in raw_links])

    relationships: list[dict[str, Any]] = []
    for display_name, system_name, linked_id, direction in raw_links:
        info = linked_info.get(linked_id)
        relationships.append(
            {
                "source_entity_id": source_entity["entity_id"],
                "source_entity_name": source_entity["entity_name"],
                "source_schema_name": source_entity["schema_name"],
                "source_schema_system_name": source_entity["schema_system_name"],
                "linked_entity_id": linked_id,
                "linked_entity_name": info.get("entity_name") if info else None,
                "linked_schema_id": info.get("schema_id") if info else None,
                "linked_schema_name": info.get("schema_name") if info else None,
                "linked_schema_system_name": info.get("schema_system_name") if info else None,
                "link_field": display_name,
                "link_field_system_name": system_name,
                "link_direction": direction,
            }
        )

    return relationships


async def _get_reverse_links(
    benchling,
    target_entity: dict[str, Any],
    field_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    sql = """
        SELECT
            sf.schema_id AS source_schema_id,
            source.name AS source_schema_name,
            source.system_name AS source_schema_system_name,
            sf.display_name AS field_display_name,
            sf.system_name AS field_system_name,
            sf.is_multi AS is_multi
        FROM schema_field$raw sf
        INNER JOIN schema$raw source ON sf.schema_id = source.id
        WHERE sf.target_schema_id = :target_schema_id
          AND sf."archived$" = false
          AND source."archived$" = false
          AND sf.type IN ('entity_link', 'custom_entity_link')
    """
    params: dict[str, Any] = {"target_schema_id": target_entity["schema_id"]}
    if field_filter:
        clause, clause_params = _build_in_clause("reverse_field", field_filter)
        sql += f" AND sf.display_name IN ({clause})"
        params.update(clause_params)
    sql += " ORDER BY source.name, sf.display_name"

    referring_fields = await benchling.query(sql, params)
    if not referring_fields:
        return []

    raw_links: list[tuple[str, str, str, str]] = []
    for field in referring_fields:
        schema_system_name = _ensure_safe_identifier(field["source_schema_system_name"])
        table_name = f"{schema_system_name}$raw"
        column_name = _ensure_safe_identifier(field["field_system_name"])
        is_multi = bool(field.get("is_multi"))

        if is_multi:
            field_sql = f"""
                SELECT parent.id AS linked_entity_id
                FROM {table_name} AS parent
                CROSS JOIN LATERAL jsonb_array_elements_text(
                    to_jsonb(parent."{column_name}")
                ) AS elements(linked_entity_id)
                WHERE parent."archived$" = false
                  AND parent."{column_name}" IS NOT NULL
                  AND elements.linked_entity_id = :entity_id
            """
        else:
            field_sql = f"""
                SELECT id AS linked_entity_id
                FROM {table_name}
                WHERE "{column_name}" = :entity_id
                  AND "archived$" = false
            """

        results = await benchling.query(field_sql, {"entity_id": target_entity["entity_id"]})
        for row in results:
            linked_id = row.get("linked_entity_id")
            if linked_id:
                raw_links.append(
                    (
                        field["field_display_name"],
                        field["field_system_name"],
                        str(linked_id),
                        schema_system_name,
                    )
                )

    if not raw_links:
        return []

    linked_info = await _fetch_entity_info_map(benchling, [link[2] for link in raw_links])

    relationships: list[dict[str, Any]] = []
    for display_name, system_name, linked_id, schema_system_name in raw_links:
        info = linked_info.get(linked_id)
        relationships.append(
            {
                "source_entity_id": target_entity["entity_id"],
                "source_entity_name": target_entity["entity_name"],
                "source_schema_name": target_entity["schema_name"],
                "source_schema_system_name": target_entity["schema_system_name"],
                "linked_entity_id": linked_id,
                "linked_entity_name": info.get("entity_name") if info else None,
                "linked_schema_id": info.get("schema_id") if info else None,
                "linked_schema_name": info.get("schema_name") if info else None,
                "linked_schema_system_name": info.get("schema_system_name")
                if info
                else schema_system_name,
                "link_field": display_name,
                "link_field_system_name": system_name,
                "link_direction": "reverse",
            }
        )

    return relationships


async def _traverse_relationships(
    benchling,
    source_entity: dict[str, Any],
    relationship_types: list[str] | None,
    depth: int,
    include_reverse: bool,
    max_results: int,
    visited: set[str] | None,
    current_depth: int,
) -> tuple[list[dict[str, Any]], bool]:
    visited_entities = visited or set()
    entity_id = source_entity["entity_id"]
    if entity_id in visited_entities:
        return [], False

    visited_entities.add(entity_id)
    if depth <= 0 or max_results <= 0:
        return [], False

    results: list[dict[str, Any]] = []
    limit_reached = False

    link_fields = await _get_entity_link_fields(
        benchling,
        schema_id=source_entity["schema_id"],
        field_filter=relationship_types,
    )

    forward_links = await _get_forward_links(
        benchling,
        source_entity=source_entity,
        link_fields=link_fields,
        field_filter=relationship_types,
    )

    for link in forward_links:
        link["depth"] = current_depth
        results.append(link)
        if len(results) >= max_results:
            limit_reached = True
            break

    reverse_links: list[dict[str, Any]] = []
    if include_reverse and not limit_reached:
        reverse_links = await _get_reverse_links(
            benchling,
            target_entity=source_entity,
            field_filter=relationship_types,
        )
        for link in reverse_links:
            link["depth"] = current_depth
            results.append(link)
            if len(results) >= max_results:
                limit_reached = True
                break

    if limit_reached or depth <= 1:
        return results, limit_reached

    all_links = forward_links + (reverse_links if include_reverse else [])
    if not all_links:
        return results, False

    remaining_budget = max_results - len(results)
    if remaining_budget <= 0:
        return results, True

    next_entity_ids = {
        link["linked_entity_id"]
        for link in all_links
        if link.get("linked_entity_id")
    }
    next_entity_ids -= visited_entities

    if not next_entity_ids:
        return results, limit_reached

    next_entities = await _fetch_entity_info_map(benchling, next_entity_ids)

    for linked_id in next_entity_ids:
        if limit_reached:
            break

        child_info = next_entities.get(linked_id)
        if not child_info:
            continue

        remaining_budget = max_results - len(results)
        if remaining_budget <= 0:
            limit_reached = True
            break

        child_links, child_limit = await _traverse_relationships(
            benchling,
            source_entity=child_info,
            relationship_types=relationship_types,
            depth=depth - 1,
            include_reverse=False,
            max_results=remaining_budget,
            visited=visited_entities,
            current_depth=current_depth + 1,
        )
        results.extend(child_links)
        if child_limit or len(results) >= max_results:
            limit_reached = True
            break

    return results, limit_reached


@tool
@tool_error_handler
async def get_entities(
    entity_names: str | None = None,
    entity_ids: str | None = None,
    schema_name: str | None = None,
    project_name: str | None = None,
    folder_name: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    creator_name: str | None = None,
    archived: bool | None = False,
    fields: str | None = None,
    allow_wildcards: bool = False,
    limit: int | None = None,
    runtime: Any | None = None,
) -> str:
    """Get registry entities from the Benchling data warehouse.

    Args:
        entity_names: Entity names (semicolon-delimited).
        entity_ids: Entity IDs (semicolon-delimited).
        schema_name: Filter by schema display name.
        project_name: Filter by project name.
        folder_name: Filter by folder name.
        created_after: Minimum creation date (YYYY-MM-DD).
        created_before: Maximum creation date (YYYY-MM-DD).
        creator_name: Filter by creator name.
        archived: Include archived entities when True.
        fields: Fields to include (semicolon-delimited). Supported: entity_id, entity_name,
            schema_name, schema_system_name, project_name, folder_name, entity_type, entity_url,
            created_at, modified_at, creator_name.
        allow_wildcards: Enable SQL-style wildcards for name filters (% and _; * and ? supported).
        limit: Max results to return (default 40, max 500).
        runtime: LangChain tool runtime for injected services/config.
    """
    context = get_tool_context(runtime)
    benchling = context.benchling

    selected_fields = parse_semicolon_delimited(fields)
    if selected_fields:
        unknown_fields = [field for field in selected_fields if field not in _ALLOWED_ENTITY_FIELDS]
        if unknown_fields:
            return f"Error: Unsupported fields requested: {', '.join(unknown_fields)}"
        select_columns = [f"{_ALLOWED_ENTITY_FIELDS[field]} AS {field}" for field in selected_fields]
    else:
        select_columns = [
            "entity.id AS entity_id",
            "entity.name AS entity_name",
            "schema.name AS schema_name",
            "project.name AS project_name",
            "folder.name AS folder_name",
            "entity.url AS entity_url",
        ]

    needs_creator = "creator_name" in selected_fields or creator_name is not None

    query = """
        SELECT {columns}
        FROM entity$raw entity
        LEFT JOIN schema$raw schema ON entity.schema_id = schema.id
        LEFT JOIN project$raw project ON entity.source_id = project.id
        LEFT JOIN folder$raw folder ON entity.folder_id = folder.id
    """.format(columns=", ".join(select_columns))

    if needs_creator:
        columns = await _get_table_columns(benchling, "entity$raw")
        creator_column = None
        if "creator_id" in columns:
            creator_column = "creator_id"
        elif "created_by" in columns:
            creator_column = "created_by"

        if not creator_column:
            return "Error: creator_name filtering is not supported by this warehouse schema."

        query += f"\nLEFT JOIN user$raw creator ON entity.{creator_column} = creator.id"

    conditions: list[str] = []
    params: dict[str, Any] = {}

    if entity_names:
        names = parse_semicolon_delimited(entity_names)
        if allow_wildcards:
            clause, clause_params = _build_like_clause("entity.name", names, "entity_name_like")
            if clause:
                conditions.append(clause)
                params.update(clause_params)
        else:
            clause, clause_params = _build_in_clause("entity_name", names)
            conditions.append(f"entity.name IN ({clause})")
            params.update(clause_params)

    if entity_ids:
        ids = parse_semicolon_delimited(entity_ids)
        clause, clause_params = _build_in_clause("entity_id", ids)
        conditions.append(f"entity.id IN ({clause})")
        params.update(clause_params)

    if schema_name:
        if allow_wildcards:
            clause, clause_params = _build_like_clause("schema.name", [schema_name], "schema_name_like")
            conditions.append(clause)
            params.update(clause_params)
        else:
            conditions.append("schema.name = :schema_name")
            params["schema_name"] = schema_name

    if project_name:
        if allow_wildcards:
            clause, clause_params = _build_like_clause("project.name", [project_name], "project_name_like")
            conditions.append(clause)
            params.update(clause_params)
        else:
            conditions.append("project.name = :project_name")
            params["project_name"] = project_name

    if folder_name:
        if allow_wildcards:
            clause, clause_params = _build_like_clause("folder.name", [folder_name], "folder_name_like")
            conditions.append(clause)
            params.update(clause_params)
        else:
            conditions.append("folder.name = :folder_name")
            params["folder_name"] = folder_name

    if creator_name:
        if allow_wildcards:
            clause, clause_params = _build_like_clause(
                "creator.name", [creator_name], "creator_name_like"
            )
            conditions.append(clause)
            params.update(clause_params)
        else:
            conditions.append("creator.name = :creator_name")
            params["creator_name"] = creator_name

    if created_after:
        conditions.append("entity.created_at >= :created_after")
        params["created_after"] = created_after
    if created_before:
        conditions.append("entity.created_at <= :created_before")
        params["created_before"] = created_before

    if archived is not None:
        conditions.append("entity.\"archived$\" = :archived")
        params["archived"] = bool(archived)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY entity.modified_at DESC"
    query += " LIMIT :limit"
    params["limit"] = ensure_limit(limit, default=40)

    rows = await benchling.query(query, params)
    if not rows:
        return "No entities found."

    return format_table(rows)


@tool
@tool_error_handler
async def get_entity_relationships(
    entity_name: str,
    schema_name: str | None = None,
    relationship_depth: int | None = 4,
    relationship_types: str | None = None,
    include_reverse_links: bool = True,
    output_format: str = "tree",
    runtime: Any | None = None,
) -> str:
    """Traverse entity relationships to understand sample lineage.

    Args:
        entity_name: Starting entity name to resolve.
        schema_name: Optional schema name hint for disambiguation/performance.
        relationship_depth: Traversal depth (default 4, max 10).
        relationship_types: Specific relationship field names to follow (semicolon-delimited).
        include_reverse_links: Include back-references when True.
        output_format: Output format ("tree", "yaml", or "json").
        runtime: LangChain tool runtime for injected services/config.
    """
    if not entity_name:
        return "Error: entity_name is required."

    normalized_format = (output_format or "tree").lower().strip()
    if normalized_format not in {"tree", "yaml", "json"}:
        return "Error: output_format must be one of: tree, yaml, json."

    if not isinstance(relationship_depth, int) or not (1 <= relationship_depth <= 10):
        return "Error: relationship_depth must be an integer between 1 and 10."

    context = get_tool_context(runtime)
    benchling = context.benchling

    parsed_relationship_types = parse_semicolon_delimited(relationship_types)
    if not parsed_relationship_types:
        parsed_relationship_types = None

    entities = await _resolve_entities(benchling, entity_name=entity_name, schema_name=schema_name)
    if not entities:
        schema_hint = f" within schema '{schema_name}'" if schema_name else ""
        return f"No entities found matching '{entity_name}'{schema_hint}."

    max_results = 500
    results: list[tuple[dict[str, Any], list[dict[str, Any]], bool]] = []
    for entity in entities:
        relationships, limit_reached = await _traverse_relationships(
            benchling,
            source_entity=entity,
            relationship_types=parsed_relationship_types,
            depth=relationship_depth,
            include_reverse=include_reverse_links,
            max_results=max_results,
            visited=set(),
            current_depth=1,
        )
        results.append((entity, relationships, limit_reached))

    if normalized_format == "json":
        payload: list[dict[str, Any]] = []
        for entity, relationships, limit_reached in results:
            payload.append(
                {
                    "entity": {
                        "id": entity["entity_id"],
                        "name": entity["entity_name"],
                        "schema": entity["schema_name"],
                    },
                    "relationships": relationships,
                    "limit_reached": limit_reached,
                }
            )
        if len(payload) == 1:
            return json.dumps(payload[0], indent=2)
        return json.dumps(payload, indent=2)

    if normalized_format == "yaml":
        sections: list[str] = []
        for entity, relationships, limit_reached in results:
            payload = {
                "entity": {
                    "id": entity["entity_id"],
                    "name": entity["entity_name"],
                    "schema": entity["schema_name"],
                },
                "relationships": relationships,
                "limit_reached": limit_reached,
            }
            sections.extend(_to_yaml(payload))
            sections.append("")
        return "\n".join(sections).rstrip()

    parts: list[str] = []
    for index, (entity, relationships, limit_reached) in enumerate(results):
        if index > 0:
            parts.append("")
        parts.append(_format_relationships_tree(entity, relationships))
        if limit_reached:
            parts.append(
                f"[warning] max_results limit ({max_results}) reached; traversal stopped early."
            )
    return "\n".join(parts)


@tool
@tool_error_handler
async def list_entries(
    entry_names: str | None = None,
    project_names: str | None = None,
    folder_names: str | None = None,
    creator_names: str | None = None,
    min_date: str | None = None,
    max_date: str | None = None,
    allow_wildcards: bool = False,
    archived: bool | None = False,
    limit: int | None = None,
    runtime: Any | None = None,
) -> str:
    """List Benchling notebook entries with optional filtering.

    Args:
        entry_names: Entry names (semicolon-delimited).
        project_names: Project names (semicolon-delimited).
        folder_names: Folder names (semicolon-delimited).
        creator_names: Creator names (semicolon-delimited).
        min_date: Minimum modified date (YYYY-MM-DD).
        max_date: Maximum modified date (YYYY-MM-DD).
        allow_wildcards: Enable SQL-style wildcards for name filters.
        archived: Include archived entries when True.
        limit: Max results to return (default 50, max 500).
        runtime: LangChain tool runtime for injected services/config.
    """
    context = get_tool_context(runtime)
    benchling = context.benchling

    query = """
        SELECT
            entry.name AS entry_name,
            entry.display_id AS display_id,
            entry.url AS url,
            entry.created_at AS created_at,
            entry.modified_at AS modified_at,
            folder.name AS folder_name,
            project.name AS project_name,
            creator.name AS creator_name
        FROM entry$raw entry
        LEFT JOIN project$raw project ON entry.source_id = project.id
        LEFT JOIN folder$raw folder ON entry.folder_id = folder.id
        LEFT JOIN user$raw creator ON entry.creator_id = creator.id
    """

    conditions: list[str] = []
    params: dict[str, Any] = {}

    def add_name_filter(column: str, values: list[str], prefix: str) -> None:
        if allow_wildcards:
            clause, clause_params = _build_like_clause(column, values, prefix)
            if clause:
                conditions.append(clause)
                params.update(clause_params)
        else:
            clause, clause_params = _build_in_clause(prefix, values)
            conditions.append(f"{column} IN ({clause})")
            params.update(clause_params)

    if entry_names:
        add_name_filter("entry.name", parse_semicolon_delimited(entry_names), "entry_name")
    if project_names:
        add_name_filter("project.name", parse_semicolon_delimited(project_names), "project_name")
    if folder_names:
        add_name_filter("folder.name", parse_semicolon_delimited(folder_names), "folder_name")
    if creator_names:
        add_name_filter("creator.name", parse_semicolon_delimited(creator_names), "creator_name")

    if min_date:
        conditions.append("entry.modified_at >= :min_date")
        params["min_date"] = min_date
    if max_date:
        conditions.append("entry.modified_at <= :max_date")
        params["max_date"] = max_date

    if archived is not None:
        conditions.append("entry.\"archived$\" = :archived")
        params["archived"] = bool(archived)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY entry.modified_at DESC"
    query += " LIMIT :limit"
    params["limit"] = ensure_limit(limit, default=50)

    rows = await benchling.query(query, params)
    if not rows:
        return "No entries found."
    return format_table(rows)


@tool
@tool_error_handler
async def get_entry_content(
    entry_names: str,
    head: int | None = None,
    tail: int | None = None,
    runtime: Any | None = None,
) -> str:
    """Fetch entry content from the Benchling warehouse.

    Args:
        entry_names: Entry names (semicolon-delimited).
        head: Number of lines from the beginning to include.
        tail: Number of lines from the end to include.
        runtime: LangChain tool runtime for injected services/config.
    """
    entries = parse_semicolon_delimited(entry_names)
    if not entries:
        return "Error: entry_names must be provided."

    context = get_tool_context(runtime)
    benchling = context.benchling

    columns = await _get_table_columns(benchling, "entry$raw")
    content_column = next((col for col in _CONTENT_COLUMNS if col in columns), None)
    if not content_column:
        return "Error: Entry content column not found in entry$raw." \
            f" Available columns: {', '.join(sorted(columns))}"

    clause, params = _build_in_clause("entry_name", entries)
    sql = f"""
        SELECT entry.name AS entry_name, entry."{content_column}" AS content
        FROM entry$raw entry
        WHERE entry.name IN ({clause})
    """
    rows = await benchling.query(sql, params)
    if not rows:
        return "No entry content found."

    parts: list[str] = []
    for row in rows:
        name = row.get("entry_name") or "(unknown entry)"
        content = row.get("content") or ""
        lines = str(content).splitlines()
        total = len(lines)

        selected = lines
        summary = ""
        if head and tail:
            selected = lines[:head] + ["..."] + lines[-tail:]
            summary = f"Showing first {head} and last {tail} of {total} lines"
        elif head:
            selected = lines[:head]
            summary = f"Showing first {min(head, total)} of {total} lines"
        elif tail:
            selected = lines[-tail:]
            summary = f"Showing last {min(tail, total)} of {total} lines"
        else:
            summary = f"{total} total lines"

        parts.append(f"Entry: {name}\n{summary}\n" + "\n".join(selected))

    return "\n\n".join(parts)


@tool
@tool_error_handler
async def get_entry_entities(
    entry_name: str,
    limit: int | None = None,
    runtime: Any | None = None,
) -> str:
    """Get entities linked to a Benchling notebook entry.

    Args:
        entry_name: Entry name to resolve.
        limit: Max entities to return (default 40, max 500).
        runtime: LangChain tool runtime for injected services/config.
    """
    if not entry_name:
        return "Error: entry_name is required."

    context = get_tool_context(runtime)
    benchling = context.benchling

    sql = """
        SELECT
            entity.id AS entity_id,
            entity.name AS entity_name,
            schema.name AS entity_schema,
            entity.type AS entity_type,
            entity.url AS entity_url
        FROM entity$raw entity
        JOIN schema$raw schema ON entity.schema_id = schema.id
        JOIN registration_origin$raw ro ON entity.id = ro.entity_id
        JOIN entry$raw entry ON ro.origin_entry_id = entry.id
        WHERE entity."archived$" = false
          AND entry.name = :entry_name
        LIMIT :limit
    """
    params = {"entry_name": entry_name, "limit": ensure_limit(limit, default=40)}
    rows = await benchling.query(sql, params)
    if not rows:
        return "No entities found for the requested entry."
    return format_table(rows)

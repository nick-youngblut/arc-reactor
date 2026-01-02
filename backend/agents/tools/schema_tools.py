from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from backend.agents.tools.base import ensure_limit, format_table, get_tool_context, tool_error_handler


_READ_ONLY_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "MERGE",
    "CREATE",
}


def _contains_disallowed_keywords(sql: str) -> bool:
    normalized = sql.upper()
    return any(
        f" {keyword}" in normalized or normalized.startswith(keyword) for keyword in _READ_ONLY_KEYWORDS
    )


def _apply_limit(sql: str, limit: int | None) -> str:
    if limit is None or limit <= 0:
        return sql
    sql_no_semicolon = sql.rstrip().rstrip(";")
    if "LIMIT" in sql_no_semicolon.upper():
        return sql_no_semicolon
    return f"{sql_no_semicolon} LIMIT {limit}"


@tool
@tool_error_handler
async def get_schemas(
    schema_names: str | None = None,
    get_all_schemas: bool = False,
    runtime: Any | None = None,
) -> str:
    """Get general information about one or more Benchling schemas.

    Args:
        schema_names: Specific schema names (semicolon-delimited).
        get_all_schemas: When True, return all schema names.
        runtime: LangChain tool runtime for injected services/config.
    """
    context = get_tool_context(runtime)
    benchling = context.benchling

    if get_all_schemas or not schema_names:
        sql = """
            SELECT schema.name AS schema_name
            FROM schema$raw schema
            WHERE schema."archived$" = false
            ORDER BY schema.name
        """
        rows = await benchling.query(sql, {}, return_format="dict")
        if not rows:
            return "No schemas found."
        names = ", ".join(row["schema_name"] for row in rows if row.get("schema_name"))
        return f"All schemas: {names}"

    names = [name.strip() for name in schema_names.split(";") if name.strip()]
    if not names:
        return "Error: schema_names must be provided."

    placeholders = ", ".join(f":name_{i}" for i in range(len(names)))
    params = {f"name_{i}": name for i, name in enumerate(names)}

    sql = f"""
        SELECT
            schema.id AS schema_id,
            schema.name AS schema_name,
            schema.system_name AS system_name,
            schema.schema_type AS schema_type
        FROM schema$raw schema
        WHERE schema."archived$" = false
          AND schema.name IN ({placeholders})
        ORDER BY schema.name
    """

    rows = await benchling.query(sql, params, return_format="dict")
    if not rows:
        return "No schemas found for the requested names."
    return format_table(rows)


@tool
@tool_error_handler
async def get_schema_field_info(
    schema_name: str,
    runtime: Any | None = None,
) -> str:
    """Get field metadata for a specific schema.

    Args:
        schema_name: Schema display name to inspect.
        runtime: LangChain tool runtime for injected services/config.
    """
    if not schema_name:
        return "Error: schema_name is required."

    context = get_tool_context(runtime)
    benchling = context.benchling

    sql = """
        SELECT
            s.name AS schema_name,
            sf.display_name AS field_name,
            sf.type AS field_type,
            s2.name AS field_linked_schema,
            d.name AS field_linked_dropdown,
            sf.is_multi AS field_is_multi,
            sf.is_required AS field_is_required,
            sf.tooltip AS field_description
        FROM schema_field$raw sf
        INNER JOIN schema$raw s ON sf.schema_id = s.id
        LEFT JOIN schema$raw s2 ON sf.target_schema_id = s2.id
        LEFT JOIN dropdown$raw d ON sf.selector_id = d.id
        WHERE s.name = :schema_name
          AND sf."archived$" = false
          AND s."archived$" = false
        ORDER BY sf.display_name
    """

    rows = await benchling.query(sql, {"schema_name": schema_name}, return_format="dict")
    if not rows:
        return f"No schema found with name: {schema_name}."
    return format_table(rows)


@tool
@tool_error_handler
async def get_dropdown_values(
    dropdown_name: str,
    runtime: Any | None = None,
) -> str:
    """Get available values for a Benchling dropdown.

    Args:
        dropdown_name: Dropdown name to query.
        runtime: LangChain tool runtime for injected services/config.
    """
    if not dropdown_name:
        return "Error: dropdown_name is required."

    context = get_tool_context(runtime)
    benchling = context.benchling

    sql = """
        SELECT DISTINCT dopt.name AS option_name
        FROM dropdown_option$raw dopt
        INNER JOIN dropdown$raw d ON dopt.dropdown_id = d.id
        WHERE d.name = :dropdown_name
          AND dopt."archived$" = false
          AND d."archived$" = false
        ORDER BY dopt.name
    """

    rows = await benchling.query(sql, {"dropdown_name": dropdown_name}, return_format="dict")
    if not rows:
        return f"No dropdown found with name: {dropdown_name}."
    return ", ".join(row["option_name"] for row in rows if row.get("option_name"))


@tool
@tool_error_handler
async def list_projects(
    wildcard_pattern: str | None = None,
    runtime: Any | None = None,
) -> str:
    """List projects in the Benchling warehouse.

    Args:
        wildcard_pattern: SQL wildcard pattern to filter projects (e.g., \"Cell%\") .
        runtime: LangChain tool runtime for injected services/config.
    """
    context = get_tool_context(runtime)
    benchling = context.benchling

    sql = """
        SELECT
            project.id AS project_id,
            project.name AS project_name,
            project.url AS project_url,
            project.created_at AS created_at,
            project.modified_at AS modified_at
        FROM project$raw project
        WHERE project."archived$" = false
    """
    params: dict[str, Any] = {}
    if wildcard_pattern:
        sql += " AND project.name LIKE :pattern"
        params["pattern"] = wildcard_pattern

    sql += " ORDER BY project.name"

    rows = await benchling.query(sql, params, return_format="dict")
    if not rows:
        return "No projects found."
    return format_table(rows)


@tool
@tool_error_handler
async def execute_warehouse_query(
    sql: str,
    params: dict | None = None,
    limit: int | None = None,
    runtime: Any | None = None,
) -> str:
    """Execute a read-only SQL query against the Benchling data warehouse.

    Args:
        sql: SQL query (SELECT/CTE only).
        params: Named parameters for the query.
        limit: Max rows to return (default 100, max 1000).
        runtime: LangChain tool runtime for injected services/config.
    """
    if not isinstance(sql, str) or not sql.strip():
        return "Error: SQL query must be a non-empty string."

    normalized = sql.strip()
    normalized_upper = normalized.upper()
    if not (normalized_upper.startswith("SELECT") or normalized_upper.startswith("WITH")):
        return "Error: Only SELECT queries are allowed."
    if _contains_disallowed_keywords(normalized):
        return "Error: Only SELECT queries are allowed."

    effective_limit = limit if limit is not None else 100
    if effective_limit > 1000:
        effective_limit = 1000
    if effective_limit < 1:
        effective_limit = 1

    sql_with_limit = _apply_limit(normalized, effective_limit)

    context = get_tool_context(runtime)
    benchling = context.benchling

    safe_params = params if isinstance(params, dict) else {}
    rows = await benchling.query(sql_with_limit, safe_params, return_format="dict")
    count = len(rows)
    if not rows:
        return "Query results (0 rows)."
    return f"Query results ({count} rows):\n\n{format_table(rows)}"

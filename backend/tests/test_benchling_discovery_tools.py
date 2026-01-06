from __future__ import annotations

import pytest

from backend.agents.tools.benchling_discovery import (
    get_entities,
    get_entity_relationships,
    get_entry_content,
    get_entry_entities,
    list_entries,
)
from backend.agents.tools.schema_tools import (
    execute_warehouse_query,
    get_dropdown_values,
    get_schema_field_info,
    get_schemas,
    list_projects,
)


class _BenchlingStub:
    def __init__(self) -> None:
        self.last_sql: str | None = None
        self.last_params: dict | None = None

    async def query(self, sql: str, params: dict | None = None, return_format: str | None = None):
        self.last_sql = sql
        self.last_params = params or {}

        if "information_schema.columns" in sql:
            table_name = (params or {}).get("table_name")
            if table_name == "entry$raw":
                return [
                    {"column_name": "id"},
                    {"column_name": "name"},
                    {"column_name": "markdown"},
                ]
            if table_name == "entity$raw":
                return [
                    {"column_name": "id"},
                    {"column_name": "name"},
                    {"column_name": "creator_id"},
                ]
            return []

        if "FROM entity$raw e" in sql and "e.name = :entity_name" in sql:
            return [
                {
                    "entity_id": "ent_1",
                    "entity_name": "LPS-001",
                    "schema_id": "schema_1",
                    "schema_name": "NGS Library Prep Sample",
                    "schema_system_name": "ngs_library_prep_sample",
                }
            ]

        if "FROM entity$raw e" in sql and "e.id IN" in sql:
            return [
                {
                    "entity_id": "ent_2",
                    "entity_name": "Pool-001",
                    "schema_id": "schema_2",
                    "schema_name": "NGS Pooled Sample",
                    "schema_system_name": "ngs_pooled_sample",
                }
            ]

        if "FROM schema_field$raw sf" in sql and "sf.schema_id = :schema_id" in sql:
            return [
                {
                    "field_display_name": "Pooled Sample",
                    "field_system_name": "pooled_sample",
                    "is_multi": False,
                    "target_schema_id": "schema_2",
                    "target_schema_name": "NGS Pooled Sample",
                    "target_schema_system_name": "ngs_pooled_sample",
                }
            ]

        if "FROM schema_field$raw sf" in sql and "sf.target_schema_id = :target_schema_id" in sql:
            return []

        if "FROM ngs_library_prep_sample$raw" in sql and "linked_entity_id" in sql:
            return [{"link_field": "Pooled Sample", "linked_entity_id": "ent_2"}]

        if "FROM entity$raw entity" in sql and "schema$raw" in sql:
            return [
                {
                    "entity_id": "ent_10",
                    "entity_name": "LPS-001",
                    "schema_name": "NGS Library Prep Sample",
                    "project_name": "CellAtlas",
                    "folder_name": "NGS",
                    "entity_url": "https://benchling/ent_10",
                }
            ]

        if "FROM entry$raw entry" in sql and 'entry."archived$"' in sql:
            return [
                {
                    "entry_name": "NGS_Run_Notes",
                    "display_id": "E-100",
                    "url": "https://benchling/entry",
                    "created_at": "2025-01-01",
                    "modified_at": "2025-01-02",
                    "folder_name": "NGS",
                    "project_name": "CellAtlas",
                    "creator_name": "Jane Smith",
                }
            ]

        if "FROM entry$raw entry" in sql and 'entry."markdown"' in sql:
            return [
                {
                    "entry_name": "NGS_Run_Notes",
                    "content": "Line1\nLine2\nLine3\nLine4",
                }
            ]

        if "FROM schema$raw schema" in sql and 'schema."archived$"' in sql:
            return [
                {"schema_name": "NGS Run"},
                {"schema_name": "NGS Library Prep Sample"},
            ]

        if "FROM schema_field$raw sf" in sql and "s.name = :schema_name" in sql:
            return [
                {
                    "schema_name": "NGS Run",
                    "field_name": "Run Name",
                    "field_type": "text",
                    "field_linked_schema": None,
                    "field_linked_dropdown": None,
                    "field_is_multi": False,
                    "field_is_required": True,
                    "field_description": "Run identifier",
                }
            ]

        if "FROM dropdown_option$raw" in sql:
            return [{"option_name": "Human"}, {"option_name": "Mouse"}]

        if "FROM project$raw project" in sql:
            return [
                {
                    "project_id": "proj_1",
                    "project_name": "CellAtlas",
                    "project_url": "https://benchling/project",
                    "created_at": "2024-01-01",
                    "modified_at": "2024-06-01",
                }
            ]

        if "SELECT 1" in sql:
            return [{"example": 1}]

        return []


class _Runtime:
    def __init__(self, benchling) -> None:
        self.config = {
            "configurable": {
                "benchling_service": benchling,
                "user_email": "dev@example.com",
                "user_name": "Developer",
            }
        }


@pytest.mark.asyncio
async def test_get_entities_with_fields():
    benchling = _BenchlingStub()
    runtime = _Runtime(benchling)

    output = await get_entities.ainvoke(
        {
            "entity_names": "LPS-001",
            "fields": "entity_id;entity_name;schema_name",
            "allow_wildcards": True,
            "runtime": runtime,
        }
    )

    assert "ent_10" in output
    assert benchling.last_sql is not None
    assert "LIKE" in benchling.last_sql


@pytest.mark.asyncio
async def test_get_entity_relationships_tree():
    benchling = _BenchlingStub()
    runtime = _Runtime(benchling)

    output = await get_entity_relationships.ainvoke(
        {
            "entity_name": "LPS-001",
            "relationship_depth": 2,
            "output_format": "tree",
            "runtime": runtime,
        }
    )

    assert "LPS-001" in output
    assert "Pooled Sample" in output


@pytest.mark.asyncio
async def test_list_entries_and_entry_content():
    benchling = _BenchlingStub()
    runtime = _Runtime(benchling)

    entries = await list_entries.ainvoke(
        {
            "entry_names": "NGS_Run_Notes",
            "allow_wildcards": False,
            "runtime": runtime,
        }
    )
    assert "NGS_Run_Notes" in entries

    content = await get_entry_content.ainvoke(
        {
            "entry_names": "NGS_Run_Notes",
            "head": 2,
            "runtime": runtime,
        }
    )
    assert "Line1" in content
    assert "Line2" in content


@pytest.mark.asyncio
async def test_get_entry_entities():
    benchling = _BenchlingStub()
    runtime = _Runtime(benchling)

    output = await get_entry_entities.ainvoke({"entry_name": "NGS_Run_Notes", "runtime": runtime})
    assert "No entities" in output or "entity_id" in output


@pytest.mark.asyncio
async def test_schema_and_dropdown_tools():
    benchling = _BenchlingStub()
    runtime = _Runtime(benchling)

    schemas = await get_schemas.ainvoke({"get_all_schemas": True, "runtime": runtime})
    assert "All schemas" in schemas

    fields = await get_schema_field_info.ainvoke({"schema_name": "NGS Run", "runtime": runtime})
    assert "NGS Run" in fields

    dropdowns = await get_dropdown_values.ainvoke({"dropdown_name": "Organism", "runtime": runtime})
    assert "Human" in dropdowns

    projects = await list_projects.ainvoke({"runtime": runtime})
    assert "CellAtlas" in projects

    query = await execute_warehouse_query.ainvoke(
        {"sql": "SELECT 1 AS example", "runtime": runtime}
    )
    assert "Query results" in query

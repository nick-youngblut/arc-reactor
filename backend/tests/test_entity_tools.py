from __future__ import annotations

import pandas as pd
import pytest

from backend.agents.tools.entity_tools import (
    find_sample_descendants,
    get_entity_relationships,
    trace_sample_lineage,
)


class _BenchlingStub:
    def __init__(self) -> None:
        self.last_call: dict[str, object] | None = None

    async def get_ancestors(
        self,
        *,
        entity_id: str,
        relationship_field: str,
        max_depth: int,
        include_path: bool,
        return_format: str,
    ):
        self.last_call = {
            "method": "get_ancestors",
            "entity_id": entity_id,
            "relationship_field": relationship_field,
            "max_depth": max_depth,
            "include_path": include_path,
            "return_format": return_format,
        }
        return pd.DataFrame([{"ancestor_id": "ent_parent", "depth": 1}])

    async def get_descendants(
        self,
        *,
        entity_id: str,
        relationship_field: str,
        max_depth: int,
        include_path: bool,
        return_format: str,
    ):
        self.last_call = {
            "method": "get_descendants",
            "entity_id": entity_id,
            "relationship_field": relationship_field,
            "max_depth": max_depth,
            "include_path": include_path,
            "return_format": return_format,
        }
        return pd.DataFrame([{"descendant_id": "ent_child", "depth": 1}])

    async def get_related_entities(self, *, entity_id: str, relationship_field: str | None, return_format: str):
        self.last_call = {
            "method": "get_related_entities",
            "entity_id": entity_id,
            "relationship_field": relationship_field,
            "return_format": return_format,
        }
        return {
            "source": {"id": entity_id, "name": "Sample 1"},
            "relationships": {"parent_sample": [{"id": "ent_parent", "name": "Parent"}]},
        }


class _Runtime:
    def __init__(self, benchling):
        self.config = {
            "configurable": {
                "benchling_service": benchling,
                "user_email": "dev@example.com",
                "user_name": "Developer",
            }
        }


@pytest.mark.asyncio
async def test_trace_sample_lineage() -> None:
    benchling = _BenchlingStub()
    runtime = _Runtime(benchling)

    output = await trace_sample_lineage(
        entity_id="ent_child",
        relationship_field="parent_sample",
        runtime=runtime,
    )

    assert "Lineage for ent_child" in output
    assert benchling.last_call is not None
    assert benchling.last_call["method"] == "get_ancestors"
    assert benchling.last_call["relationship_field"] == "parent_sample"


@pytest.mark.asyncio
async def test_find_sample_descendants() -> None:
    benchling = _BenchlingStub()
    runtime = _Runtime(benchling)

    output = await find_sample_descendants(
        entity_id="ent_parent",
        relationship_field=None,
        runtime=runtime,
    )

    assert "Descendants for ent_parent" in output
    assert benchling.last_call is not None
    assert benchling.last_call["method"] == "get_descendants"
    assert benchling.last_call["relationship_field"] == "parent_sample"


@pytest.mark.asyncio
async def test_get_entity_relationships() -> None:
    benchling = _BenchlingStub()
    runtime = _Runtime(benchling)

    output = await get_entity_relationships(entity_id="ent_123", runtime=runtime)

    assert "Relationships for Sample 1" in output
    assert "parent_sample" in output
    assert "Parent" in output
    assert benchling.last_call is not None
    assert benchling.last_call["method"] == "get_related_entities"

# Benchling-py Usage Examples

These examples show how Arc Reactor interacts with Benchling via `benchling-py`.
All access is read-only.

## BenchlingService Query

```python
from backend.services.benchling import BenchlingService
from backend.utils.circuit_breaker import create_breakers
from backend.config import settings

breakers = create_breakers(settings)
service = BenchlingService.create(breakers)

rows = await service.query(
    "SELECT id, \"name$\" AS name FROM ngs_run$raw WHERE archived$ = FALSE LIMIT 5",
    return_format="dict",
)
```

## Entity Lookup

```python
entity = await service.get_entity("ent_123")
```

## Relationship Traversal

```python
lineage = await service.get_ancestors(
    entity_id="ent_child",
    relationship_field="parent_sample",
    return_format="tree",
)
```

## Return Formats

- API routes: use `return_format="dict"` for JSON responses.
- Agent tools: use `return_format="dict"` and format with TOON (`format_table`).
- Data analysis: use `return_format="dataframe"` locally.

## Notes

- Benchling tenant selection is controlled by `DYNACONF` (`test`, `dev`, `prod`).
- Credentials are provided via `BENCHLING_{TEST,PROD}_*` environment variables.

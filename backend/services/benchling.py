"""Benchling service using benchling-py BenchlingSession.

This service wraps benchling-py's synchronous operations for use in FastAPI's
async context using asyncio.to_thread().

IMPORTANT: benchling-py has TWO different EntityOperations classes:
- benchling_py.api.entity.EntityOperations: For Benchling API CRUD operations
- benchling_py.warehouse.entity.EntityOperations: For warehouse SQL queries

The BenchlingSession exposes:
- session.entities -> API EntityOperations (for create/update/delete)
- session.warehouse.entity -> Warehouse EntityOperations (for queries)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Literal

import pandas as pd
from benchling_py import BenchlingSession
from benchling_py.warehouse import RelationshipNavigator, WarehouseConnection

from ..utils.circuit_breaker import Breakers


@dataclass
class BenchlingService:
    """Service for Benchling warehouse and API operations.

    Wraps benchling-py's synchronous BenchlingSession for async FastAPI compatibility.
    The DYNACONF environment variable determines which tenant (prod/test) is used.

    Properties exposed from BenchlingSession:
        - warehouse: WarehouseClient for SQL queries
        - warehouse.entity: Warehouse EntityOperations (queries)
        - warehouse.schema: SchemaOperations
        - warehouse.entry: EntryOperations
        - warehouse.dropdown: DropdownOperations
        - warehouse.folder: FolderOperations
        - entities: API EntityOperations (CRUD via Benchling API)
        - navigator: RelationshipNavigator
        - api_client: Full APIClient access
    """

    _session: BenchlingSession = field(repr=False)
    _breaker: object = field(repr=False)

    @classmethod
    def create(cls, breakers: Breakers) -> "BenchlingService":
        """Create a new BenchlingService.

        Args:
            breakers: Circuit breakers for resilience.

        Returns:
            Configured BenchlingService instance.

        Note:
            The Benchling tenant is determined by the DYNACONF environment variable:
            - DYNACONF=prod: Uses arcinstitute.benchling.com (registry: src_0JyjRuJh)
            - DYNACONF=test: Uses arcinstitutetest.benchling.com (registry: src_CUHVHLsC)
            - DYNACONF=dev: Same as test (copies test configuration)
        """
        session = BenchlingSession()
        return cls(_session=session, _breaker=breakers.benchling)

    @property
    def session(self) -> BenchlingSession:
        """Access the underlying BenchlingSession."""
        return self._session

    @property
    def warehouse(self):
        """Access the WarehouseClient for SQL queries.

        Sub-components:
            - warehouse.entity: Warehouse EntityOperations (for SQL queries)
            - warehouse.schema: SchemaOperations
            - warehouse.entry: EntryOperations
            - warehouse.dropdown: DropdownOperations
            - warehouse.folder: FolderOperations
            - warehouse.convert: Alias for entity (field conversion helpers)
            - warehouse.model: TableRegistry
        """
        return self._session.warehouse

    @property
    def entities(self):
        """Access API EntityOperations for CRUD operations via Benchling API.

        Methods:
            - list_entities(schema_id, page_size, max_pages)
            - get_entity(entity_id)

        Note: This is different from warehouse.entity which is for SQL queries.
        """
        return self._session.entities

    @property
    def navigator(self) -> RelationshipNavigator:
        """Access the RelationshipNavigator for traversing entity relationships."""
        return self._session.navigator

    @property
    def api_client(self):
        """Access the full APIClient for advanced operations."""
        return self._session.api_client

    async def query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        return_format: Literal["dataframe", "dict", "yaml", "toon", "raw", "map"] = "dict",
        key_value_map: list[str] | None = None,
    ) -> list[dict[str, Any]] | pd.DataFrame | dict[str, Any] | str:
        """Execute a SQL query against the Benchling data warehouse.

        Args:
            sql: SQL query string.
            params: Query parameters for parameterized queries.
            return_format: Output format:
                - "dataframe": pandas DataFrame (default in benchling-py)
                - "dict": list of dicts (default here for JSON serialization)
                - "yaml": YAML string
                - "toon": TOON table format (compact, token-efficient)
                - "raw": Raw SQLAlchemy result
                - "map": dict mapping (requires key_value_map)
            key_value_map: Two-element list specifying key/value column names for "map".

        Returns:
            Query results in the requested format.
        """

        @self._breaker
        def _run() -> list[dict[str, Any]] | pd.DataFrame | dict[str, Any] | str:
            return self._session.warehouse.query(
                sql=sql,
                params=params,
                return_format=return_format,
                key_value_map=key_value_map,
            )

        return await asyncio.to_thread(_run)

    async def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        """Get a single entity by ID via the Benchling API.

        Args:
            entity_id: Benchling entity ID.

        Returns:
            Entity data or None if not found.
        """

        @self._breaker
        def _run() -> dict[str, Any] | None:
            return self._session.entities.get_entity(entity_id)

        return await asyncio.to_thread(_run)

    async def convert_fields_to_api_format(
        self,
        schema_name: str,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert system field names to API display names.

        Args:
            schema_name: Schema display name (e.g., 'ngs_run_output_sample').
            fields: Dict with system field names as keys.

        Returns:
            Dict with API display names as keys.

        Example:
            >>> await service.convert_fields_to_api_format(
            ...     "ngs_run_output_sample",
            ...     {"link_to_fastq_file": "gs://bucket/file.fastq.gz"}
            ... )
            {"Link to FASTQ File": "gs://bucket/file.fastq.gz"}
        """

        def _run() -> dict[str, Any]:
            return self._session.warehouse.convert_fields_to_api_format_by_schema_name(
                schema_name, fields
            )

        return await asyncio.to_thread(_run)

    async def get_ancestors(
        self,
        entity_id: str,
        relationship_field: str,
        max_depth: int = 10,
        include_path: bool = True,
        return_format: Literal["dataframe", "tree", "graph"] = "dataframe",
    ) -> pd.DataFrame | dict[str, Any]:
        """Trace entity lineage (ancestors) through relationship fields.

        Args:
            entity_id: Starting entity ID.
            relationship_field: Field name containing parent reference.
            max_depth: Maximum depth to traverse.
            include_path: Whether to include the traversal path.
            return_format: Output format:
                - "dataframe": pandas DataFrame with columns like ancestor_id, depth
                - "tree": Nested dict structure
                - "graph": RelationshipGraph object

        Returns:
            Ancestor information in the requested format.
        """

        @self._breaker
        def _run() -> pd.DataFrame | dict[str, Any]:
            return self._session.navigator.get_ancestors(
                entity_id=entity_id,
                relationship_field=relationship_field,
                max_depth=max_depth,
                include_path=include_path,
                return_format=return_format,
            )

        return await asyncio.to_thread(_run)

    async def get_descendants(
        self,
        entity_id: str,
        relationship_field: str,
        max_depth: int = 10,
        include_path: bool = True,
        return_format: Literal["dataframe", "tree", "graph"] = "dataframe",
    ) -> pd.DataFrame | dict[str, Any]:
        """Find entity descendants through relationship fields.

        Args:
            entity_id: Starting entity ID.
            relationship_field: Field name containing parent reference.
            max_depth: Maximum depth to traverse.
            include_path: Whether to include the traversal path.
            return_format: Output format (dataframe, tree, or graph).

        Returns:
            Descendant information in the requested format.
        """

        @self._breaker
        def _run() -> pd.DataFrame | dict[str, Any]:
            return self._session.navigator.get_descendants(
                entity_id=entity_id,
                relationship_field=relationship_field,
                max_depth=max_depth,
                include_path=include_path,
                return_format=return_format,
            )

        return await asyncio.to_thread(_run)

    async def get_related_entities(
        self,
        entity_id: str,
        relationship_field: str | None = None,
        return_format: Literal["dataframe", "dict", "graph"] = "dataframe",
    ) -> pd.DataFrame | dict[str, Any]:
        """Get entities related through entity_link fields.

        Args:
            entity_id: Entity ID to find relationships for.
            relationship_field: Specific field to query (None for all).
            return_format: Output format.

        Returns:
            Related entities in the requested format.
        """

        @self._breaker
        def _run() -> pd.DataFrame | dict[str, Any]:
            return self._session.navigator.get_related_entities(
                entity_id=entity_id,
                relationship_field=relationship_field,
                return_format=return_format,
            )

        return await asyncio.to_thread(_run)

    async def health_check(self) -> bool:
        """Check if Benchling warehouse connection is healthy.

        Returns:
            True if connection is healthy, False otherwise.
        """
        try:

            def _run() -> bool:
                self._session.warehouse.query("SELECT 1")
                return True

            return await asyncio.to_thread(_run)
        except Exception:
            return False

    def close(self) -> None:
        """Close the Benchling session.

        Note: This drops references but does NOT dispose the global SQLAlchemy
        engine. The engine is shared across all WarehouseConnection instances
        pointing to the same database URI.

        For full engine cleanup (e.g., at application shutdown), use:
            WarehouseConnection.close_all()
        """
        self._session.close()

    @staticmethod
    def close_all_engines() -> None:
        """Dispose all SQLAlchemy engines in the global registry.

        Call this at application shutdown to properly release all database
        connections. Use with caution - this affects ALL WarehouseConnection
        instances in the process.
        """
        WarehouseConnection.close_all()

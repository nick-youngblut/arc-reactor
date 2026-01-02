from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd
import pytest

from backend.services import benchling as benchling_module


class _Breaker:
    def __call__(self, func):
        return func


@pytest.fixture
def mock_breakers():
    return SimpleNamespace(benchling=_Breaker())


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.warehouse = MagicMock()
    session.entities = MagicMock()
    session.upsert = MagicMock()
    session.navigator = MagicMock()
    session.api_client = MagicMock()
    return session


@pytest.fixture
def service(mock_breakers, mock_session, monkeypatch):
    session_ctor = MagicMock(return_value=mock_session)
    monkeypatch.setattr(benchling_module, "BenchlingSession", session_ctor)
    return benchling_module.BenchlingService.create(mock_breakers)


def test_create_uses_benchling_session(mock_breakers, mock_session, monkeypatch) -> None:
    session_ctor = MagicMock(return_value=mock_session)
    monkeypatch.setattr(benchling_module, "BenchlingSession", session_ctor)

    service = benchling_module.BenchlingService.create(mock_breakers)

    assert service.session is mock_session
    session_ctor.assert_called_once_with()


def test_properties_expose_session_clients(service, mock_session) -> None:
    assert service.session is mock_session
    assert service.warehouse is mock_session.warehouse
    assert service.entities is mock_session.entities
    assert service.upsert is mock_session.upsert
    assert service.navigator is mock_session.navigator
    assert service.api_client is mock_session.api_client


@pytest.mark.asyncio
@pytest.mark.parametrize("return_format", ["dict", "dataframe", "toon"])
async def test_query_with_return_formats(service, mock_session, return_format) -> None:
    mock_session.warehouse.query.return_value = {"format": return_format}

    result = await service.query("SELECT 1", return_format=return_format)

    assert result == {"format": return_format}
    mock_session.warehouse.query.assert_called_with(
        sql="SELECT 1",
        params=None,
        return_format=return_format,
        key_value_map=None,
    )


@pytest.mark.asyncio
async def test_get_entity(service, mock_session) -> None:
    mock_session.entities.get_entity.return_value = {"id": "ent_123", "name": "Sample"}

    result = await service.get_entity("ent_123")

    assert result == {"id": "ent_123", "name": "Sample"}
    mock_session.entities.get_entity.assert_called_once_with("ent_123")


@pytest.mark.asyncio
async def test_convert_fields_to_api_format(service, mock_session) -> None:
    mock_session.warehouse.convert_fields_to_api_format_by_schema_name.return_value = {
        "Link to FASTQ File": "gs://example.fastq.gz"
    }

    result = await service.convert_fields_to_api_format(
        "ngs_run_output_sample",
        {"link_to_fastq_file": "gs://example.fastq.gz"},
    )

    assert result == {"Link to FASTQ File": "gs://example.fastq.gz"}
    mock_session.warehouse.convert_fields_to_api_format_by_schema_name.assert_called_once_with(
        "ngs_run_output_sample",
        {"link_to_fastq_file": "gs://example.fastq.gz"},
    )


@pytest.mark.asyncio
async def test_get_ancestors(service, mock_session) -> None:
    expected = pd.DataFrame([{"ancestor_id": "ent_parent", "depth": 1}])
    mock_session.navigator.get_ancestors.return_value = expected

    result = await service.get_ancestors(
        entity_id="ent_child",
        relationship_field="parent_sample",
        max_depth=3,
        include_path=True,
        return_format="dataframe",
    )

    assert result is expected
    mock_session.navigator.get_ancestors.assert_called_once_with(
        entity_id="ent_child",
        relationship_field="parent_sample",
        max_depth=3,
        include_path=True,
        return_format="dataframe",
    )


@pytest.mark.asyncio
async def test_get_descendants(service, mock_session) -> None:
    expected = pd.DataFrame([{"descendant_id": "ent_child", "depth": 1}])
    mock_session.navigator.get_descendants.return_value = expected

    result = await service.get_descendants(
        entity_id="ent_parent",
        relationship_field="parent_sample",
        max_depth=4,
        include_path=False,
        return_format="dataframe",
    )

    assert result is expected
    mock_session.navigator.get_descendants.assert_called_once_with(
        entity_id="ent_parent",
        relationship_field="parent_sample",
        max_depth=4,
        include_path=False,
        return_format="dataframe",
    )


@pytest.mark.asyncio
async def test_get_related_entities(service, mock_session) -> None:
    expected = {"relationships": {"parent_sample": [{"id": "ent_1"}]}}
    mock_session.navigator.get_related_entities.return_value = expected

    result = await service.get_related_entities(
        entity_id="ent_123",
        relationship_field=None,
        return_format="dict",
    )

    assert result == expected
    mock_session.navigator.get_related_entities.assert_called_once_with(
        entity_id="ent_123",
        relationship_field=None,
        return_format="dict",
    )


@pytest.mark.asyncio
async def test_health_check_success(service, mock_session) -> None:
    mock_session.warehouse.query.return_value = [{"ok": 1}]

    result = await service.health_check()

    assert result is True
    mock_session.warehouse.query.assert_called_once_with("SELECT 1")


@pytest.mark.asyncio
async def test_health_check_failure(service, mock_session) -> None:
    mock_session.warehouse.query.side_effect = Exception("boom")

    result = await service.health_check()

    assert result is False
    mock_session.warehouse.query.assert_called_once_with("SELECT 1")


def test_close(service, mock_session) -> None:
    service.close()
    mock_session.close.assert_called_once_with()


def test_close_all_engines(monkeypatch) -> None:
    close_all = MagicMock()
    monkeypatch.setattr(benchling_module.WarehouseConnection, "close_all", close_all)

    benchling_module.BenchlingService.close_all_engines()

    close_all.assert_called_once_with()

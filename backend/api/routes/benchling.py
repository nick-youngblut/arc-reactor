from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query

from backend.dependencies import get_benchling_service
from backend.services.benchling import BenchlingService
from backend.utils.errors import BenchlingError

router = APIRouter(tags=["benchling"])

_METADATA_CACHE: dict[str, Any] = {"expires_at": datetime.min.replace(tzinfo=timezone.utc), "data": {}}


@router.get("/benchling/runs")
async def list_ngs_runs(
    name: str | None = Query(default=None),
    instrument: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    benchling: BenchlingService = Depends(get_benchling_service),
) -> dict[str, Any]:
    filters = ["archived$ = FALSE"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if name:
        filters.append('"name$" ILIKE :name')
        params["name"] = f"%{name}%"
    if instrument:
        filters.append("instrument = :instrument")
        params["instrument"] = instrument

    where_clause = " AND ".join(filters)
    sql = f"""
        SELECT id, "name$" AS name, instrument, sequencing_reagent_kit,
               created_at$ AS created_at, modified_at$ AS modified_at, archived$
        FROM ngs_run$raw
        WHERE {where_clause}
        ORDER BY created_at$ DESC
        LIMIT :limit OFFSET :offset
    """
    try:
        runs = await benchling.query(sql, params)
    except Exception as exc:
        raise BenchlingError("Benchling query failed", detail=str(exc)) from exc

    return {"runs": runs, "limit": limit, "offset": offset}


@router.get("/benchling/runs/{name}/samples")
async def get_run_samples(
    name: str,
    benchling: BenchlingService = Depends(get_benchling_service),
) -> dict[str, Any]:
    sql = """
        SELECT
          lps.sample_id,
          nros.link_to_fastq_file,
          nros.read,
          md.organism,
          md.cell_line,
          md.tissue,
          md.perturbation,
          md.replicate
        FROM library_prep_sample$raw lps
        INNER JOIN ngs_library_pooling_v2$raw nlp ON lps.id = nlp.source
        INNER JOIN pooled_sample$raw ps ON nlp.destination = ps.id
        INNER JOIN ngs_run_pooling_v2$raw nrp ON ps.id = nrp.ngs_library_pool
        INNER JOIN ngs_run$raw nr ON nrp.ngs_run = nr.id
        INNER JOIN ngs_run_output_sample$raw nros
          ON nr.id = nros.ngs_run AND lps.id = nros.ngs_library
        LEFT JOIN ngs_library_metadata_v2$raw md ON lps.id = md.ngs_library
        WHERE nr."name$" = :name
          AND lps.archived$ = FALSE
    """
    try:
        rows = await benchling.query(sql, {"name": name})
    except Exception as exc:
        raise BenchlingError("Benchling query failed", detail=str(exc)) from exc

    return {"run_name": name, "samples": rows}


@router.get("/benchling/metadata")
async def get_benchling_metadata(
    benchling: BenchlingService = Depends(get_benchling_service),
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    if _METADATA_CACHE["expires_at"] > now:
        return _METADATA_CACHE["data"]

    sql_instruments = """
        SELECT DISTINCT instrument FROM ngs_run$raw
        WHERE archived$ = FALSE
        ORDER BY instrument
    """
    sql_reagent = """
        SELECT DISTINCT sequencing_reagent_kit FROM ngs_run$raw
        WHERE archived$ = FALSE
        ORDER BY sequencing_reagent_kit
    """
    sql_projects = """
        SELECT DISTINCT project FROM library_prep_sample$raw
        WHERE archived$ = FALSE AND project IS NOT NULL
        ORDER BY project
    """
    try:
        instruments = await benchling.query(sql_instruments)
        reagents = await benchling.query(sql_reagent)
        projects = await benchling.query(sql_projects)
    except Exception as exc:
        raise BenchlingError("Benchling query failed", detail=str(exc)) from exc

    data = {
        "instruments": [row["instrument"] for row in instruments if row.get("instrument")],
        "sequencing_reagent_kits": [
            row["sequencing_reagent_kit"] for row in reagents if row.get("sequencing_reagent_kit")
        ],
        "projects": [row["project"] for row in projects if row.get("project")],
    }
    _METADATA_CACHE["data"] = data
    _METADATA_CACHE["expires_at"] = now + timedelta(minutes=5)
    return data

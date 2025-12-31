from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.models.schemas.pipelines import PipelineListResponse, PipelineSchema
from backend.services.pipelines import PipelineRegistry

router = APIRouter(tags=["pipelines"])


@router.get("/pipelines", response_model=PipelineListResponse)
async def list_pipelines() -> PipelineListResponse:
    registry = PipelineRegistry.create()
    return PipelineListResponse(pipelines=registry.list_pipelines())


@router.get("/pipelines/{name}", response_model=PipelineSchema)
async def get_pipeline(name: str) -> PipelineSchema:
    registry = PipelineRegistry.create()
    pipeline = registry.get_pipeline(name)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return pipeline


@router.get("/pipelines/{name}/schema")
async def get_pipeline_schema(name: str) -> dict[str, object]:
    registry = PipelineRegistry.create()
    pipeline = registry.get_pipeline(name)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return {
        "samplesheet_columns": pipeline.samplesheet_columns,
        "required_params": pipeline.required_params,
        "optional_params": pipeline.optional_params,
    }

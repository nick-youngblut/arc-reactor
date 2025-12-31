from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PipelineParam(BaseModel):
    name: str
    type: str
    description: str
    required: bool
    default: Any | None = None
    options: list[str] | None = None


class SamplesheetColumn(BaseModel):
    name: str
    description: str
    required: bool
    type: str


class PipelineSchema(BaseModel):
    name: str
    display_name: str
    description: str
    repository: str
    versions: list[str]
    default_version: str
    samplesheet_columns: list[SamplesheetColumn]
    required_params: list[PipelineParam]
    optional_params: list[PipelineParam]


class PipelineListResponse(BaseModel):
    pipelines: list[PipelineSchema]

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FileState(BaseModel):
    content: str | None = None
    modified_by: Literal["agent", "user"] | None = None
    modified_at: datetime | None = None


class ValidationError(BaseModel):
    field: str
    message: str
    sample: str | None = None


class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[ValidationError] = Field(default_factory=list)


class WorkspaceResponse(BaseModel):
    id: UUID
    user_email: str
    thread_id: str | None
    pipeline: str | None
    version: str | None
    samplesheet: FileState
    config: FileState
    validation_result: ValidationResult | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceCreateRequest(BaseModel):
    thread_id: str | None = None
    pipeline: str | None = None
    version: str | None = None
    samplesheet: str | None = None
    config: str | None = None


class WorkspaceUpdateRequest(BaseModel):
    pipeline: str | None = None
    version: str | None = None
    samplesheet: str | None = None
    config: str | None = None


class FileUpdateRequest(BaseModel):
    content: str


class PipelineUpdateRequest(BaseModel):
    pipeline: str
    version: str | None = None


class AssociateThreadRequest(BaseModel):
    thread_id: str

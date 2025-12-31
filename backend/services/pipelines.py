from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.models.schemas.pipelines import PipelineParam, PipelineSchema, SamplesheetColumn


@dataclass(frozen=True)
class PipelineRegistry:
    pipelines: dict[str, PipelineSchema]

    @classmethod
    def create(cls) -> "PipelineRegistry":
        scrnaseq = PipelineSchema(
            name="nf-core/scrnaseq",
            display_name="Single-cell RNA-seq",
            description="nf-core pipeline for single-cell RNA sequencing data analysis",
            repository="https://github.com/nf-core/scrnaseq",
            versions=["2.7.1", "2.6.0", "2.5.1"],
            default_version="2.7.1",
            samplesheet_columns=[
                SamplesheetColumn(
                    name="sample",
                    description="Sample identifier",
                    required=True,
                    type="string",
                ),
                SamplesheetColumn(
                    name="fastq_1",
                    description="Path to R1 FASTQ",
                    required=True,
                    type="path",
                ),
                SamplesheetColumn(
                    name="fastq_2",
                    description="Path to R2 FASTQ",
                    required=True,
                    type="path",
                ),
                SamplesheetColumn(
                    name="expected_cells",
                    description="Expected cell count",
                    required=False,
                    type="integer",
                ),
            ],
            required_params=[
                PipelineParam(
                    name="genome",
                    type="enum",
                    description="Reference genome",
                    required=True,
                    options=["GRCh38", "GRCm39"],
                ),
                PipelineParam(
                    name="protocol",
                    type="enum",
                    description="10x protocol version",
                    required=True,
                    options=["10XV2", "10XV3", "10XV4"],
                ),
            ],
            optional_params=[
                PipelineParam(
                    name="aligner",
                    type="enum",
                    description="Alignment tool",
                    required=False,
                    default="simpleaf",
                    options=["simpleaf", "star", "kallisto", "cellranger"],
                ),
                PipelineParam(
                    name="expected_cells",
                    type="integer",
                    description="Default expected cells",
                    required=False,
                    default=10000,
                ),
            ],
        )
        return cls(pipelines={scrnaseq.name: scrnaseq})

    def list_pipelines(self) -> list[PipelineSchema]:
        return list(self.pipelines.values())

    def get_pipeline(self, name: str) -> PipelineSchema | None:
        return self.pipelines.get(name)

    def get_samplesheet_schema(self, name: str) -> list[SamplesheetColumn] | None:
        pipeline = self.get_pipeline(name)
        if not pipeline:
            return None
        return pipeline.samplesheet_columns

    def validate_params(self, name: str, params: dict[str, Any]) -> list[str]:
        pipeline = self.get_pipeline(name)
        if not pipeline:
            return ["Pipeline not found"]

        errors: list[str] = []
        required = {param.name: param for param in pipeline.required_params}
        for key, param in required.items():
            if key not in params:
                errors.append(f"Missing required param: {key}")
            else:
                errors.extend(self._validate_param(param, params[key]))

        optional = {param.name: param for param in pipeline.optional_params}
        for key, value in params.items():
            if key in required:
                continue
            if key not in optional:
                continue
            errors.extend(self._validate_param(optional[key], value))

        return errors

    def render_config(self, name: str, params: dict[str, Any]) -> str:
        pipeline = self.get_pipeline(name)
        if not pipeline:
            raise ValueError("Pipeline not found")

        lines = ["params {"]
        for key, value in params.items():
            formatted = self._format_value(value)
            lines.append(f"  {key} = {formatted}")
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def _format_value(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        return f"\"{value}\""

    @staticmethod
    def _validate_param(param: PipelineParam, value: Any) -> list[str]:
        errors: list[str] = []
        if param.type == "integer":
            if not isinstance(value, int):
                errors.append(f"Param {param.name} must be an integer")
        elif param.type == "boolean":
            if not isinstance(value, bool):
                errors.append(f"Param {param.name} must be a boolean")
        elif param.type == "enum":
            if param.options and value not in param.options:
                errors.append(
                    f"Param {param.name} must be one of {', '.join(param.options)}"
                )
        elif param.type == "string":
            if not isinstance(value, str):
                errors.append(f"Param {param.name} must be a string")
        return errors

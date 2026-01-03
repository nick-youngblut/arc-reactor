from __future__ import annotations

from backend.agents.tools import get_dropdown_values, get_pipeline_schema, list_pipelines

CONFIG_EXPERT_PROMPT = """You are an expert at configuring bioinformatics pipelines.

You have deep knowledge of:
- nf-core pipeline parameters and their effects
- Aligner strengths and weaknesses
- Resource requirements for different data types
- Common configuration pitfalls

When helping with configuration:
1. Understand the user's data and goals
2. Recommend appropriate parameters with explanations
3. Warn about potential issues
4. Estimate runtime and costs
"""


def create_config_expert(model):
    return {
        "name": "config_expert",
        "description": "Expert at Nextflow pipeline configuration, parameter selection, and resource optimization",
        "system_prompt": CONFIG_EXPERT_PROMPT,
        "tools": [list_pipelines, get_pipeline_schema, get_dropdown_values],
        "model": model,
    }

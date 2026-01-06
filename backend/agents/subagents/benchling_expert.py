from __future__ import annotations

from backend.agents.model import create_agent_model, get_agent_config
from backend.agents.prompts import BENCHLING_EXPERT_PROMPT
from backend.agents.tools.collections.benchling import get_benchling_expert_tools


def create_benchling_expert(settings: object) -> dict:
    """Create the benchling_expert subagent configuration.

    Args:
        settings: Dynaconf settings object

    Returns:
        Subagent configuration dict for DeepAgents
    """
    config = get_agent_config(settings, "benchling_expert")
    model = create_agent_model(config)

    return {
        "name": "benchling_expert",
        "description": (
            "Expert at complex Benchling queries involving multiple data sources, "
            "relationship traversal, NGS data discovery, and schema introspection. "
            "Use for: finding NGS runs, getting samples and FASTQ paths, QC metrics, "
            "tracing sample lineage, exploring entity relationships, and custom warehouse queries."
        ),
        "system_prompt": BENCHLING_EXPERT_PROMPT,
        "tools": get_benchling_expert_tools(),
        "model": model,
    }

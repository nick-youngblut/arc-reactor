from __future__ import annotations

from backend.agents.model import create_agent_model, get_agent_config
from backend.agents.prompts import CONFIG_EXPERT_PROMPT
from backend.agents.tools.collections.config import get_config_expert_tools


def create_config_expert(settings: object) -> dict:
    """Create the config_expert subagent configuration.

    Args:
        settings: Dynaconf settings object

    Returns:
        Subagent configuration dict for DeepAgents
    """
    config = get_agent_config(settings, "config_expert")
    model = create_agent_model(config)

    return {
        "name": "config_expert",
        "description": (
            "Expert at Nextflow pipeline configuration, parameter selection, "
            "and file generation. Use for: listing available pipelines, explaining parameters, "
            "generating samplesheets and configs, recommending settings based on data type."
        ),
        "system_prompt": CONFIG_EXPERT_PROMPT,
        "tools": get_config_expert_tools(),
        "model": model,
    }

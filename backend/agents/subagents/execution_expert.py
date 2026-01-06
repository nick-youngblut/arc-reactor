from __future__ import annotations

from backend.agents.middleware.hitl import build_hitl_interrupt_map
from backend.agents.model import create_agent_model, get_agent_config
from backend.agents.prompts import EXECUTION_EXPERT_PROMPT
from backend.agents.tools.collections.execution import get_execution_expert_tools


def create_execution_expert(settings: object) -> dict:
    """Create the execution_expert subagent configuration.

    Args:
        settings: Dynaconf settings object

    Returns:
        Subagent configuration dict for DeepAgents
    """
    config = get_agent_config(settings, "execution_expert")
    model = create_agent_model(config)

    return {
        "name": "execution_expert",
        "description": (
            "Expert at pipeline validation, submission, monitoring, and troubleshooting. "
            "Use for: validating inputs, submitting runs, checking run/task status, "
            "diagnosing failures, analyzing logs, recovering failed runs, "
            "accessing outputs, and cleanup operations. "
            "Destructive operations (submit, cancel, recover, delete) require human approval."
        ),
        "system_prompt": EXECUTION_EXPERT_PROMPT,
        "tools": get_execution_expert_tools(),
        "model": model,
        "interrupt_on": build_hitl_interrupt_map(),
    }

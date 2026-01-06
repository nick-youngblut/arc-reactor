from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain.chat_models import init_chat_model

DEFAULT_MODEL = "google_genai:gemini-3-flash-preview"
DEFAULT_TEMPERATURE = 1.0
DEFAULT_MAX_OUTPUT_TOKENS = 8192
DEFAULT_THINKING_LEVEL = "low"


@dataclass
class AgentModelConfig:
    """Configuration for an agent's model."""

    model: str
    temperature: float = DEFAULT_TEMPERATURE
    thinking_level: str = DEFAULT_THINKING_LEVEL
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS


def get_chat_model(
    settings: object,
    *,
    thinking_level: str | None = None,
    streaming: bool = True,
) -> Any:
    model_id = getattr(settings, "gemini_model", "gemini-3-flash-preview")
    resolved_thinking_level = thinking_level or getattr(
        settings, "gemini_thinking_level", DEFAULT_THINKING_LEVEL
    )

    return init_chat_model(
        f"google_genai:{model_id}",
        temperature=DEFAULT_TEMPERATURE,
        max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
        thinking_level=resolved_thinking_level,
        streaming=streaming,
    )


def get_agent_config(settings: object, agent_name: str) -> AgentModelConfig:
    """Get model configuration for a specific agent.

    Args:
        settings: Dynaconf settings object
        agent_name: One of 'orchestrator', 'benchling_expert',
            'config_expert', 'execution_expert'

    Returns:
        AgentModelConfig with model settings
    """
    base_model = f"google_genai:{getattr(settings, 'gemini_model', 'gemini-3-flash-preview')}"
    base_thinking = getattr(settings, "gemini_thinking_level", DEFAULT_THINKING_LEVEL)

    agent_settings = getattr(settings, "agent", {}) or {}
    if agent_name == "orchestrator":
        config = agent_settings.get("orchestrator", {}) or {}
    else:
        subagents = agent_settings.get("subagents", {}) or {}
        config = subagents.get(agent_name, {}) or {}

    return AgentModelConfig(
        model=config.get("model", base_model),
        temperature=config.get("temperature", DEFAULT_TEMPERATURE),
        thinking_level=config.get("thinking_level", base_thinking),
        max_output_tokens=config.get("max_output_tokens", DEFAULT_MAX_OUTPUT_TOKENS),
    )


def create_agent_model(config: AgentModelConfig, *, streaming: bool = True):
    """Create a chat model from configuration.

    Args:
        config: AgentModelConfig instance
        streaming: Whether to enable streaming

    Returns:
        Initialized chat model
    """
    return init_chat_model(
        config.model,
        temperature=config.temperature,
        max_output_tokens=config.max_output_tokens,
        thinking_level=config.thinking_level,
        streaming=streaming,
    )

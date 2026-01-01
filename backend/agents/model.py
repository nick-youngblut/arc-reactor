from __future__ import annotations

import os
from typing import Any

from langchain.chat_models import init_chat_model

DEFAULT_MODEL = "google_genai:gemini-3-flash-preview"
DEFAULT_TEMPERATURE = 1.0
DEFAULT_MAX_OUTPUT_TOKENS = 8192
DEFAULT_THINKING_LEVEL = "low"


def _use_vertex_ai(settings: object) -> bool:
    return bool(os.getenv("GOOGLE_CLOUD_PROJECT") or getattr(settings, "google_cloud_project", None))


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

    provider = "google_vertexai" if _use_vertex_ai(settings) else "google_genai"

    return init_chat_model(
        f"{provider}:{model_id}",
        temperature=DEFAULT_TEMPERATURE,
        max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
        thinking_level=resolved_thinking_level,
        streaming=streaming,
    )

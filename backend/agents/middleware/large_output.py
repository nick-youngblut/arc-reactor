from __future__ import annotations

import uuid

from langchain.agents.middleware.types import AgentMiddleware, ToolCallRequest
from langchain_core.messages import ToolMessage


class LargeOutputMiddleware(AgentMiddleware):
    """Offload large tool results to agent state and replace with references."""

    def __init__(self, max_chars: int = 20000) -> None:
        self.max_chars = max_chars

    def wrap_tool_call(self, request: ToolCallRequest, handler):  # type: ignore[override]
        result = handler(request)
        content = getattr(result, "content", None)
        if not isinstance(content, str):
            return result

        if len(content) <= self.max_chars:
            return result

        runtime = request.runtime
        config = getattr(runtime, "config", None)
        if not isinstance(config, dict):
            return result

        configurable = config.setdefault("configurable", {})
        if not isinstance(configurable, dict):
            return result

        outputs = configurable.setdefault("tool_outputs", {})
        if not isinstance(outputs, dict):
            outputs = {}
            configurable["tool_outputs"] = outputs

        output_id = f"{request.tool_call.get('name', 'tool')}-{uuid.uuid4().hex[:8]}"
        outputs[output_id] = {
            "tool": request.tool_call.get("name"),
            "content": content,
        }

        return ToolMessage(
            content=(
                "Tool output was large and stored in agent state. "
                f"Reference: {output_id}"
            ),
            tool_call_id=request.tool_call.get("id"),
        )

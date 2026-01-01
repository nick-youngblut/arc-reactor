from __future__ import annotations

from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, AgentState
from langchain_core.messages import SystemMessage


class SummarizationMiddleware(AgentMiddleware):
    """Summarize older messages when context usage exceeds threshold."""

    def __init__(self, trigger_ratio: float = 0.85, max_chars: int = 200000) -> None:
        self.trigger_ratio = trigger_ratio
        self.max_chars = max_chars

    def after_model(self, state: AgentState, runtime: Any) -> dict[str, Any] | None:
        messages = list(state.get("messages", []))
        if len(messages) < 10:
            return None

        total_chars = sum(len(str(getattr(msg, "content", ""))) for msg in messages)
        if total_chars < int(self.max_chars * self.trigger_ratio):
            return None

        summary_parts = []
        for msg in messages[:4]:
            content = getattr(msg, "content", "")
            summary_parts.append(str(content)[:200])
        for msg in messages[-3:]:
            content = getattr(msg, "content", "")
            summary_parts.append(str(content)[:200])

        summary_text = "\n".join(summary_parts)
        summary_message = SystemMessage(
            content=(
                "Conversation summary (auto-generated):\n"
                f"{summary_text}\n"
                "Earlier details were truncated to preserve context."
            )
        )

        return {"messages": [summary_message] + messages[-5:]}

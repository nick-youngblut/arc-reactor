from __future__ import annotations

from typing import Any, Callable

from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.agents.middleware.human_in_the_loop import InterruptOnConfig

HITL_REQUIRED_TOOLS = {
    "submit_run",
    "cancel_run",
    "delete_file",
    "clear_samplesheet",
}


def _format_hitl_description(tool_call: dict[str, Any], *_args) -> str:
    args = tool_call.get("args", {})
    arg_preview = ", ".join(f"{key}={value}" for key, value in args.items())
    return (
        "Approval required before executing this action:\n"
        f"Tool: {tool_call.get('name')}\n"
        f"Parameters: {arg_preview or 'none'}\n"
        "Expected impact: This action will modify run state or storage.\n"
        "Respond with approve or reject."
    )


def build_hitl_middleware() -> HumanInTheLoopMiddleware:
    interrupt_on: dict[str, InterruptOnConfig] = {}
    for tool_name in HITL_REQUIRED_TOOLS:
        interrupt_on[tool_name] = InterruptOnConfig(
            allowed_decisions=["approve", "reject"],
            description=_format_hitl_description,
        )
    return HumanInTheLoopMiddleware(interrupt_on=interrupt_on)


def build_hitl_interrupt_map(
    description_builder: Callable[[dict[str, Any], Any, Any], str] | None = None,
) -> dict[str, dict[str, Any]]:
    description = description_builder or _format_hitl_description
    return {
        tool_name: {
            "allowed_decisions": ["approve", "reject"],
            "description": description,
        }
        for tool_name in HITL_REQUIRED_TOOLS
    }

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Iterable

logger = logging.getLogger(__name__)


def _safe_serialize(obj: Any) -> Any:
    """Recursively convert non-serializable objects to strings."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(item) for item in obj]
    # For non-serializable objects, convert to string representation
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def _format_chunk(code: str, payload: Any) -> str:
    safe_payload = _safe_serialize(payload)
    return f"{code}:{json.dumps(safe_payload)}\n"


def _extract_text_blocks(chunk: Any) -> Iterable[str]:
    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        yield content
        return

    blocks = getattr(chunk, "content_blocks", None)
    if isinstance(blocks, list):
        for block in blocks:
            if block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    yield text
        return

    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    yield text


def _filter_runtime_args(args: Any) -> Any:
    """Filter out 'runtime' key from tool args - it's not JSON serializable."""
    if isinstance(args, dict):
        return {k: v for k, v in args.items() if k != "runtime"}
    return args


def _extract_tool_result(output: Any) -> Any:
    """Extract the content from a ToolMessage or return as-is."""
    if hasattr(output, "content"):
        return output.content
    return output


def _tool_start_payload(event: dict[str, Any]) -> dict[str, Any]:
    """Build tool start payload from event (not just data)."""
    data = event.get("data", {})
    raw_args = data.get("input") or data.get("args") or {}
    args = _filter_runtime_args(raw_args)
    return {
        "toolCallId": event.get("run_id") or "unknown",
        "toolName": event.get("name") or "unknown_tool",
        "args": args,
    }


def _tool_end_payload(event: dict[str, Any]) -> dict[str, Any]:
    """Build tool end payload from event (not just data)."""
    data = event.get("data", {})
    output = data.get("output")
    return {
        "toolCallId": event.get("run_id") or "unknown",
        "result": _extract_tool_result(output),
    }


async def stream_agent_response(
    agent: Any,
    messages: list[Any],
    *,
    config: dict[str, Any] | None = None,
) -> AsyncIterator[str]:
    try:
        async for event in agent.astream_events(
            {"messages": messages},
            version="v2",
            config=config,
        ):
            event_type = event.get("event")
            data = event.get("data", {})
            logger.debug("Event: %s", event_type)
            if event_type == "on_chat_model_stream":
                chunk = data.get("chunk")
                if chunk is None:
                    continue
                for text in _extract_text_blocks(chunk):
                    if text:
                        yield _format_chunk("0", text)
            elif event_type == "on_tool_start":
                yield _format_chunk("9", _tool_start_payload(event))
            elif event_type == "on_tool_end":
                yield _format_chunk("a", _tool_end_payload(event))
    except Exception as exc:
        logger.exception("Error during agent streaming: %s", exc)
        yield _format_chunk("3", str(exc))
        yield _format_chunk("d", {"finishReason": "error"})
        return

    yield _format_chunk("d", {"finishReason": "stop"})

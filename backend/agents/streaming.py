from __future__ import annotations

import json
from typing import Any, AsyncIterator, Iterable


def _format_chunk(code: str, payload: Any) -> str:
    return f"{code}:{json.dumps(payload)}\n"


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


def _tool_call_id(data: dict[str, Any]) -> str:
    return (
        str(data.get("run_id"))
        or str(data.get("tool_call_id"))
        or str(data.get("id"))
        or str(data.get("name"))
    )


def _tool_start_payload(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "toolCallId": _tool_call_id(data),
        "toolName": data.get("name"),
        "args": data.get("input") or data.get("args") or {},
    }


def _tool_end_payload(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "toolCallId": _tool_call_id(data),
        "result": data.get("output"),
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
            if event_type == "on_chat_model_stream":
                chunk = data.get("chunk")
                if chunk is None:
                    continue
                for text in _extract_text_blocks(chunk):
                    if text:
                        yield _format_chunk("0", text)
            elif event_type == "on_tool_start":
                yield _format_chunk("9", _tool_start_payload(data))
            elif event_type == "on_tool_end":
                yield _format_chunk("a", _tool_end_payload(data))
    except Exception as exc:
        yield _format_chunk("3", str(exc))
        yield _format_chunk("d", {"finishReason": "error"})
        return

    yield _format_chunk("d", {"finishReason": "stop"})

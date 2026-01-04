from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Iterable

logger = logging.getLogger(__name__)

FILE_UPDATE_CODE = "b"


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


def _content_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _format_file_update(
    *,
    filename: str,
    content: str,
    metadata: dict[str, Any],
) -> dict[str, Any] | None:
    file_type_map = {
        "samplesheet.csv": "samplesheet",
        "nextflow.config": "config",
    }
    file_type = file_type_map.get(filename)
    if not file_type:
        logger.warning("Unknown generated file type for %s", filename)
        return None

    event_metadata = dict(metadata)
    if "sample_count" in event_metadata and "sampleCount" not in event_metadata:
        event_metadata["sampleCount"] = event_metadata["sample_count"]

    event_metadata["modifiedBy"] = "agent"
    event_metadata["modifiedAt"] = datetime.now(timezone.utc).isoformat()

    return {
        "fileType": file_type,
        "content": content,
        "metadata": event_metadata,
    }


def _extract_file_updates(
    config: dict[str, Any] | None,
    emitted_hashes: dict[str, str],
) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    try:
        if not isinstance(config, dict):
            logger.warning("Streaming config is not a dict; skipping file updates.")
            return updates
        configurable = config.get("configurable")
        if not isinstance(configurable, dict):
            logger.warning("Streaming config missing configurable dict; skipping file updates.")
            return updates
        generated = configurable.get("generated_files")
        if not isinstance(generated, dict):
            logger.warning("Streaming config missing generated_files dict; skipping file updates.")
            return updates

        for filename, file_data in generated.items():
            if not isinstance(file_data, dict):
                logger.warning("Invalid generated file entry for %s", filename)
                continue
            content = file_data.get("content")
            if content is None:
                logger.warning("Generated file %s missing content", filename)
                continue
            if not isinstance(content, str):
                try:
                    content = str(content)
                except Exception:
                    logger.warning("Generated file %s content is not serializable", filename)
                    continue

            content_hash = _content_hash(content)
            if emitted_hashes.get(filename) == content_hash:
                continue
            emitted_hashes[filename] = content_hash

            metadata = file_data.get("metadata", {})
            if metadata is None:
                metadata = {}
            if not isinstance(metadata, dict):
                logger.warning("Generated file %s metadata is invalid", filename)
                metadata = {}

            update = _format_file_update(filename=filename, content=content, metadata=metadata)
            if update:
                updates.append(update)
    except Exception as exc:
        logger.exception("Failed to extract file updates: %s", exc)

    return updates


async def stream_agent_response(
    agent: Any,
    messages: list[Any],
    *,
    config: dict[str, Any] | None = None,
) -> AsyncIterator[str]:
    emitted_hashes: dict[str, str] = {}
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
                for update in _extract_file_updates(config, emitted_hashes):
                    yield _format_chunk(FILE_UPDATE_CODE, update)
    except Exception as exc:
        logger.exception("Error during agent streaming: %s", exc)
        yield _format_chunk("3", str(exc))
        yield _format_chunk("d", {"finishReason": "error"})
        return

    yield _format_chunk("d", {"finishReason": "stop"})

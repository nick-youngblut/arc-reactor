from __future__ import annotations

import json

import pytest

from backend.agents import streaming


class _FakeAgent:
    def __init__(self, events):
        self._events = events

    async def astream_events(self, *_args, **_kwargs):
        for event in self._events:
            yield event


@pytest.mark.asyncio
async def test_workspace_signal_emitted_for_generate_samplesheet() -> None:
    events = [
        {
            "event": "on_tool_end",
            "name": "generate_samplesheet",
            "run_id": "tool-1",
            "data": {"output": "Generated samplesheet..."},
        }
    ]
    agent = _FakeAgent(events)

    chunks = [chunk async for chunk in streaming.stream_agent_response(agent, [])]
    signal_chunks = [c for c in chunks if c.startswith("w:")]

    assert len(signal_chunks) == 1
    payload = json.loads(signal_chunks[0][2:])
    assert payload == {"refresh": "workspace"}


@pytest.mark.asyncio
async def test_workspace_signal_emitted_for_generate_config() -> None:
    events = [
        {
            "event": "on_tool_end",
            "name": "generate_config",
            "run_id": "tool-1",
            "data": {"output": "Generated config..."},
        }
    ]
    agent = _FakeAgent(events)

    chunks = [chunk async for chunk in streaming.stream_agent_response(agent, [])]
    signal_chunks = [c for c in chunks if c.startswith("w:")]

    assert len(signal_chunks) == 1


@pytest.mark.asyncio
async def test_workspace_signal_emitted_for_update_samplesheet() -> None:
    events = [
        {
            "event": "on_tool_end",
            "name": "update_samplesheet",
            "run_id": "tool-1",
            "data": {"output": "Samplesheet updated successfully."},
        }
    ]
    agent = _FakeAgent(events)

    chunks = [chunk async for chunk in streaming.stream_agent_response(agent, [])]
    signal_chunks = [c for c in chunks if c.startswith("w:")]

    assert len(signal_chunks) == 1


@pytest.mark.asyncio
async def test_workspace_signal_emitted_for_update_config() -> None:
    events = [
        {
            "event": "on_tool_end",
            "name": "update_config",
            "run_id": "tool-1",
            "data": {"output": "Config updated successfully."},
        }
    ]
    agent = _FakeAgent(events)

    chunks = [chunk async for chunk in streaming.stream_agent_response(agent, [])]
    signal_chunks = [c for c in chunks if c.startswith("w:")]

    assert len(signal_chunks) == 1


@pytest.mark.asyncio
async def test_no_workspace_signal_for_other_tools() -> None:
    events = [
        {
            "event": "on_tool_end",
            "name": "search_ngs_runs",
            "run_id": "tool-1",
            "data": {"output": "Found 5 runs..."},
        }
    ]
    agent = _FakeAgent(events)

    chunks = [chunk async for chunk in streaming.stream_agent_response(agent, [])]
    signal_chunks = [c for c in chunks if c.startswith("w:")]

    assert len(signal_chunks) == 0


@pytest.mark.asyncio
async def test_tool_end_still_emits_a_event() -> None:
    """Verify that 'a' (tool_end) event is still emitted alongside 'w' signal."""
    events = [
        {
            "event": "on_tool_end",
            "name": "generate_samplesheet",
            "run_id": "tool-1",
            "data": {"output": "ok"},
        }
    ]
    agent = _FakeAgent(events)

    chunks = [chunk async for chunk in streaming.stream_agent_response(agent, [])]
    a_chunks = [c for c in chunks if c.startswith("a:")]
    w_chunks = [c for c in chunks if c.startswith("w:")]

    assert len(a_chunks) == 1
    assert len(w_chunks) == 1

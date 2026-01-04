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
async def test_stream_agent_response_emits_file_update() -> None:
    events = [
        {
            "event": "on_tool_end",
            "run_id": "tool-1",
            "data": {"output": "ok"},
        }
    ]
    agent = _FakeAgent(events)
    config = {
        "configurable": {
            "generated_files": {
                "samplesheet.csv": {
                    "content": "col1,col2\n1,2",
                    "metadata": {"pipeline": "nf-core/scrnaseq", "sample_count": 1},
                }
            }
        }
    }

    chunks = [chunk async for chunk in streaming.stream_agent_response(agent, [], config=config)]
    file_chunks = [chunk for chunk in chunks if chunk.startswith("b:")]
    assert len(file_chunks) == 1

    payload = json.loads(file_chunks[0][2:])
    assert payload["fileType"] == "samplesheet"
    assert payload["content"].startswith("col1,col2")
    assert payload["metadata"]["modifiedBy"] == "agent"
    assert "modifiedAt" in payload["metadata"]
    assert payload["metadata"]["sampleCount"] == 1


def test_extract_file_updates_handles_malformed_data() -> None:
    emitted: dict[str, str] = {}
    updates = streaming._extract_file_updates(
        {"configurable": {"generated_files": {"samplesheet.csv": "bad"}}},
        emitted,
    )
    assert updates == []


def test_extract_file_updates_emits_on_content_change() -> None:
    emitted: dict[str, str] = {}
    config = {
        "configurable": {
            "generated_files": {
                "nextflow.config": {"content": "alpha", "metadata": {"pipeline": "x"}}
            }
        }
    }

    first = streaming._extract_file_updates(config, emitted)
    assert len(first) == 1

    second = streaming._extract_file_updates(config, emitted)
    assert second == []

    config["configurable"]["generated_files"]["nextflow.config"]["content"] = "beta"
    third = streaming._extract_file_updates(config, emitted)
    assert len(third) == 1

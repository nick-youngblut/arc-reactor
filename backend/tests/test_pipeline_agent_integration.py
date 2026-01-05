from __future__ import annotations

import types

from backend.agents.pipeline_agent import PipelineAgent
from backend.agents.prompts import ORCHESTRATOR_SYSTEM_PROMPT


def _make_settings():
    return types.SimpleNamespace(agent={})


def test_pipeline_agent_create_builds_deep_agent(monkeypatch):
    captured = {}

    def fake_create_deep_agent(**kwargs):
        captured.update(kwargs)
        return "agent"

    monkeypatch.setattr("backend.agents.pipeline_agent._IMPORT_ERROR", None)
    monkeypatch.setattr("backend.agents.pipeline_agent.create_deep_agent", fake_create_deep_agent)
    monkeypatch.setattr("backend.agents.pipeline_agent.get_agent_config", lambda *_args, **_kwargs: object())
    monkeypatch.setattr("backend.agents.pipeline_agent.create_agent_model", lambda _config: "model")
    monkeypatch.setattr("backend.agents.pipeline_agent.get_orchestrator_tools", lambda: ["tool-a"])
    monkeypatch.setattr(
        "backend.agents.pipeline_agent.create_benchling_expert", lambda _settings: {"name": "benchling"}
    )
    monkeypatch.setattr(
        "backend.agents.pipeline_agent.create_config_expert", lambda _settings: {"name": "config"}
    )
    monkeypatch.setattr(
        "backend.agents.pipeline_agent.create_execution_expert", lambda _settings: {"name": "execution"}
    )
    monkeypatch.setattr(
        "backend.agents.pipeline_agent.build_hitl_interrupt_map", lambda: {"submit_run": True}
    )

    agent = PipelineAgent.create(_make_settings(), checkpointer="checkpointer")

    assert agent.agent == "agent"
    assert agent.model == "model"
    assert agent.tools == ["tool-a"]
    assert captured["tools"] == ["tool-a"]
    assert captured["subagents"] == [
        {"name": "benchling"},
        {"name": "config"},
        {"name": "execution"},
    ]
    assert captured["system_prompt"] == ORCHESTRATOR_SYSTEM_PROMPT.strip()
    assert captured["checkpointer"] == "checkpointer"
    assert captured["interrupt_on"] == {"submit_run": True}

from __future__ import annotations

import types

from backend.agents.subagents import (
    create_benchling_expert,
    create_config_expert,
    create_execution_expert,
)


def _make_settings():
    return types.SimpleNamespace(agent={})


def test_benchling_expert_factory_applies_model_config(monkeypatch):
    captured = {}

    def fake_get_agent_config(_settings, agent_name):
        captured["agent_name"] = agent_name
        return object()

    def fake_create_agent_model(config):
        captured["config"] = config
        return "model"

    monkeypatch.setattr(
        "backend.agents.subagents.benchling_expert.get_agent_config", fake_get_agent_config
    )
    monkeypatch.setattr(
        "backend.agents.subagents.benchling_expert.create_agent_model", fake_create_agent_model
    )

    result = create_benchling_expert(_make_settings())

    assert captured["agent_name"] == "benchling_expert"
    assert result["model"] == "model"
    assert result["name"] == "benchling_expert"
    assert any(tool.name == "search_ngs_runs" for tool in result["tools"])


def test_config_expert_factory_applies_model_config(monkeypatch):
    captured = {}

    def fake_get_agent_config(_settings, agent_name):
        captured["agent_name"] = agent_name
        return object()

    def fake_create_agent_model(config):
        captured["config"] = config
        return "model"

    monkeypatch.setattr(
        "backend.agents.subagents.config_expert.get_agent_config", fake_get_agent_config
    )
    monkeypatch.setattr(
        "backend.agents.subagents.config_expert.create_agent_model", fake_create_agent_model
    )

    result = create_config_expert(_make_settings())

    assert captured["agent_name"] == "config_expert"
    assert result["model"] == "model"
    assert result["name"] == "config_expert"
    assert any(tool.name == "generate_config" for tool in result["tools"])


def test_execution_expert_factory_includes_hitl(monkeypatch):
    captured = {}

    def fake_get_agent_config(_settings, agent_name):
        captured["agent_name"] = agent_name
        return object()

    def fake_create_agent_model(config):
        captured["config"] = config
        return "model"

    def fake_interrupt_map():
        return {"submit_run": True}

    monkeypatch.setattr(
        "backend.agents.subagents.execution_expert.get_agent_config", fake_get_agent_config
    )
    monkeypatch.setattr(
        "backend.agents.subagents.execution_expert.create_agent_model", fake_create_agent_model
    )
    monkeypatch.setattr(
        "backend.agents.subagents.execution_expert.build_hitl_interrupt_map", fake_interrupt_map
    )

    result = create_execution_expert(_make_settings())

    assert captured["agent_name"] == "execution_expert"
    assert result["model"] == "model"
    assert result["name"] == "execution_expert"
    assert result["interrupt_on"] == {"submit_run": True}
    assert any(tool.name == "submit_run" for tool in result["tools"])

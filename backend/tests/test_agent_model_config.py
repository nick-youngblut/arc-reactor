import types

from backend.agents.model import AgentModelConfig, create_agent_model, get_agent_config


def _make_settings(**values):
    return types.SimpleNamespace(**values)


def test_get_agent_config_uses_base_settings():
    settings = _make_settings(
        gemini_model="gemini-3-flash-preview",
        gemini_thinking_level="medium",
    )

    config = get_agent_config(settings, "orchestrator")

    assert config.model == "google_genai:gemini-3-flash-preview"
    assert config.thinking_level == "medium"
    assert config.temperature == 1.0
    assert config.max_output_tokens == 8192


def test_get_agent_config_applies_overrides():
    settings = _make_settings(
        gemini_model="gemini-3-flash-preview",
        gemini_thinking_level="low",
        agent={
            "orchestrator": {
                "model": "google_genai:gemini-3-pro",
                "thinking_level": "high",
                "temperature": 0.2,
                "max_output_tokens": 1024,
            },
            "subagents": {
                "benchling_expert": {
                    "thinking_level": "medium",
                }
            },
        },
    )

    orchestrator_config = get_agent_config(settings, "orchestrator")
    benchling_config = get_agent_config(settings, "benchling_expert")

    assert orchestrator_config.model == "google_genai:gemini-3-pro"
    assert orchestrator_config.thinking_level == "high"
    assert orchestrator_config.temperature == 0.2
    assert orchestrator_config.max_output_tokens == 1024

    assert benchling_config.model == "google_genai:gemini-3-flash-preview"
    assert benchling_config.thinking_level == "medium"


def test_create_agent_model_uses_config(monkeypatch):
    captured = {}

    def fake_init_chat_model(model, **kwargs):
        captured["model"] = model
        captured.update(kwargs)
        return {"model": model, **kwargs}

    monkeypatch.setattr("backend.agents.model.init_chat_model", fake_init_chat_model)

    config = AgentModelConfig(
        model="google_genai:test-model",
        temperature=0.7,
        thinking_level="low",
        max_output_tokens=2048,
    )

    result = create_agent_model(config, streaming=False)

    assert result["model"] == "google_genai:test-model"
    assert captured["temperature"] == 0.7
    assert captured["max_output_tokens"] == 2048
    assert captured["thinking_level"] == "low"
    assert captured["streaming"] is False

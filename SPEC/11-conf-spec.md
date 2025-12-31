# Arc Reactor - Configuration Specification

This document is the single source of truth for shared configuration values. All
specifications and implementation examples must reference the values here.

## AI Model Configuration (Google Gemini)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Model | `gemini-3-flash-preview` | Google Gemini 3 Flash via google_genai provider |
| LangChain Format | `google_genai:gemini-3-flash-preview` | Use with `init_chat_model()` |
| Temperature | 1.0 | Required for Gemini models with thinking enabled |
| Max output tokens | 8192 | Allow longer, structured responses |
| Thinking Level | `low` | Default thinking level for balanced speed/quality |

### Thinking Level Options

| Level | Use Case | Latency |
|-------|----------|---------|
| `minimal` | Simple queries, fast responses | Lowest |
| `low` | Standard agent interactions (recommended default) | Low |
| `medium` | Complex reasoning, multi-step tool use | Medium |
| `high` | Deep analysis, research tasks | Highest |

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI API key (Gemini Developer API) | Yes* |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID (for Vertex AI) | Yes* |

*One of these is required depending on the deployment mode.

## Usage Guidance

- Reference this document from other specs instead of duplicating values.
- If a value changes, update it here and then update any examples that embed the values.

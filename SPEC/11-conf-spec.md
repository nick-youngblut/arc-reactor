# Arc Reactor - Configuration Specification

This document is the single source of truth for shared configuration values. All
specifications and implementation examples must reference the values here.

## AI Model Configuration (Google Gemini)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Model | `gemini-3-flash-preview` | Google Gemini 3 Flash |
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

> **Note:** Regardless of thinking level, reasoning blocks are **not displayed to users**.
> They are filtered during stream processing. See `04-frontend-spec.md` (ChatPanel section)
> for details on AI response element rendering.

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI API key (Gemini Developer API) | Yes |

## Benchling Configuration

Benchling configuration is sourced via `benchling-py`'s Dynaconf settings.

| Variable | Description | Required |
|----------|-------------|----------|
| `DYNACONF` | Benchling tenant selector (`test`, `dev`, `prod`) | Yes |
| `BENCHLING_TEST_API_KEY` | Benchling test API key | Yes (test/dev) |
| `BENCHLING_TEST_DATABASE_URI` | Benchling test DB URI | Yes (test/dev) |
| `BENCHLING_TEST_APP_CLIENT_ID` | Benchling test OAuth client ID | Yes (test/dev) |
| `BENCHLING_TEST_APP_CLIENT_SECRET` | Benchling test OAuth client secret | Yes (test/dev) |
| `BENCHLING_PROD_API_KEY` | Benchling prod API key | Yes (prod) |
| `BENCHLING_PROD_DATABASE_URI` | Benchling prod DB URI | Yes (prod) |
| `BENCHLING_PROD_APP_CLIENT_ID` | Benchling prod OAuth client ID | Yes (prod) |
| `BENCHLING_PROD_APP_CLIENT_SECRET` | Benchling prod OAuth client secret | Yes (prod) |

## Usage Guidance

- Reference this document from other specs instead of duplicating values.
- If a value changes, update it here and then update any examples that embed the values.

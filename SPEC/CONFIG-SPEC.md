# Arc Reactor - Configuration Specification

This document is the single source of truth for shared configuration values. All
specifications and implementation examples must reference the values here.

## AI Model Configuration (Anthropic)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Model | `claude-sonnet-4-5-20250929` | Use the canonical Anthropic model ID |
| Temperature | 0.1 | Low temperature for consistent tool use |
| Max completion tokens | 6000 | Allow longer, structured responses |

## Usage Guidance

- Reference this document from other specs instead of duplicating values.
- If a value changes, update it here and then update any examples that embed the values.

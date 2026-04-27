---
name: launch-1c-apps
description: Launch 1C applications in the local development environment. Use when the user asks to open a thin client, thick client, or configurator/designer, or when colloquial names must be mapped to `v8-runner` launch aliases.
---

# Launch 1C Apps

## Workflow

1. Read `references/aliases.md`.
2. Normalize the user request to one of: `thin-client`, `thick-client`, `designer`.
3. Use `v8-runner-workflow` to launch the matching 1C application with a supported alias from that row.
4. Report which alias succeeded.
5. If all supported aliases fail, return the exact tool error.

## Rules

- Use only aliases listed in `references/aliases.md`.
- Prefer the canonical alias first when it is available.
- Do not invent variants from memory.
- If the user asks for a test client, do not use this skill for launch. Use project-specific docs such as `docs/mcp-test-client/tasks/01-client-control.md`.

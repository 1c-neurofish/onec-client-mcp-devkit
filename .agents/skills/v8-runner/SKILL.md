---
name: v8-runner
description: Use when the user asks to initialize the local 1C test runner, build the project, run tests, launch 1C applications, or use `mcp__v8_runner__*` tools in this repository.
---

# V8 Runner

## Workflow

1. Read `/workspace/.agents/tools/onec-client-mcp-devkit.edt.yaml` when the task depends on local runner initialization.
2. Initialize the environment with:
   `/home/vscode/tools/v8-test-runner --config /workspace/.agents/tools/onec-client-mcp-devkit.edt.yaml init`
3. Prefer the `mcp__v8_runner__*` tools for build, syntax checks, test runs, config dump, and app launch.
4. Use `/workspace/.agents/tools/v8-runner.yml` as the project runner definition when the task depends on source-set or tool configuration.
5. If a runner command or MCP tool fails, report the exact error and separate initialization problems from test or build failures.

## Rules

- Use the exact init command above; do not invent alternate config paths.
- Re-run initialization when the environment looks uninitialized or the runner reports setup issues.
- Keep follow-up actions scoped to the user's request; do not run unrelated checks by default.

---
name: v8-runner
description: Use when the user asks to initialize the local 1C test runner through CLI, or after initialization to build the project, run tests, launch 1C applications, or use the `v8-test-runner` workflow in this repository.
---

# V8 Runner

## Workflow

1. Read `.agents/tools/onec-client-mcp-devkit.edt.yaml` when the task depends on local runner initialization.
2. Initialize the environment through CLI with:
   `/home/vscode/tools/v8-test-runner --config .agents/tools/onec-client-mcp-devkit.edt.yaml init`
3. After successful CLI initialization, use the `v8-test-runner` workflow for build, syntax checks, test runs, config dump, and app launch.
4. Use `.agents/tools/v8-runner.yml` as the project runner definition when the task depends on source-set or tool configuration.
5. If a runner command fails, report the exact error and separate initialization problems from test or build failures.

## Rules

- Use the exact init command above; do not invent alternate config paths.
- Do not treat initialization as an MCP action; `init` must be executed through CLI.
- `v8-test-runner` does not support parallel execution; serialize init, build, syntax-check, test, dump, and app-launch actions within this workspace.
- Re-run initialization when the environment looks uninitialized or the runner reports setup issues.
- Keep follow-up actions scoped to the user's request; do not run unrelated checks by default.

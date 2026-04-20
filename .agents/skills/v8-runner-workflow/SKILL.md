---
name: v8-runner-workflow
description: "Use when Codex needs to operate v8-runner on local 1C projects: create or repair v8project.yaml, initialize a file infobase or EDT workspace, build Designer or EDT sources, run syntax checks, run YaXUnit or Vanessa Automation tests, dump changes back to Git sources, launch 1C clients, use v8-runner MCP tools, diagnose setup/build failures separately from test failures, or choose safe command sequences for 1C development workflows."
---

# v8-runner Workflow

Use this skill to run `v8-runner` as an automation layer around local 1C development projects.

## Command Form

Resolve the executable before the first run:

1. If the user supplied an absolute `v8-runner` path, use that path consistently.
2. Otherwise prefer `command -v v8-runner`.
3. When working inside the `v8-runner` source repository and no installed binary is available, use `cargo run --`.
4. If no runner is available, stop and report a local environment issue; do not fall back to raw `1cv8` commands.

```bash
v8-runner --config v8project.yaml --output json build
cargo run -- --config v8project.yaml --output json build
```

Use `--output json` when another tool, script, or final answer needs structured results. Use text output for direct human diagnostics.

## First Pass

1. Check whether `v8project.yaml` exists.
2. If it exists, inspect it before mutating the infobase. Treat `.agents/tools/*.yml` and similar files as hints, not as the active config unless the user selected them.
3. If it is missing, run `v8-runner config init` from the 1C project root.
4. Inspect the generated config before running mutating commands.
5. Run `v8-runner init` when the file infobase or EDT workspace needs to be created.
6. Run the narrowest validation command that answers the user's goal.

Useful bootstrap commands:

```bash
v8-runner config init
v8-runner config init --connection "File=build/ib"
v8-runner config init --format edt
v8-runner config init --builder IBCMD
v8-runner init
```

## Daily Git Workflow

Use these sequences for common 1C project tasks:

- Apply source changes to the infobase:

```bash
v8-runner build
```

- Recover after branch switch, rebase, large moves, or suspicious incremental state:

```bash
v8-runner build --full-rebuild
```

- Quick pre-commit validation for Designer sources:

```bash
v8-runner build
v8-runner syntax designer-modules --server --thin-client
```

- Quick pre-commit validation for EDT sources:

```bash
v8-runner build
v8-runner syntax edt
```

- Stronger pre-push validation:

```bash
v8-runner test yaxunit all
```

- Targeted YaXUnit run:

```bash
v8-runner test yaxunit module <MODULE_NAME>
```

- Vanessa Automation run using the configured profile:

```bash
v8-runner test va
```

- Bring manual Designer changes back into Git-visible files:

```bash
v8-runner dump --mode incremental
git diff
```

- Dump specific objects when Designer backend supports it:

```bash
v8-runner dump --mode partial --object <TYPE:NAME>
```

## Command Selection

- Use `build` before manual checks when Git files changed and the infobase may be stale.
- Use `test` directly when behavior matters; it already performs `build` first.
- Use `syntax designer-modules` for fast module-level checks on Designer projects.
- Use `syntax designer-config` for broader Designer configuration checks.
- Use `syntax edt` for EDT projects.
- Use `dump` only when the desired source of truth is the current infobase state.
- Use `extensions` when extension properties need to be synchronized without a broader recovery step.
- Use `launch designer`, `launch thin`, `launch thick`, or `launch ordinary` instead of manually assembling `1cv8` command lines.

## Format And Backend Rules

- `format=DESIGNER`, `builder=DESIGNER`: supports init, build, extensions, dump, Designer syntax checks, tests, make/load/artifact workflows if configured.
- `format=DESIGNER`, `builder=IBCMD`: supports init, build, extensions, dump with a limited backend and only file infobases.
- `format=EDT`, `builder=DESIGNER`: supports init, build through EDT export to Designer files, EDT syntax checks, extensions, and tests.
- `syntax designer-config` and `syntax designer-modules` require Designer format with Designer backend.
- `syntax edt` requires EDT format with Designer backend.
- `dump --mode partial` with IBCMD degrades to incremental dump and should be called out in user-facing summaries.

## Config Checks

When diagnosing setup issues, inspect these fields first:

- `basePath`: root of 1C source files.
- `workPath`: generated state, temp files, and workspace location.
- `format`: `DESIGNER` or `EDT`.
- `builder`: `DESIGNER` or `IBCMD`.
- `connection`: usually `File=build/ib` for local automation.
- `source-set`: ordered configuration and extension sources.
- `tools.platform.path` or `tools.platform.version`: 1C platform discovery hints.
- `tools.edt_cli.path`, `version`, and `interactive-mode`: EDT CLI discovery and execution mode.
- `tests.yaxunit` and `tests.va`: test runner configuration.

For each `source-set` entry:

- Check that `path` exists and points at the intended source root.
- Check that `type`/`purpose` uses the schema accepted by the selected `v8-runner` version (`type` in `v8project.yaml`, `purpose` in some legacy project configs).
- For extensions, make sure `name` matches the actual extension metadata name, not merely the folder name. In EDT sources this is the first `<name>` in `src/Configuration/Configuration.mdo`. A mismatch can make incremental builds try to load the same extension twice.

## MCP Usage

Use MCP when the task is to expose or consume `v8-runner` through an assistant client:

```bash
v8-runner mcp serve stdio
v8-runner mcp serve http
```

Map CLI intents to tools:

- `build` -> `build_project`
- `test yaxunit all` -> `run_all_tests`
- `test yaxunit module <NAME>` -> `run_module_tests`
- `dump` -> `dump_config`
- `launch` -> `launch_app`
- `syntax edt` -> `check_syntax_edt`
- `syntax designer-config` -> `check_syntax_designer_config`
- `syntax designer-modules` -> `check_syntax_designer_modules`

MCP request fields use `camelCase`.

## Troubleshooting

- If `test yaxunit ...` fails before a JUnit report is parsed, treat it as setup/build failure first. Inspect the runner diagnostic, `build/logs/platform/*.log`, and the temporary run directory named in the output.
- If platform output says `An extension with this name already exists!`, compare `source-set[].name` with each extension metadata name and with existing hash-storage/log names under `workPath`. Fix the contract in `v8project.yaml` rather than deleting the infobase unless the user explicitly asks for reset.
- If a command returns `unexpected argument found`, read `v8-runner <command> --help` and retry with the displayed syntax before changing project files.
- If tests pass but diagnostics contain expected negative-case errors, report the test summary first and mention that diagnostics came from asserted failure scenarios.

## Guardrails

- Do not delete or recreate an infobase, workspace, temp directory, or generated state unless the user explicitly asks or the command itself is the documented recovery path.
- Do not invent raw `1cv8`, `ibcmd`, or `1cedtcli` flags; prefer the `v8-runner` command surface.
- Check `git status` before `dump` if the result may overwrite or mix with existing source changes.
- Preserve failed test artifacts under `workPath/temp/<runner-id>/runs/<run-id>/` for diagnosis instead of cleaning them immediately.
- Report missing local 1C utilities as environment/setup issues, not as project source failures.
- Keep final answers concrete: command run, result, relevant artifact path, and any follow-up command.

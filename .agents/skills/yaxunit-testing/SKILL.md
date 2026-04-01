---
name: yaxunit-testing
description: Run, scope, and interpret YAxUnit tests for 1C projects. Use when selecting or executing tests located in `./tests/src/CommonModules/`, especially modules prefixed with `ОМ_`, or when verifying changes against YAxUnit test suites.
---

# YAxUnit Testing

## Overview
Use this skill to locate relevant YAxUnit test modules, understand test coverage, and run or scope tests through the `v8-test-runner` workflow first.

## Workflow
1. Identify relevant test modules.
- Test modules live in `./tests/src/CommonModules/`.
- Test module names start with `ОМ_` and usually mirror the tested module name, e.g. `ОМ_ЮТКоллекции` for `ЮТКоллекции`.
- Use `rg --files -g 'Module.bsl' ./tests/src/CommonModules` and filter by `ОМ_`.

2. Inspect the module’s `ИсполняемыеСценарии()`.
- This procedure enumerates tests via `ЮТТесты.ДобавитьТест("ИмяМетода")`.
- The listed methods are the test entry points to focus on.

3. Run tests.
- Primary path: use `v8-test-runner` via the `$v8-runner` skill for module-scoped or full-suite runs.
- If the infobase may be stale after source changes, rebuild through the `v8-test-runner` workflow before rerunning tests.
- Do not run YAxUnit jobs in parallel: `v8-test-runner` does not support parallel execution, and concurrent runs can interfere with the shared infobase and test artifacts.
- Use manual CLI launch with `/C RunUnitTests=<path to config>` only if the `v8-test-runner` workflow is unavailable.
- Ensure the YAxUnit extension has **safe mode** and **dangerous action protection** disabled as required by YAxUnit docs.

4. Report results.
- If tests are not run, state why and list the relevant modules and methods identified.
- If `v8-test-runner` fails before producing a JUnit report, inspect the runner output and log paths and report the infrastructure cause separately from test failures.

## Resources
- `references/yaxunit-tests.md` for paths, naming conventions, and run documentation pointers.

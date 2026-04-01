# YAxUnit Test Sources and Run Pointers

## Test locations
- Test modules: `./tests/src/CommonModules/`
- Test modules are named with prefix `ОМ_` (e.g., `ОМ_ЮТКоллекции`).

## Naming convention
- The test module name usually mirrors the tested module name with `ОМ_` prefix.
- Use this mapping to select tests when a production module changes.

## Run documentation
- Primary path in this workspace: run tests via the `v8-test-runner` workflow from the `$v8-runner` skill.
- Rebuild through the `v8-test-runner` workflow before rerunning tests if source changes have not been built yet.
- YAxUnit run guide: `https://bia-technologies.github.io/yaxunit/docs/getting-started/run/configuration`
- Do not run tests in parallel: `v8-test-runner` does not support parallel execution, and concurrent runs can interfere with the shared infobase and test artifacts.
- Manual fallback: launch 1C with `RunUnitTests` and a config file only when the `v8-test-runner` workflow is unavailable.
- EDT plugin supports run from module and command palette.
- The YAxUnit extension requires safe mode and dangerous action protection to be disabled for test runs.

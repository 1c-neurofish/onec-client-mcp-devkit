# 1C App Launch Aliases

These aliases are supported by the `v8-runner` launch workflow and may also appear in user requests.

| Normalized kind | Supported aliases |
| --- | --- |
| `thin-client` | `thin-client`, `тонкий клиент`, `тонкий`, `thin client`, `thin`, `tc` |
| `thick-client` | `thick-client`, `толстый клиент`, `толстый`, `thick client`, `thick` |
| `designer` | `designer`, `конфигуратор`, `configurator` |

## Notes

- Prefer the first alias in each row as the canonical form.
- If all supported aliases fail, return the exact error and do not claim a launch succeeded.
- This file does not cover test-client launch.

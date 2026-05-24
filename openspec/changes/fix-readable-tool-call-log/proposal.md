## Why

Issue #13 reports that the MCP log file is unreadable when the user expects to see which tools the LLM called, which parameters were passed, and what each tool returned. The current debug log records transport events and response send status, but it does not provide a stable, human-readable tool-call trace for diagnosis.

## What Changes

- Add readable diagnostic log entries for `MCP_TOOL_CALL` execution at debug level.
- Include the tool name, request id, execution mode, task id when present, input arguments, and final response or error payload.
- Keep log output UTF-8 text and avoid binary or incorrectly encoded content in the configured log file.
- Keep MCP JSON-RPC envelopes, tool argument contracts, and response structures unchanged.
- Do not add hidden input normalization or compatibility adapters.

## Capabilities

### New Capabilities

- `readable-mcp-logging`: Human-readable MCP diagnostic logging for tool-call requests and responses.

### Modified Capabilities

- None.

## Impact

- Affected code: `exts/client-mcp/src/CommonModules/Мсп_ЛогированиеКлиент/Module.bsl`, `exts/client-mcp/src/CommonModules/Мсп_ТранспортСобытияКлиент/Module.bsl`, and focused tests under `tests/src/CommonModules/ОМ_ЛогированиеКлиент` or the transport test modules.
- Public API impact: none; logging remains controlled by existing `log`, `logLevel`, and `logFile` launch parameters/form settings.
- Dependencies: none.
- Documentation impact: update README or operational docs only if the implementation exposes a documented log format example.

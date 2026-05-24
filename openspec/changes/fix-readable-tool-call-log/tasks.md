## 1. Logging Helpers

- [x] 1.1 Add a safe helper in `Мсп_ЛогированиеКлиент` to serialize arbitrary structured payloads to readable JSON text for diagnostics.
- [x] 1.2 Ensure the helper degrades to an explicit serialization-error marker without interrupting request handling.
- [x] 1.3 Keep file logging append-only UTF-8 text through the existing `ФайлЛога` writer.

## 2. Tool-Call Trace Entries

- [x] 2.1 Log accepted `MCP_TOOL_CALL` requests with event type, request id, tool name, execution mode, optional task id, and serialized arguments.
- [x] 2.2 Log synchronous tool-call responses with request id, tool name, success/error status, and serialized JSON-RPC response payload.
- [x] 2.3 Log deferred tool-call acceptance with request id, tool name, and `deferred` status.
- [x] 2.4 Log task-based tool-call completion with task id, tool name, status, and serialized completion payload.

## 3. Tests

- [x] 3.1 Add focused tests for diagnostic payload serialization and UTF-8/Cyrillic file output behavior.
- [x] 3.2 Add focused transport/tool-call tests proving request and response trace entries include tool name, arguments, ids, and status.
- [x] 3.3 Add a regression check that logging does not change the JSON-RPC response sent to the MCP client.

## 4. Verification

- [x] 4.1 Run the relevant YAxUnit module(s) for logging and transport/tool-call behavior.
- [x] 4.2 Run repository formatting/diff checks without applying unrelated formatting cleanup.
- [x] 4.3 Review the final diff for minimal scope and confirm no public MCP API, provider contract, or input-normalization behavior changed.

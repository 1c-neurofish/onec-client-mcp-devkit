## Context

`client-mcp` owns transport, protocol routing, state, logging, and registries. Current logging is controlled by `Мсп_ЛогированиеКлиент` through `log`, `logLevel`, and `logFile`; messages are written to the user-facing message stream and optionally appended to a file as UTF-8 text.

`Мсп_ТранспортСобытияКлиент` already receives raw `MCP_TOOL_CALL` JSON, parses it, builds a `Мсп_ПротоколКлиент.НовыйВызовИнструмента(...)` contract, invokes the protocol layer, and sends the serialized response. Existing debug messages confirm event begin/end and response send status, but they do not log the tool name, arguments, or response body in a form that lets a user diagnose what the LLM asked the 1C client to do.

## Goals / Non-Goals

**Goals:**

- Produce readable debug log entries for tool-call request and response diagnostics.
- Preserve the existing logging configuration surface.
- Keep serialized argument and response payloads valid UTF-8 text.
- Keep the change narrow to `client-mcp` logging and transport event handling.
- Cover the behavior with focused tests around logging parameters and transport/tool-call trace formatting.

**Non-Goals:**

- Do not change MCP JSON-RPC response envelopes.
- Do not normalize incoming tool arguments beyond the current protocol validation.
- Do not add a new log storage subsystem, binary log format, or external dependency.
- Do not redact payload fields automatically without a separate explicit contract.
- Do not change resource, prompt, notification, or task-cancellation logging except where shared helper code is reused internally.

## Decisions

1. Keep tool-call trace logging behind the existing debug level.

   Rationale: the requested data can include full arguments and responses, so it belongs in diagnostics enabled explicitly through existing `log` and `logLevel=debug` controls. This avoids a new public option and keeps non-debug logs compact.

   Alternative considered: add a separate `toolTrace` setting. Rejected because issue #13 asks for the configured log to become useful, and adding a new option would widen the public configuration contract before the basic debug log is correct.

2. Serialize structured payloads with the existing JSON serializer before logging.

   Rationale: `Мсп_СериализацияКлиент.Сериализовать` is already the local JSON writer used for MCP responses. Reusing it keeps logged arguments and responses close to the wire shape and avoids ad hoc string formatting.

   Alternative considered: log `Представление()` of structures. Rejected because it is less stable for nested JSON-like payloads and does not show the actual JSON response shape.

3. Add small logging helper functions instead of changing the protocol contract.

   Rationale: the protocol layer should continue returning the same `Ответ` structures. Transport-level helpers can emit trace entries immediately after request parsing and after response/task completion without altering handler input or output contracts.

   Alternative considered: embed trace data into `Контекст` or `Ответ`. Rejected because that would mix observability concerns into public execution data and risk changing provider-facing behavior.

4. Preserve readable file output as append-only UTF-8 text.

   Rationale: `ЗаписьТекста(ФайлЛога, КодировкаТекста.UTF8, , Истина)` is already the file writer boundary. The implementation should ensure only strings are passed to it, replace control line breaks inside embedded previews if needed, and avoid writing binary component payloads directly.

   Alternative considered: write raw request bytes to the file. Rejected because the reported problem is unreadable log content, and raw transport bytes would make the symptom worse.

## Risks / Trade-offs

- Full arguments or responses can contain sensitive data -> keep entries at debug level and do not enable them independently of existing explicit logging configuration.
- Large tool responses can make logs noisy -> serialize the final response body, but consider bounded previews only if tests or runtime evidence show unacceptable file growth.
- Serialization failures could hide the original handler result -> helper functions must degrade to an explicit `<serialization-error>` diagnostic in the log and must not change the MCP response path.
- The screenshot may also involve an external log viewer opening UTF-8 as another encoding -> verify the produced file bytes/text locally and document UTF-8 expectations if implementation confirms that root cause.

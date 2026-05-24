## ADDED Requirements

### Requirement: Tool-call requests are readable in debug logs

The system SHALL write a human-readable debug log entry for every accepted `MCP_TOOL_CALL` request when MCP logging is enabled at `debug` level.

#### Scenario: Sync tool-call request is logged

- **WHEN** the transport layer accepts an `MCP_TOOL_CALL` request with a tool name, request id, execution mode, and arguments
- **THEN** the log entry contains the event type, tool name, request id, execution mode, and JSON text for the arguments

#### Scenario: Task tool-call request is logged

- **WHEN** the transport layer accepts a task-based `MCP_TOOL_CALL` request with a task id
- **THEN** the log entry contains the event type, tool name, execution mode, task id, and JSON text for the arguments

### Requirement: Tool-call responses are readable in debug logs

The system SHALL write a human-readable debug log entry for every completed `MCP_TOOL_CALL` response when MCP logging is enabled at `debug` level.

#### Scenario: Successful sync tool-call response is logged

- **WHEN** a synchronous tool call returns a JSON-RPC success response
- **THEN** the log entry contains the request id, tool name, status `success`, and JSON text for the response payload

#### Scenario: Failed sync tool-call response is logged

- **WHEN** a synchronous tool call returns a JSON-RPC error response
- **THEN** the log entry contains the request id, tool name, status `error`, and JSON text for the error payload

#### Scenario: Deferred tool-call response is logged

- **WHEN** a synchronous tool call is accepted for deferred completion and returns no immediate response
- **THEN** the log entry contains the request id, tool name, and status `deferred`

#### Scenario: Task tool-call completion is logged

- **WHEN** a task-based tool call is completed through the task completion path
- **THEN** the log entry contains the task id, tool name, status, and JSON text for the task completion payload

### Requirement: Log file remains UTF-8 text

The system SHALL append MCP log entries to the configured log file as readable UTF-8 text lines.

#### Scenario: Cyrillic and JSON payload text is written readably

- **WHEN** a log entry contains Cyrillic text and JSON payload content
- **THEN** the configured log file contains readable UTF-8 text rather than binary or mojibake output

#### Scenario: Structured payload logging does not change MCP responses

- **WHEN** a tool-call request and response are logged
- **THEN** the JSON-RPC response sent to the MCP client remains unchanged by the logging behavior

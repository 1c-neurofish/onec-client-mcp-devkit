#!/usr/bin/env python3
"""Small live UAT runner for the 1C MCP HTTP endpoint."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request


URL = os.environ.get("MCP_UAT_URL", "http://127.0.0.1:9874/mcp")
TOOL_NAME = os.environ.get("MCP_UAT_TOOL", "Timer")
LONG_TICKS = int(os.environ.get("MCP_UAT_LONG_TICKS", "31"))
MIN_SECONDS = float(os.environ.get("MCP_UAT_MIN_SECONDS", "30"))
REQUEST_TIMEOUT = float(os.environ.get("MCP_UAT_REQUEST_TIMEOUT", "180"))
PROGRESS_TOKEN = os.environ.get("MCP_UAT_PROGRESS_TOKEN", "uat-progress-1")


class UatFailure(Exception):
    pass


class McpClient:
    def __init__(self, url: str) -> None:
        self.url = url
        self.session_id = ""

    def initialize(self) -> dict:
        response, headers = self.request(
            1,
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "onec-client-mcp-uat", "version": "1.0.0"},
            },
        )
        self.session_id = headers.get("mcp-session-id", "")
        if not self.session_id:
            self.session_id = headers.get("Mcp-Session-Id", "")
        self.notify("notifications/initialized")
        return response

    def request(self, request_id: int, method: str, params: dict | None = None) -> tuple[dict, object]:
        messages, headers = self.request_messages(request_id, method, params)
        return find_response(messages, request_id), headers

    def request_messages(self, request_id: int, method: str, params: dict | None = None) -> tuple[list[dict], object]:
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        body, headers = self.post(payload, REQUEST_TIMEOUT)
        return parse_messages(body), headers

    def notify(self, method: str, params: dict | None = None) -> None:
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self.post(payload, 10)

    def post(self, payload: dict, timeout: float) -> tuple[str, object]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8"), response.headers


def parse_response(body: str, request_id: int) -> dict:
    return find_response(parse_messages(body), request_id)


def find_response(messages: list[dict], request_id: int) -> dict:
    for message in messages:
        if message.get("id") == request_id:
            return message
    raise UatFailure(f"response id={request_id} not found")


def parse_messages(body: str) -> list[dict]:
    stripped = body.strip()
    if not stripped:
        return []
    if stripped.startswith("{"):
        return [json.loads(stripped)]

    messages: list[dict] = []
    event_lines: list[str] = []
    for line in body.splitlines():
        if not line:
            append_event(messages, event_lines)
            event_lines = []
        elif line.startswith("data:"):
            event_lines.append(line.removeprefix("data:").strip())
    append_event(messages, event_lines)
    return messages


def append_event(messages: list[dict], event_lines: list[str]) -> None:
    if not event_lines:
        return
    data = "\n".join(event_lines)
    if data == "[DONE]":
        return
    messages.append(json.loads(data))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UatFailure(message)


def require_ok(response: dict) -> dict:
    if "error" in response:
        raise UatFailure(response["error"].get("message", "MCP error"))
    result = response.get("result")
    require(isinstance(result, dict), "result is not an object")
    return result


def tools_list(client: McpClient) -> list[dict]:
    response, _ = client.request(2, "tools/list", {})
    result = require_ok(response)
    tools = result.get("tools")
    require(isinstance(tools, list), "tools/list result has no tools")
    return tools


def call_long_operation(client: McpClient) -> tuple[dict, float, list[dict]]:
    started_at = time.monotonic()
    messages, _ = client.request_messages(
        3,
        "tools/call",
        {
            "name": TOOL_NAME,
            "arguments": {"ticks": LONG_TICKS},
            "_meta": {"progressToken": PROGRESS_TOKEN},
        },
    )
    elapsed = time.monotonic() - started_at
    response = find_response(messages, 3)
    result = require_ok(response)
    return result, elapsed, progress_notifications(messages)


def progress_notifications(messages: list[dict]) -> list[dict]:
    return [
        message
        for message in messages
        if message.get("method") == "notifications/progress"
    ]


def result_json(result: dict) -> dict:
    content = result.get("content")
    require(isinstance(content, list) and content, "tool result has no content")
    text = content[0].get("text")
    require(isinstance(text, str), "tool result content has no text")
    return json.loads(text)


def require_progress(messages: list[dict]) -> None:
    require(messages, "progress notification not found")
    for message in messages:
        params = message.get("params")
        if not isinstance(params, dict):
            continue
        if params.get("progressToken") != PROGRESS_TOKEN:
            continue
        require(isinstance(params.get("progress"), (int, float)), "progress is not numeric")
        require(params.get("total") == LONG_TICKS, f"unexpected progress total: {params.get('total')}")
        return
    raise UatFailure("matching progress notification not found")


def run() -> list[str]:
    client = McpClient(URL)
    passed: list[str] = []

    require_ok(client.initialize())
    passed.append("initialize")

    tools = tools_list(client)
    require(any(tool.get("name") == TOOL_NAME for tool in tools), f"tool {TOOL_NAME} not listed")
    passed.append(f"tools/list has {TOOL_NAME}")

    result, elapsed, progress = call_long_operation(client)
    require_progress(progress)
    data = result_json(result)
    require(elapsed >= MIN_SECONDS, f"{TOOL_NAME} completed too fast: {elapsed:.1f}s")
    require(data.get("ticks") == LONG_TICKS, f"unexpected ticks: {data.get('ticks')}")
    passed.append(f"progress notification for {PROGRESS_TOKEN}")
    passed.append(f"{TOOL_NAME} ticks={LONG_TICKS} completed in {elapsed:.1f}s")

    return passed


def main() -> int:
    print("MCP protocol UAT")
    print(f"endpoint: {URL}")
    try:
        passed = run()
    except (UatFailure, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"FAIL {error}")
        return 1

    for item in passed:
        print(f"PASS {item}")
    print(f"{len(passed)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

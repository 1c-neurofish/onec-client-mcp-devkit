#!/usr/bin/env python3
"""Live UAT runner for command-line MCP autostart."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.error
from pathlib import Path

sys.dont_write_bytecode = True

import run as protocol_uat
from run import McpClient, UatFailure, require, require_ok, result_json, tools_list


ROOT = Path(__file__).resolve().parents[2]
UAT_DIR = ROOT / "uat" / "mcp-protocol"
BUILD_DIR = ROOT / "build" / "uat" / "mcp-protocol"
RUNNER = os.environ.get("V8_RUNNER", "v8-runner")
V8PROJECT = os.environ.get("MCP_UAT_V8PROJECT", str(UAT_DIR / "v8project.yaml"))
HOST = os.environ.get("MCP_UAT_HOST", "127.0.0.1")
PORT = int(os.environ.get("MCP_UAT_AUTOSTART_PORT", "9874"))
CONFIG_PORT = int(os.environ.get("MCP_UAT_AUTOSTART_CONFIG_PORT", "9888"))
SERVER_TIMEOUT = int(os.environ.get("MCP_UAT_SERVER_TIMEOUT", "10"))
STARTUP_TIMEOUT = float(os.environ.get("MCP_UAT_AUTOSTART_TIMEOUT", "90"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run command-line MCP autostart UAT.")
    parser.add_argument(
        "--scenario",
        choices=("default", "json", "override", "case", "long"),
        default=os.environ.get("MCP_UAT_AUTOSTART_SCENARIO", "override"),
        help="Autostart contract scenario to run.",
    )
    return parser.parse_args()


def command_line_parameter(scenario: str, config_path: Path) -> tuple[str, int]:
    if scenario == "default":
        return "runMcp", 8080
    if scenario == "json":
        write_config(config_path, PORT)
        return f"runMcp={config_path}", PORT
    if scenario == "case":
        write_config(config_path, PORT)
        return f"RUNMCP={config_path}", PORT

    write_config(config_path, CONFIG_PORT)
    return f"runMcp={config_path};mcpPort={PORT}", PORT


def write_config(path: Path, port: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"port": port, "timeout": SERVER_TIMEOUT}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def clear_component_cache() -> None:
    cache_dir = Path.home() / ".1cv8" / "1C" / "1cv8" / "ExtCompT"
    if not cache_dir.exists():
        return
    for path in cache_dir.glob("WebTransportAddIn_x64*.so"):
        path.unlink(missing_ok=True)


def endpoint_url(port: int) -> str:
    return f"http://{HOST}:{port}/mcp"


def launch_client(command_parameter: str, log_path: Path) -> subprocess.Popen:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        RUNNER,
        "--config",
        V8PROJECT,
        "--no-color",
        "launch",
        "--c",
        command_parameter,
        "thin",
    ]
    log = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    log.close()
    return process


def wait_for_endpoint(url: str, timeout: float) -> None:
    host, port = endpoint_host_port(url)
    deadline = time.monotonic() + timeout
    last_error: BaseException | None = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                pass
            return
        except OSError as error:
            last_error = error
            time.sleep(1)
    raise UatFailure(f"MCP endpoint did not become ready: {last_error}")


def endpoint_host_port(url: str) -> tuple[str, int]:
    prefix = "http://"
    require(url.startswith(prefix), f"unsupported endpoint URL: {url}")
    host_port = url.removeprefix(prefix).split("/", 1)[0]
    host, port = host_port.rsplit(":", 1)
    return host, int(port)


def require_endpoint_free(url: str) -> None:
    try:
        client = McpClient(url)
        require_ok(client.initialize())
    except (OSError, UatFailure, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return
    raise UatFailure(f"MCP endpoint is already running before launch: {url}")


def probe_endpoint(url: str) -> list[str]:
    client = McpClient(url)
    passed: list[str] = []

    require_ok(client.initialize())
    passed.append("initialize")

    tools = tools_list(client)
    require(any(tool.get("name") == "infobase_info" for tool in tools), "tool infobase_info not listed")
    passed.append("tools/list has infobase_info")

    response, _ = client.request(
        3,
        "tools/call",
        {
            "name": "infobase_info",
            "arguments": {},
        },
    )
    data = result_json(require_ok(response))
    require(isinstance(data.get("Платформа"), dict), "infobase_info has no platform data")
    passed.append("tools/call infobase_info")

    return passed


def run_long_operation(url: str) -> list[str]:
    protocol_uat.URL = url
    return protocol_uat.run()


def stop_client(process: subprocess.Popen) -> None:
    client_pids = launch_client_pids(BUILD_DIR / "autostart-launch.log")
    try:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=10)
    except ProcessLookupError:
        pass
    except subprocess.TimeoutExpired:
        kill_process_group(process.pid, signal.SIGKILL)
    for pid in client_pids:
        stop_pid(pid)


def launch_client_pids(log_path: Path) -> list[int]:
    if not log_path.exists():
        return []
    text = log_path.read_text(encoding="utf-8", errors="replace")
    return [int(match) for match in re.findall(r"\bpid[: ]+(\d+)\b", text)]


def stop_pid(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.5)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def kill_process_group(pid: int, sig: signal.Signals) -> None:
    try:
        os.killpg(pid, sig)
    except ProcessLookupError:
        pass


def run(scenario: str) -> list[str]:
    config_path = BUILD_DIR / "autostart-mcp.json"
    log_path = BUILD_DIR / "autostart-launch.log"
    command_parameter, port = command_line_parameter(scenario, config_path)
    url = endpoint_url(port)

    require_endpoint_free(url)
    clear_component_cache()
    process = launch_client(command_parameter, log_path)
    try:
        wait_for_endpoint(url, STARTUP_TIMEOUT)
        if scenario == "long":
            passed = run_long_operation(url)
        else:
            passed = probe_endpoint(url)
    finally:
        stop_client(process)

    passed.insert(0, f"launch /C\"{command_parameter}\"")
    passed.append(f"endpoint {url}")
    passed.append(f"launch log {log_path.relative_to(ROOT)}")
    return passed


def main() -> int:
    args = parse_args()
    print("MCP command-line autostart UAT")
    print(f"scenario: {args.scenario}")
    try:
        passed = run(args.scenario)
    except (UatFailure, OSError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print(f"FAIL {error}")
        return 1

    for item in passed:
        print(f"PASS {item}")
    print(f"{len(passed)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

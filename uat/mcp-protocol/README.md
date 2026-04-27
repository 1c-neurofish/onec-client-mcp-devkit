# MCP protocol UAT

Отдельный UAT-проект для проверки MCP протокола через реальный HTTP MCP endpoint.

## Подготовка

1. Поднять отдельную базу. `build` загружает все source-set из `v8project.yaml`, включая расширение `test_client` с UAT-инструментом `Timer`; `extensions` отключает safe mode для `client_mcp`, чтобы JSON-конфиг из `/C"runMcp=<path>"` читался в UAT:

```bash
v8-runner --config uat/mcp-protocol/v8project.yaml init
v8-runner --config uat/mcp-protocol/v8project.yaml build
v8-runner --config uat/mcp-protocol/v8project.yaml extensions --name client_mcp
```

2. Для ручного отладочного запуска можно поднять тонкий клиент:

```bash
v8-runner --config uat/mcp-protocol/v8project.yaml launch thin
```

## Запуск

Основной long-running UAT сам запускает тонкий клиент и MCP через `/C`:

```bash
V8_RUNNER=/home/alko/develop/tools/v8-runner python3 uat/mcp-protocol/run-autostart.py --scenario long
```

Проверка уже поднятого вручную MCP endpoint:

```bash
python3 uat/mcp-protocol/run.py
```

Проверка автозапуска MCP из `/C` запускает тонкий клиент сама:

```bash
V8_RUNNER=/home/alko/develop/tools/v8-runner python3 uat/mcp-protocol/run-autostart.py
```

По умолчанию запускается сценарий `override`: JSON-конфиг содержит `port`, а `/C` передает `mcpPort`, который должен иметь приоритет. Остальные сценарии:

```bash
python3 uat/mcp-protocol/run-autostart.py --scenario default
python3 uat/mcp-protocol/run-autostart.py --scenario json
python3 uat/mcp-protocol/run-autostart.py --scenario case
```

Переменные окружения:

- `MCP_UAT_URL` - адрес MCP endpoint, по умолчанию `http://127.0.0.1:9874/mcp`.
- `MCP_UAT_TOOL` - имя long-running инструмента, по умолчанию `Timer`.
- `MCP_UAT_LONG_TICKS` - длительность операции, по умолчанию `31`.
- `MCP_UAT_MIN_SECONDS` - минимальная ожидаемая длительность, по умолчанию `30`.
- `V8_RUNNER` - путь к `v8-runner` для проверки автозапуска, если он не доступен в `PATH`.
- `MCP_UAT_AUTOSTART_PORT` - порт endpoint для сценариев `json`, `override` и `case`, по умолчанию `9874`.
- `MCP_UAT_SERVER_TIMEOUT` - таймаут MCP-сервера в JSON-конфиге автозапуска, по умолчанию `10`.
- `MCP_UAT_AUTOSTART_TIMEOUT` - ожидание старта endpoint в секундах, по умолчанию `90`.

## Сценарии

Сценарии описаны в `scenarios.md`. Runner выводит только краткий список `PASS/FAIL`.
Проверка long-running вызова остается обычным `tools/call`; task-based режим в этом UAT не используется.

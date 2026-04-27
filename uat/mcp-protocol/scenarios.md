# MCP protocol UAT scenarios

## UAT-MCP-001 Long-running tools/call

Цель: подтвердить, что обычный long-running `tools/call` живет дольше 30 секунд, отправляет `notifications/progress` и возвращает результат через MCP. Это не task-based сценарий.

Шаги:

1. Подготовить UAT-базу через `v8-runner --config uat/mcp-protocol/v8project.yaml init`, `build` и `extensions --name client_mcp`; `build` загружает расширение `test_client` с инструментом `Timer`.
2. Запустить `python3 uat/mcp-protocol/run-autostart.py --scenario long`.
3. Runner создает JSON-конфиг с `port` и `timeout = 10`, стартует тонкий клиент с `/C"runMcp=<config>;mcpPort=9874"`.
4. Runner выполняет `initialize`, `notifications/initialized`, `tools/list`.
5. Runner выполняет `tools/call` -> `Timer` с `ticks = 31` и `_meta.progressToken`.

Ожидания:

1. `tools/list` содержит `Timer`.
2. `tools/call` завершается не раньше чем через 30 секунд.
3. В потоке ответа есть `notifications/progress` с тем же `progressToken`, числовым `progress` и `total = 31`.
4. Ответ содержит JSON с `ticks = 31`.
5. MCP endpoint поднят автозапуском клиента через `/C`, без ручной команды формы.

## UAT-MCP-002 Command-line autostart

Цель: подтвердить, что тонкий клиент, запущенный с `/C`, сам поднимает MCP endpoint без ручной команды формы.

Шаги:

1. Подготовить UAT-базу через `v8-runner --config uat/mcp-protocol/v8project.yaml init`, `build` и `extensions --name client_mcp`.
2. Запустить `python3 uat/mcp-protocol/run-autostart.py --scenario override`.
3. Runner создает JSON-конфиг с `port`, стартует тонкий клиент с `/C"runMcp=<config>;mcpPort=9874"`.
4. Runner выполняет `initialize`, `tools/list`, `tools/call` -> `infobase_info`.

Ожидания:

1. MCP endpoint становится доступен на порту из `mcpPort`, а не на порту из JSON-конфига.
2. `tools/list` содержит встроенный инструмент `infobase_info`.
3. `tools/call infobase_info` возвращает JSON со сведениями о платформе.

Дополнительные варианты того же контракта:

1. `--scenario default` проверяет `/C"runMcp"` и порт `8080`.
2. `--scenario json` проверяет `/C"runMcp=<config>"` и поле JSON `port`.
3. `--scenario case` проверяет регистронезависимость ключа запуска `runMcp`.

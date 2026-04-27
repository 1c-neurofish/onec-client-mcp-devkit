# MCP protocol UAT scenarios

## UAT-MCP-001 Long-running tools/call

Цель: подтвердить, что обычный `tools/call` для отложенного инструмента живет дольше 30 секунд, отправляет `notifications/progress` и возвращает результат через MCP. Это не task-based сценарий.

Шаги:

1. `initialize`
2. `notifications/initialized`
3. `tools/list`
4. `tools/call` -> `Timer` с `ticks = 31` и `_meta.progressToken`

Ожидания:

1. `tools/list` содержит `Timer`.
2. `tools/call` завершается не раньше чем через 30 секунд.
3. В потоке ответа есть `notifications/progress` с тем же `progressToken`, числовым `progress` и `total = 31`.
4. Ответ содержит JSON с `ticks = 31`.

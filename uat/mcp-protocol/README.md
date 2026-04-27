# MCP protocol UAT

Отдельный UAT-проект для проверки MCP протокола через реальный HTTP MCP endpoint.

## Подготовка

1. Поднять отдельную базу:

```bash
v8-runner --config uat/mcp-protocol/v8project.yaml init
v8-runner --config uat/mcp-protocol/v8project.yaml build
```

2. Запустить тонкий клиент:

```bash
v8-runner --config uat/mcp-protocol/v8project.yaml launch thin
```

3. Открыть обработку `ВнешнийИнструментАсинхроннаяОперация`.
4. Выполнить команды формы:
   - `ЗарегистрироватьИнструменты`
   - `ЗапуститьСервер`

## Запуск

```bash
python3 uat/mcp-protocol/run.py
```

Переменные окружения:

- `MCP_UAT_URL` - адрес MCP endpoint, по умолчанию `http://127.0.0.1:9874/mcp`.
- `MCP_UAT_TOOL` - имя long-running инструмента, по умолчанию `Timer`.
- `MCP_UAT_LONG_TICKS` - длительность операции, по умолчанию `31`.
- `MCP_UAT_MIN_SECONDS` - минимальная ожидаемая длительность, по умолчанию `30`.

## Сценарии

Сценарии описаны в `scenarios.md`. Runner выводит только краткий список `PASS/FAIL`.
Проверка long-running вызова остается обычным deferred `tools/call`; task-based режим в этом UAT не используется.

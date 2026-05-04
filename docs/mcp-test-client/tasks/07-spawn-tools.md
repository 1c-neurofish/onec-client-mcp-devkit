# Задача 07: System spawn/kill tools (перенос из Rust addin)

Статус: `todo`

## Цель

Реализовать в расширении `exts/test_client/` MCP-tools `system_spawn_1c_client` / `system_kill_pid`, заменяющие текущую реализацию `addin.spawn` / `addin.kill` в Rust-компоненте `web-transport-addin`. Это завершит чистое разделение слоёв: транспорт остаётся в Rust, прикладные операции — в BSL-расширениях.

## Область

**Входит:**
- Новый общий модуль `Мсп_СпавнИнструменты` в `exts/test_client/`.
- Tools:
  - `system_spawn_1c_client` — запуск дочернего 1С-клиента.
  - `system_kill_pid` — завершение процесса по PID.
- Валидатор `Мсп_СпавнВалидатор` — allow-list + regex.
- JSON-Schema параметров каждого tool.
- Регистрация в `Мсп_РеестрКлиент.ЗарегистрироватьИнструмент`.
- Объявление capabilities `["spawn","kill"]` от имени расширения (механизм объявления — отдельная подзадача, см. ниже).
- Unit-тесты валидатора (YaxUnit): allow-list, regex, shell-injection попытки.
- Документация `test-client-api.md` — секция «System tools».

**Не входит:**
- Изменения в Rust-компоненте `web-transport-addin` — отдельная задача в репозитории компоненты (см. парный ADR-0005).
- Изменения в `v8-client-session-manager` — отдельная задача в репозитории менеджера.
- `system_list_children` — опционально, если будет согласован контракт получения списка от менеджера (без локального supervisor'а нужен push от менеджера).

## Входные данные и допущения

- Расширение `test_client` уже подключено к ядру `client-mcp` и регистрирует tools (см. задачу 01).
- `ЗапуститьПриложение` доступна и тестировалась на Linux/Windows (см. `Мсп_УправлениеТестКлиентом.ЗапуститьПроцессТестКлиента`).
- `КаталогПрограммы()` возвращает путь к каталогу 1С платформы (источник `1cv8c`).
- Текущий PID собственного процесса доступен через `Мсп_МетаданныеСервер.ТекущийPID` (если ещё нет — добавить как часть задачи).
- Менеджер сопоставляет spawn-запрос с подключившимся ребёнком по `client_uid`. Поэтому tool может НЕ возвращать PID — достаточно success/fail.

## API tools

### `system_spawn_1c_client`

**Назначение.** Запуск дочернего 1С-клиента с параметрами, переданными от менеджера.

**JSON-Schema аргументов:**

```json
{
  "type": "object",
  "required": ["kind", "client_uid"],
  "additionalProperties": false,
  "properties": {
    "binary":     { "type": "string", "enum": ["1cv8", "1cv8c", "auto"] },
    "kind":       { "type": "string", "pattern": "^[A-Za-z0-9_-]{1,32}$" },
    "client_uid": { "type": "string", "pattern": "^[0-9a-fA-F-]{36}$" },
    "corr_id":    { "type": "string", "pattern": "^[A-Za-z0-9_-]{0,64}$" },
    "manager_url":{ "type": "string", "pattern": "^wss?://[A-Za-z0-9._:/-]+$" },
    "ib": {
      "type": "object",
      "properties": {
        "server": { "type": "string", "pattern": "^[A-Za-z0-9._-]+\\\\[A-Za-z0-9._-]+$" },
        "user":   { "type": "string", "pattern": "^[A-Za-z0-9._-]{1,64}$" },
        "password":{"type": "string", "maxLength": 128 }
      },
      "required": ["server","user"]
    },
    "language":   { "type": "string", "enum": ["ru","en","tr"] },
    "extra_c_args": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "mcpMode":            { "type": "string", "enum": ["ws","http","auto"] },
        "mcp_ws_timeout_ms":  { "type": "integer", "minimum": 1, "maximum": 60000 }
      }
    }
  }
}
```

**Контракт:**
- `binary = "auto"` — берётся `КаталогПрограммы() + "1cv8c"` (Linux) или `1cv8c.exe` (Windows).
- Любое поле, не прошедшее regex/enum — отказ с `result.is_error = true` и описанием в `content`.
- Любое поле с shell metacharacters (`; & | $ \` ` < > ( ) { } [ ] !`) — отказ с пометкой `validation_failed: shell_metacharacter_detected`.
- Команда собирается через `СтрШаблон` с уже валидированными значениями. Никакой строковой конкатенации.

**Результат:**

```json
{
  "success": true,
  "client_uid": "<echo>",
  "command_line_preview": "<masked password>"
}
```

или

```json
{
  "success": false,
  "error_code": "validation_failed | spawn_failed | binary_not_found",
  "error_message": "<human-readable>"
}
```

PID **не возвращается** — менеджер получит его через последующий `session.register` от запустившегося клиента.

### `system_kill_pid`

**Назначение.** Принудительное завершение процесса по PID. Используется как fallback для зомби-клиентов, не отвечающих на `session.shutdown`.

**JSON-Schema аргументов:**

```json
{
  "type": "object",
  "required": ["pid"],
  "additionalProperties": false,
  "properties": {
    "pid":    { "type": "integer", "minimum": 2 },
    "signal": { "type": "string", "enum": ["term", "kill"], "default": "term" }
  }
}
```

**Контракт:**
- `pid >= 2` (защита от kill PID 1).
- **Перед kill — проверка существования процесса**: `kill -0 PID` (Linux) или `tasklist /FI "PID eq N"` (Windows) через `ЗапуститьПриложение` с захватом stderr. Если процесс не существует → `error_code = "pid_not_found"`.
- **Опционально (этап 2):** проверка, что PID принадлежит дочернему процессу 1С (`/proc/PID/cmdline` на Linux содержит `1cv8c`). Если нет — отказ с `error_code = "pid_not_owned"`. Это защита от случайного kill чужих процессов.
- Сборка команды:
  - Linux: `kill -TERM PID` или `kill -KILL PID` (по signal).
  - Windows: `taskkill /PID N` или `taskkill /PID N /F` (по signal).
- Результат: `success: bool`, `error_code` при ошибке.

## Валидатор

Отдельный модуль `Мсп_СпавнВалидатор` с экспортируемыми функциями:

- `ВалидироватьSpawnАргументы(Аргументы)` → `Структура { Успех: Булево, Ошибки: Массив }`.
- `ВалидироватьKillАргументы(Аргументы)` → аналогично.
- `СодержитShellMetacharacter(Значение)` → `Булево` — общая проверка строки на запрещённые символы.

Каждый валидатор:
1. Проверяет наличие обязательных полей.
2. Прогоняет regex/enum по schema.
3. Запрещает shell metacharacters в значениях.
4. Возвращает все обнаруженные ошибки массивом (а не первую найденную) — для человекочитаемого фидбэка.

## Сборка команды (Linux пример)

```bsl
Функция СобратьКомандуСпавна(Аргументы)
    Бинарь = РазрешитьБинарь(Аргументы.binary);  // через КаталогПрограммы() + allow-list
    
    Шаблон = "%1 ENTERPRISE";
    
    Если ЗначениеЗаполнено(Аргументы.ib) Тогда
        Шаблон = Шаблон + " /S""%2"" /N""%3"" /P""%4""";
    КонецЕсли;
    
    Шаблон = Шаблон + " /C""kind=%5;client_uid=%6";
    Если ЗначениеЗаполнено(Аргументы.corr_id) Тогда
        Шаблон = Шаблон + ";corr_id=%7";
    КонецЕсли;
    Шаблон = Шаблон + """ /DisableStartupMessages /DisableStartupDialogs";
    
    Возврат СтрШаблон(Шаблон,
        Бинарь,
        Аргументы.ib.server, Аргументы.ib.user, Аргументы.ib.password,
        Аргументы.kind, Аргументы.client_uid, Аргументы.corr_id);
КонецФункции
```

Все %N-плейсхолдеры заполняются уже-валидированными значениями. Аналогичный шаблон строится для Windows с учётом особенностей кавычек.

## Объявление capabilities (подзадача)

В ядре `client-mcp` отсутствует механизм объявления capabilities от имени прикладного расширения. Сейчас `["spawn","kill"]` зашиты в Rust (`session_params.rs`). После переноса tools в BSL нужен механизм:

- Расширение регистрирует свои tools в `Мсп_РеестрКлиент.ЗарегистрироватьИнструмент`.
- Каждое описание инструмента опционально содержит поле `Capabilities: Массив` (свободный список строк).
- Ядро (`Мсп_ТранспортСессионКлиент.ОтправитьSessionRegister`) собирает уникальные capabilities из всех зарегистрированных tools и кладёт в `session.register.params.capabilities`.
- Альтернатива: расширения объявляют capabilities явно через новый API `Мсп_РеестрКлиент.ОбъявитьCapability("spawn")` — независимо от tools.

Решение между этими двумя альтернативами — отдельный sub-ADR (или подзадача в этой задаче, fix перед началом реализации).

## Тесты

YaxUnit-модуль `Тесты_СпавнИнструменты`:

1. **Allow-list бинарника:** запрос с `binary = "rm"` → отказ.
2. **Regex `client_uid`:** запрос с невалидным UUID → отказ с правильным error_code.
3. **Shell metacharacter в `kind`:** `kind = "test;rm"` → отказ.
4. **Shell metacharacter в `client_uid`:** `client_uid = "uuid$(whoami)"` → отказ.
5. **Все обязательные поля:** отсутствует `client_uid` → отказ.
6. **Happy path:** все поля валидны → success, command_line_preview содержит ожидаемую структуру (без выполнения реального ЗапуститьПриложение в тесте).
7. **Kill PID 1:** отказ.
8. **Kill non-existent PID:** `pid_not_found`.
9. **Длинные значения:** `client_uid` длиной 200 → отказ по maxLength.

## Критерии готовности

- [ ] `Мсп_СпавнИнструменты` создан и подключён в `Configuration.mdo` расширения `test_client`.
- [ ] `Мсп_СпавнВалидатор` создан с покрытием 100% allow-list и regex.
- [ ] Tools зарегистрированы и видны в `tools/list` через MCP.
- [ ] JSON-Schema валидируется на стороне сервера (через `Мсп_СхемаПараметров`).
- [ ] YaxUnit-модуль `Тесты_СпавнИнструменты` зелёный (минимум 9 тестов из плана).
- [ ] Документация в `docs/mcp-test-client/test-client-api.md` и `contracts.md` обновлена.
- [ ] Прецедент в `Мсп_УправлениеТестКлиентом` (старый ЗапуститьПриложение для тест-клиента) сохраняет работоспособность (не сломали соседнее расширение).
- [ ] Capability-объявление работает: при загрузке расширения `test_client` в `session.register.params.capabilities` появляются `["spawn","kill"]`.
- [ ] Парный ADR `0003-spawn-tools-in-test-client.md` переведён в `accepted`.

## Риски

- **Объявление capabilities** требует доработки ядра `client-mcp`. Если решение «через атрибут описания инструмента» — затронет `Мсп_РеестрКлиент`, `Мсп_ИнструментыКлиент`, `Мсп_ТранспортСессионКлиент`. Подзадача может потребовать отдельного PR в ядро до начала работы над spawn tools.
- **Кросс-платформенность.** Linux и Windows требуют разных шаблонов команды и разных утилит kill. Нужно явное разделение в коде с тестами на обеих ОС (хотя бы один YaxUnit с моком `Метаданные.ЗначенияПеречислений` имитирующим ОС).
- **Shell-эскейпинг кавычек на Windows.** Microsoft `CommandLineToArgvW`-quoting сложнее, чем на Linux: кавычки внутри значений требуют escaping через `\"` плюс backslash-doubling перед закрывающей `"`. Нужно либо тщательная реализация, либо запрет кавычек в значениях через regex (что приемлемо при нашем allow-list — ни одно поле не содержит кавычки).

## Связанные документы

- ADR-0003: `docs/decisions/0003-spawn-tools-in-test-client.md` (этот ADR описывает решение, текущая задача — план реализации).
- Парный ADR: `web-transport-addin/docs/decisions/0005-transport-only-rust.md`.
- Прецедент: `exts/test_client/CommonModules/Мсп_УправлениеТестКлиентом/Module.bsl`.
- Implementation-plan: `docs/mcp-test-client/implementation-plan.md` — этот документ нужно дополнить ссылкой на текущую задачу (этап 6).

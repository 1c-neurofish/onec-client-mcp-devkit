# ADR-0003: Spawn/Kill tools переезжают в прикладное расширение `exts/test_client`

- Статус: accepted
- Дата: 2026-05-04 (proposed) → 2026-05-05 (accepted после реализации этапов А/Б/В).
- Связанные ADR: [ADR-0001 (архитектура провайдеров)](0001-wt-mcp-adapter-provider-architecture.md), [ADR-0002 (запуск из командной строки)](0002-command-line-mcp-server-startup.md). Парный ADR — `web-transport-addin/docs/decisions/0005-transport-only-rust.md`.
- Связанные документы: [`FORK_CHANGES.md`](../../FORK_CHANGES.md), [`docs/mcp-test-client/implementation-plan.md`](../mcp-test-client/implementation-plan.md), задача `docs/mcp-test-client/tasks/07-spawn-tools.md`.

## Контекст

В этапе 6 (см. коммит `94bc171`) во внешнюю компоненту `web-transport-addin` была встроена реализация JSON-RPC методов `addin.spawn` / `addin.kill` плюс process supervisor. Это позволило `v8-client-session-manager` удалённо порождать дочерние 1С-клиенты на хостах, где уже зарегистрирован клиент с capability `spawn`.

После архитектурного ревью обнаружено, что spawn-функциональность принципиально **прикладная**: запуск 1С-клиента — это бизнес-операция, не часть транспорта. Помещать её в `web-transport-addin` нарушает разделение слоёв:

- **Транспортный слой** (`web-transport-addin`) — WS pump, reconnect, FFI.
- **MCP-ядро** (`exts/wt-mcp-adapter/`) — JSON-RPC, реестр tools/resources/prompts, маршрутизация.
- **Прикладной слой** (отдельные расширения, например `exts/test_client/`) — конкретные бизнес-операции, регистрируемые в реестре tools через `Мсп_РеестрКлиент.ЗарегистрироватьИнструмент`.

В репозитории уже существует прецедент: `exts/test_client/CommonModules/Мсп_УправлениеТестКлиентом` управляет жизненным циклом локального тест-клиента 1С (запуск через `ЗапуститьПриложение`, подключение по TCP, остановка). Это документировано в `docs/mcp-test-client/` с проработанным API. То есть **архитектура уже допускает** размещение spawn-логики в прикладном расширении.

Помимо разделения слоёв, перенос tools в BSL даёт:

1. **Видимость в стандартном MCP-каталоге.** Сейчас `addin.spawn` живёт в приватном namespace `addin.*` и не виден через `tools/list`. После переноса — обычный tool, доступный любому MCP-клиенту (включая AI-агента напрямую, без специального кода в менеджере).
2. **Policy / audit / read-only mode** в BSL. Можно проверять `AccessRight` текущего пользователя 1С, писать в ЖР каждый спавн, лимитировать число дочерних процессов. Всё это правится без перекомпиляции Rust-компоненты.
3. **JSON-Schema валидация аргументов** через стандартный MCP-механизм (см. `Мсп_ИнструментыКлиент.ОписаниеИнструмента`).

## Решение

Spawn/Kill tools реализуются как обычные MCP-tools в расширении `exts/test_client/`. Application API:

| Tool | Назначение | Параметры |
|------|-----------|-----------|
| `system_spawn_1c_client` | Запуск дочернего 1С-клиента | `binary` (allow-list), `kind` (allow-list), `client_uid` (UUID), `connection_string` (regex), `extra_c_args` (allow-list по ключам) |
| `system_kill_pid` | Принудительное завершение по PID | `pid` (int > 0), `signal` (опц., по умолчанию SIGTERM на Linux / `/F` на Windows) |
| `system_list_children` | (опционально) Список запущенных детей | без параметров |

PID получается **не от tool'а spawn**, а из последующего `session.register.params.pid` дочернего клиента. Менеджер сопоставляет spawn-запрос с регистрацией по `client_uid` (который передаётся через `/C client_uid=...` при спавне).

### Контракт безопасности

`ЗапуститьПриложение` в BSL принимает одну строку, парсимую платформой. Это создаёт потенциальную поверхность shell-injection, если аргументы попадают из MCP без валидации. Защита — **строгий allow-list плюс regex-валидация**:

1. **Allow-list бинарников.** Только `1cv8`, `1cv8c`, и абсолютные пути из конфигурации расширения (`Константа.DSSL_AdditionalSystemSettings` или эквивалент). Любой другой → отказ на этапе `system_spawn_1c_client`.
2. **Allow-list ключей `/C`.** Принимаются только: `kind`, `client_uid`, `corr_id`, `manager_url`, `mcp_ws_timeout_ms`, `mcpMode`. Любой неизвестный ключ → отказ.
3. **Allow-list платформенных ключей.** Принимаются: `/S`, `/N`, `/P`, `/L`, `/DisableStartupMessages`, `/DisableStartupDialogs`, `/IBConnectionString`, `/TESTCLIENT`, `/TPort`. Расширяется по мере необходимости.
4. **Regex-валидация значений.** Каждый ключ имеет шаблон:
   - `/N` — `^[A-Za-z0-9._-]{1,64}$`
   - `/L` — `^(ru|en|tr)$`
   - `/S` — `^[A-Za-z0-9._-]+\\[A-Za-z0-9._-]+$` или `^tcp://[A-Za-z0-9.:_-]+$`
   - `client_uid` — `^[0-9a-fA-F-]{36}$`
   - `kind` — `^[A-Za-z0-9_-]{1,32}$`
   - `pid` (для kill) — целое > 0, проверка существования через `kill -0` (Linux) / TaskList (Windows) перед kill.
5. **Запрет shell metacharacters.** Любой символ из набора `; & | $ \` ` < > ( ) { } [ ] ! \n \r \t` в любом значении → BLOCK на этапе валидации, до построения команды.
6. **Сборка через шаблон с фиксированными плейсхолдерами.** Никакой конкатенации в цикле. `СтрШаблон("%1 ENTERPRISE /S\"%2\" /N\"%3\" ...", БинарьВалидный, ServerStringВалидный, ИмяВалидное, ...)`. Каждое значение к моменту подстановки уже прошло regex.

### Маршрутизация (без отдельного механизма capabilities)

В текущей реализации Rust-форка `web-transport-addin` каждый клиент анонсирует менеджеру массив `capabilities` (например, `["spawn","kill"]`) в `session.register`, и менеджер использует `find_spawner(host_id, "spawn")` для выбора сессии-исполнителя. После переноса tools в BSL эта роль становится избыточной: имя инструмента (`system_spawn_1c_client` / `system_kill_pid`) уже однозначно говорит, какие сессии умеют спавнить.

Решение: **отдельного механизма `capabilities` не вводим.** В `session.register.params.tools` уже идёт массив с именами инструментов. Менеджер заменяет `find_spawner(host_id, "spawn")` на поиск сессии, в чьём каталоге tools есть имя `system_spawn_1c_client`. Поле `capabilities` в `SessionRecord` менеджера и в payload `session.register` помечается deprecated и удаляется на этапе В вместе с зачисткой `session_params.rs` (см. парный ADR-0005).

Если расширение `test_client` не загружено — соответствующих tools в каталоге нет, и менеджер просто не находит исполнителя на этом хосте. Поведение функционально эквивалентно «отсутствию capability», но без второго регистра и без правок ядра `wt-mcp-adapter`.

### Жизненный цикл (child_exited заменяется heartbeat'ом)

Уведомление `addin.child_exited` из Rust исчезает. Менеджер обнаруживает мёртвого клиента через timeout: если клиент не отвечает на JSON-RPC `ping` в течение настраиваемого окна (по умолчанию 30 сек) — менеджер помечает сессию как `dead` и инициирует cleanup. Это устраняет дублирование сигналов смерти (TCP-разрыв + `child_exited` + heartbeat-timeout) и упрощает логику менеджера.

## Последствия

### Положительные

- Слой application live в `exts/test_client/`, как и должно быть по архитектуре. Размывание границ устранено.
- Spawn-tool виден в стандартном `tools/list` — AI-агент использует его напрямую.
- Policy / audit / read-only добавляются в BSL без перекомпиляции компоненты.
- Расширение спавна на новые сценарии (например, `system_spawn_yaxunit_runner`) — добавление одного tool в BSL, без правки Rust.
- Удалить можно ~800 строк из `web-transport-addin` (см. парный ADR).

### Отрицательные

- **Breaking change для менеджера.** `v8-client-session-manager` должен отказаться от `addin.spawn` / `addin.kill` и переключиться на `tool.call name=system_spawn_1c_client`. Версионирование протокола обязательно.
- **Latency +5–20 мс** на спавн через дополнительный hop (Rust tunnel → BSL handler → `ЗапуститьПриложение`). Для 3–5-сек операции — несущественно.
- **Shell-injection поверхность переезжает в BSL.** Защита — строгий allow-list плюс regex-валидация. Если контракт нарушен — потенциальная уязвимость.
- **General-purpose spawn недоступен.** Спавн только 1С-клиента с известными ключами. Для произвольного binary потребуется отдельный tool с собственным allow-list.

### Риски

- Если allow-list окажется слишком узким для некоторых сценариев (например, в menedzher'е появится потребность спавнить с custom env), потребуется расширение валидатора. Контракт на `extra_c_args` должен учитывать это с самого начала.
- BSL стартует на ~1–3 сек позже, чем загружается addin. В этот промежуток менеджер не сможет дёрнуть spawn — решение: при `session.register` BSL отправляет уже полный список tools, менеджер не вызывает spawn раньше получения каталога. Естественный contract.

## План перехода

Поэтапный, синхронизированный с парным ADR в `web-transport-addin`:

1. **Этап А (это расширение).** Создать `exts/test_client/CommonModules/Мсп_СпавнИнструменты` с tools `system_spawn_1c_client` / `system_kill_pid`. Регистрация в `Мсп_РеестрКлиент`. Валидатор. JSON-Schema аргументов. Тесты YaxUnit для allow-list и regex.
2. **Этап Б (менеджер).** `v8-client-session-manager` переключается на новые MCP-tools. Heartbeat-monitor реализуется как замена `child_exited`.
3. **Этап В (Rust addin).** После подтверждения паритета удаляется `system_capability.rs` (см. парный ADR).

На промежуточных стадиях оба пути работают параллельно (graceful migration). Подробности — см. `docs/mcp-test-client/tasks/07-spawn-tools.md`.

## Ссылки

- Парный ADR: `web-transport-addin/docs/decisions/0005-transport-only-rust.md`.
- Прецедент использования `ЗапуститьПриложение` в test_client: `exts/test_client/CommonModules/Мсп_УправлениеТестКлиентом/Module.bsl:425`.
- Документация прикладного расширения: `docs/mcp-test-client/`.
- Дискуссия по архитектуре, диалог 2026-05-04.

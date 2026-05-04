# Доработки форка SteelMorgan/onec-client-mcp-devkit

> Документ описывает доработки относительно upstream-проекта `1c-neurofish/onec-client-mcp-devkit`. Форк построен поверх upstream `master` и реализует **транспорт-агностичный режим работы MCP-сервера**: расширение умеет работать как через локальный HTTP-сервер (исходный режим), так и через WebSocket к внешнему оркестратору `v8-client-session-manager` (новый режим).

## Назначение доработок

Upstream работает только в режиме «локальный HTTP MCP-сервер внутри 1С», и каждый AI-агент должен подключаться к каждому 1С-клиенту отдельно. В форке добавлен режим WS-клиента к внешнему менеджеру сессий — это даёт single-point-of-integration: менеджер агрегирует tools со многих 1С-клиентов и публикует общий MCP-каталог. Прежний HTTP-режим сохранён без изменений (backward compatibility).

## Bundle компоненты `AddIn.WebTransport` 0.7.0

`exts/client-mcp/src/CommonTemplates/Мсп_webTransport/Template.addin` обновлён с upstream `alkoleft/web-transport-addin@0.6.4` на собственный билд `SteelMorgan/web-transport-addin@7e76820` (0.7.0):

- Полная матрица ОС: Win x32+x64, Linux x32+x64, macOS x64 (versioned filenames).
- Новый класс `AddIn.WebTransport.session` (WS-клиент к session-manager).
- Прокидывание `host_id` + `pid` + `capabilities` в `session.register`.
- Системные методы `addin.spawn` / `addin.kill` для удалённого порождения дочерних 1С-клиентов.
- Override `/C client_uid=...` для manager-spawned клиентов.

## Новые общие модули

| Модуль | Назначение |
|--------|-----------|
| `Мсп_ТранспортСессионКлиент` | WS-клиент к session-manager через `AddIn.WebTransport.session`. Обрабатывает события `WS_RECONNECT_STATE` / `WS_INCOMING`, отправляет `session.register`, маршрутизирует входящие RPC: `tool.call` / `tool.cancel` / `session.shutdown` / `ping`. Хранит client state с полем `kind`. |
| `Мсп_СерверОтветы` | Транспорт-агностичный фасад отправки JSON-RPC ответов. Выбор канала: `ws` → `Мсп_ТранспортСессионКлиент`, `http` → `Мсп_ТранспортСобытияКлиент`. |

Оба зарегистрированы в `Configuration.mdo`.

## Расширение существующих модулей

### `Мсп_ПараметрыЗапускаКлиент` (+133 строки)

Dual-mode startup через `/C mcpMode=ws|http|auto`:

- `http` — исходное поведение (локальный HTTP-сервер).
- `ws` — подключение к session-manager.
- `auto` — попытка WS, fallback на HTTP при неудаче. При срабатывании fallback состояние сбрасывается через `Мсп_СостояниеКлиент.УстановитьЗначениеСостоянияСервера("РежимТранспорта", "http")`, чтобы фасад `Мсп_СерверОтветы` вернулся к HTTP-маршруту. Логи перехода — через `Мсп_ЛогированиеКлиент`.
- **(нет ключа)** — backward compatibility: ветка `runMcp=` работает как в upstream без изменений (если `mcpMode` не задан и `runMcp=` отсутствует — расширение просто не стартует никакого транспорта).

Резолвинг `manager_url`: при отсутствии `/C manager_url=...` используется default `ws://127.0.0.1:4000/sessions` (доступен и из контейнера, и с Windows-хоста через port-forwarding VS Code).

Парсинг дополнительных `/C`-параметров (через разделитель `;`): `manager_url`, `client_uid`, `kind`, `corr_id`, `mcp_ws_timeout_ms`. Эвристика `kind` по умолчанию: `1c-client`. Если `client_uid` не передан — генерируется свежий `Новый УникальныйИдентификатор`.

Точечная правка `ЗапуститьИзПараметраЗапуска`: добавлен dispatch по `mcpMode`, остальная сигнатура и backward-compat поведение сохранены. Шесть новых служебных функций: `НормализоватьРежим`, `ManagerURLПоУмолчанию`, `ИзвлечьПараметрыWS`, `ЗапуститьWS`, `ЗапуститьHTTPПоПараметрам`, `ЗапуститьAuto`.

### `ManagedApplicationModule` (dual-language hooks)

Идемпотентные обёртки `&После` сразу для двух языковых веток БСП:

```bsl
&После("OnStart")                  // EN-БСП (Drive, ERP World)
&После("ПриНачалеРаботыСистемы")   // RU-БСП (УНФ, ERP, Бухгалтерия)
&После("ExternEventProcessing")
&После("ОбработкаВнешнегоСобытия")
```

Каждая пара EN/RU делегирует общему диспетчеру (`Мсп_ИнициироватьСтарт` / `Мсп_ДиспетчерВнешнегоСобытия`). Идемпотентность через флаг `Мсп_СтартИнициирован` — гарантирует ровно один запуск, если БСП-конфигурация (нестандартно) имеет оба хука стартовых событий. Диспетчер внешних событий маршрутизирует `WebTransport.WS_RECONNECT_STATE` / `WS_INCOMING` в `Мсп_ТранспортСессионКлиент`, остальное — в существующий `Мсп_ТранспортСобытияКлиент`.

## Сценарий использования

1. Пользователь запускает 1С с параметром `/C "mcpMode=ws;manager_url=ws://host:4000/sessions"`.
2. После старта `Мсп_ТранспортСессионКлиент.Запустить(...)` подключает компоненту `AddIn.WebTransport.session` и инициирует подключение к менеджеру.
3. После события `WS_RECONNECT_STATE = connected` расширение шлёт `session.register` с локальным каталогом MCP tools/resources/prompts (включая VA-шаги, если установлена Vanessa Automation).
4. AI-агент получает агрегированный MCP-каталог от менеджера и вызывает tools через JSON-RPC поверх WS.
5. `Мсп_СерверОтветы` отправляет результаты обратно по тому же WS-каналу.

## Распределение ответственности: установка соединения и пинги

Связано с парным форком `SteelMorgan/web-transport-addin` — внешняя компонента (Rust) под этим расширением.

### Установка соединения

| Слой | Файл | Что делает |
|------|------|-----------|
| **Rust addin (низ)** | `web-transport-addin/src/session_integration.rs:145` (`WsConnector::connect`) | `tokio_tungstenite::connect_async(url)` с таймаутом 5 сек, возвращает (Stream, Sink). |
| **Rust addin (orchestrator)** | `web-transport-addin/src/reconnect.rs` (`run_with_reconnect`) | Auto-reconnect с экспоненциальным backoff. Публикует `WS_RECONNECT_STATE = connecting / connected / disconnected / give_up` в 1С через `AddinHost`. |
| **Rust addin (фасад)** | `web-transport-addin/src/session_integration.rs:105` (`SessionIntegration::start`) | Высокоуровневый API. Принимает URL → создаёт `WsConnector` → запускает `reconnect`+`tunnel`. |
| **FFI-обёртка** | `web-transport-addin/src/session/addin.rs:176` | Метод `ЗапуститьСессионнуюИнтеграцию(URL, ClientUID, Kind, CorrelationID)` для 1С. |
| **BSL (точка входа)** | `Мсп_ТранспортСессионКлиент.Module.bsl:18` (`Запустить`) | Подключает компоненту, создаёт `AddIn.WebTransport.session`, дёргает `Компонента.ЗапуститьСессионнуюИнтеграцию(...)`. Реальное «connected» приходит асинхронно событием `WS_RECONNECT_STATE`. |
| **BSL (poll connected)** | `Мсп_ТранспортСессионКлиент.Module.bsl:78` (`ДождатьсяConnected`) | Опрос `WSСостояние` каждые 20 мс с таймаутом — используется для `mcpMode=auto` fallback. |

### Пинги

Два независимых уровня:

**WebSocket protocol-level ping/pong (RFC 6455):**
- Где: `tokio_tungstenite` обрабатывает их сам внутри `WebSocketStream`.
- Кто инициирует: session-manager (отправляет `Ping` фреймы клиенту по таймеру).
- Кто отвечает: Rust addin → автоматический `Pong` через tokio-tungstenite, в BSL не пробрасывается. См. `web-transport-addin/src/session_integration.rs:202-227` (бинарные/ping/pong/frame игнорируются).
- Зачем: keep-alive TCP-соединения, обнаружение разрыва без потери данных.

**Application-level JSON-RPC ping:**
- Где (приём): `Мсп_ТранспортСессионКлиент.Module.bsl:259-262`:
  ```bsl
  ИначеЕсли Метод = "ping" Тогда
      Ждать Мсп_СерверОтветы.Отправить(
          Идентификатор,
          Новый Структура("jsonrpc, id, result", "2.0", Идентификатор, Новый Структура));
  ```
- Кто инициирует: session-manager шлёт `{"jsonrpc":"2.0","method":"ping","id":N}`, клиент возвращает пустой `result`.
- Кто отвечает: BSL-расширение (1С), не Rust.
- Зачем: liveness-check на уровне приложения — проверка, что 1С-клиент не завис в обработчике (TCP keep-alive это не покажет).

### session.register после connect

BSL-сторона (`Мсп_ТранспортСессионКлиент.Module.bsl:185-226`) — обработчик `WS_RECONNECT_STATE = connected` сам собирает каталог tools/resources/prompts (snake_case wire format) и шлёт `session.register` менеджеру. Список знает только 1С, поэтому Rust в этом не участвует — комментарий в `web-transport-addin/src/session_integration.rs`: *«1С-код сам отвечает за session.register после WS_RECONNECT_STATE=connected»*.

## TL;DR ответственности

- **WS-handshake + auto-reconnect + WS-уровневый ping/pong** → Rust addin (`SteelMorgan/web-transport-addin`).
- **Application-level JSON-RPC ping и session.register** → BSL (этот репозиторий).

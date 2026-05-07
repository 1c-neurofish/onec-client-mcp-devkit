# Контракты и процессы

## MCP методы
- `initialize` / `initialized`.
- `tools/list`, `tools/call`.
- `resources/list`, `resources/templates/list`, `resources/read`.
- `prompts/list`, `prompts/get`.
- Уведомления `notifications/tools/listChanged`, `notifications/resources/listChanged`, `notifications/prompts/listChanged`.
- Уведомления о смене UI‑состояния (см. ниже).

## Ресурсы (URI)
- `window://active` — активное окно.
- `window://{path}` — конкретное окно по навигационной ссылке.
- `form://{name}` — форма по имени формы.
- `control://{form}/{name}` — элемент формы по имени формы и имени элемента.
- `form://{name}` возвращает JSON-снимок формы с полями `type`, `uri`, `title`, `name`, `children`.
- `control://{form}/{name}` формируется только для элементов формы с заполненным `name`.
- Resource templates публикуются через `resources/templates/list`.
- Поддерживаемый subset RFC 6570 ограничен выражениями `{var}`.
- URI `ui://active/form` и `ui://forms/{formId}` больше не публикуются.

## Формат ресурса
- `contents` массив.
- Каждый content: `uri`, `text` (JSON‑снимок), `mimeType=application/json`.

## Снимок UI (JSON)
- `type` — `window|form|group|button|field|table|decoration`.
- `name` — внутреннее имя элемента.
- `title` — заголовок.
- `uri` — URI формы/окна или именованного элемента формы.
- `visible|enabled|readOnly` — доступность.
- `children` — массив вложенных элементов (ограничение по `depth`).
- `path` — путь до элемента (опционально).

## Уведомления UI
- `notifications/ui/changed` — структура UI изменилась.
- Поля уведомления: `scope`, `reason`, `timestamp`, `formId` (опционально).

## Процессы

### 1. Запуск тест‑клиента
1. Вызов `tools/call` -> `test_client_start`.
2. Сервер запускает процесс 1С и подключается к тест‑клиенту.
3. Сервер обновляет состояние и отправляет ответ.

### 2. Чтение дерева элементов
1. Вызов `resources/read` -> `window://active` или `form://{name}`.
2. Сервер строит снимок UI.
3. Сервер возвращает ресурс.

### 3. Пользовательское действие
1. Вызов `tools/call` -> `find` / `activate` / `close` / `open_form`.
2. Сервер разрешает URI или выполняет поиск в иерархии тест‑клиента.
3. Сервер выполняет действие и возвращает результат.

### 4. Spawn дочернего клиента (system tools)
1. Менеджер выбирает сессию по имени tool в её каталоге `session.register.params.tools` (`system_spawn_1c_client`). Отдельный массив `capabilities` не используется.
2. Менеджер вызывает `tools/call` -> `system_spawn_1c_client` с уникальным `client_uid`.
3. Прикладное расширение валидирует аргументы (`Мсп_СпавнВалидатор`), собирает команду через `СтрШаблон`, запускает `ЗапуститьПриложение(...)` без ожидания.
4. Дочерний клиент стартует, регистрируется на менеджере собственным `session.register` с тем же `client_uid` — менеджер связывает spawn-запрос с ребёнком по этому идентификатору.
5. Если ребёнок зависает — менеджер вызывает `system_kill_pid` с PID, полученным из его `session.register`.

## Ошибки
- Ошибки MCP: `-32602` для неверных параметров, `-32603` для ошибки выполнения.
- Ошибки домена: `UI_NOT_FOUND`, `UI_NOT_READY`, `UI_AMBIGUOUS_OBJECT`, `ACTION_DENIED`.
- Ошибки system tools: `validation_failed`, `binary_not_found`, `spawn_failed`, `pid_not_found`, `kill_failed`.

## Заглушки
- Правила построения `path`.
- Расширенные операторы и модификаторы RFC 6570 (`{+x}`, `{?x}`, `{x*}`, `{x:3}`).
- Поведение при множественных совпадениях элементов.

## Ссылки
- MCP spec 2025-06-18 (messages, tools, resources, prompts, notifications).

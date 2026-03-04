---
name: remarks-handling
description: Use when handling EDT remarks/issues for ClientMcp; outlines how to obtain remarks and when @skip-check is acceptable.
---

# Remarks Handling

Rules:
- Obtain remarks using `edt get_project_errors` with `projectName = ClientMcp`.
- Use `@skip-check` annotations only in exceptional cases.

# Method Doc Format

Use the following format for method descriptions:

```bsl
// бизнес описание
//
// Параметры:
//  ИмяПараметра - ТипПараметра - бизнес описание
// Возвращаемое значение:
//  ТипВозврата - бизнес описание
```

Return value is used only for functions.

Example:

```bsl
// Запускает MCP-сервер на указанном порту.
//
// Параметры:
//  Порт - Число - Номер порта для прослушивания.
//  Параметры - Структура - Дополнительные параметры запуска.
//
// Возвращаемое значение:
//  Булево - Истина при успешном запуске.
```

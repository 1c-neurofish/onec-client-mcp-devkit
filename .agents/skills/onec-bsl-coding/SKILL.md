---
name: onec-bsl-coding
description: Write, review, and refactor 1C (BSL) code with project design principles and coding standards. Use when generating BSL code, evaluating BSL quality, or applying BSL conventions in 1C modules and forms.
---

# 1C BSL Coding

## Overview

Use this skill to produce and assess 1C (BSL) code that follows the project rules and coding standards, including during code review.

## Quick Start

1. Read `references/codex-rules-1c.md` to apply SRP, OCP, DRY, YAGNI, and related principles.
2. Read `references/steel-morgan-coding-standards.md` for detailed BSL coding standards.
3. Follow `docs/code-style.md` when the repository provides it.
4. Keep changes minimal and scoped to the task.
5. When reviewing BSL code, explicitly apply this skill.

## Workflow

- Identify the module type and execution context before writing code.
- Apply the design principles from `references/codex-rules-1c.md`.
- Keep procedures small, focused, and named by action.
- Separate UI, business logic, and data access responsibilities.
- Avoid deep call chains; add accessors on the owning object instead.
- Prefer extension points over long type-based branching.
- Verify public method comments, parameter types, and return types.

## Review Checklist

- Check for duplicated logic or repeated queries.
- Flag procedures that exceed 40–60 lines as decomposition candidates.
- Ensure UI forms call services instead of embedding business logic.
- Confirm low coupling between common modules.

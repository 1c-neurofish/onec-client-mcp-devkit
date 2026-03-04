## Multiagent Workflow (Required)
Each task must pass through the following stages, in order:
1. Requirements analysis.
2. Planning (implementation plan + verification plan).
3. Implementation.
4. Testing.
5. Review.

## Scope & Diff Constraints
- Minimal diffs only.
- No refactors, no formatting runs, no lint cleanup.
- Never do wide edits across unrelated files.
- If any agent proposes changes outside the current task scope: STOP and correct scope.

## Code Style
- When editing BSL modules, follow `docs/code-style.md`.
- Для методов не добавляем префикс (например MCP).

## Branching & Commits
- Large tasks must be done in their own branch: `feat/<issue-i>-<short-description>`.
- Work on an existing task can continue in the same branch (even in a new chat). Small microtasks should stay on the current branch.
- If unsure whether a task is “large,” ask first.
- Commit at the end of the task using Conventional Commits (e.g., `feat: ...`, `fix: ...`, `chore: ...`).

## Roles
- Coordinator (default agent): owns the workflow, ensures every stage is completed and documented.
- Explorer: gather evidence only; no fixes unless requested.
- Worker: implement code changes as assigned by the coordinator.
- Reviewer: review changes for correctness, security, regressions, and missing tests.

## Stage Outputs
- Analysis: concise requirements, assumptions, and risks.
- Planning: bullet list of steps + how each step will be verified.
- Implementation: changes made with file references.
- Testing: commands run + results (or reason not run).
- Review: reviewer findings or explicit “no findings”.

## EDT Build & Checks
- After changes, run build using `update_database` (EDT tools).
- Check extension issues with `get_project_errors` using `projectName = ClientMcp`.
- To obtain current remarks/issues, use EDT tools (primarily `get_project_errors` for `ClientMcp`).

## Remarks Handling Rule
- Use `edt get_project_errors` with `projectName = ClientMcp` to obtain remarks.
- Use `@skip-check` annotations only in exceptional cases.

## 1C App Module State
- Application module may contain only global variables and application event handlers.
- Global state should be stored in exported variables in the application module.
- Access to global state must be via getter/setter methods placed in a common module (not in the application module).

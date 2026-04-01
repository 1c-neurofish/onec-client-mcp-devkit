---
name: plan-review
description: Run iterative subagent review and revision loops for implementation plans until a reviewer explicitly approves the plan. Use when Codex needs to draft, harden, or sign off a plan before implementation, especially for multi-step, risky, or ambiguous coding tasks where the user wants plan review by subagents rather than a single local pass.
---

# Plan Review

## Overview

Use this skill to turn a draft plan into an approved plan by alternating reviewer and fixer subagents.
Keep the coordinator responsible for scope, context curation, and the final approved plan shown to the user.

## Preconditions

- Have the user request, repository constraints, and known risks in hand.
- Have a current plan written in concrete steps with a verification approach.
- If no draft exists yet, write the first plan locally before starting the review loop.

## Workflow

1. Restate the plan target:
   - summarize scope, assumptions, and non-goals;
   - define the approval token as the exact single-line response `APPROVED`;
   - define the loop limit as reviewer passes, not total agent calls: default to 3 reviewer passes, raise to 5 only for genuinely complex work;
   - create a findings ledger with one entry per reviewer finding: `open`, `resolved`, `rejected as out of scope`, or `blocked`.

2. Launch a reviewer subagent:
   - prefer the `reviewer` agent type;
   - pass only raw task context, repository instructions, and the current plan;
   - ask for either the exact single-line response `APPROVED` with no extra text, or concrete findings grouped as scope issues, correctness risks, and missing verification;
   - instruct the reviewer not to expand scope and not to rewrite the entire plan unless a finding requires an example.

3. If the reviewer returns `APPROVED`, stop the loop:
   - publish the approved plan;
   - name the approval round;
   - do not keep iterating after explicit approval;
   - treat any response that contains `APPROVED` plus extra findings or caveats as not approved.

4. If the reviewer returns findings, launch a fixer subagent:
   - prefer the `worker` agent type;
   - do this only when at least one reviewer pass remains after the fix;
   - pass the same task context, the current plan, and the reviewer findings;
   - pass the findings ledger and require the fixer to map every open finding to a concrete plan change or an explicit blocked/out-of-scope note;
   - ask for a replacement plan, not a discussion;
   - require the fixer to keep scope tight and include verification for each step.

5. Integrate the revised plan locally:
   - keep good unchanged steps;
   - accept only changes that answer reviewer findings;
   - remove any new scope or speculative work;
   - update the findings ledger entry-by-entry;
   - update the coordinator's plan state before the next review round.

6. Repeat reviewer -> fixer rounds until one of these conditions is met:
   - the reviewer returns `APPROVED`;
   - the reviewer-pass limit is reached;
   - the feedback becomes contradictory under the contradiction rule below;
   - approval is blocked on missing user input.

7. If the loop stops without approval:
   - present the latest reviewer-validated plan, not an unreviewed fixer draft;
   - list the unresolved ledger entries and any missing inputs;
   - tell the user approval was not achieved.

## Recovery Rules

- If the reviewer output is malformed, rerun the reviewer once with a stricter format reminder. If the retry is still malformed, stop and report a review-format blocker.
- If the fixer output is malformed, rerun the fixer once with the missing sections called out. If the retry is still malformed, stop and report a fix-format blocker.
- If the current reviewer pass returns findings and no reviewer pass remains for validating a rewrite, do not launch a fixer. Stop with the latest reviewer-validated plan and findings.
- Treat feedback as contradictory only when two consecutive reviewer passes make mutually exclusive demands on the same unchanged requirement, or when a requested change would violate the user request or repository rules. Escalate the conflict instead of guessing.

## Prompt Templates

Use short prompts and keep them artifact-centered.

Reviewer prompt skeleton:

```text
Review this implementation plan against the user request and repository rules.
Return either:
1. APPROVED
or
2. Findings grouped as:
- Scope issues
- Correctness risks
- Missing verification

If you approve, return exactly one line: APPROVED
If any issue remains, do not use the word APPROVED.
Do not widen scope. Do not rewrite the whole plan unless needed to show a correction.
```

Fixer prompt skeleton:

```text
Revise this implementation plan to resolve the reviewer findings.
Return only:
1. Updated plan
2. Verification plan
3. Findings resolution map
4. Remaining assumptions or blockers

Keep the scope exactly aligned with the request and repository rules.
```

## Rules

- Preserve reviewer independence: do not send your preferred fix to the reviewer before the review pass.
- Preserve scope discipline: reject any fixer output that adds refactors, cleanup, or unrelated checks.
- Preserve verification quality: every implementation step should have a matching verification action or observable outcome.
- Preserve reviewer-pass integrity: never present an unreviewed fixer rewrite as the latest approved or latest best reviewed plan.
- Escalate to the user instead of looping forever when approval depends on missing business decisions.
- Do not start implementation under this skill until the plan is approved or the user explicitly waives approval.

## Deliverable

Return a concise planning package:
- requirements, assumptions, and risks;
- the approved plan or the latest non-approved plan;
- the verification plan;
- the findings ledger or unresolved objections;
- the current round result: `APPROVED` or unresolved blockers.

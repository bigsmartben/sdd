---
description: Generate the pending research.md artifact selected from the current feature branch plan.md.
handoffs:
  - label: Continue Test Matrix Queue
    agent: sdd.plan.test-matrix
    prompt: Run /sdd.plan.test-matrix with the same active feature branch context.
    send: true
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Argument Parsing

Treat all `$ARGUMENTS` as optional scoped user context.
Resolve `PLAN_FILE` from the current feature branch using `{SCRIPT}` defaults.

## Goal

Generate exactly one `research.md` artifact by consuming the first pending `research` row from `PLAN_FILE`.
This command is single-unit only and MUST NOT perform any other planning stage work.

Scope authority note: `research.md` output is **optional clarification input** for downstream planning stages — `/sdd.plan.data-model` may read it; `/sdd.plan.test-matrix` MUST NOT read it. However, the `research` stage row reaching `Status = done` is a **hard gate** for `/sdd.tasks`; this command must be completed successfully before task decomposition can begin.

Use `.specify/templates/research-template.md` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or prior outputs.

## Selection Rules

1. Run `{SCRIPT}` once from repo root. Resolve `FEATURE_DIR` and planning preflight context.
2. Resolve `PLAN_FILE` as `<FEATURE_DIR>/plan.md` and `FEATURE_SPEC` as `<FEATURE_DIR>/spec.md`; read only the resolved `PLAN_FILE`
3. Find the first `Stage Queue` row where:
   - `Stage ID = research`
   - `Status = pending`
4. If no such row exists, stop and report that the research queue is already complete
5. Do not scan the repository to invent other work

## Stage Packet (Research Unit)

Build one bounded run-local packet for the selected `research` row from:

- selected `Stage Queue` row in resolved `PLAN_FILE`
- `Shared Context Snapshot` in resolved `PLAN_FILE`
- resolved `FEATURE_SPEC` path
- selected row status/output-path/blocker fields

Use this packet as the default context for generation.
Do not load additional artifacts unless a selected-row blocker or a concrete decision-evidence gap explicitly requires them.

## Plan Control-Plane Input Path (Mandatory)

Use only the resolved `PLAN_FILE` from `{SCRIPT}` as planning control plane.
Ignore alternate `plan.md` paths from environment variables or repository discovery.
Non-`plan.md` user files are allowed only when already listed in `Allowed Inputs`; they never redefine control-plane state.
If `PLAN_FILE` is missing or non-consumable, stop and report a blocker.

## Allowed Inputs

Read only:

- `.specify/templates/research-template.md` for output structure
- selected `Stage Queue` row from the resolved `PLAN_FILE` only
- `Shared Context Snapshot` from the resolved `PLAN_FILE` only
- resolved `FEATURE_SPEC`
- `.specify/memory/constitution.md`
- targeted repo anchors when required by the active research blocker or by concrete decision-evidence gaps

### Conditional Inputs

Read additional files only when the selected row's blocker or a concrete decision-evidence gap cannot be resolved from the stage packet.
When conditional reads are required, prefer section-level rereads over whole-file replay.

### Repo Anchor Input Limits

Keep repo-backed reads bounded to the selected unit and active blocker.
When emitting `Repository Reuse Anchors`, every `Source Path / Symbol` value MUST be a concrete file path or `path/to/file.ext::Symbol`; module-root or directory-only placeholders such as `aidm-api/` are invalid.
If ambiguity/conflict remains after bounded reads, keep unresolved findings explicit in `research.md` and set row `Blocker` instead of expanding scope.

`research.md` remains the authoritative output for research semantics.
`PLAN_FILE` is queue state only.

## Required Writeback

After generating `research.md`, update the selected `Stage Queue` row only:

- `Status`
- `Output Path`
- `Blocker`

Do not write long summaries or detailed research prose back into `PLAN_FILE`.

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`: `/sdd.plan.test-matrix`
- `Decision Basis`: `test-matrix` consumes `spec.md` as its semantic source and does not depend on `research.md` output to proceed
- `Selected Stage ID`: selected `research` stage row id
- `Ready/Blocked`: `Ready` when the selected row is updated to `done`; otherwise `Blocked`

`Ready/Blocked` is stage-local readiness only and MUST NOT be treated as cross-artifact final PASS/FAIL; centralized final gating belongs to `/sdd.analyze`.
`research` remains optional clarification for `/sdd.plan.data-model`, but the `research` stage row must still be `done` before `/sdd.tasks` can proceed.

## Final Output

Report:

- resolved `PLAN_FILE`
- selected stage row id
- `research.md` path
- updated stage status
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected Stage ID`, and `Ready/Blocked`

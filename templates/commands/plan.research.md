---
description: Generate the pending research.md artifact selected from an explicit plan.md path.
handoffs:
  - label: Continue Data Model Queue
    agent: sdd.plan.data-model
    prompt: Continue the planning queue by running /sdd.plan.data-model <path/to/plan.md> with the same explicit plan.md path.
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

1. Parse the first positional token from `$ARGUMENTS` as `PLAN_FILE`
2. `PLAN_FILE` is mandatory and MUST resolve from repo root to an existing file named `plan.md`
3. `PLAN_FILE` MUST stay under `repo/specs/**`
4. Any remaining text after removing `PLAN_FILE` is optional scoped user context

If `PLAN_FILE` is missing or invalid, stop immediately and report the required invocation:

`/sdd.plan.research <path/to/plan.md> [context...]`

## Goal

Generate exactly one `research.md` artifact by consuming the first pending `research` row from `PLAN_FILE`.
This command is single-unit only and MUST NOT perform any other planning stage work.
Use `.specify/templates/research-template.md` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or prior outputs.

## Selection Rules

1. Run `{SCRIPT} --plan-file <PLAN_FILE>` once and resolve `FEATURE_DIR`, `FEATURE_SPEC`, and `IMPL_PLAN`
2. Read only the resolved `IMPL_PLAN`
3. Find the first `Stage Queue` row where:
   - `Stage ID = research`
   - `Status = pending`
4. If no such row exists, stop and report that the research queue is already complete
5. Do not scan the repository to invent other work

## Plan Control-Plane Input Path (Mandatory)

- Use only the explicit `PLAN_FILE` resolved through `{SCRIPT}` as planning control plane.
- Ignore alternate `plan.md` paths from environment variables or repository discovery. Non-`plan.md` user files are allowed only when they are already listed in `Allowed Inputs`; they never redefine control-plane state.
- If `PLAN_FILE` is missing or non-consumable, stop and report a blocker.

## Allowed Inputs

Read only:

- `.specify/templates/research-template.md` for output structure
- selected `Stage Queue` row from the explicit `PLAN_FILE` only
- `Shared Context Snapshot` from the explicit `PLAN_FILE` only
- resolved `FEATURE_SPEC`
- `.specify/memory/constitution.md`
- targeted repo anchors only when required by the active research blocker

`research.md` remains the authoritative output for research semantics.
`PLAN_FILE` is queue state only.

## Required Writeback

After generating `research.md`, update the selected `Stage Queue` row only:

- `Status`
- `Output Path`
- `Source Fingerprint`
- `Output Fingerprint`
- `Blocker`

Do not write long summaries or detailed research prose back into `PLAN_FILE`.

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`: `/sdd.plan.data-model <absolute path to plan.md>`
- `Decision Basis`: `Stage Queue` shows the selected `research` row is complete and the fixed next pending stage is `data-model`
- `Selected Stage ID`: selected `research` stage row id
- `Ready/Blocked`: `Ready` when the selected row is updated to `done`; otherwise `Blocked`

## Final Output

Report:

- resolved `PLAN_FILE`
- selected stage row id
- `research.md` path
- updated stage status
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected Stage ID`, and `Ready/Blocked`

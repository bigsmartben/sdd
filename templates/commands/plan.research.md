---
description: Generate the pending research.md artifact selected from FEATURE_DIR/plan.md Stage Queue.
handoffs:
  - label: Continue Data Model Queue
    agent: sdd.plan.data-model
    prompt: Continue the planning queue by generating the next pending data-model artifact from FEATURE_DIR/plan.md.
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

## Goal

Generate exactly one `research.md` artifact by consuming the first pending `research` row from `FEATURE_DIR/plan.md`.
This command is single-unit only and MUST NOT perform any other planning stage work.
Use `.specify/templates/research-template.md` as the structural source of truth for the generated artifact. If the runtime template is missing or non-consumable, stop and report the blocker. Do not substitute `templates/research-template.md`, any other template directory, or existing generated `research.md` files.

## Selection Rules

1. Run `{SCRIPT}` once and resolve `FEATURE_DIR`
2. Read only `FEATURE_DIR/plan.md`
3. Find the first `Stage Queue` row where:
   - `Stage ID = research`
   - `Status = pending`
4. If no such row exists, stop and report that the research queue is already complete
5. Do not scan the repository to invent other work

## Plan Control-Plane Input Path (Mandatory)

- The only allowed planning control-plane input path is `FEATURE_DIR/plan.md` resolved from `{SCRIPT}`.
- Do not accept, infer, or override any alternate `plan.md` path from `$ARGUMENTS`, environment variables, or repository scanning.
- User-provided non-`plan.md` file paths may be consumed only when they fall within this command's `Allowed Inputs` scope.
- User-provided files MUST NOT replace or redefine the planning control-plane source.
- If `FEATURE_DIR/plan.md` is missing or non-consumable, stop and report a blocker.

## Allowed Inputs

Read only:

- `.specify/templates/research-template.md` for output structure
- selected `Stage Queue` row from `FEATURE_DIR/plan.md` only
- `Shared Context Snapshot` from `FEATURE_DIR/plan.md` only
- `spec.md`
- `.specify/memory/constitution.md`
- targeted repo anchors only when required by the active research blocker

`research.md` remains the authoritative output for research semantics.
`FEATURE_DIR/plan.md` is queue state only.

## Required Writeback

After generating `research.md`, update the selected `Stage Queue` row only:

- `Status`
- `Output Path`
- `Source Fingerprint`
- `Output Fingerprint`
- `Blocker`

Do not write long summaries or detailed research prose back into `FEATURE_DIR/plan.md`.

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`: `/sdd.plan.data-model`
- `Decision Basis`: `Stage Queue` shows the selected `research` row is complete and the fixed next pending stage is `data-model`
- `Selected Stage ID`: selected `research` stage row id
- `Ready/Blocked`: `Ready` when the selected row is updated to `done`; otherwise `Blocked`

## Final Output

Report:

- selected stage row id
- `research.md` path
- updated stage status
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected Stage ID`, and `Ready/Blocked`

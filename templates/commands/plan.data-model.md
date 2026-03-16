---
description: Generate the pending data-model.md artifact selected from FEATURE_DIR/plan.md Stage Queue.
handoffs:
  - label: Continue Test Matrix Queue
    agent: sdd.plan.test-matrix
    prompt: Continue the planning queue by generating the next pending test-matrix artifact from FEATURE_DIR/plan.md.
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

Generate exactly one `data-model.md` artifact by consuming the first pending `data-model` row from `FEATURE_DIR/plan.md`.
This command is single-unit only and MUST NOT perform any other planning stage work.
Use `.specify/templates/data-model-template.md` as the structural source of truth for the generated artifact. If the runtime template is missing or non-consumable, stop and report the blocker. Do not substitute `templates/data-model-template.md`, any other template directory, or infer style/structure from other existing `data-model.md` files.

## Selection Rules

1. Run `{SCRIPT}` once and resolve `FEATURE_DIR`
2. Read only `FEATURE_DIR/plan.md`
3. Find the first `Stage Queue` row where:
   - `Stage ID = data-model`
   - `Status = pending`
4. Require the `research` row to be `done`
5. If the required row does not exist or prerequisites are not done, stop and report the blocker

## Plan Control-Plane Input Path (Mandatory)

- The only allowed planning control-plane input path is `FEATURE_DIR/plan.md` resolved from `{SCRIPT}`.
- Do not accept, infer, or override any alternate `plan.md` path from `$ARGUMENTS`, environment variables, or repository scanning.
- User-provided non-`plan.md` file paths may be consumed only when they fall within this command's `Allowed Inputs` scope.
- User-provided files MUST NOT replace or redefine the planning control-plane source.
- If `FEATURE_DIR/plan.md` is missing or non-consumable, stop and report a blocker.

## Path Constraints

- Limit reads to resolved `FEATURE_DIR` plus the explicit files listed in `Allowed Inputs`.
- Lifecycle anchors MUST be targeted symbols/files explicitly referenced by `Shared Context Snapshot` (or by a concrete blocker in the selected row).
- Do not perform repository-wide discovery/search to find additional context.
- Do not read other feature folders under `specs/`.
- Do not scan the repository for alternate `plan.md` paths.
- Do not use any existing `data-model.md` (outside the current target artifact path) as an input or style source.

## Allowed Inputs

Read only:

- `.specify/templates/data-model-template.md` for output structure
- selected `Stage Queue` row from `FEATURE_DIR/plan.md` only
- `Shared Context Snapshot` from `FEATURE_DIR/plan.md` only
- `spec.md`
- `research.md`
- targeted lifecycle repo anchors required for stable states and invariants

`data-model.md` remains the authoritative output for backbone semantics.
`FEATURE_DIR/plan.md` remains queue state plus binding projection state only.

## Required Writeback

After generating `data-model.md`, update the selected `Stage Queue` row only:

- `Status`
- `Output Path`
- `Source Fingerprint`
- `Output Fingerprint`
- `Blocker`

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`: `/sdd.plan.test-matrix`
- `Decision Basis`: `Stage Queue` shows the selected `data-model` row is complete and the fixed next pending stage is `test-matrix`
- `Selected Stage ID`: selected `data-model` stage row id
- `Ready/Blocked`: `Ready` when the selected row is updated to `done`; otherwise `Blocked`

## Final Output

Report:

- selected stage row id
- `data-model.md` path
- updated stage status
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected Stage ID`, and `Ready/Blocked`

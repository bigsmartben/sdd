---
description: Generate exactly one pending interface detail artifact selected from FEATURE_DIR/plan.md Artifact Status.
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

Generate exactly one minimum interface-detail artifact by consuming the first pending `interface-detail` row from `FEATURE_DIR/plan.md` `Artifact Status`.
This command MUST NOT generate multiple interface-detail files in one run.
Use `.specify/templates/interface-detail-template.md` as the structural source of truth for the generated artifact. If the runtime template is missing or non-consumable, stop and report the blocker. Do not substitute `templates/interface-detail-template.md`, any other template directory, or existing generated interface-detail files.

## Selection Rules

1. Run `{SCRIPT}` once and resolve `FEATURE_DIR`
2. Read only `FEATURE_DIR/plan.md`
3. In `Artifact Status`, find the first row where:
   - `Unit Type = interface-detail`
   - `Status = pending`
4. Resolve the matching `BindingRowID` row in `Binding Projection Index`
5. Require the matching contract row for the same `BindingRowID` to be `done`
6. If no pending interface-detail row exists, stop and report that the queue is complete

## Plan Control-Plane Input Path (Mandatory)

- The only allowed planning control-plane input path is `FEATURE_DIR/plan.md` resolved from `{SCRIPT}`.
- Do not accept, infer, or override any alternate `plan.md` path from `$ARGUMENTS`, environment variables, or repository scanning.
- User-provided non-`plan.md` file paths may be consumed only when they fall within this command's `Allowed Inputs` scope.
- User-provided files MUST NOT replace or redefine the planning control-plane source.
- If `FEATURE_DIR/plan.md` is missing or non-consumable, stop and report a blocker.

## Path Constraints

- Limit reads to resolved `FEATURE_DIR` plus the explicit files listed in `Allowed Inputs`.
- Complete `BindingRowID` selection, matching contract-row resolution, and prerequisite validation from `FEATURE_DIR/plan.md` before reading `research.md`, `data-model.md`, `test-matrix.md`, the matching contract artifact, or any repo anchors.
- Until the selected interface-detail row is resolved and the matching contract row is confirmed `done`, do not open repository files, generated artifacts, or run repository-wide discovery/search.
- After selection, read only the selected row's bound planning inputs, the matching contract artifact, and the targeted symbols/files required for that `BindingRowID`.
- Do not read other feature folders under `specs/`.
- Do not scan the repository for alternate `plan.md` paths.

## Allowed Inputs

Read only:

- `.specify/templates/interface-detail-template.md` for output structure
- selected `Artifact Status` row from `FEATURE_DIR/plan.md` only
- matching `BindingRowID` row from `Binding Projection Index` in `FEATURE_DIR/plan.md` only
- `Shared Context Snapshot` from `FEATURE_DIR/plan.md` only
- `research.md` when constraints materially affect this `BindingRowID`
- `data-model.md`
- `test-matrix.md`
- matching contract artifact
- targeted repo façade/DTO/collaborator anchors required for the selected `BindingRowID`

`interface-details/` remains the authoritative source for operation-local design semantics.
`FEATURE_DIR/plan.md` remains queue state plus stable binding keys only.

## Required Writeback

Update only the selected interface-detail row in `Artifact Status`:

- `Target Path`
- `Status`
- `Source Fingerprint`
- `Output Fingerprint`
- `Blocker`

Do not modify unrelated `BindingRowID` rows.
Do not write interface-detail prose into `FEATURE_DIR/plan.md`.

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`
- `Decision Basis`
- `Selected BindingRowID`: selected `BindingRowID`
- `Ready/Blocked`

Determine `Next Command` from `FEATURE_DIR/plan.md` state only after the selected interface-detail row writeback:

- If any `interface-detail` rows remain `pending`, `Next Command = /sdd.plan.interface-detail`
- Otherwise, if all required planning rows are complete, `Next Command = /sdd.tasks`
- Otherwise, if queue state is inconsistent with either condition, keep `Next Command` empty and set `Ready/Blocked = Blocked`

`Decision Basis` MUST cite the post-writeback `Artifact Status` state and planning-complete check that produced the routing decision.

## Final Output

Report:

- selected `BindingRowID`
- generated interface-detail path
- updated interface-detail row status
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected BindingRowID`, and `Ready/Blocked`

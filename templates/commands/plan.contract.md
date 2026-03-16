---
description: Generate exactly one pending contract artifact selected from FEATURE_DIR/plan.md Artifact Status.
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

Generate exactly one minimum contract artifact by consuming the first pending `contract` row from `FEATURE_DIR/plan.md` `Artifact Status`.
This command MUST NOT generate multiple contract files in one run.
Use `.specify/templates/contract-template.md` as the structural source of truth for the generated artifact. If the runtime template is missing or non-consumable, stop and report the blocker. Do not substitute `templates/contract-template.md`, any other template directory, or existing generated contract files.

## Selection Rules

1. Run `{SCRIPT}` once and resolve `FEATURE_DIR`
2. Read only `FEATURE_DIR/plan.md`
3. In `Artifact Status`, find the first row where:
   - `Unit Type = contract`
   - `Status = pending`
4. Resolve the matching `BindingRowID` row in `Binding Projection Index`
5. Require `test-matrix` stage row to be `done`
6. If no pending contract row exists, stop and report that the contract queue is complete

## Plan Control-Plane Input Path (Mandatory)

- The only allowed planning control-plane input path is `FEATURE_DIR/plan.md` resolved from `{SCRIPT}`.
- Do not accept, infer, or override any alternate `plan.md` path from `$ARGUMENTS`, environment variables, or repository scanning.
- User-provided non-`plan.md` file paths may be consumed only when they fall within this command's `Allowed Inputs` scope.
- User-provided files MUST NOT replace or redefine the planning control-plane source.
- If `FEATURE_DIR/plan.md` is missing or non-consumable, stop and report a blocker.

## Allowed Inputs

Read only:

- `.specify/templates/contract-template.md` for output structure
- selected `Artifact Status` row from `FEATURE_DIR/plan.md` only
- matching `BindingRowID` row from `Binding Projection Index` in `FEATURE_DIR/plan.md` only
- `Shared Context Snapshot` from `FEATURE_DIR/plan.md` only
- `spec.md`
- `data-model.md`
- `test-matrix.md`
- targeted repo boundary symbols, façade methods, and DTO anchors required for the selected `BindingRowID`

`contracts/` remains the authoritative source for interface semantics.
`FEATURE_DIR/plan.md` is queue state plus stable binding keys only.

## Required Writeback

Update only the selected contract row in `Artifact Status`:

- `Target Path`
- `Status`
- `Source Fingerprint`
- `Output Fingerprint`
- `Blocker`

Do not modify unrelated `BindingRowID` rows.
Do not write contract semantics into `FEATURE_DIR/plan.md`.

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`
- `Decision Basis`
- `Selected BindingRowID`: selected `BindingRowID`
- `Ready/Blocked`

Determine `Next Command` from `FEATURE_DIR/plan.md` state only after the selected contract row writeback:

- If any `contract` rows remain `pending`, `Next Command = /sdd.plan.contract`
- Otherwise, if no `contract` rows remain `pending` and at least one `interface-detail` row is `pending`, `Next Command = /sdd.plan.interface-detail`
- Otherwise, if queue state is inconsistent with either condition, keep `Next Command` empty and set `Ready/Blocked = Blocked`

`Decision Basis` MUST cite the post-writeback `Artifact Status` state that produced the routing decision.

## Final Output

Report:

- selected `BindingRowID`
- generated contract path
- updated contract row status
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected BindingRowID`, and `Ready/Blocked`

---
description: Generate the pending test-matrix.md artifact and initialize binding rows in FEATURE_DIR/plan.md.
handoffs:
  - label: Continue Contract Queue
    agent: sdd.plan.contract
    prompt: Continue the planning queue by generating the next pending contract artifact from FEATURE_DIR/plan.md.
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

Generate exactly one `test-matrix.md` artifact by consuming the first pending `test-matrix` row from `FEATURE_DIR/plan.md`.
After writing `test-matrix.md`, initialize or refresh the `Binding Projection Index` and `Artifact Status` tables in `FEATURE_DIR/plan.md`.
Use `.specify/templates/test-matrix-template.md` as the structural source of truth for the generated artifact. If the runtime template is missing or non-consumable, stop and report the blocker. Do not substitute `templates/test-matrix-template.md`, any other template directory, or existing generated `test-matrix.md` files.

## Selection Rules

1. Run `{SCRIPT}` once and resolve `FEATURE_DIR`
2. Read only `FEATURE_DIR/plan.md`
3. Find the first `Stage Queue` row where:
   - `Stage ID = test-matrix`
   - `Status = pending`
4. Require `research` and `data-model` rows to be `done`
5. If prerequisites are not satisfied, stop and report the blocker

## Plan Control-Plane Input Path (Mandatory)

- The only allowed planning control-plane input path is `FEATURE_DIR/plan.md` resolved from `{SCRIPT}`.
- Do not accept, infer, or override any alternate `plan.md` path from `$ARGUMENTS`, environment variables, or repository scanning.
- User-provided non-`plan.md` file paths may be consumed only when they fall within this command's `Allowed Inputs` scope.
- User-provided files MUST NOT replace or redefine the planning control-plane source.
- If `FEATURE_DIR/plan.md` is missing or non-consumable, stop and report a blocker.

## Allowed Inputs

Read only:

- `.specify/templates/test-matrix-template.md` for output structure
- selected `Stage Queue` row from `FEATURE_DIR/plan.md` only
- `Shared Context Snapshot` from `FEATURE_DIR/plan.md` only
- `spec.md`
- `research.md`
- `data-model.md`

`test-matrix.md` remains the authoritative source for verification semantics and stable tuple keys.
`FEATURE_DIR/plan.md` receives only a binding projection index and artifact queue rows derived from that matrix.

## Binding Projection Rules

Project stable and unique binding rows from `test-matrix.md` into `Binding Projection Index` only.
Do not copy narrative scenario prose into `FEATURE_DIR/plan.md`.

Required columns in each binding row:

- `BindingRowID`
- `UC ID`
- `UIF ID`
- `FR ID`
- `IF ID / IF Scope`
- `TM ID`
- `TC IDs`
- `Operation ID`
- `Boundary Anchor`

For each `BindingRowID`, initialize exactly two `Artifact Status` rows:

1. `Unit Type = contract`
2. `Unit Type = interface-detail`

Each artifact row must include:

- `BindingRowID`
- `Unit Type`
- `Target Path`
- `Status = pending`
- `Source Fingerprint`
- `Output Fingerprint`
- `Blocker`

The total number of minimum planning interface units equals the row count of `Binding Projection Index`.

## Required Writeback

Update only:

- selected `test-matrix` stage row status and fingerprints
- `Binding Projection Index`
- `Artifact Status`

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`: `/sdd.plan.contract`
- `Decision Basis`: `Binding Projection Index` and `Artifact Status` are refreshed from `test-matrix.md`, and the next planning unit starts at the first pending `contract` row
- `Selected Stage ID`: selected `test-matrix` stage row id
- `Ready/Blocked`: `Ready` when binding rows and artifact rows are initialized successfully; otherwise `Blocked`

## Final Output

Report:

- selected stage row id
- `test-matrix.md` path
- `Binding Projection Index` row count
- initialized `Artifact Status` row count
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected Stage ID`, and `Ready/Blocked`

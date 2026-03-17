---
description: Generate the pending test-matrix.md artifact and initialize binding rows from an explicit plan.md path.
handoffs:
  - label: Continue Contract Queue
    agent: sdd.plan.contract
    prompt: Continue the planning queue by running /sdd.plan.contract <path/to/plan.md> with the same explicit plan.md path.
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

`/sdd.plan.test-matrix <path/to/plan.md> [context...]`

## Goal

Generate exactly one `test-matrix.md` artifact by consuming the first pending `test-matrix` row from `PLAN_FILE`.
After writing `test-matrix.md`, initialize or refresh the `Binding Projection Index` and `Artifact Status` tables in `PLAN_FILE`.
Use `.specify/templates/test-matrix-template.md` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or prior outputs.

## Selection Rules

1. Run `{SCRIPT} --plan-file <PLAN_FILE>` once and resolve `FEATURE_DIR`, `FEATURE_SPEC`, and `IMPL_PLAN`
2. Read only the resolved `IMPL_PLAN`
3. Find the first `Stage Queue` row where:
   - `Stage ID = test-matrix`
   - `Status = pending`
4. Require `research` and `data-model` rows to be `done`
5. If prerequisites are not satisfied, stop and report the blocker

## Plan Control-Plane Input Path (Mandatory)

- Use only the explicit `PLAN_FILE` resolved through `{SCRIPT}` as planning control plane.
- Ignore alternate `plan.md` paths from environment variables or repository discovery. Non-`plan.md` user files are allowed only when they are already listed in `Allowed Inputs`; they never redefine control-plane state.
- If `PLAN_FILE` is missing or non-consumable, stop and report a blocker.

## Allowed Inputs

Read only:

- `.specify/templates/test-matrix-template.md` for output structure
- selected `Stage Queue` row from the explicit `PLAN_FILE` only
- `Shared Context Snapshot` from the explicit `PLAN_FILE` only
- resolved `FEATURE_SPEC`
- `research.md`
- `data-model.md`

`test-matrix.md` remains the authoritative source for verification semantics and stable tuple keys.
`PLAN_FILE` receives only a binding projection index and artifact queue rows derived from that matrix.

## Binding Projection Rules

Project only stable and unique binding rows from `test-matrix.md` into `Binding Projection Index`.
Do not copy scenario prose into `PLAN_FILE`.
Project `Boundary Anchor` as the client-facing contract binding key only, preserving the first consumer-callable entry selected in `test-matrix.md`.
Do not add internal handoff fields to `Binding Projection Index`; realization-design details are authored in the generated `contracts/` artifact.
Apply repo-anchor decision order `existing -> extended -> new -> todo`.
`extended` is valid only for same-entity field/state expansion.
`new` is normative only when explicit `path::symbol` target evidence is present.
Rows with `Anchor Status = todo` remain forward-looking/non-normative and MUST NOT be projected as main-path binding rows.

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

For each `BindingRowID`, initialize exactly one `Artifact Status` row:

1. `Unit Type = contract`

Each artifact row must include:

- `BindingRowID`
- `Unit Type`
- `Target Path`
- `Status = pending`
- `Source Fingerprint`
- `Output Fingerprint`
- `Blocker`

The total number of minimum planning artifact units equals the row count of `Binding Projection Index`.

## Required Writeback

Update only:

- selected `test-matrix` stage row status and fingerprints
- `Binding Projection Index`
- `Artifact Status`

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`: `/sdd.plan.contract <absolute path to plan.md>`
- `Decision Basis`: `Binding Projection Index` and `Artifact Status` are refreshed from `test-matrix.md`, and the next planning unit starts at the first pending `contract` row
- `Selected Stage ID`: selected `test-matrix` stage row id
- `Ready/Blocked`: `Ready` when binding rows and artifact rows are initialized successfully; otherwise `Blocked`

## Final Output

Report:

- resolved `PLAN_FILE`
- selected stage row id
- `test-matrix.md` path
- `Binding Projection Index` row count
- initialized `Artifact Status` row count
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected Stage ID`, and `Ready/Blocked`

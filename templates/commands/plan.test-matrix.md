---
description: Generate the pending test-matrix.md artifact and initialize binding rows from an explicit plan.md path.
handoffs:
  - label: Continue Contract Queue
    agent: sdd.plan.contract
    prompt: Run /sdd.plan.contract <path/to/plan.md> with the same absolute plan.md path.
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

## Stage Packet (Test-Matrix Unit)

Build one bounded run-local packet for the selected `test-matrix` row from:

- selected `Stage Queue` row in explicit `PLAN_FILE`
- `Shared Context Snapshot` in explicit `PLAN_FILE`
- resolved `FEATURE_SPEC` path
- resolved `research.md` path
- resolved `data-model.md` path
- selected row source/output fingerprint fields

Use this packet as the default context for generation and binding projection.
Do not load additional artifacts unless the selected-row blocker cannot be resolved from this packet.

## Plan Control-Plane Input Path (Mandatory)

Use only the explicit `PLAN_FILE` resolved through `{SCRIPT}` as planning control plane.
Ignore alternate `plan.md` paths from environment variables or repository discovery.
Non-`plan.md` user files are allowed only when already listed in `Allowed Inputs`; they never redefine control-plane state.
If `PLAN_FILE` is missing or non-consumable, stop and report a blocker.

## Allowed Inputs

Read only:

- `.specify/templates/test-matrix-template.md` for output structure
- selected `Stage Queue` row from the explicit `PLAN_FILE` only
- `Shared Context Snapshot` from the explicit `PLAN_FILE` only
- resolved `FEATURE_SPEC`
- `research.md`
- `data-model.md`

When consuming allowed inputs, prefer section-level rereads over whole-file replay for the selected unit.

`test-matrix.md` remains the authoritative source for verification semantics and stable tuple keys.
`test-matrix.md` also carries the per-binding contract bootstrap packet consumed by `/sdd.plan.contract`.
`PLAN_FILE` receives only a compact binding projection index and artifact queue rows derived from that matrix.

## Binding Projection Rules

Project only stable and unique binding rows from `test-matrix.md` into `Binding Projection Index`.
Do not copy scenario prose into `PLAN_FILE`.
Project `Boundary Anchor` as the client-facing contract binding key only, preserving the first consumer-callable entry selected in `test-matrix.md`.
Project only the minimum extra fields required to help `/sdd.plan.contract` select and validate the next unit without re-reading broad context.
Keep DTO anchors, collaborator anchors, and other realization-detail evidence in `test-matrix.md`; do not mirror them into `PLAN_FILE`.
Apply repo-anchor decision order `existing -> extended -> new -> todo`.
`extended` is valid only for same-entity field/state expansion.
`new` is normative only when explicit `path::symbol` target evidence is present.
Rows with `Boundary Anchor Status = todo` or `Implementation Entry Anchor Status = todo` remain forward-looking/non-normative and MUST NOT be projected as main-path binding rows.

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
- `Implementation Entry Anchor`
- `Boundary Anchor Status`
- `Implementation Entry Anchor Status`
- `Test Scope`

## Binding Contract Packet Requirements

For each stable binding in `test-matrix.md`, emit a contract bootstrap packet that `/sdd.plan.contract` can consume without re-deriving the tuple from broad context.
This packet remains authoritative in `test-matrix.md`; do not mirror it in full into `PLAN_FILE`.

Each binding packet MUST include:

- `BindingRowID`
- `Operation ID`
- `IF Scope`
- `Boundary Anchor`
- `Boundary Anchor Status`
- `Implementation Entry Anchor`
- `Implementation Entry Anchor Status`
- `Request DTO Anchor`
- `Response DTO Anchor`
- `Primary Collaborator Anchor`
- `TM ID`
- `TC IDs`
- `Spec Ref(s)`
- `Scenario Ref(s)`
- `Success Ref(s)`
- `Edge Ref(s)`
- `Main Pass Anchor`
- `Branch/Failure Anchor(s)`

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

---
description: Generate the pending test-matrix.md artifact and initialize binding rows from the current feature branch plan.md.
handoffs:
  - label: Continue Contract Queue
    agent: sdd.plan.contract
    prompt: Run /sdd.plan.contract with the same active feature branch context.
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

Generate exactly one `test-matrix.md` artifact by consuming the first pending `test-matrix` row from `PLAN_FILE`.
After writing `test-matrix.md`, initialize or refresh the `Binding Projection Index` and `Artifact Status` tables in `PLAN_FILE`.
This stage owns feature-level test strategy: coverage scope, path decomposition, verification goals, observability signals, and the contract seed packets required downstream.
Use `.specify/templates/test-matrix-template.md` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or prior outputs.

## Selection Rules

1. Run `{SCRIPT}` once from repo root. Resolve `FEATURE_DIR`, `FEATURE_SPEC`, and `IMPL_PLAN`
2. Read only the resolved `IMPL_PLAN`
3. Find the first `Stage Queue` row where:
   - `Stage ID = test-matrix`
   - `Status = pending`
4. Require `research` and `data-model` rows to be `done`
5. If prerequisites are not satisfied, stop and report the blocker

## Stage Packet (Test-Matrix Unit)

Build one bounded run-local packet for the selected `test-matrix` row from:

- selected `Stage Queue` row in resolved `PLAN_FILE`
- `Shared Context Snapshot` in resolved `PLAN_FILE`
- resolved `FEATURE_SPEC` path
- resolved `research.md` path
- resolved `data-model.md` path
- selected row source/output fingerprint fields

Use this packet as the default context for generation and binding projection.
Do not load additional artifacts unless the selected-row blocker cannot be resolved from this packet.

## Plan Control-Plane Input Path (Mandatory)

Use only the resolved `PLAN_FILE` from `{SCRIPT}` as planning control plane.
Ignore alternate `plan.md` paths from environment variables or repository discovery.
Non-`plan.md` user files are allowed only when already listed in `Allowed Inputs`; they never redefine control-plane state.
If `PLAN_FILE` is missing or non-consumable, stop and report a blocker.

## Allowed Inputs

Read only:

- `.specify/templates/test-matrix-template.md` for output structure
- selected `Stage Queue` row from the resolved `PLAN_FILE` only
- `Shared Context Snapshot` from the resolved `PLAN_FILE` only
- resolved `FEATURE_SPEC`
- `research.md`
- `data-model.md`

When consuming allowed inputs, prefer section-level rereads over whole-file replay for the selected unit.

`test-matrix.md` remains the authoritative source for verification semantics and stable tuple keys.
`test-matrix.md` also carries the per-binding contract seed packet consumed by `/sdd.plan.contract`.
`PLAN_FILE` receives only a compact binding projection index and artifact queue rows derived from that matrix.
Treat `data-model.md` as authoritative for globally stable owner classes/fields/states that support shared projections, derivations, counters, badges, role labels, and lifecycle guards.
Use `spec.md` as the primary source for deciding which paths must be covered and what each path must prove; use `data-model.md` only to keep that strategy inside the declared model boundary.

## Binding Projection Rules

Project only stable and unique binding rows from `test-matrix.md` into `Binding Projection Index`.
Do not copy scenario prose into `PLAN_FILE`.
Project `Boundary Anchor` as the client-facing contract binding key only, preserving the first consumer-callable entry selected in `test-matrix.md`.
For HTTP-facing bindings, keep the HTTP route as `Boundary Anchor` and the owning controller method as `Implementation Entry Anchor`.
If a selected binding drifts away from controller-first HTTP placement, correct it back to `HTTP METHOD /path -> controller -> collaborator` and record the drift/blocker in the generation output rather than preserving the wrong tuple.
Project only the minimum extra fields required to help `/sdd.plan.contract` select and validate the next unit without re-reading broad context.
Keep DTO anchors, state-owner anchors, collaborator anchors, and other realization-detail evidence in `test-matrix.md`; do not mirror them into `PLAN_FILE`.
Apply repo-anchor decision order `existing -> extended -> new`.
`extended` is valid only for same-entity field/state expansion.
`new` is normative only when explicit `path::symbol` target evidence is present.
Rows with `Boundary Anchor Status = todo` or `Implementation Entry Anchor Status = todo` remain forward-looking/non-normative and MUST NOT be projected as main-path binding rows.
`Request DTO Anchor`, `Response DTO Anchor`, and `State Owner Anchor(s)` MAY remain `TODO(REPO_ANCHOR)` only as explicit contract-gap sources; they MUST NOT trigger a fallback back to minimal-field contract output.
Do not introduce new globally stable state owners, owner fields, or lifecycle vocabulary that are absent from `data-model.md`; when a selected binding needs them, keep the gap explicit and route upstream to `/sdd.plan.data-model`.

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

For each stable binding in `test-matrix.md`, emit an authoritative contract seed packet that `/sdd.plan.contract` can consume without re-deriving the tuple from broad context.
This packet remains authoritative in `test-matrix.md`; do not mirror it in full into `PLAN_FILE`.
The packet MUST be sufficient to seed the operation-scoped `Full Field Dictionary` in `contracts/`, even when some field anchors remain explicit gaps.

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
- `State Owner Anchor(s)`
- `TM ID`
- `TC IDs`
- `Spec Ref(s)`
- `Scenario Ref(s)`
- `Success Ref(s)`
- `Edge Ref(s)`
- `Main Pass Anchor`
- `Branch/Failure Anchor(s)`

When the selected binding is HTTP-facing, keep the first downstream service/facade symbol in `Primary Collaborator Anchor`; if the controller symbol cannot be confirmed, set `Implementation Entry Anchor = TODO(REPO_ANCHOR)` and `Implementation Entry Anchor Status = todo` rather than guessing.
`Primary Collaborator Anchor` MAY be `N/A`, but `State Owner Anchor(s)` MUST NOT be replaced by `Primary Collaborator Anchor`.
`State Owner Anchor(s)` MUST identify the owner classes that this operation reads, writes, projects, or uses for state/default/validation decisions.
If a required `State Owner Anchor(s)` row would introduce a new owner concept or owner field that `data-model.md` did not model as globally stable, block the selected row and send the issue back to `/sdd.plan.data-model` instead of widening Stage 2 scope.

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

- `Next Command`: `/sdd.plan.contract`
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

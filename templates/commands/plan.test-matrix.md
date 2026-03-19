---
description: Generate the pending test-matrix.md artifact and initialize binding rows from the current feature branch plan.md.
handoffs:
  - label: Continue Data-Model Queue
    agent: sdd.plan.data-model
    prompt: Run /sdd.plan.data-model with the same active feature branch context.
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
This stage owns only two outputs:

- stable binding projection from `spec.md`
- test semantics for those bindings
- one spec-derived `UIF Full Path (Mermaid)` section that completes the overview UIF by integrating relevant `UC`-local UIF paths into one replayable flow

Use `.specify/templates/test-matrix-template.md` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or prior outputs.

## Selection Rules

1. Run `{SCRIPT}` once from repo root. Resolve `FEATURE_DIR` and planning preflight context.
2. Resolve `PLAN_FILE` as `<FEATURE_DIR>/plan.md` and `FEATURE_SPEC` as `<FEATURE_DIR>/spec.md`; read only the resolved `PLAN_FILE`
3. Find the first `Stage Queue` row where:
   - `Stage ID = test-matrix`
   - `Status = pending`
4. Require resolved `FEATURE_SPEC` to be consumable
5. Do not require `research` or `data-model` rows to be `done` before this stage
6. Keep this stage scoped to spec-driven binding projection and test semantics only

## Stage Packet (Test-Matrix Unit)

Build one bounded run-local packet for the selected `test-matrix` row from:

- selected `Stage Queue` row in resolved `PLAN_FILE`
- `Shared Context Snapshot` in resolved `PLAN_FILE`
- resolved `FEATURE_SPEC` path
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

When consuming allowed inputs, prefer section-level rereads over whole-file replay for the selected unit.

Do not consume `research.md`, `data-model.md`, repo anchors, or generated contract artifacts in this stage.
`test-matrix.md` remains the authoritative source for verification semantics and stable binding packets.
`PLAN_FILE` receives only the compact projection needed to select downstream contract work.

## Binding Projection Rules

Project only stable and unique binding rows from `test-matrix.md` into `Binding Projection Index`.
Do not copy scenario prose into `PLAN_FILE`.

One `BindingRowID` corresponds to one UIF-based consumer-visible interface binding unit.
Determine uniqueness from:

- consumer-visible interaction family
- `Operation ID`
- `IF Scope`
- `UIF Path Ref(s)`

Apply these rules exactly:

- Merge happy / alternate / exception paths when they preserve the same interaction family, requirement projection, and external contract intent.
- Represent merged-path differences only through `TC IDs`, `Scenario Ref(s)`, `Success Ref(s)`, and `Edge Ref(s)`.
- Split bindings when UIF path family changes, UDD projection scope changes, or consumer-visible trigger/result semantics change.
- Do not create a packet for pure internal steps.
- Do not create a new packet for a branch or exception path that still belongs to the same binding.

Required columns in each binding row:

- `BindingRowID`
- `UC ID`
- `UIF ID`
- `FR ID`
- `IF ID / IF Scope`
- `TM ID`
- `TC IDs`
- `Operation ID`
- `UIF Path Ref(s)`
- `UDD Ref(s)`
- `Test Scope`

## Test Semantics Requirements

`Scenario Matrix` and `Verification Case Anchors` define the bounded test semantics for each binding.
Keep them spec-led and verification-led:

- emit one `UIF Full Path (Mermaid)` section for the selected feature scope as a spec-derived overview UIF completion
- integrate the relevant `UC`-internal UIF paths into one consumer-visible full-path map instead of leaving them fragmented across `UC` sections
- derive that Mermaid section only from `spec.md`; do not treat it as repo realization, interface closure, or implementation sequencing
- use the happy path as the backbone and extend it with alternate / exception / degraded branches only when they materially complete the same spec-defined path family
- `Scenario Matrix` captures path type, preconditions, expected outcomes, and related spec refs
- `Verification Case Anchors` captures what each case proves and how it is observed
- use the smallest row set that still preserves materially distinct behavior
- do not repeat `Operation ID` or `IF Scope` inside `TM/TC` rows when the owning binding packet already fixes them
- keep `Observability / Signal` focused on pass/fail evidence
- do not infer controllers, services, DTOs, collaborators, repository anchors, or shared-semantics ownership into the Mermaid or TM/TC outputs

## Binding Contract Packet Requirements

For each stable binding in `test-matrix.md`, emit one authoritative minimal packet for that binding.
This packet remains authoritative in `test-matrix.md`; do not mirror it in full into `PLAN_FILE`.
It identifies what the binding is and which spec/test slices belong to it.

Each binding packet MUST include:

- `BindingRowID`
- `Operation ID`
- `IF Scope`
- `UIF Path Ref(s)`
- `UDD Ref(s)`
- `TM ID`
- `TC IDs`
- `Test Scope`
- `Spec Ref(s)`
- `Scenario Ref(s)`
- `Success Ref(s)`
- `Edge Ref(s)`

Field semantics MUST stay deterministic and stable:

- `BindingRowID`: one stable downstream contract unit
- `Operation ID`: spec-defined operation token
- `IF Scope`: interface scope aligned to the same binding
- `UIF Path Ref(s)`: consumer-visible path refs that define the interaction family
- `UDD Ref(s)`: data refs that materially affect the binding; use `N/A` when none apply
- `TM ID`: primary scenario row for the packet
- `TC IDs`: ordered verification case ids for the same binding
- `Test Scope`: concise statement of covered behavior surface
- `Spec Ref(s)`: authoritative `UC / FR / UIF / UDD` refs
- `Scenario Ref(s)`: scenario refs that materialize the packet
- `Success Ref(s)`: refs proving main-path behavior
- `Edge Ref(s)`: refs proving alternate / exception / degraded behavior

Treat the packet as a spec-slice locator:

- `Spec Ref(s)` must point to the authoritative `UC / FR / UIF / UDD` ids behind the binding
- `UIF Path Ref(s)` must locate the exact consumer-visible path family that defines the binding
- `UDD Ref(s)` must locate only the data semantics actually needed downstream
- `Scenario Ref(s)`, `Success Ref(s)`, and `Edge Ref(s)` must be direct locator refs, not copied prose
- the packet should eliminate rebinding work without becoming a second semantic authority beside `spec.md`

If the selected packet cannot be closed from `spec.md` and selected plan-row context, keep the missing projection explicit in stage output and set blockers.

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

- `Next Command`: `/sdd.plan.data-model`
- `Decision Basis`: `test-matrix` derives stable binding projections and test semantics from `spec.md`; `data-model` aligns shared semantics for those bindings before contract design
- `Selected Stage ID`: selected `test-matrix` stage row id
- `Ready/Blocked`: `Ready` when binding rows and artifact rows are initialized successfully; otherwise `Blocked`

`Ready/Blocked` is stage-local readiness only and MUST NOT be treated as cross-artifact final PASS/FAIL; centralized final gating belongs to `/sdd.analyze`.

## Final Output

Report:

- resolved `PLAN_FILE`
- selected stage row id
- `test-matrix.md` path
- `Binding Projection Index` row count
- initialized `Artifact Status` row count
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected Stage ID`, and `Ready/Blocked`

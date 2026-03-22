---
description: Generate the pending test-matrix.md artifact, derive stable northbound interface partitions, and initialize Binding Projection Index and Artifact Status contract rows in plan.md.
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
This stage owns these outputs:

- stable northbound interface partition decisions from `spec.md` plus bounded repo evidence
- stable binding projection for those interface units
- test semantics attached to those bindings
- one spec-derived `UIF Full Path Coverage Graph (Mermaid)` plus `UIF Path Coverage Ledger` that provide full-path coverage over selected-scope UIF paths

Use `.specify/templates/test-matrix-template.md` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or prior outputs.

## Selection Rules

1. Run `{SCRIPT}` once from repo root. Resolve `FEATURE_DIR` and planning preflight context.
2. Resolve `PLAN_FILE` as `<FEATURE_DIR>/plan.md` and `FEATURE_SPEC` as `<FEATURE_DIR>/spec.md`; read only the resolved `PLAN_FILE`
3. Find the first `Stage Queue` row where:
   - `Stage ID = test-matrix`
   - `Status = pending`
4. Require resolved `FEATURE_SPEC` to be consumable
5. Do not require `research` or `data-model` rows to be `done` before this stage
6. Keep this stage scoped to spec-led interface partitioning plus bounded repo-informed landing hints; do not perform contract closure in this stage

## Stage Packet (Test-Matrix Unit)

Build one bounded run-local packet for the selected `test-matrix` row from:

- selected `Stage Queue` row in resolved `PLAN_FILE`
- `Shared Context Snapshot` in resolved `PLAN_FILE`
- `Repository-First Consumption Slice` in resolved `PLAN_FILE`
- resolved `FEATURE_SPEC` path
- selected row status/output-path/blocker fields

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
- `Repository-First Consumption Slice` from the resolved `PLAN_FILE` only
- resolved `FEATURE_SPEC`
- bounded repo evidence needed to decide whether candidate user actions land on the same northbound entry family:
  - existing northbound entry candidates
  - adjacent request / response models
  - permission / idempotency / transaction / side-effect evidence
  - only when those reads are directly relevant to the selected feature scope

When consuming allowed inputs, prefer section-level rereads over whole-file replay for the selected unit.

Do not consume `data-model.md` or generated contract artifacts in this stage.
`test-matrix.md` remains the authoritative source for verification semantics and stable binding packets.
`PLAN_FILE` receives only the compact projection needed to select downstream contract work.

## Interface Partition Rules

Derive northbound interface partitions before writing test packets.
This stage answers "how many northbound interface units exist for this feature slice?" before it answers "which TM/TC rows verify them?"

One `BindingRowID` corresponds to one client-callable northbound interface unit.
It is not a page-state bucket and not a path-family bucket.

Determine partition uniqueness from:

- user intent / northbound action
- consumer-visible trigger boundary
- request semantics
- visible result semantics
- side-effect type
- permission / idempotency / transaction boundary
- bounded repo landing hint

Apply these rules exactly:

- Split bindings when user intent, request semantics, side effect, permission boundary, idempotency semantics, transaction boundary, or repo landing family materially differ.
- Merge `Happy` / `Alternate` / `Exception` / `Degraded` / `Duplicate` / `Timeout` paths when they still exercise the same northbound action boundary.
- Do not split a binding only because `Path Type` changes across those verification paths under the same northbound action.
- Do not split a binding only because page state, button state, reminder behavior, or branch path differs under the same northbound action.
- Do not split a binding only because one action has multiple validation or duplicate branches.

## Binding Projection Rules

Project only stable and unique binding rows from `test-matrix.md` into `Binding Projection Index`.
Do not copy scenario prose into `PLAN_FILE`.

Apply these rules exactly:

- Merge TM/TC branches when they preserve the same northbound action boundary, requirement projection, and repo landing hint.
- Represent merged-path differences only through `TC IDs`, `Scenario Ref(s)`, `Success Ref(s)`, and `Edge Ref(s)`.
- Split bindings when the upstream interface partition rules identify a different northbound action unit.
- Do not create a packet for pure internal steps.
- Do not create a new packet for a branch or exception path that still belongs to the same binding.

Required columns in each `Binding Projection Index` row:

- `BindingRowID`
- `UC ID`
- `UIF ID`
- `FR ID`
- `IF ID / IF Scope`
- `Trigger Ref(s)`
- `Primary TM IDs`
- `TC IDs`
- `UIF Path Ref(s)`
- `UDD Ref(s)`
- `Test Scope`

Projection encoding rules:

- `IF ID / IF Scope` must contain one normalized scope token (`IF-###` or `N/A`) only.
- `UC ID`, `UIF ID`, and `FR ID` must use deterministic id encoding when multiple refs are needed (comma-separated ids, stable sort, no prose).

## Test Semantics Requirements

`Scenario Matrix` and `Verification Case Anchors` define the bounded test semantics for each binding.
Keep them spec-led and verification-led:

- emit one `UIF Full Path Coverage Graph (Mermaid)` section for the selected feature scope as a spec-derived overview UIF completion
- integrate the relevant `UC`-internal UIF paths into one consumer-visible full-path map instead of leaving them fragmented across `UC` sections
- derive that Mermaid section only from `spec.md`; do not treat it as repo realization, interface closure, or implementation sequencing
- use the happy path as the backbone and extend it with alternate / exception / degraded branches only when they materially complete the same spec-defined path family
- require full selected-scope UIF path accounting via `UIF Path Coverage Ledger`:
  - every selected-scope `UIF Path Ref` is present exactly once in the ledger
  - rows rendered in Mermaid must be marked `Included in Graph = yes`
  - rows intentionally omitted from Mermaid must be marked `Included in Graph = no` with explicit omission reason
- `Scenario Matrix` captures path type, preconditions, expected outcomes, related spec refs, and the owning `BindingRowID`
- `Path Type` is verification coverage metadata only; it does not define a new interface partition by itself
- `Verification Case Anchors` captures what each case proves and how it is observed
- use the smallest row set that still preserves materially distinct behavior
- do not let `TM/TC` rows redefine interface partition boundaries; they attach to the already-decided `BindingRowID`
- keep `Observability / Signal` focused on pass/fail evidence
- do not infer controllers, services, DTOs, collaborators, repository anchors, or shared-semantics ownership into the Mermaid or TM/TC outputs

## Binding Packet Requirements

For each stable binding in `test-matrix.md`, emit one authoritative complete scope-reference packet for that binding.
This packet remains authoritative in `test-matrix.md`; do not mirror it in full into `PLAN_FILE`.
It identifies what the binding is and which spec/test slices belong to it.

Each binding packet MUST include:

- `BindingRowID`
- `IF Scope`
- `User Intent`
- `Trigger Ref(s)`
- `Request Semantics`
- `Visible Result`
- `Side Effect`
- `Boundary Notes`
- `Repo Landing Hint`
- `UIF Path Ref(s)`
- `UDD Ref(s)`
- `Primary TM IDs`
- `TM IDs`
- `TC IDs`
- `Test Scope`
- `Spec Ref(s)`
- `Scenario Ref(s)`
- `Success Ref(s)`
- `Edge Ref(s)`

Field semantics MUST stay deterministic and stable:

- `BindingRowID`: one stable downstream contract unit
- `IF Scope`: interface scope aligned to the same binding
- `User Intent`: concise statement of the northbound action this binding exists to serve
- `Trigger Ref(s)`: user-visible trigger refs that identify the northbound action boundary
- `Request Semantics`: behavior-significant input semantics only; do not use DTO or class names
- `Visible Result`: the contract-visible result class of the binding from the user's perspective
- `Side Effect`: the externally meaningful state change, persistence, authorization, or transition effect; use `none` for read-only bindings
- `Boundary Notes`: lightweight notes about idempotency, permission, transaction, or state-transition characteristics that influenced the split
- `Repo Landing Hint`: bounded hint about the likely northbound entry family; not a final boundary anchor
- `UIF Path Ref(s)`: consumer-visible path refs that define the interaction family
- `UDD Ref(s)`: data refs that materially affect the binding; use `N/A` when none apply
- `Primary TM IDs`: the primary scenario rows that prove the main binding surface
- `TM IDs`: the full scenario set attached to the binding
- `TC IDs`: ordered verification case ids for the same binding
- `Test Scope`: concise statement of covered behavior surface
- `Spec Ref(s)`: authoritative `UC / FR / UIF / UDD` refs
- `Scenario Ref(s)`: scenario refs that materialize the packet
- `Success Ref(s)`: refs proving main-path behavior
- `Edge Ref(s)`: refs proving alternate / exception / degraded behavior

Treat the packet as a spec-slice locator:

- `Spec Ref(s)` must point to the authoritative `UC / FR / UIF / UDD` ids behind the binding
- `User Intent`, `Request Semantics`, `Visible Result`, `Side Effect`, and `Boundary Notes` are downstream scope references only; they do not replace contract design authority
- `Trigger Ref(s)` must locate the exact user-visible trigger set that caused the interface partition decision
- `Repo Landing Hint` must stay at entry-family granularity; it must not name final controller/facade/DTO anchors
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
- `Blocker`

The total number of minimum planning artifact units equals the row count of `Binding Projection Index`.

## Required Writeback

Update only:

- selected `test-matrix` stage row status/output-path/blocker fields
- `Binding Projection Index`: one row per stable `BindingRowID` derived from this run
- `Artifact Status`: initialize exactly one `contract` row per `BindingRowID` (as specified in Binding Packet Requirements above); `Unit Type = contract`, `Status = pending`; do not modify or add other row types

Stage-row status transition is mandatory and explicit:

- Set selected `test-matrix` row `Status = done` only when `test-matrix.md` is written and both `Binding Projection Index` + `Artifact Status` are initialized/refreshed consistently.
- Otherwise set selected row `Status = blocked` with concrete `Blocker` details (missing binding packet fields, unresolved refs, or projection initialization failures).

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

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
4. Require resolved `FEATURE_SPEC` to be consumable
5. Do not require `research` or `data-model` rows to be `done` before this stage
6. Keep this stage scoped to verification semantics and binding projection only

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

`test-matrix.md` remains the authoritative source for verification semantics and stable tuple keys.
`test-matrix.md` also carries the per-binding contract seed packet consumed by `/sdd.plan.contract`.
`PLAN_FILE` receives only a compact binding projection index and artifact queue rows derived from that matrix.
Use `spec.md` as the primary source for deciding which paths must be covered and what each path must prove.
Do not consume `research.md` or `data-model.md` semantics in this stage.

## Binding Projection Rules

Project only stable and unique binding rows from `test-matrix.md` into `Binding Projection Index`.
Do not copy scenario prose into `PLAN_FILE`.
Project `Boundary Anchor` as the client-facing contract binding key only, preserving the first consumer-callable entry selected in `test-matrix.md`.
Keep `Operation ID` as feature-level operation semantics; multiple `Operation ID` rows MAY share one spec-declared `Boundary Anchor` when they enter through the same consumer boundary.
`Repo Anchor` (if present) is optional traceability context only and MUST NOT replace or redefine `Boundary Anchor`.
For HTTP-facing bindings, keep the HTTP route as `Boundary Anchor` and the owning controller method as `Implementation Entry Anchor` when the spec declares that split.
A normative `Boundary Anchor` MUST be explicitly consumer-callable in spec context; do not replace spec-declared HTTP/controller entries with abstract facade operation names.
If no consumer-callable boundary can be established from `spec.md`, set `Boundary Anchor = N/A` and keep the row non-normative or blocked instead of inventing operation/facade names.
If a selected binding drifts away from spec-declared boundary placement, correct it and record the drift/blocker in the generation output rather than preserving the wrong tuple.
Project only the minimum extra fields required to help `/sdd.plan.contract` select and validate the next unit without re-reading broad context.
Keep DTO anchors, state-owner anchors, collaborator anchors, lifecycle/invariant refs, and other realization-detail evidence in `test-matrix.md`; do not mirror them into `PLAN_FILE`.
Apply tuple legality and anchor-status rules exactly as defined by `.specify/templates/test-matrix-template.md`; this command only projects stable rows and routes upstream on gaps.
Do not perform shared-semantic class/owner/lifecycle modeling in this stage; keep Stage 2 focused on spec-driven verification semantics and binding projection.

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
The packet MUST be sufficient to scope targeted contract reads in `contracts/` and seed interface-level realization design without reopening broad feature context.

Each binding packet MUST include:

- `BindingRowID`
- `Operation ID`
- `IF Scope`
- `Boundary Anchor`
- `Boundary Anchor Status`
- `Boundary Anchor Strategy Evidence`
- `Implementation Entry Anchor`
- `Implementation Entry Anchor Status`
- `Implementation Entry Anchor Strategy Evidence`
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

Field semantics MUST stay deterministic and tuple-stable:

- `BindingRowID`: stable row key for one contract-seed packet; never reuse across different tuple meanings
- `Operation ID`: feature operation identifier from `spec.md` path semantics; keep stable across reruns
- `IF Scope`: interface scope (`IF-###` or `N/A`) aligned with the same operation path
- `Boundary Anchor`: client-facing boundary token used by downstream contract selection
- `Boundary Anchor Status`: one of `existing|extended|new|todo`, evaluated for this boundary token only
- `Boundary Anchor Strategy Evidence`: required when boundary status is `new`; otherwise `N/A`
- `Implementation Entry Anchor`: concrete implementation entry token for realization handoff; use `TODO(REPO_ANCHOR)` when unknown
- `Implementation Entry Anchor Status`: one of `existing|extended|new|todo`, evaluated independently from boundary status
- `Implementation Entry Anchor Strategy Evidence`: required when implementation-entry status is `new`; otherwise `N/A`
- `Request DTO Anchor`: request payload anchor for contract shaping (`path::symbol`, `N/A`, or `TODO(REPO_ANCHOR)`)
- `Response DTO Anchor`: response payload anchor for contract shaping (`path::symbol`, `N/A`, or `TODO(REPO_ANCHOR)`)
- `Primary Collaborator Anchor`: first mandatory downstream collaborator anchor (`path::symbol` or `N/A`)
- `TM ID`: primary scenario-matrix row key linked to this packet
- `TC IDs`: ordered verification-case keys linked to this packet
- `Spec Ref(s)`: explicit spec references (`UC/UIF/FR`) proving this packet is spec-grounded
- `Scenario Ref(s)`: scenario-row references that materialize this tuple
- `Success Ref(s)`: success-case references proving the main expected outcome
- `Edge Ref(s)`: edge/exception references proving degraded or failure paths
- `Main Pass Anchor`: canonical success assertion/check anchor
- `Branch/Failure Anchor(s)`: canonical branch/failure assertion/check anchors

When the selected binding is HTTP-facing, keep the first downstream service/facade symbol in `Primary Collaborator Anchor`; if the controller symbol cannot be confirmed, set `Implementation Entry Anchor = TODO(REPO_ANCHOR)` and `Implementation Entry Anchor Status = todo` rather than guessing.
If `Boundary Anchor Status = new` or `Implementation Entry Anchor Status = new`, the matching strategy-evidence field MUST explicitly mention why `existing` was rejected and why `extended` was rejected or unsafe.
Keep this stage spec-led: if a binding packet cannot be closed from `spec.md` and selected plan-row context, keep the unresolved items explicit in stage output and continue to `/sdd.plan.data-model` by fixed handoff.

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
- `Artifact Status` (keep tuple keys unchanged)

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`: `/sdd.plan.data-model`
- `Decision Basis`: `test-matrix` derives verification semantics and stable binding packets from `spec.md`; `data-model` runs next in the fixed planning chain before `contract`
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

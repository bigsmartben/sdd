---
description: Generate exactly one pending northbound interface design artifact selected from an explicit plan.md path.
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

`/sdd.plan.contract <path/to/plan.md> [context...]`

## Goal

Generate exactly one unified northbound interface design artifact by consuming the first pending `contract` row from `PLAN_FILE` `Artifact Status`.
This command MUST NOT generate multiple contract files in one run.
Use `.specify/templates/contract-template.md` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or prior generated artifacts.

This unified artifact includes both:

- Northbound minimal contract semantics (`UIF` + necessary `UDD` slice only)
- Delivery-level realization design (internal handoff, sequence, UML, failure propagation, southbound dependencies)
- Explicit downstream projection slices for execution (`spec` refs + `test` scope/anchors) used by `/sdd.tasks` and `/sdd.implement`

## Selection Rules

1. Run `{SCRIPT} --plan-file <PLAN_FILE>` once and resolve `FEATURE_DIR`, `FEATURE_SPEC`, and `IMPL_PLAN`
2. Read only the resolved `IMPL_PLAN`
3. In `Artifact Status`, find the first row where:
   - `Unit Type = contract`
   - `Status = pending`
4. If no pending contract row exists, stop and report that the contract queue is complete
5. Resolve the matching `BindingRowID` row in `Binding Projection Index`
6. Require `test-matrix` stage row to be `done`
7. Attempt to resolve one selected binding packet in `test-matrix.md` by the same `BindingRowID`; if absent, enter compatibility fallback mode

## Plan Control-Plane Input Path (Mandatory)

Use only the explicit `PLAN_FILE` resolved through `{SCRIPT}` as planning control plane.
Ignore alternate `plan.md` paths from environment variables or repository discovery.
Non-`plan.md` user files are allowed only when already listed in `Allowed Inputs`; they never redefine control-plane state.
If `PLAN_FILE` is missing or non-consumable, stop and report a blocker.

## Path Constraints

- Stay inside the resolved `FEATURE_DIR` plus the explicit files listed in `Allowed Inputs`.
- Complete `BindingRowID` selection and prerequisite validation from the explicit `PLAN_FILE` before reading `test-matrix.md`, any conditional inputs, or any repo anchors.
- Before that point, do not open repository files, generated artifacts, or run repository-wide discovery/search.
- After selection, treat the selected binding packet in `test-matrix.md` as the default semantic source for the contract run.
- Read conditional inputs only when the selected binding packet is missing required fields for downstream projection or contract-visible behavior.
- Read only the selected row's planning inputs and the targeted symbols/files required for that `BindingRowID`.
- Keep repo-backed verification bounded to no more than five files in one contract run; if that cap is insufficient, keep unresolved items explicit as `todo` / `gap` instead of expanding scope.
- If `test-matrix.md` has no `Binding Contract Packets` section or no packet matching the selected `BindingRowID`, enter compatibility fallback mode and derive a minimal packet from `Scenario Matrix` + `Verification Case Anchors` rows that match the selected binding tuple.

## Northbound Entry Selection (Client Entry First)

- Treat this artifact as the northbound interface definition for the selected binding.
- Select `Boundary Anchor` as the first consumer-callable entry, not an internal service/manager/mapper hop.
- If the operation is consumer-called via HTTP, prefer `HTTP METHOD /path` and keep any controller symbol as repo anchor evidence.
- If the operation is consumer-called via RPC/facade, use the anchored `Facade.method` surface.
- If both HTTP/controller and facade symbols exist, keep the actual consumer-visible first callable entry as normative `Boundary Anchor`.

## Unified Design Requirements

- Contract scope is `UIF` semantics plus necessary `UDD` only: lock behavior-significant request/response fields, constraints, and visible outcomes; do not expand to an exhaustive payload handbook.
- Realization design scope is delivery-ready: internal handoff, failure propagation, sequence closure, UML ownership, and southbound dependency chain.
- Fill `Downstream Projection Input (Required)` with one executable slice for the selected `IF Scope` / `Operation ID`: include `spec` refs (`UC/UIF/FR/SC/EC`) and `test` refs (`Test Scope`, `TM/TC`, pass/failure anchors, command/assertion signal).
- Sequence design MUST start from consumer/client entry and reach the internal implementation entry within the first two request hops.
- Sequence design MUST remain end-to-end contiguous at current document granularity; no disconnected hops, orphan participants, or broken return chains.
- Each declared behavior path MUST map to one contiguous ordered sequence step chain from trigger entry to contract-visible outcome/failure.
- If `Boundary Anchor` and `Implementation Entry Anchor` resolve to the same repo-backed symbol, do not invent a handoff relay hop; reuse one participant/class in sequence and UML.
- UML MUST cover all executable sequence participants at this document granularity.
- Every sequence call MUST map to an owning UML method with directed caller/callee relationship.
- Any newly introduced field/method/call MUST be explicitly marked as new and connected to owner/consumer or caller/callee.

## Repo Anchor Decision Protocol (Mandatory)

- Apply repo-anchor decision order `existing -> extended -> new -> todo`.
- `extended` is valid only for same-entity field/state expansion.
- `new` is normative only when explicit `path::symbol` target evidence is present.
- If explicit target evidence is missing, set status to `todo` and keep the tuple forward-looking/non-normative.
- Repo anchors in this stage are for naming/lifecycle correction and traceability only; do not invent business semantics from anchors.

## Allowed Inputs

Read only, in this order:

- `.specify/templates/contract-template.md` for output structure
- selected `Artifact Status` row from the explicit `PLAN_FILE` only
- matching `BindingRowID` row from `Binding Projection Index` in the explicit `PLAN_FILE` only
- `Shared Context Snapshot` from the explicit `PLAN_FILE` only
- selected binding packet from `test-matrix.md`

Treat the selected binding packet in `test-matrix.md` as the default authoritative semantic input for this stage.
Do not read `spec.md`, `research.md`, or `data-model.md` unless the selected binding packet is missing required fields.

### Compatibility Fallback (Legacy `test-matrix.md`)

If `Binding Contract Packets` is missing or no row matches the selected `BindingRowID`, keep the run unblocked by deriving a minimal compatibility packet from:

- selected `BindingRowID` row in `PLAN_FILE` `Binding Projection Index`
- matching rows in `test-matrix.md` `Scenario Matrix`
- matching rows in `test-matrix.md` `Verification Case Anchors`

In compatibility fallback mode:

- treat `spec.md` as allowed for missing `UC/UIF/FR/SC/EC` refs
- treat `data-model.md` as allowed only for lifecycle/invariant constraints required by the selected tuple
- do not read `research.md`; keep fallback bounded to `PLAN_FILE` + `test-matrix.md` + conditional `spec.md`/`data-model.md` only

### Conditional Inputs

Read `spec.md` only if the selected binding packet is missing any of:

- `UC Ref(s)`
- `UIF Ref(s)`
- `FR Ref(s)`
- scenario / success / edge-case refs used by `Downstream Projection Input (Required)`

Read `data-model.md` only if the selected binding packet explicitly depends on:

- lifecycle transitions
- state invariants
- entity constraints required for contract-visible behavior

Do not read `research.md` in default mode for this stage.

### Repo Anchor Input Limits

Read only the minimum repo-backed targets required to confirm the selected binding:

- boundary entry anchor target
- implementation entry anchor target
- request DTO anchor target, when present
- response DTO anchor target, when present
- one primary collaborator anchor, when required for contract-visible behavior

Do not run repository-wide discovery or broad symbol scans.
If required evidence is still missing after reading the allowed repo-backed targets, keep the unresolved tuple forward-looking:

- set missing anchor to `TODO(REPO_ANCHOR)`
- set anchor status to `todo`
- continue with explicit blocker / gap markers instead of expanding scope

After generation, the selected artifact under `contracts/` becomes the authoritative source for interface semantics and realization design semantics for that binding.
`PLAN_FILE` remains queue state plus stable binding keys only.

## Required Writeback

Update only the selected contract row in `Artifact Status`:

- `Target Path`
- `Status`
- `Source Fingerprint`
- `Output Fingerprint`
- `Blocker`

Do not modify unrelated `BindingRowID` rows.
Do not write contract/design prose into `PLAN_FILE`.

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`
- `Decision Basis`
- `Selected BindingRowID`: selected `BindingRowID`
- `Ready/Blocked`

Determine `Next Command` from the explicit `PLAN_FILE` state only after the selected contract row writeback:

- If any `contract` rows remain `pending`, `Next Command = /sdd.plan.contract <absolute path to plan.md>`
- Otherwise, if all required planning rows are complete, `Next Command = /sdd.tasks`
- Otherwise, if queue state is inconsistent with either condition, keep `Next Command` empty and set `Ready/Blocked = Blocked`

`Decision Basis` MUST cite the post-writeback `Artifact Status` state and planning-complete check that produced the routing decision.

## Final Output

Report:

- resolved `PLAN_FILE`
- selected `BindingRowID`
- generated contract path
- updated contract row status
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected BindingRowID`, and `Ready/Blocked`

---
description: Generate test-matrix.md, derive interface partitions, and initialize Artifact Status rows in plan.md.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

Treat all `$ARGUMENTS` as optional scoped user context.
Resolve `PLAN_FILE` using `{SCRIPT}` defaults.

## Goal

Generate one `test-matrix.md` from the first `pending` `test-matrix` row in `PLAN_FILE`.
Initialize or refresh `Binding Projection Index` and `Artifact Status` in `PLAN_FILE`.
Use `.specify/templates/test-matrix-template.md` only.

`/sdd.plan.test-matrix` owns:
- Northbound interface partition decisions from `spec.md` + repo evidence.
- Binding projections for interface units.
- Test semantics (Scenario Matrix / Verification Case Anchors).
- `UIF Full Path Coverage Graph (Mermaid)` + `UIF Path Coverage Ledger`.

## Stage Packet (Test-Matrix Unit)

1. Run `{SCRIPT}` to resolve `FEATURE_DIR` and `PLAN_FILE`.
2. Find first `Stage Queue` row where `Stage ID = test-matrix` and `Status = pending`.
3. Require `FEATURE_SPEC` to be consumable.
4. Do not require `research` or `data-model` rows to be `done` before this stage.
5. Do not consume `data-model.md` or generated contract artifacts in this stage.
6. Use this packet as the default context for generation and binding projection.
7. prefer section-level rereads over whole-file replay for the selected unit.
8. If the selected packet cannot be closed from `spec.md` and selected plan-row context, stop and report the blocker.

## Binding Packet Requirements

Read only:
- `spec.md` (UC/FR/UIF/UDD authority)
- `PLAN_FILE` (snapshot + queue state)

Each binding packet MUST provide:
- `UIF Path Ref(s)`
- `UDD Ref(s)`
- stable binding projection for those interface units

`Path Type` is verification coverage metadata only — do not promote it to interface-design input.

## Governance / Authority

- **Authority rule**: `PLAN_FILE` is authoritative only for queue state; `spec.md` is the semantic authority.
- **Stage boundary rule**: No contract closure or DTO naming; only interface partitioning and test semantics.
  - `Unit Type = contract` is the artifact type for each projected `BindingRowID` row in `Artifact Status`.
- **Shared protocol rule**: Apply **Unified Repository-First Gate Protocol (URFGP)**.

## Allowed Inputs

- `.specify/templates/test-matrix-template.md` (structure)
- `PLAN_FILE` (queue state and shared snapshot)
- `FEATURE_SPEC` (UC/FR/UIF/UDD authority)
- Bounded repo evidence (action targets, permission/idempotency/transaction boundaries)

**Prohibited**: `data-model.md`, `contracts/`, or broad symbol scans.

## Reasoning Order

1. **Interface Partitioning**: Decide binding boundaries from user-visible action semantics.
2. **Verification Attachment**: Attach paths and observability to fixed bindings.
3. **Projection**: Derive stable downstream refs into packets and plan rows.

## Artifact Quality Contract

- Must: output stable binding cuts, verification semantics, and reusable packets from `spec.md`.
- Strictly: `BindingRowID` MUST be stable — do not reassign after first projection.

## Writeback Contract

Update exactly three targets in `PLAN_FILE`:
- Selected `test-matrix` stage row (`Status = done`, `Output Path`, `Blocker`).
- `Binding Projection Index`: Refresh `Binding Projection Index` by `BindingRowID`; replace matching rows, do not append duplicates.
- `Artifact Status`: Keep exactly one `contract` row per projected `BindingRowID` (`Unit Type = contract`, `Status = pending`).

**MUST NOT** rewrite `spec.md` or other planning artifacts.

## Output Contract

- **BindingRowID**: One per client-callable northbound interface unit.
- **UIF Coverage Graph**: Spec-derived Mermaid overview of all feature-scope UIF paths.
- **Binding Packet**: locator-strong packet in `test-matrix.md` for each binding.
- **MUST NOT** infer controllers, services, DTOs, or repo anchors.
- **Partition Rule**: Merge happy/alternate/exception/timeout paths if they share the same action boundary.

## Handoff Decision

Emit exactly these fields:
- `Next Command`: `/sdd.plan.data-model`
- `Decision Basis`: `test-matrix` completed; next is shared semantic alignment.
- `Selected Stage ID`: selected row.
- `Ready/Blocked`: Local readiness only.

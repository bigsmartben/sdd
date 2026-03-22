---
description: Initialize or refresh the planning control-plane artifact plan.md.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

Treat all `$ARGUMENTS` as user planning context.

## Goal

Initialize or update `plan.md` for the current feature branch.
Use `.specify/templates/plan-template.md` only.

`plan.md` is the sole planning control plane. `/sdd.plan` does **not** generate downstream planning-stage artifacts directly.

`/sdd.plan` owns:
- Planning control-plane state (Stage Queue / Binding Index / Artifact Status).
- Shared context snapshot for the feature branch.
- Repository-first consumption slice (baselines projection).

## Planning Sharding Model (Mandatory)

- **Stage sharding (fixed): delivery path `research -> test-matrix -> data-model`** — each produces one output artifact.
- **Binding sharding (fixed): `/sdd.plan.contract` consumes one `BindingRowID` row per run** — runs repeat until queue clears.
- `contract` is not a `Stage Queue` row; it is tracked in `Artifact Status` only.
- explicit handoff order: `sdd.plan.research -> sdd.plan.test-matrix -> sdd.plan.data-model -> sdd.plan.contract`.

`Binding Projection Index` columns:
- `BindingRowID`, `UC ID`, `UIF ID`, `FR ID`, `IF ID / IF Scope`, `Trigger Ref(s)`, `Primary TM IDs`, `TC IDs`
- `UIF Path Ref(s)`
- `UDD Ref(s)`
- `Test Scope`

Do not add `Boundary Anchor` or other design output columns to the index — those belong to contracts.

## Governance / Authority

- **Authority rule**: `plan.md` is authoritative for queue state only. **MUST NOT** override semantic authority from `spec.md`, `research.md`, or downstream designs.
- **Stage boundary rule**: No design/implementation semantics.
- **Protocol rule**: Apply **Unified Repository-First Gate Protocol (`URFGP`)**. Final audit/PASS/FAIL is owned by `/sdd.analyze`.

## Allowed Inputs

- `.specify/templates/plan-template.md` (structure)
- `FEATURE_SPEC` (path and basic scope)
- `.specify/memory/repository-first/*.md` (canonical baselines)

**Prohibited**: `contracts/`, `data-model.md`, or directory-wide exploratory scans.

## Reasoning Order

1. **Prerequisite Check**: Resolve `FEATURE_DIR` and `FEATURE_SPEC`.
2. **Snapshot**: Capture spec/repo metadata into the `Shared Context Snapshot`.
3. **Queue Initialization**: Seed `Stage Queue` in fixed order (`research`, `test-matrix`, `data-model`).
4. **Index Seed**: Initialize empty `Binding Projection Index` with correct column headers.

## Artifact Quality Contract

- Must: output one deterministic control plane that downstream stages can rely on without reinterpretation.
- Strictly: Write `PLAN_FILE` as a control-plane scaffold only. Keep markdown table headers unchanged. Do not populate design columns.

## Writeback Contract

- Create or refresh `plan.md` using the runtime template.
- Seed `Stage Queue` in fixed order: `research`, `test-matrix`, `data-model` — all with `Status = pending`.
- Update only queue and snapshot sections.
- **MUST NOT** rewrite `spec.md`.

## Output Contract

- **Stage Queue**: MUST use lowercase tokens (`pending`, `in_progress`, `done`, `blocked`).
- **Index Projection**: Initialize empty index with correct column headers; wait for `test-matrix` to populate rows.
- **Prohibited**: Stage prose, audit payloads, or execution logs in the artifact.

## Handoff Decision

Emit exactly these fields:
- `Next Command`: `/sdd.plan.research` (if needed) or `/sdd.plan.test-matrix`.
- `Decision Basis`: Control plane initialized.
- `Ready/Blocked`: Local readiness only.

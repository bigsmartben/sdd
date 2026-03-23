# Planning Control Plane: [FEATURE]

**Branch**: `[feature-YYYYMMDD-slug]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[YYYYMMDD-slug]/spec.md`

## Summary

[Short summary of the feature and why this control plane exists]

`plan.md` exists only to initialize and maintain the planning control plane for this feature.
It is the orchestration authority for queue state, binding projection, and artifact execution status.
It is not a semantic authority and MUST NOT supersede `spec.md`, `research.md`, `test-matrix.md`, `data-model.md`, or `contracts/`.

## Artifact Quality Signals

- Must: behave like a trustworthy control plane.
- Must not: duplicate semantics or force child commands to guess intent.
- Strictly: prefer stable ids, exact paths, and explicit statuses over prose.

## Shared Context Snapshot

Shared bootstrap facts only.
Do not place stage prose, audit payload, or execution logs here.

### Feature Identity

- Feature: [name]
- Scope anchor: [link or stable id]
- Status: [planning-not-started / planning-in-progress / planning-complete]

### Stable Shared Inputs

- Actors: [stable actor references only]
- In Scope: [stable scope bullets only]
- Out of Scope: [stable scope bullets only]
- Stable UC / UIF / FR Scope: [stable ids only]
- Constitution constraints: [only constraints that affect every downstream stage]
- Shared blockers: [only blockers that affect multiple planning stages]
- Must-read anchors: [shared upstream anchors only]

### Repository-First Consumption Slice

- Relevant dependency usage rows / `SIG-*`: [cite concrete rows only]
- Relevant module-edge rules: [cite concrete module-to-module rows only]
- Bounded repo candidate anchors: [only feature-relevant northbound entry candidates and semantic landing anchors; no contract conclusions]

## Stage Queue

| Stage ID | Command | Required Inputs | Output Path | Status | Blocker |
|----------|---------|-----------------|-------------|--------|---------|
| research | `/sdd.plan.research` | `plan.md`, `spec.md`, constitution, targeted repo anchors | `research.md` | pending | [none] |
| test-matrix | `/sdd.plan.test-matrix` | `plan.md`, `spec.md`, bounded repo slice | `test-matrix.md` | pending | [none] |
| data-model | `/sdd.plan.data-model` | `plan.md`, `spec.md`, `test-matrix.md`, bounded repo semantic slice | `data-model.md` | pending | [none] |

Rules:

- Queue order is fixed.
- Child commands take the first matching `pending` row only.
- `research` is optional clarification input for `/sdd.plan.data-model`, but it remains a required completed stage before `/sdd.tasks`.
- `data-model` is the fixed shared-semantic alignment row after `test-matrix`; complete it before entering `contract`.
- `contract` is not a stage row; it is a per-binding artifact queue unit selected from `Artifact Status`.
- Do not add prose summaries into this table.

## Binding Projection Index

Initialize empty until `test-matrix.md` creates stable rows.
Project stable binding keys only; do not copy scenario text or contract-design conclusions.

| BindingRowID | UC ID | UIF ID | FR ID | IF ID / IF Scope | Trigger Ref(s) | Primary TM IDs | TC IDs | UIF Path Ref(s) | UDD Ref(s) | Test Scope |
|--------------|-------|--------|-------|------------------|----------------|----------------|--------|-----------------|------------|------------|
<!-- Keep table body empty until /sdd.plan.test-matrix projects stable binding rows. -->

Rules:

- Each row must be uniquely identifiable.
- `BindingRowID` is the plan-local identifier for one stable binding row projected from `test-matrix.md`.
- `Binding Projection Index` is a projection ledger only; it is not a semantic authority.
- Semantic authority for binding meaning is the matching `Binding Packets` row in `test-matrix.md`.
- `IF ID / IF Scope` stores one normalized IF scope token (`IF-###` or `N/A`) for downstream selection; do not pack mixed labels/prose into this cell.
- `UC ID`, `UIF ID`, and `FR ID` must use deterministic id encoding (comma-separated ids, stable sort, no prose) when multiple refs are needed.
- Keep only the minimal selection and scheduling fields needed for downstream `plan.contract` and `plan.data-model`.
- Do not mirror packet-level scope reference fields such as `User Intent`, `Request Semantics`, `Visible Result`, `Side Effect`, `Boundary Notes`, or `Repo Landing Hint` into this index; those remain authoritative only in `test-matrix.md`.
- `Boundary Anchor`, `Implementation Entry Anchor`, anchor statuses, DTO anchors, collaborator anchors, lifecycle refs, invariant refs, and realization design remain downstream responsibilities.
- Downstream commands MUST use this index for row selection only and MUST read `test-matrix.md` for binding semantics.
- Keep this index aligned only from `/sdd.plan.test-matrix`; if binding meaning changes later, repair upstream and regenerate the projection instead of letting downstream commands rewrite it.
- If a stable key is not confirmed, keep it out of the index.

## Artifact Status

Track minimum planning artifacts derived from each `BindingRowID`.

| BindingRowID | Unit Type | Target Path | Status | Blocker |
|--------------|-----------|-------------|--------|---------|
<!-- Keep table body empty until binding rows exist. -->

Rules:

- `contract` is tracked as the single per-binding interface design artifact.
- Write scope is command-specific:
  - `/sdd.plan.test-matrix` may batch initialize one `contract` row per projected `BindingRowID`.
  - `/sdd.plan.data-model` may batch update only blocker fields for affected `contract` rows.
  - `/sdd.plan.contract` updates exactly one selected `contract` row per run.
- Child commands may write only status, target path, and blocker.

## Handoff Protocol

- `/sdd.plan` initializes `Shared Context Snapshot`, `Stage Queue`, and the empty downstream ledgers.
- `/sdd.plan.research` advances `research`.
- `/sdd.plan.test-matrix` advances `test-matrix` and initializes `Binding Projection Index` plus `Artifact Status`.
- `/sdd.plan.data-model` advances `data-model` and may update contract-readiness blockers only.
- `/sdd.plan.contract` advances `Artifact Status` one row at a time.
- `/sdd.tasks` starts only after `research`, `test-matrix`, `data-model`, and all required `contract` rows are `done`.

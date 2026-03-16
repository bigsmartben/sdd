# Planning Control Plane: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

## Summary

[Short summary of the feature and why the planning queue exists]

`plan.md` is the planning control plane for this feature.
It is authoritative for planning queue state, binding-projection rows, and source/output fingerprints only.
It is derived for planning semantics and MUST NOT supersede `research.md`, `data-model.md`, `test-matrix.md`, `contracts/`, or `interface-details/`.

## Shared Context Snapshot

Use this section for shared bootstrap facts only.
Do not place stage prose, audit payload, or execution logs here.

### Feature Identity

- Feature: [name]
- Scope anchor: [link or stable id]
- Status: [planning-not-started / planning-in-progress / planning-complete]

### Stable Shared Inputs

- Actors: [stable actor references only]
- In Scope: [stable scope bullets only]
- Out of Scope: [stable scope bullets only]
- Shared blockers: [only blockers that affect multiple planning stages]

### Repository-First Consumption Slice

- Relevant dependency-governance facts: [short bullets]
- Relevant domain-boundary anchors: [short bullets]
- Relevant invocation-governance facts: [short bullets]

## Stage Queue

| Stage ID | Command | Required Inputs | Output Path | Status | Source Fingerprint | Output Fingerprint | Blocker |
|----------|---------|-----------------|-------------|--------|--------------------|--------------------|---------|
| research | `/sdd.plan.research` | `plan.md`, `spec.md`, constitution, targeted repo anchors | `research.md` | pending | [fingerprint] | [fingerprint] | [none] |
| data-model | `/sdd.plan.data-model` | `plan.md`, `spec.md`, `research.md`, lifecycle repo anchors | `data-model.md` | pending | [fingerprint] | [fingerprint] | [none] |
| test-matrix | `/sdd.plan.test-matrix` | `plan.md`, `spec.md`, `research.md`, `data-model.md` | `test-matrix.md` | pending | [fingerprint] | [fingerprint] | [none] |

Rules:

- Queue order is fixed.
- Child commands take the first matching `pending` row only.
- Do not add prose summaries into this table.

## Binding Projection Index

Initialize empty until `test-matrix.md` creates stable rows.
Project stable binding keys only; do not copy narrative scenario text.

| BindingRowID | UC ID | UIF ID | FR ID | IF ID / IF Scope | TM ID | TC IDs | Operation ID | Boundary Anchor |
|--------------|-------|--------|-------|------------------|-------|--------|--------------|-----------------|
| [BindingRowID-001] | [UC-001] | [UIF-001] | [FR-001] | [IF-001] | [TM-001] | [TC-001, TC-002] | [operationId] | [METHOD /path or symbol] |

Rules:

- Each row must be uniquely identifiable.
- `BindingRowID` is the plan-local identifier for one stable binding row projected from `test-matrix.md`.
- `Binding Projection Index` is a projection ledger only.
- `Boundary Anchor` is the client-facing contract binding key projected from `test-matrix.md`; it is not the internal implementation handoff anchor.
- Internal handoff anchors such as `Implementation Entry Anchor` belong in `interface-details/`, not `plan.md`.
- If a stable key is not confirmed, keep it out of the index.

## Artifact Status

Track minimum planning artifacts derived from each `BindingRowID`.

| BindingRowID | Unit Type | Target Path | Status | Source Fingerprint | Output Fingerprint | Blocker |
|--------------|-----------|-------------|--------|--------------------|--------------------|---------|
| [BindingRowID-001] | contract | `contracts/[artifact].md` | pending | [fingerprint] | [fingerprint] | [none] |
| [BindingRowID-001] | interface-detail | `interface-details/[operationId].md` | pending | [fingerprint] | [fingerprint] | [none] |

Rules:

- `contract` and `interface-detail` are tracked independently.
- One command run updates one row only.
- Child commands may write only status, target path, blocker, and fingerprints.

## Handoff Protocol

- `/sdd.plan` initializes this file and starts the queue.
- `/sdd.plan.research`, `/sdd.plan.data-model`, and `/sdd.plan.test-matrix` advance `Stage Queue`.
- `/sdd.plan.contract` and `/sdd.plan.interface-detail` advance `Artifact Status` one row at a time.
- `/sdd.tasks` starts only after all required stage and artifact rows are `done`.

## Complexity Tracking

> Fill only if constitution check has violations that must be justified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., extra service boundary] | [reason] | [why simpler option failed] |

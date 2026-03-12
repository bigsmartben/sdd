---
description: "Interface-centric task orchestration template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Upstream design artifacts from `/specs/[###-feature-name]/`  
**Outputs**: `tasks.md` (this document)

## 1) Document Positioning

- This document is the executable task orchestration source for implementation.
- `tasks.md` MUST define clear task units, explicit execution dependencies, and deterministic upstream references.
- `tasks.md` MUST NOT duplicate interface/data-model/test semantics from upstream documents.

Boundary ownership:

- `plan.md`: implementation structure, interfaces registry snapshot
- `interface-details/<operationId>.md`: interface-level behavior/design details
- `data-model.md`: global object semantics and invariants
- `test-matrix.md` (if present): coverage and verification semantics

## 2) Generation Readiness Summary

- Overall Status: `READY | DEGRADED | BLOCKED`
- Interface Status:
  - `IFxx: READY | DEGRADED | BLOCKED`
- Notes:
  - `DEGRADED`: non-blocking gaps and workaround
  - `BLOCKED`: blocking gaps and remediation steps

## 3) Upstream Reference Index

### 3.1 IF Registry Reference

| InterfaceID | operationId | Interface | Served User Stories | Status (`READY\|DEGRADED\|BLOCKED`) | Remediation |
| --- | --- | --- | --- | --- | --- |
| IF01 | [operationId] | [method path] | [US###, ...] | READY | N/A |

### 3.2 Interface Detail References

| InterfaceID | operationId | Interface Detail Path | CaseID / TM / TC Refs | Status (`READY\|DEGRADED\|BLOCKED`) | Remediation |
| --- | --- | --- | --- | --- | --- |
| IF01 | [operationId] | interface-details/[operationId].md | [C-001 / TM-001 / TC-001] | READY | N/A |

### 3.3 Data Model Baseline Reference

| Data Model Path | Baseline Object Scope | Consumption Rule | Status (`READY\|DEGRADED\|BLOCKED`) | Remediation |
| --- | --- | --- | --- | --- |
| `specs/[###-feature-name]/data-model.md` | `[Entity / VO / FSM anchors]` | `[reference and refine mapping only]` | READY | N/A |

### 3.4 Verification Reference (`test-matrix.md`, if present)

| Source | Required Reference Type | Usage in tasks | Status (`READY\|DEGRADED\|BLOCKED`) | Remediation |
| --- | --- | --- | --- | --- |
| `specs/[###-feature-name]/test-matrix.md` | `[CaseID / TM / TC refs]` | `[Verify task target mapping]` | READY | N/A |

## 4) Task Traceability Projection Index

- Every task row in this document MUST have one trace row.
- `Scope` is `IFxx` or `GLOBAL`.
- `GLOBAL` tasks may use `InterfaceID/operationId = N/A`, but must keep requirement and/or verification refs explainable.

| TaskID | Scope (`IFxx\|GLOBAL`) | InterfaceID | operationId | FR/UC/UIF Refs | CaseID/TM/TC Refs | Source Refs | Status (`READY\|DEGRADED\|BLOCKED`) | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | IF01 | IF01 | [operationId] | [FR-001 / UC-001 / UIF-001] | [C-001 / TM-001 / TC-001] | [plan.md, interface-details/[operationId].md, test-matrix.md] | READY | N/A |
| T099 | GLOBAL | N/A | N/A | [FR-099 / UC-099] | [TM-099] | [plan.md, test-matrix.md] | READY | [cross-cutting] |

## 5) Execution Ordering Model

### 5.1 Task DAG (Dependency Authority)

- Task DAG is the only dependency authority for runtime scheduling.
- Dependencies MUST be declared as adjacency list.

```text
T001 -> T002, T003
T002 -> T010
T003 -> T010
```

### 5.2 Ordering Rules

- Runtime scheduling follows Task DAG.
- Section order and task numbering are readability aids, not dependency authority.
- `[Pre:T###,...]` is an inline mirror and SHOULD stay consistent with Task DAG.

## 6) Task Definition Canon

### 6.1 Task Line Format

`- [ ] T### [Type:Research|Interface|Verify|Infra|Docs] [IFxx?] [Role:...] [Pre:T###,...] Description with file path`

### 6.2 Task Type Canon

- `Research`
- `Interface`
- `Verify`
- `Infra`
- `Docs`

### 6.3 Metadata Semantics

- `IFxx`: interface delivery scope tag; optional only for global tasks.
- `Role`: execution focus for downstream implementation.
- `Pre`: optional inline predecessors; DAG remains authority.
- File paths define execution boundary and must be explicit.
- `Interface` / `Infra` tasks SHOULD include completion anchor (build pass / CaseID pass / acceptance check).

## 7) Global Foundation Tasks

Purpose: shared prerequisites before interface-specific delivery.

- [ ] T001 [Type:Infra] [Role:bootstrap] Initialize project structure per plan in [path]
- [ ] T002 [Type:Infra] [Role:tooling] Configure lint/format/test runner in [path]
- [ ] T003 [Type:Infra] [Role:config] Add runtime/env configuration in [path]

## 8) Interface Delivery Units

```markdown
## Interface IFxx — [name]

- Goal: [one-line delivery goal]
- Contract: [operationId / method path]
- Served User Stories: [US refs]
- Definition of Done: [verifiable completion criteria]

- [ ] T### [Type:Verify] [IFxx] [Role:contract|smoke|manual-check] [Pre:T###,...] Validate [operationId] in [path]
- [ ] T### [Type:Interface] [IFxx] [Role:handler|service|persistence|wiring] [Pre:T###,...] Implement [operationId] in [path] (Completion Anchor: [build|CaseID|acceptance-check])
```

Rules:

- Organize implementation primarily by IF delivery units.
- Each IF unit SHOULD include at least one `Verify` task and one `Interface` task (document exceptions).
- Keep IF sections reference-oriented; do not copy upstream design prose.

## 9) Cross-Cutting and Finalization

- [ ] T### [Type:Docs] [Role:quickstart] Update validation notes in `specs/[###-feature-name]/quickstart.md`
- [ ] T### [Type:Infra] [Role:validation] Run final validation command set in [path] (Completion Anchor: [command + pass signal])

Rules:

- Use this section only for tasks that cannot be scoped to one IF unit.
- Cross-cutting tasks without `[IFxx]` MUST appear as `Scope=GLOBAL` in traceability index.

## 10) Consumption Rules for Implement

- `/speckit.implement` MUST consume `tasks.md` directly.
- Required consumable sections:
  - `Generation Readiness Summary`
  - `Upstream Reference Index`
  - `Task Traceability Projection Index`
  - `Execution Ordering Model` (`Task DAG`)
  - Interface and global task checklist rows
- Runtime progress statuses belong to implementation runtime, not generation metadata.

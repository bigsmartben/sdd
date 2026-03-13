---
description: "Interface-delivery-oriented execution orchestration template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Upstream design artifacts from `/specs/[###-feature-name]/`  
**Outputs**: `tasks.md` (this document)

## 1) Document Purpose

- This document is the executable delivery orchestration source for implementation.
- `tasks.md` organizes work primarily by shared foundation and interface delivery units (`IFxx`).
- `tasks.md` MUST define clear task units, explicit execution dependencies, and completion anchors.
- `tasks.md` MUST NOT duplicate interface/data-model/test semantics from upstream documents.

Boundary ownership:

- `plan.md`: implementation structure and stage outputs
- `interface-details/<operationId>.md`: per-interface detailed design projection
- `data-model.md`: global object semantics and invariants
- `test-matrix.md` (if present): verification anchors (`CaseID` / `TM-*` / `TC-*`)

Reference precedence:

- Requirement semantics: `spec.md`
- Contract semantics: `contracts/`
- Global model semantics: `data-model.md`
- Coverage and verification semantics: `test-matrix.md`
- `tasks.md`: execution mapping only; must not redefine the above semantics

Stage boundary guard:

- `tasks.md` consumes Stage 3 outputs; it does not generate or backfill missing Stage 3 interface design artifacts.
- If required interface detail docs are missing, stop task generation and request upstream completion first.

## 2) Upstream Inputs (Execution References)

Use concise references only. Do not build registry/audit tables here.

| Input Artifact | Usage in Tasks | Required |
| --- | --- | --- |
| `plan.md` | structure, stack, project paths | Yes |
| `spec.md` | FR/UC/UIF requirement context | Yes |
| `contracts/` | interface operation targets | Yes |
| `interface-details/` | per-interface behavior anchors | If exists |
| `data-model.md` | entity/invariant references | If exists |
| `test-matrix.md` | verification anchors (`CaseID` / `TM-*` / `TC-*`) | If exists |

## 3) Execution Ordering Model

### 3.1 Task DAG (Dependency Authority)

- Task DAG is the baseline dependency authority for runtime scheduling.
- In `strict` mode, Task DAG is followed exactly.
- In `adaptive` mode, local split/merge/resequence is allowed only within Section 3.3 guardrails.
- Dependencies MUST be declared as adjacency list.

```text
T001 -> T002, T003
T002 -> T010
T003 -> T010
```

### 3.2 Ordering Rules

- Runtime scheduling follows Task DAG.
- Section order and task numbering are readability aids, not dependency authority.
- `[Pre:T###,...]` is an inline mirror and SHOULD stay consistent with Task DAG.

### 3.3 Execution Flexibility Policy

- Default mode: `strict`
- Supported modes:
  - `strict`: execute exactly against Task DAG and task rows
  - `adaptive`: allow bounded runtime split/merge/resequence while preserving dependency safety and task intent

Adaptive guardrails:

- Do not violate Task DAG predecessor constraints.
- Do not remove task references to operationId/requirement/verification anchors when they exist.
- Keep completion anchors explicit.
- Record runtime adaptations in implementation runtime output.

## 4) Task Definition Canon

### 4.1 Task Line Format

`- [ ] T### [Type:Research|Interface|Verify|Infra|Docs] [IFxx?] [Role:...] [Pre:T###,...] Description with file path`

### 4.2 Task Type Canon

- `Research`
- `Interface`
- `Verify`
- `Infra`
- `Docs`

### 4.3 Metadata Semantics

- `IFxx`: interface delivery scope tag; optional only for global tasks.
- `Role`: execution focus for downstream implementation.
- `Pre`: optional inline predecessors; DAG remains authority.
- File paths define execution boundary and must be explicit.
- Core `Interface` / `Verify` tasks SHOULD include completion anchors (build pass / CaseID pass / acceptance check).

Role guidance:

- Prefer intent-oriented roles where feasible (e.g., `input-boundary`, `business-rule`, `state-change`, `integration`, `verification`).
- Architecture-bound roles (e.g., `handler`, `service`, `persistence`) are allowed when they reflect confirmed project structure.

## 5) Shared Foundation

Purpose: shared prerequisites before interface-specific delivery.

- [ ] T001 [Type:Infra] [Role:bootstrap] Initialize project structure per plan in [path]
- [ ] T002 [Type:Infra] [Role:tooling] Configure lint/format/test runner in [path]
- [ ] T003 [Type:Infra] [Role:config] Add runtime/env configuration in [path]

Rules:

- Keep this section minimal and shared.
- Do not place interface-specific implementation tasks here.

## 6) Interface Delivery Units

```markdown
## Interface IFxx — [name]

- Goal: [one-line delivery goal]
- Contract: [operationId / method path]
- Primary Refs: [FR / UC / UIF / CaseID / TM / TC]
- Served User Stories: [US refs]
- Definition of Done: [verifiable completion criteria]

Recommended delivery loop:
- establish verification target
- implement interface behavior
- confirm completion against contract/scenario refs

- [ ] T### [Type:Verify] [IFxx] [Role:contract|smoke|manual-check] [Pre:T###,...] Validate [operationId] in [path]
- [ ] T### [Type:Interface] [IFxx] [Role:handler|service|persistence|wiring] [Pre:T###,...] Implement [operationId] in [path] (Completion Anchor: [build|CaseID|acceptance-check])
- [ ] T### [Type:Verify] [IFxx] [Role:completion] [Pre:T###,...] Confirm [operationId] delivery in [path] (Completion Anchor: [CaseID|TM|contract pass])
```

Rules:

- Organize implementation primarily by IF delivery units.
- Each IF unit SHOULD form a verification-implementation-completion loop (document exceptions).
- Keep IF sections reference-oriented; do not copy upstream design prose.
- Use `CaseID/TM/TC` as completion anchors for verification whenever test-matrix is available.

## 7) Cross-Interface Finalization

- [ ] T### [Type:Docs] [Role:quickstart] Update validation notes in `specs/[###-feature-name]/quickstart.md`
- [ ] T### [Type:Infra] [Role:validation] Run final validation command set in [path] (Completion Anchor: [command + pass signal])

Rules:

- Use this section only for tasks that cannot be scoped to one IF unit.
- Do not use this section as overflow for interface-local tasks.

## 8) Implementation Consumption

- `/sdd.implement` MUST consume `tasks.md` directly.
- Required consumable sections:
  - `Upstream Inputs (Execution References)`
  - `Execution Ordering Model` (`Task DAG`)
  - `Shared Foundation`
  - `Interface Delivery Units (IFxx)`
  - `Cross-Interface Finalization`
- Runtime progress statuses belong to implementation runtime, not generation metadata.

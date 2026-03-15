---
description: "Interface-delivery-oriented execution orchestration template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Upstream design artifacts from `/specs/[###-feature-name]/`  
**Outputs**: `tasks.md` (this document)

## 1) Document Purpose

- This document is the executable delivery orchestration source for implementation.
- `tasks.md` organizes work primarily by shared foundation and interface delivery units keyed by `IF Scope` (`IF-###`).
- `tasks.md` MUST define clear task units and explicit execution dependencies.
- `tasks.md` MUST NOT duplicate interface/data-model/test semantics from upstream documents.

Boundary ownership:

- `plan.md`: implementation structure and stage outputs
- `interface-details/<operationId>.md`: per-interface detailed design projection
- `data-model.md`: global object semantics and invariants
- `test-matrix.md`: feature verification anchors (`TM-*` / `TC-*`)

Reference precedence:

- Requirement semantics: `spec.md`
- Contract semantics: `contracts/`
- Global model semantics: `data-model.md`
- Feature verification semantics: `test-matrix.md`
- `tasks.md`: execution mapping only; must not redefine the above semantics

Stage boundary guard:

- `tasks.md` consumes Stage 4 outputs; it does not generate or backfill missing interface design artifacts.

## 2) Upstream Inputs (Execution References)

Use concise references only. Do not build registry/audit tables here.

| Input Artifact | Usage in Tasks | Required |
| --- | --- | --- |
| `plan.md` | structure, stack, project paths | Yes |
| `spec.md` | FR/UC/UIF requirement context | Yes |
| `data-model.md` | entity/invariant references | Yes |
| `test-matrix.md` | feature verification anchors (`TM-*` / `TC-*`) | Yes |
| `contracts/` | interface operation targets | Yes |
| `interface-details/` | per-interface behavior anchors | Yes |

## 3) Execution Ordering Model

### 3.1 Task DAG (Dependency Authority)

- Task DAG is the baseline dependency authority for runtime scheduling.
- In `strict` mode, Task DAG is followed exactly.
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
- If adaptive execution needs special caution, add one short note here; otherwise omit extra policy text.

## 4) Task Definition Canon

### 4.1 Task Line Format

`- [ ] T### [Type:Research|Interface|Verify|Infra|Docs] [IF-###?] [Role:...] [Pre:T###,...] Description with file path or command target`

### 4.2 Task Type Canon

- `Research`
- `Interface`
- `Verify`
- `Infra`
- `Docs`

### 4.3 Metadata Semantics

- `IF-###`: interface delivery scope tag; optional only for global tasks.
- `Role`: execution focus for downstream implementation when useful.
- `Pre`: optional inline predecessors; DAG remains authority.
- File paths or command targets define execution boundary and should be explicit.
- Core `Interface` / `Verify` tasks SHOULD include completion anchors when they help prove completion.

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
## Interface IF-### — [name]

- Goal: [one-line delivery goal]
- Contract: [operationId / method path]
- Primary Refs: [refs that help execution or completion checks]

Recommended delivery loop:
- establish verification target
- implement interface behavior
- confirm completion against contract/scenario refs

- [ ] T### [Type:Verify] [IF-###] [Role:contract|smoke|manual-check] [Pre:T###,...] Validate [operationId] in [path]
- [ ] T### [Type:Interface] [IF-###] [Role:handler|service|persistence|wiring] [Pre:T###,...] Implement [operationId] in [path] (Completion Anchor: [build|CaseID|acceptance-check])
- [ ] T### [Type:Verify] [IF-###] [Role:completion] [Pre:T###,...] Confirm [operationId] delivery in [path] (Completion Anchor: [CaseID|TM|contract pass])
```

Rules:

- Organize implementation primarily by interface delivery units keyed by `IF Scope`.
- Each IF unit SHOULD form a verification-implementation-completion loop (document exceptions).
- Keep IF sections reference-oriented; do not copy upstream design prose.
- Use `CaseID/TM/TC` as completion anchors only when they help prove delivery.

## 7) Cross-Interface Finalization

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
  - `Interface Delivery Units`
  - `Cross-Interface Finalization`
- Runtime progress statuses belong to implementation runtime, not generation metadata.

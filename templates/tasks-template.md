---
description: "Interface-delivery-oriented execution orchestration template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Upstream design artifacts from `/specs/[YYYYMMDD-feature-name]/`
**Outputs**: `tasks.md` (this document), `tasks.manifest.json` (machine-readable sidecar projection)

## 1) Document Purpose

- This document is the executable delivery orchestration source for implementation.
- This document projects completed `plan`-stage detailed design into execution decomposition only.
- `tasks.md` organizes work primarily by shared foundation and interface delivery units keyed by `IF Scope` (`IF-###`).
- Interface delivery units are IF-scoped execution work packages derived from approved planning artifacts.
- `tasks.md` MUST define clear task units and explicit execution dependencies.
- `tasks.md` MUST NOT duplicate interface/data-model/test semantics from upstream documents.
- `tasks.md` consumes approved planning artifacts and MUST NOT redesign research, data model, or contract semantics.
- `tasks.md` MUST NOT supplement missing design, verification semantics, target paths, completion anchors, or dependency meaning.
- Comprehensive cross-artifact auditing (consistency/coverage/ambiguity/drift/traceability hygiene) is owned by `/sdd.analyze`, not this task-orchestration artifact.

Boundary ownership:

- `plan.md`: planning control plane, queue state, and artifact target paths
- `contracts/<operationId>.md`: per-interface northbound contract + realization design projection
- `data-model.md`: global object semantics and invariants
- `test-matrix.md`: feature verification anchors (`TM-*` / `TC-*`)

Reference precedence:

- Requirement semantics: `spec.md`
- Contract semantics: `contracts/`
- Global model semantics: `data-model.md`
- Feature verification semantics: `test-matrix.md`
- Downstream execution projection authority (per IF unit): selected contract `Spec Projection Slice` + `Test Projection Slice`
- `tasks.md`: execution mapping only; must not redefine the above semantics
- Inline task summaries, local execution notes, and other derived views must yield to the authoritative artifacts above when conflicts appear.
- If contract projection slices drift from `spec.md` or `test-matrix.md`, keep contract projection as execution truth for this run and emit explicit upstream writeback repair actions (no local semantic merge).

Stage boundary guard:

- `tasks.md` consumes Stage 4 outputs; it does not generate or backfill missing interface design artifacts.
- Task generation must start only after `TASKS_BOOTSTRAP.execution_readiness.ready_for_task_generation = true`; if bootstrap is missing or invalid, use one bounded fallback validation from `plan.md` control-plane fields before stopping.
- If executable tuples depend on `Anchor Status = new` / `Implementation Entry Anchor Status = new`, include explicit strategy evidence refs showing `existing` and `extended` were evaluated and rejected; otherwise stop and repair upstream artifacts.
- If required execution anchors are missing from `plan.md`, `contracts/`, or `test-matrix.md`, stop and repair upstream artifacts rather than writing compensating tasks.
- `tasks.md` uses `GLOBAL` and `Interface Delivery Units` as execution packages only, not as replacement design sections.

## 2) Upstream Inputs (Execution References)

Use concise references only. Do not build registry/audit tables here.

| Input Artifact | Usage in Tasks | Required |
| --- | --- | --- |
| `plan.md` | structure, stack, project paths | Yes |
| `spec.md` | FR/UC/UIF requirement context | Yes |
| `data-model.md` | entity/invariant references | Yes |
| `test-matrix.md` | feature verification anchors (`TM-*` / `TC-*`) | Yes |
| `contracts/` | interface operation targets | Yes |

## 2.1) Upstream Alignment Repair (Required On Projection Drift)

Only include this section when drift exists between contract projection slices and upstream artifacts.

| Drift Type | Contract Projection Evidence | Upstream Target | Owner Command | Required Repair |
| --- | --- | --- | --- | --- |
| `spec` drift | [operationId + `Spec Projection Slice` refs] | `spec.md` | `/sdd.specify` | [align `spec.md` refs/phrasing to contract projection] |
| `test` drift | [operationId + `Test Projection Slice` refs] | `test-matrix.md` | `/sdd.plan.test-matrix` | [align TM/TC rows and anchors to contract projection] |

Rules:

- Keep entries execution-oriented and file-targeted; do not add audit prose.
- These rows are mandatory when drift is detected during `/sdd.tasks`.
- Do not dual-write conflicting semantics into `tasks.md`; keep one active projection source per IF unit.

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

`- [ ] T### [Type:Research|Interface|Verify|Infra|Docs] [IF-###?] [Role:...] [Pre:T###,...] Description with explicit file path or command target (Completion Anchor: [single primary pass signal])`

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
- Each task is one projected execution work package from completed plan-stage design.
- Each task MUST map to exactly one execution target: one `operationId` or one shared prerequisite objective.
- Each task MUST declare exactly one explicit target path cluster or one command target.
- Each task MUST declare exactly one primary completion anchor; if no primary completion anchor can be projected, do not generate the task.
- A task MUST NOT combine multiple operations, multiple unrelated file clusters, or multiple distinct validation objectives.
- File paths or command targets define execution boundary, must be explicit, and must come from authoritative upstream artifacts rather than task-stage inference.

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
- Only place prerequisites here when they are consumed by multiple IF units.
- Do not place interface-specific implementation tasks here.
- Treat use of `GLOBAL` as overflow for one-scope work as invalid task generation.

## 6) Interface Delivery Units

Interface delivery units are IF-scoped execution work packages. Keep them execution-oriented and reference-driven.

```markdown
## Interface IF-### — [name]

- Goal: [one-line delivery goal; short execution-only reference]
- Contract: [single operationId / boundary anchor]
- Implementation Entry: [single repo-backed entry anchor from contract realization section, or same as contract boundary]
- Spec Slice: [UC/UIF/FR/SC/EC refs projected from contract `Spec Projection Slice`]
- Test Slice: [Test Scope + TM/TC + pass/failure anchors projected from contract `Test Projection Slice`]
- Primary Refs: [short refs that help execution or completion checks]

Recommended delivery loop:
- establish verification target
- implement interface behavior
- confirm completion against contract/scenario refs

- [ ] T### [Type:Verify] [IF-###] [Role:contract|smoke|manual-check] [Pre:T###,...] Validate [operationId] in [path] (Completion Anchor: [TM|TC|contract check])
- [ ] T### [Type:Interface] [IF-###] [Role:handler|service|persistence|wiring] [Pre:T###,...] Implement [operationId] via [Implementation Entry Anchor] in [path] (Completion Anchor: [build|CaseID|acceptance-check])
- [ ] T### [Type:Verify] [IF-###] [Role:completion] [Pre:T###,...] Confirm [operationId] delivery in [path] (Completion Anchor: [CaseID|TM|contract pass])
```

Rules:

- Organize implementation primarily by interface delivery units keyed by `IF Scope`.
- Treat each interface delivery unit as an execution work package derived from approved planning artifacts, not a second design pass.
- Each IF unit SHOULD form a verification-implementation-completion loop (document exceptions).
- Keep IF sections reference-oriented; do not copy upstream design prose or add design explanation paragraphs.
- Use `Contract` as the client-facing binding reference and `Implementation Entry` as the internal execution-target reference when they differ.
- `Spec Slice` and `Test Slice` are mandatory per IF unit and are the authoritative downstream execution projection slices from contract; they are not optional narrative notes.
- Keep `Goal`, `Contract`, `Implementation Entry`, and `Primary Refs` as short execution references only.
- If multiple operations share an `IF Scope`, keep them as separate work packages inside the same IF unit; do not merge them into a composite task.
- Use `CaseID/TM/TC` as completion anchors only when they help prove delivery.

## 7) Cross-Interface Finalization

- [ ] T### [Type:Verify] [Role:smoke] [Pre:T###,...] Run cross-interface smoke chain [SMK-### -> SMK-###] using [command/path] (Completion Anchor: [SMK-### pass signal])
- [ ] T### [Type:Infra] [Role:validation] Run final validation command set in [path] (Completion Anchor: [command + pass signal])

Rules:

- Use this section only for tasks that cannot be scoped to one IF unit.
- Cross-interface smoke tasks MUST be projected from contract `Cross-Interface Smoke Candidate (Required)` rows.
- If all contract rows carry `Candidate Role = none`, document this explicitly and skip smoke-task generation.
- Do not use this section for work that exists only because upstream design anchors are missing.
- Do not use this section as overflow for interface-local tasks.

## 8) Implementation Consumption

- `/sdd.implement` MUST prefer `tasks.manifest.json` for runtime scheduling metadata.
- If `tasks.manifest.json` is missing or invalid, `/sdd.implement` falls back to parsing `tasks.md`.
- `tasks.md` remains the human-review and execution-orchestration authority.
- `tasks.manifest.json` is a machine-readable projection only and MUST NOT introduce new semantics.
- `tasks.manifest.json` should be refreshed from the same run-local execution graph used to render `tasks.md`, so both outputs stay atomically aligned for a run.
- `tasks.manifest.json` top-level keys MUST include `schema_version`, `generated_at`, `generated_from`, and `tasks`.
- `generated_from` MUST include `plan_path`, `plan_source_fingerprint`, and `contract_source_fingerprints`.
- `tasks.manifest.json` task IDs and dependencies must stay aligned with the `tasks.md` lines rendered from the same execution graph.
- Required consumable sections in `tasks.md` (authoritative fallback + human review):
  - `Upstream Inputs (Execution References)`
  - `Execution Ordering Model` (`Task DAG`)
  - `Shared Foundation`
  - `Interface Delivery Units`
  - `Cross-Interface Finalization`
- These sections are execution packages, not replacement design documents.
- Runtime progress statuses belong to implementation runtime, not generation metadata.

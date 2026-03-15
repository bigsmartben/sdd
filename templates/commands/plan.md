---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
handoffs:
  - label: Create Tasks
    agent: sdd.tasks
    prompt: Break the plan into tasks
    send: true
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR`, and `BRANCH`.
2. **Bootstrap shared context only**: Read `FEATURE_SPEC`, `/memory/constitution.md`, the copied `IMPL_PLAN`, and `templates/plan-template.md`.
   - Extract only the feature goal, must-have requirements, explicit constraints, user-supplied technical direction, and unresolved blockers needed to start planning.
   - Do not preload stage templates or completed stage artifacts before they are needed.
3. **Fill plan.md from the template**:
   - Use `plan-template.md` as the structure source for `plan.md`.
   - Fill `Summary`, `Technical Context`, `Constitution Check`, and the stage sections at summary level first.
   - Keep `plan.md` focused on planning-stage inputs, outputs, stage intent, boundary notes, and short downstream projection notes.
   - Treat `plan.md` as the planning compression ledger for downstream stage reuse.
4. **Build the runtime work queue before each stage**:
   - This runtime scheduling guidance is execution-only. It MUST NOT change stage order, required outputs, stage boundaries, evidence thresholds, or artifact coverage defined elsewhere in this command.
   - Keep only three context tiers active:
     - **Bootstrap packet**: feature goal, must-have requirements, explicit constraints, unresolved blockers, absolute paths, and the current stage index
     - **Stage workset**: the active stage template plus the minimum upstream artifact slices needed for that stage
     - **Unit card**: exactly one active planning unit at a time (`research question`, `backbone group`, `scenario cluster`, or active `Operation ID` / `Boundary Anchor` / `IF Scope` tuple)
   - Turn each stage into one parent task with bounded subtasks: `Discover -> Generate -> Compress`.
   - Before opening a subtask, declare its exact inputs, expected output, and stop condition; do not load extra files until the current subtask proves they are needed.
   - When multiple candidate subtasks exist, pick the smallest next subtask that unblocks the stage instead of broad repository exploration.
   - After a subtask writes its output, discard its detailed working set and carry forward only stable anchors, IDs, constraints, and blockers.
5. **Run the planning workflow as a context-minimized loop**:
   - For each stage, apply `Clarify -> Generate -> Boundary Check -> Compress`.
   - Immediately before a stage, read only that stage's template plus the minimum upstream artifacts required for that stage.
   - Prefer section-level or row-level rereads over whole-file replay whenever downstream scope is narrower.
   - After each stage, write a 3-7 bullet downstream projection note set in `plan.md` covering only what later stages must consume: canonical terms, stable IDs, binding tuples, hard constraints, and unresolved blockers.
   - Do not write retrospective recaps or generic stage summaries in these projection notes.
   - Once the downstream projection notes are recorded, do not keep the full completed artifact active unless an exact detail is required to avoid contradiction.
   - If a stage is underspecified or drifts into another stage's responsibility, resolve the issue before moving forward.
   - Do not preserve or describe historical workflow variants.
6. **Execute stages in fixed order with stage-local reads**:
   - Stage 0: `research.md` from `templates/research-template.md`; use `spec.md`, user input, constitution, and targeted repository evidence only
   - Stage 1: `data-model.md` from `templates/data-model-template.md`; use `spec.md` and `research.md`
   - Stage 2: `test-matrix.md` from `templates/test-matrix-template.md`; use `spec.md`, `research.md`, and `data-model.md`; derive stable tuple keys early
   - Stage 3: `contracts/` using `templates/contract-template.md`; use only the relevant `spec.md`, `data-model.md`, and `test-matrix.md` slices for each boundary/operation; generate one contract artifact at a time
   - Stage 4: `interface-details/` using `templates/interface-detail-template.md`; use only the matching contract binding row, matching `TM/TC` rows, and relevant `data-model.md` / `research.md` anchors for each operation; generate one detail artifact at a time
7. **Stop and report**: End after Stage 4. Report the branch, `plan.md` path, and generated artifacts.

## Workflow Rules

- The workflow order is fixed: `Research -> Data Model -> Feature Verification Design -> Contracts -> Interface Detailed Design`.
- `/memory/constitution.md` and `spec.md` are the authoritative upstream semantics for `/sdd.plan`.
- `plan-template.md` defines `plan.md` only; planning artifact structure comes from the sibling planning templates in `templates/`.
- Record only planning-stage inputs, outputs, stage intent, and boundary notes in `plan.md`; detailed artifact structure lives in the sibling templates.
- `plan.md` downstream projection notes and any temporary extraction tables or summaries are derived views only; they MUST NOT override upstream artifacts or downstream stage artifacts.
- Minimize active context: default to stage-local reads and `plan.md` projection notes rather than replaying full upstream artifacts.
- Treat repository investigation as a bounded discovery subtask, not a standing background activity.
- Never reread a completed artifact in full when a specific section, row, or anchor is enough to keep downstream output correct.
- Do not copy large upstream tables or prose into downstream artifacts; carry forward stable anchors, IDs, and concise summaries instead.
- When repository evidence is needed, start with targeted path discovery and matched-file reads; avoid broad sweeps unrelated to the current stage.
- If an upstream artifact changes, conflicts with a projection note, or appears stale, discard the stale derived view and reread the authoritative slice before continuing downstream generation.
- Stage 1 outputs only `data-model.md`.
- `test-matrix.md` remains the file name for Feature Verification Design.
- `test-matrix.md` is a planning-stage test design supplement, not an audit/traceability ledger.
- `contracts/` defines minimum external I/O only.
- `interface-details/` focuses on field semantics, sequence diagrams, UML class design, and upstream references.
- When Stages 3 and 4 span multiple operations, process them sequentially and keep only the active tuple (`Operation ID`, `Boundary Anchor`, `IF Scope`) in working context.
- Normalize canonical terms and stable IDs as soon as they appear; downstream artifacts should reuse them verbatim.
- Do not add compatibility instructions, dual-path behavior, or legacy terminology explanations.

## Stage 0: Research

- Resolve planning blockers, record evidence-backed decisions, and stay out of models, verification paths, contracts, and interface design.

## Stage 1: Data Model

- Capture backbone-only shared semantics, repository anchors, invariants, and lifecycle anchors without drifting into per-operation or implementation-layer design.

## Stage 2: Feature Verification Design

- Produce scenario-oriented test design with stable `Operation ID` / `Boundary Anchor` / `IF Scope` tuple keys and stay out of contracts and interface internals.

## Stage 3: Contracts

- Define minimum external I/O, success/failure semantics, and tuple-aligned boundary bindings without sequence or UML detail.

## Stage 4: Interface Detailed Design

- Produce operation-level field semantics, sequences, and UML that preserve upstream tuple compatibility without redefining contract or global model semantics.

## Final Checks

- Stage order matches the fixed workflow.
- `plan.md` acts as a compression ledger with short downstream projection notes instead of duplicated artifact content.
- Stage 1 output is concrete and reusable (shared elements, repository anchors, stable fields, grouped relationships, invariants, lifecycle anchors) while remaining backbone-only.
- Stage 1 avoids generalized placeholder prose and does not drift into DTO-complete, implementation-layer, persistence-schema, or operation-level design.
- Stages 3 and 4 are generated sequentially per boundary/operation tuple rather than as one monolithic expansion.
- Downstream artifacts keep anchor and tuple alignment without copying large upstream sections verbatim.
- Command instructions describe workflow and boundaries only.
- Output structure details stay in the template, not here.

## Key Rules

- Use absolute paths.
- Stop on unresolved critical constraints or unresolved clarifications.

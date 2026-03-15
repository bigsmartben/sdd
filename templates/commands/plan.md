---
description: Generate implementation planning artifacts from authoritative upstream inputs using a fixed Stage 0-4 workflow.
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

## Goal

Produce planning artifacts with strict stage responsibilities and minimal context loading. Keep `/sdd.plan` focused on generation-time boundaries, handoff-ready outputs, and downstream projection notes. Do not perform centralized cross-artifact audit gating in this command.

## Stage Flow

Run `{SCRIPT}` once from repo root and parse JSON for `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR`, and `BRANCH`.

Workflow order is fixed and non-negotiable:

1. Stage 0 -> `research.md`
2. Stage 1 -> `data-model.md`
3. Stage 2 -> `test-matrix.md`
4. Stage 3 -> `contracts/`
5. Stage 4 -> `interface-details/`

## Stage Template Bindings

## Stage 0: Research

- Template: `templates/research-template.md`

## Stage 1: Data Model

- Template: `templates/data-model-template.md`

## Stage 2: Feature Verification Design

- Template: `templates/test-matrix-template.md`

## Stage 3: Contracts

- Template: `templates/contract-template.md`

## Stage 4: Interface Detailed Design

- Template: `templates/interface-detail-template.md`

Stage I/O boundaries:

- **Stage 0 (Research)**
  - Inputs: `spec.md`, user input, `.specify/memory/constitution.md`, targeted repo anchors only
  - Output: `research.md`
  - Boundary: resolve planning blockers and evidence-backed decisions only
- **Stage 1 (Data Model)**
  - Inputs: `spec.md`, `research.md`, and lifecycle repo anchors (enum definitions, persisted `status/state` fields, mapper status values)
  - Output: `data-model.md`
  - Boundary: canonical terms, stable IDs, `INV-*`, lifecycle anchors (backbone scope only)
  - Mandatory sequence: resolve lifecycle repo anchors first, then write lifecycle/invariant semantics
- **Stage 2 (Feature Verification Design)**
  - Inputs: `spec.md`, `research.md`, `data-model.md`
  - Output: `test-matrix.md`
  - Boundary: scenario-oriented verification design with stable tuple keys
- **Stage 3 (Contracts)**
  - Inputs: only per-operation slices from `spec.md`, `data-model.md`, `test-matrix.md`, plus anchored boundary symbols and anchored facade method + request/response DTO
  - Output: `contracts/*`
  - Boundary: minimum external I/O and tuple-aligned binding rows
  - Mandatory sequence: locate repo boundary anchor first, then generate `Operation ID` / `Boundary Anchor` / `IF Scope`, then draft contract I/O
- **Stage 4 (Interface Detailed Design)**
  - Inputs: only matching Stage 3 binding rows, matching `TM/TC` rows, relevant anchors from `data-model.md` / `research.md`, anchored facade method + request/response DTO, and anchored implementation collaborators (`service impl` / `manager` when present)
  - Output: `interface-details/*`
  - Boundary: operation-level field semantics/sequence/UML only; MUST NOT redefine contract semantics or global model semantics
  - Mandatory sequence: for each operation, read facade method, DTOs, and implementation collaborators before generating interface details

After each stage, write 3-7 concise downstream projection notes into `plan.md` and keep handoff-ready anchors only.

### Runtime Context Minimization Rules

- Bootstrap shared context only.
- Do not preload stage templates or completed stage artifacts before they are needed.
- Treat `plan.md` as the planning compression ledger.
- Build the runtime work queue before each stage.
- This runtime scheduling guidance is execution-only.
- Keep only three context tiers active.
- Turn each stage into one parent task with bounded subtasks: `Discover -> Generate -> Compress`.
- For each stage, discard its detailed working set and carry forward only stable anchors.
- For each stage, read only that stage's template plus the minimum upstream artifacts required for that stage.
- After each stage, write a 3-7 bullet downstream projection note set.
- Do not write retrospective recaps or generic stage summaries.
- In Stage 3, generate one contract artifact at a time.
- In Stage 4, generate one detail artifact at a time.
- For tuple-scoped generation, keep only the active tuple (`Operation ID`, `Boundary Anchor`, `IF Scope`) in working context.
- For `/sdd.plan`, `repo anchor` means source-code files/symbols plus `.specify/memory/constitution.md` only.
- `README.md`, `docs/**`, `specs/**`, historical examples, and generated artifacts are supporting inputs only.

## Generation Rules

- Use `templates/plan-template.md` as the structure source for `plan.md`.
- Keep `plan.md` as a planning compression ledger: stage intent, boundaries, blockers, and downstream projection notes.
- Apply stage-local read discipline:
  - Read only the active stage template plus minimum required upstream slices.
  - Prefer section/row-level rereads over full-file replay.
  - Generate one unit at a time (research question, backbone group, scenario cluster, or one tuple scope).
- Authority and derivation protocol:
  - `.specify/memory/constitution.md` and `spec.md` are the authoritative upstream semantics for `/sdd.plan`.
  - `plan.md` downstream projection notes and any temporary extraction tables or summaries are derived views only; they MUST NOT override upstream artifacts or downstream stage artifacts.
  - When temporary notes drift from current authoritative source artifacts, discard the stale derived view and reread the authoritative slice before continuing downstream generation.
- Repo-anchor discipline:
  - For `/sdd.plan`, semantic repo anchors are source code symbols/files plus `.specify/memory/constitution.md`.
  - `spec.md`, planning artifacts, `README.md`, `docs/**`, `specs/**`, and generated outputs are supporting inputs only, and they MUST NOT be promoted into repo semantic anchors.
- Missing-anchor rule:
  - If semantic evidence lacks repo anchor, mark `TODO(REPO_ANCHOR)` as `forward-looking`.
  - Stop semantic promotion for that item in current stage.
  - Carry it forward as explicit blocker instead of upgrading into stable semantics.

### Hard Constraint Closure Rules

- Boundary-anchor protocol (Stage 3 + Stage 4):
  - Locate real repo boundary symbol before generating tuple keys.
  - Valid normative `Boundary Anchor` forms are only: RPC/Façade method, HTTP `METHOD /path`, `event.topic`, or CLI command.
  - `BA-*` is never a normative anchor; it may appear only as a non-normative helper label.
  - If no repo boundary anchor exists, use `TODO(REPO_ANCHOR)` and keep that tuple out of main validation paths.
- Participant/collaborator protocol (Stage 4):
  - Reuse anchored source symbols first in sequence participants and UML collaborators.
  - When repo symbols exist, do not invent layered collaborator names such as `*BoundaryAdapter`, `*Service`, `*Policy`, or `*Assembler`.
- Runtime correctness protocol (Stage 4 guidance):
  - Use the `Runtime Correctness Check` section in the interface detail template as generation guidance for contract-visible runtime paths.
  - Pre-filling the check table is recommended but not required during `/sdd.plan`; centralized blocking validation remains in `/sdd.analyze`.
- Contract/interface I/O protocol (Stage 3 + Stage 4):
  - Read anchored facade method signature plus request/response DTO before drafting contract or interface detail.
  - `Request` / `Success Output` / `Failure Output` and field semantics must match anchored method signature and DTO structure (including nesting and anchored status vocabulary).
  - You may add business meaning, but do not rename fields, flatten DTO nesting, or split fields that do not exist in anchored DTOs.
- Lifecycle protocol (Stage 1):
  - Read anchored enum/status field/mapper status values before writing lifecycle anchors.
  - UX phase/page step/flow node is not aggregate lifecycle state.
  - States without repo anchors stay `forward-looking` only and must not enter `INV-*`, lifecycle stable states, or contract-binding tuples.
  - Apply constitution state-machine applicability policy during planning output generation:
    - when a Full FSM is required by constitution applicability thresholds, ensure planning outputs include the expected FSM artifacts;
    - when a Full FSM is used below threshold, record explicit justification in planning complexity tracking.

### Non-Negotiable Semantic Projection

- Stage 0 research outputs project only required evidence and blockers to later stages.
- Stage 1 canonical terms / stable IDs / `INV-*` / lifecycle anchors project to Stage 2-4 verbatim.
- Stage 2 tuple keys (`Operation ID` / `Boundary Anchor` / `IF Scope`) project to Stage 3-4 as binding identity.
- Stage 3 contract binding rows project to Stage 4 without semantic reinterpretation.
- If repo anchor is missing, stop semantic upgrade for that item and preserve blocker state.

## Reference Strength Policy

- Core semantics (`canonical term`, `stable field`, `INV-*`, `lifecycle state`, `Operation ID`, normative `Boundary Anchor`) require repo-anchor evidence before becoming stable outputs.
- Path-only inference is forbidden.
- Helper documents and generated artifacts cannot independently prove semantics.
- `forward-looking` / `TODO(REPO_ANCHOR)` items MUST NOT enter shared invariants, lifecycle-stable states, primary validation rows, or contract/interface binding tuples.

## Stop Conditions

Stop immediately when any of the following occurs:

- Required stage input is missing or contradictory.
- Critical clarification or constraint remains unresolved.
- Semantic item requires repo anchor but none is found (`TODO(REPO_ANCHOR)`).
- `Boundary Anchor` uses non-normative form (including `BA-*`) as if it were authoritative.
- Stage 3/4 I/O semantics drift from anchored facade signature or anchored DTO structure.
- Stage 4 participant/collaborator set invents layered placeholders while anchored repo symbols already exist.
- Stage 1 lifecycle states are inferred from UX phases/flow nodes or drift from anchored enum/status sources.
- Stage output drifts beyond its boundary.

End after Stage 4 and report branch, `plan.md` path, and generated artifacts.

## Final Checks

- Stage order remains `Research -> Data Model -> Feature Verification Design -> Contracts -> Interface Detailed Design`.
- Each stage respects I/O boundaries and stage-local read policy.
- `plan.md` contains concise downstream projection notes, not duplicated large tables/prose.
- Semantic projection chain is preserved: Research -> Stage 1 -> Stage 2 -> Stage 3 -> Stage 4.
- Stage 4 preserves upstream contract/global-model semantics without redefinition.
- Use absolute paths.

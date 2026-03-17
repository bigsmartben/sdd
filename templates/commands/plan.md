---
description: Run the complete planning suite in one call via an internal staged orchestrator with fail-fast execution.
handoffs:
  - label: Create Tasks
    agent: sdd.tasks
    prompt: Break the plan into tasks
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

Run `/sdd.plan` as a single-run planning orchestrator with strict stage boundaries and minimal context loading. One `/sdd.plan` invocation MUST attempt the complete planning suite in fixed order: `research.md -> data-model.md -> test-matrix.md -> interface-package loop -> plan.md` downstream projection. Keep `/sdd.plan` focused on generation-time boundaries, handoff-ready outputs, and downstream projection notes. Do not perform centralized cross-artifact audit gating in this command.

## Single-Run Planning Protocol (Non-Negotiable)

Run `{SCRIPT}` once from repo root and parse JSON for `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR`, and `BRANCH`.

`/sdd.plan` MUST behave as one full planning run:

1. Build shared planning bootstrap
2. Generate/update `research.md`
3. Generate/update `data-model.md`
4. Generate/update `test-matrix.md`
5. Run the `interface-package` loop one operation at a time:
   - generate/update one contract artifact under `contracts/`
   - hand off internally to generate/update the matching interface-detail artifact under `interface-details/`
   - complete the current operation package before moving to the next operation
6. Refresh `plan.md` as the planning compression ledger and downstream projection

Do not require or expose user-facing target-entry selection. Do not expose first-call/second-call behavior. Any attempt to run only a partial planning suite in the mainline flow is invalid.

## Repository-First Projection Artifacts (Mandatory)

`/sdd.plan` MUST consume the repository-first canonical baseline produced by `/sdd.constitution`.
These artifacts are authoritative at the project level and live under `.specify/memory/repository-first/`:

1. `.specify/memory/repository-first/technical-dependency-matrix.md`
2. `.specify/memory/repository-first/module-invocation-spec.md`

Repository-first consumption rules:

- If any canonical artifact is missing, stale, or non-traceable, stop and route to `/sdd.constitution` before continuing planning generation.
- Feature-local copies under `FEATURE_DIR` are derived views only and MUST NOT be treated as repository-first semantic authority.
- Build-manifest auto-detection processes supported ecosystems in deterministic priority: Maven (`pom.xml`), Node (`package.json`), Python (`pyproject.toml` + requirements/lock hints), Go (`go.mod`).
- Dependency key normalization remains: Maven = `group:artifact`; Node/Python/Go = `ecosystem:package_or_module`.
- `technical-dependency-matrix.md` remains the dependency-governance fact source, including version divergence and `unresolved`.
- `module-invocation-spec.md` remains the invocation/layering fact source and MUST consume version-divergence and `unresolved` signals from the canonical dependency matrix.

## Stage Template Bindings

Template authority note:
- In this repository, `templates/...` is the source-of-truth; initialized workspaces use `.specify/templates/...`.
- For interface detail generation in feature workspaces, use `.specify/templates/interface-detail-template.md`.

Planning-stage templates (single run):
- Research unit -> `templates/research-template.md`
- Data-model unit -> `templates/data-model-template.md`
- Verification-design unit -> `templates/test-matrix-template.md`
- Interface-definition unit -> `templates/contract-template.md`
- Interface-detail unit -> `templates/interface-detail-template.md`

Stage I/O boundaries:

- **Stage A / Bootstrap**
  - Inputs: `spec.md`, user input, `.specify/memory/constitution.md`, canonical repository-first baseline, and targeted repo anchors only
  - Output: shared planning bootstrap state for later internal stages
  - Boundary: shared reusable planning inputs only; no artifact drafting beyond bootstrap framing
- **Stage B / Research**
  - Inputs: Stage A bootstrap plus minimum repo/source slices needed for decisions and blockers
  - Output: `research.md`
  - Boundary: research decisions, source-code reuse anchors, constraints, and blocking open questions only
- **Stage C / Data Model**
  - Inputs: Stage A bootstrap, `research.md`, and minimum upstream semantic slices
  - Output: `data-model.md`
  - Boundary: backbone-only data semantics; no per-operation contract/detail drafting
- **Stage D / Verification Design**
  - Inputs: Stage A bootstrap, `research.md`, `data-model.md`, and minimum upstream semantic slices
  - Output: `test-matrix.md`
  - Boundary: scenario/path verification design only; no interface internals
- **Stage E / Interface-Package Loop**
  - Inputs: Stage A bootstrap, `research.md`, `data-model.md`, `test-matrix.md`, plus one active operation workset at a time
  - Output: one contract + one matching interface-detail per active operation
  - Boundary: one operation-local package at a time; complete `interface-definition -> handoff -> interface-detail` before advancing
- **Stage F / Final Compression**
  - Inputs: completed stage artifacts only
  - Output: `plan.md`
  - Boundary: planning compression ledger and downstream projection only; no new semantics

### Runtime Context Minimization Rules

- Bootstrap shared context only.
- Do not preload stage templates or completed stage artifacts before they are needed.
- Treat `plan.md` as the planning compression ledger.
- Build the runtime work queue before each stage.
- This runtime scheduling guidance is execution-only.
- Keep only three context tiers active.
- Turn each stage into one parent task with bounded subtasks: `Discover -> Generate -> Compress -> Handoff`.
- For each stage, read only that stage's template plus the minimum upstream artifacts required for that stage, then discard its detailed working set and carry forward only stable anchors.
- After each stage, write a 3-7 bullet downstream projection note set. Do not write retrospective recaps or generic stage summaries.
- Keep the externally visible command as one full planning run, while internal handoff payloads remain runtime-only.
- For the interface-package loop, keep only one active tuple (`Operation ID`, `Boundary Anchor`, `IF Scope`) in working context at a time.
- For `/sdd.plan`, repo semantic evidence follows constitution `Repo-Anchor Evidence Protocol`: source anchors plus engineering assembly facts only.
- Dependency-matrix conclusions MUST come from canonical repository-first baseline files, not feature-local regeneration.
- `.specify/memory/constitution.md` is rule authority for this command and MUST NOT be treated as component-boundary evidence.
- `README.md`, `docs/**`, `specs/**`, `tests/**`, `plans/**`, `templates/**`, historical examples, and generated artifacts are supporting inputs only.
- Auxiliary-document checks are not a planning prerequisite in this command.

## Internal Handoff Payload Protocol (Runtime-Only)

`handoff payload` is an internal `/sdd.plan` scheduler construct. It exists only during the current `/sdd.plan` run and MUST NOT be written as a sidecar file, embedded as structured data in `plan.md`, or sent through frontmatter `handoffs` to other commands.

Required payload fields:

- `from_stage`
- `to_stage`
- `unit_type`
- `unit_id`
- `goal`
- `authoritative_inputs`
- `allowed_reads`
- `write_targets`
- `stable_anchors`
- `blockers`
- `stop_reason`
- `projection_notes`
- `aux_docs_checked: false`

Payload rules:

- Each stage may read only the authoritative inputs and minimum slices named by the active payload.
- `allowed_reads` MUST be explicit and minimum-bounded for the active stage or operation package.
- `write_targets` MUST name the artifact(s) allowed in the active stage; for the interface-package loop, it MUST include both the contract path and the matching interface-detail path.
- Payloads may carry stable anchors, blockers, and downstream projection notes only; they MUST NOT carry full reasoning transcripts or auxiliary-document summaries.
- `/sdd.tasks` and `/sdd.implement` MUST NOT consume `/sdd.plan` internal handoff payloads.

## Generation Rules

- Use `templates/plan-template.md` as the structure source for `plan.md`.
- Keep `plan.md` as a planning compression ledger: stage intent, boundaries, blockers, and downstream projection notes.
- Apply stage-local read discipline:
  - Prefer section/row-level rereads over full-file replay.
  - Generate one unit at a time (one stage artifact or one active operation package).
- Authority and derivation protocol:
  - `.specify/memory/constitution.md` and `spec.md` are the authoritative upstream semantics for `/sdd.plan`.
  - `plan.md` downstream projection notes and any temporary extraction tables or summaries are derived views only; they MUST NOT override upstream artifacts or downstream stage artifacts.
  - When temporary notes drift from current authoritative source artifacts, discard the stale derived view and reread the authoritative slice before continuing downstream generation.
- Supporting-input discipline:
  - `spec.md`, planning artifacts, `README.md`, `docs/**`, `specs/**`, `tests/**`, `plans/**`, `templates/**`, and generated outputs are supporting inputs only, and they MUST NOT be promoted into repo semantic anchors.
- Missing-anchor rule:
  - If semantic evidence lacks repo anchor, mark `TODO(REPO_ANCHOR)` as `forward-looking`.
  - Stop semantic promotion for that item in current stage.
  - Carry it forward as explicit blocker instead of upgrading into stable semantics.

### Hard Constraint Closure Rules

- Boundary-anchor protocol (active generation stage):
  - Locate real repo boundary symbol before generating tuple keys.
  - Valid normative `Boundary Anchor` forms are only: RPC/Façade method, HTTP `METHOD /path`, `event.topic`, or CLI command.
  - `BA-*` is never a normative anchor; it may appear only as a non-normative helper label.
  - If no repo boundary anchor exists, use `TODO(REPO_ANCHOR)` and keep that tuple out of main validation paths.
- Contract/interface I/O protocol (`interface-package` loop):
  - Read anchored facade method signature plus request/response DTO before drafting contract or interface detail.
  - `Request` / `Success Output` / `Failure Output` and field semantics must match anchored method signature and DTO structure (including nesting and anchored status vocabulary).
  - You may add business meaning, but do not rename fields, flatten DTO nesting, or split fields that do not exist in anchored DTOs.
- Lifecycle protocol (`data-model` unit only):
  - Read anchored enum/status field/mapper status values before writing lifecycle anchors.
  - UX phase/page step/flow node is not aggregate lifecycle state.
  - States without repo anchors stay `forward-looking` only and must not enter `INV-*`, lifecycle stable states, or contract-binding tuples.
  - Apply constitution state-machine applicability policy during planning output generation:
    - when a Full FSM is required by constitution applicability thresholds, ensure planning outputs include the expected FSM artifacts;
    - when a Full FSM is used below threshold, record explicit justification in planning complexity tracking.
- Participant/collaborator protocol (`interface-detail` unit only):
  - Reuse anchored source symbols first in sequence participants and UML collaborators.
  - When repo symbols exist, do not invent layered collaborator names such as `*BoundaryAdapter`, `*Service`, `*Policy`, or `*Assembler`.
- Runtime correctness protocol (`interface-detail` guidance):
  - Use the `Runtime Correctness Check` section in the interface detail template as generation guidance for contract-visible runtime paths.
  - Pre-filling the check table is recommended but not required during `/sdd.plan`; centralized blocking validation remains in `/sdd.analyze`.

### Non-Negotiable Semantic Projection

- Research, data-model, verification-design, and each interface package MUST preserve tuple identity (`Operation ID` / `Boundary Anchor` / `IF Scope`) when applicable.
- Inside the interface-package loop, contract output must hand off matching contract-binding semantics to the paired interface detail without reinterpretation.
- `forward-looking` / `TODO(REPO_ANCHOR)` items MUST NOT enter shared invariants, lifecycle-stable states, primary validation rows, or contract/interface binding tuples.

## Stop Conditions

Stop immediately when any of the following occurs:

- Required stage input is missing or contradictory.
- Canonical repository-first baseline files are missing or stale (`.specify/memory/repository-first/*.md`); route to `/sdd.constitution`.
- Critical clarification or constraint remains unresolved.
- Semantic item requires repo anchor but none is found (`TODO(REPO_ANCHOR)`).
- `Boundary Anchor` uses non-normative form (including `BA-*`) as if it were authoritative.
- `data-model` lifecycle states are inferred from UX phases/flow nodes or drift from anchored enum/status sources.
- `test-matrix.md` cannot bind stable verification tuples needed by later interface packages.
- An interface-package contract or detail I/O semantic drifts from anchored facade signature or anchored DTO structure.
- An interface-package detail participant/collaborator set invents layered placeholders while anchored repo symbols already exist.
- An interface package cannot complete both contract and matching detail in the current run.
- Any stage or unit attempts to bypass or freely expand beyond payload-scoped reads, or stage output drifts beyond its boundary.

Fail fast on the first blocking stage or operation package. Report branch, `plan.md` path, and the planning artifact paths that were generated before the stop condition.

## Final Checks

- One `/sdd.plan` invocation completes the full planning suite when no blockers occur.
- Stage order remains `Bootstrap -> Research -> Data Model -> Verification Design -> Interface-Package Loop -> Final Compression`.
- The interface-package loop completes `contract -> handoff -> detail` per operation before advancing.
- Internal handoff payloads remain runtime-only and are not exposed as persisted contract artifacts.
- `research.md`, `data-model.md`, `test-matrix.md`, `contracts/`, and `interface-details/` are all present before `/sdd.tasks`.
- Use absolute paths.

---
description: Generate tasks.md and tasks.manifest.json for the current feature branch.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --task-preflight
  ps: scripts/powershell/check-prerequisites.ps1 -Json -TaskPreflight
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Run `{SCRIPT}` once from repo root.
Parse `FEATURE_DIR`, `AVAILABLE_DOCS`, `LOCAL_EXECUTION_PROTOCOL`, and `TASKS_BOOTSTRAP`.

## Goal

Generate one `tasks.md` and one `tasks.manifest.json` for the current feature branch.
Use `.specify/templates/tasks-template.md` only.

`/sdd.tasks` owns:
- Decomposing delivery design (plan.md / selected `contracts/` slices / data-model.md) into actionable, DAG-ordered tasks.
- Mapping each task to its design refs and target paths.
- Defining completion anchors for execution validation.

## Read Only

- `TASKS_BOOTSTRAP` packet (from `{SCRIPT}`)
- `plan.md` — Stage Queue / Artifact Status / Shared Context Snapshot
- `contracts/` — selected binding slices only
- `data-model.md`, `test-matrix.md`, `research.md`
- `FEATURE_SPEC`
- `LOCAL_EXECUTION_PROTOCOL` (from `TASKS_BOOTSTRAP`; includes `LOCAL_EXECUTION_PROTOCOL.python.runner_cmd` and `LOCAL_EXECUTION_PROTOCOL.runtime_tools`)
- `LOCAL_EXECUTION_PROTOCOL.repo_search.list_files_cmd`
- If `LOCAL_EXECUTION_PROTOCOL.repo_search.available = false`, do not run repo-search commands; continue with available runtime tools only.

## Write Only

- `tasks.md`
- `tasks.manifest.json`

## Final Output

- `tasks.md` — execution-ordered work packages using `Task DAG`, `GLOBAL`, and `IF-###` scopes
- `tasks.manifest.json` — machine-readable manifest
  - Generate `tasks.manifest.json` from the same run-local execution graph used to render `tasks.md`.
  - Top-level keys: `schema_version`, `generated_at`, `generated_from`, `tasks`, `presentation`
  - `generated_from` minimal provenance: `plan_path` only
  - `presentation` MUST describe the enhanced task board projection without adding semantic task data.
  - `presentation.board_style` MUST be `enhanced`.
  - `presentation.source_lineage` MUST include `plan_path`.

## Prerequisite Gate

Treat `TASKS_BOOTSTRAP.execution_readiness` as the primary hard gate.

- If `TASKS_BOOTSTRAP.execution_readiness.errors` contains blockers, stop immediately and report the runtime bootstrap blocker.
- do not recompute full hard gates by re-deriving complete `plan.md` tables from scratch; the bootstrap packet is the authority.
- Active executable tuples select `new` repo anchors but lack explicit rejection evidence for `existing` and `extended` — treat this as a hard blocker.
- Any selected `contract` row is missing `Full Field Dictionary (Operation-scoped)` — treat this as a hard blocker.
- binding-packet projection stability must be confirmed before decomposition.

## Governance / Authority

- **Authority rule**: `plan.md` (Stage Queue / Artifact Status) and design artifacts (`contracts/`, `data-model.md`) are the semantic authority.
- **Stage boundary rule**: No design/modeling; only task decomposition and orchestration.
- **Shared protocol rule**: Apply **Unified Repository-First Gate Protocol (`URFGP`)**.
- Keep contract projection authoritative for the current run.
- On projection drift, emit upstream writeback actions only:
  - `/sdd.specify` — if spec drift is the root cause
  - `/sdd.plan.test-matrix` — if binding-packet projection is unstable
  - do not repair upstream artifacts locally

## Repository-First Protocol

- Repository-first explainable evidence MUST back every new repo anchor decision.
- Apply **Repository-First Evidence Bundle (`RFEB`)** format for evidence fields:
  - `source_refs` — concrete file/symbol paths
  - `signal_ids` (`SIG-*` from `.specify/memory/repository-first/`)
  - `module_edge_ids` — from module-invocation-spec

## Hook and Manifest Boundaries

- Hook dispatch here is phase-boundary execution only — do not invoke implementation-phase hooks.
- same run-local execution graph used to render `tasks.md` drives the manifest generation.
- Do not re-parse the just-written markdown to construct the manifest; use the in-memory run-local model.
- Invalidate run-local derived views on any plan writeback.
- Write only execution decomposition artifacts.

## Reasoning Order

1. **Prerequisite Check**: Consume `TASKS_BOOTSTRAP.execution_readiness`; hard-fail on errors.
2. **Decomposition**: Map every designed contract, model, and research decision to one or more tasks.
3. **DAG Ordering**: Sequence tasks by implementation dependency.

## Artifact Quality Contract

- Must: generate execution-ready work packages with clear dependencies, targets, and completion anchors.
- Strictly: Every task MUST trace back to a `BindingRowID` or `SSE/SFV` ref.

## Writeback Contract

- Create or refresh `tasks.md` and `tasks.manifest.json` only.
- **MUST NOT** rewrite `plan.md`, `spec.md`, or design artifacts.

## Output Contract

- **Traceability**: Every task MUST trace back to a `BindingRowID` or `SSE/SFV` ref.
- **Topology**: All tasks MUST have explicit dependencies and topo-layer identifiers.
- **Completion Anchors**: MUST be concrete and executable for `/sdd.implement`.
- **Prohibited**: Synthesized tasks with no upstream design authority.

## Stop Conditions

Stop immediately if:
1. `TASKS_BOOTSTRAP.execution_readiness` reports errors.
2. Any required planning row (`research`, `test-matrix`, `data-model`) is not `done`.
3. Any selected `contract` row is `blocked` or missing `Full Field Dictionary (Operation-scoped)`.
4. Active execution targets rely on `new` repo anchors without explicit rejection evidence for `existing` and `extended`.

## Handoff Decision

Emit exactly these fields:
- `Next Command`: `/sdd.analyze`
- `Decision Basis`: Tasks decomposed; ready for pre-implementation audit.
- `Ready/Blocked`: Local readiness only.

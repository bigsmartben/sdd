---
description: Execute the implementation plan by processing tasks in tasks.md.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks --implement-preflight
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks -ImplementPreflight
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Run `{SCRIPT}` once from repo root; parse `FEATURE_DIR`, `AVAILABLE_DOCS`, `LOCAL_EXECUTION_PROTOCOL`, `IMPLEMENT_BOOTSTRAP`, and `TASKS_MANIFEST_BOOTSTRAP`.

## Goal

Execute approved task packages from `tasks.md`.
`/sdd.implement` owns execution and task-state transitions only.

## Read Only

- `IMPLEMENT_BOOTSTRAP` packet (from `{SCRIPT}`)
- `tasks.md` / `tasks.manifest.json` (DAG authority)
- `contracts/` (active task context)
- `data-model.md`, `test-matrix.md` (active task context)
- `LOCAL_EXECUTION_PROTOCOL` (from `IMPLEMENT_BOOTSTRAP`; includes `LOCAL_EXECUTION_PROTOCOL.python.runner_cmd` and `LOCAL_EXECUTION_PROTOCOL.runtime_tools`)
- `LOCAL_EXECUTION_PROTOCOL.repo_search.list_files_cmd`
- `.specify/memory/repository-first/*.md` (canonical baselines)
- Read `plan.md` only as control-plane context (`Shared Context Snapshot`, `Stage Queue`, `Artifact Status`, `Binding Projection Index`)

## Write Only

- Implementation code, tests, and configuration files per task scope
- Task-completion state transitions in `tasks.md`

## Final Output

- Code, test, and configuration changes per task scope
- Updated task-state in `tasks.md` for tasks executed in this run

## Prerequisite Gate

Treat `IMPLEMENT_BOOTSTRAP.analyze_readiness` as the primary analyze hard gate.

- If `IMPLEMENT_BOOTSTRAP.analyze_readiness.errors` contains blockers, stop immediately and report the runtime bootstrap blocker.
- Pass `waive-analyze-gate` only when explicitly provided by the user.
- no bypass of repo-anchor strategy priority (`existing -> extended -> new`).
- no local CLI trial-and-error outside `LOCAL_EXECUTION_PROTOCOL`.

## Governance / Authority

- **Authority rule**: `tasks.md` is authoritative for execution progress. **MUST NOT** override semantics in `spec.md`, `plan.md`, `data-model.md`, `test-matrix.md`, or `contracts/`.
- **Stage boundary rule**: Execute approved tasks only. **MUST NOT** backfill planning or design semantics.
- **Shared protocol rule**: Apply **Unified Repository-First Gate Protocol (`URFGP`)**.
- **Gate ownership rule**: Enforce run-local execution safety; final audit/PASS/FAIL remains with `/sdd.analyze`.

## Repository-First Protocol

- Apply **Repository-First Evidence Bundle (`RFEB`)** format for any anchor evidence emitted.

## Reasoning Order

1. **Bootstrap**: Resolve execution protocol and analyze-readiness gate from `IMPLEMENT_BOOTSTRAP`.
2. **DAG Selection**: Identify ready tasks by dependency closure.
3. **Validation**: Confirm Repository-first Validation Trace for affected repo scope.
4. **Execution**: Execute completion anchors or repo-backed scripts; update completion state.

## Artifact Quality Contract

- Must: Produce implementation results that feel native to the repository and pass the completion anchors specified in `tasks.md`.
- Strictly: No speculative design changes, no invented anchors.

## Writeback Contract

- Update task-state transitions in `tasks.md` only for tasks actually executed in this run.
- Create code/config/test changes as required by tasks.
- Do not rewrite `plan.md`, `spec.md`, `research.md`, `test-matrix.md`, `data-model.md`, or `contracts/`.

## Output Contract

- Results MUST follow repo-native patterns and upstream design.
- Adapting to minor drift is allowed in `adaptive` mode; otherwise, stop and route to owner.
- Task completion MUST be semantically complete (integration + validation).

## Stop Conditions (MUST)

Stop immediately if:
1. `IMPLEMENT_BOOTSTRAP.analyze_readiness.ready_for_implementation = false`.
2. Required DAG predecessors fail.
3. Canonical repo evidence for affected scope is missing or stale.
4. Active execution targets rely on `new` repo anchors without explicit rejection evidence.
5. Local CLI trial-and-error required outside `LOCAL_EXECUTION_PROTOCOL`.

## Handoff Decision

Emit exactly these fields:
- `Next Command`: Remediation owner command if blocked.
- `Decision Basis`: Cite execution mode and gate status.
- `Ready/Blocked`: Local readiness only.

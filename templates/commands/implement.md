---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks --implement-preflight
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks -ImplementPreflight
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

`/sdd.implement` owns execution only.

1. Consume task orchestration artifacts.
2. Execute DAG-safe work in `strict` or `adaptive` mode.
3. Update task completion state and report run status.

Comprehensive audit ownership remains with `/sdd.analyze`.

## Governance Guardrails (Mandatory)

- **Authority rule**: `/sdd.implement` is authoritative only for runtime execution progress and task-state transitions. It MUST NOT override semantic authority in `spec.md`, `plan.md`, `data-model.md`, `test-matrix.md`, or `contracts/`.
- **Stage boundary rule**: execute approved task packages only. Do not backfill planning/design artifacts, assign implementation ownership semantics such as `Repo Anchor Role`, or rewrite contract/schema semantics.
- **Gate ownership rule**: this stage enforces run-local execution safety and analyze-readiness gating only. Cross-artifact final PASS/FAIL remains owned by `/sdd.analyze`.
- **Shared protocol rule**: apply **Unified Repository-First Gate Protocol (`URFGP`)** as the shared authority for repository-first execution gating and remediation routing.

## Read Only

1. Run `{SCRIPT}` once and parse `FEATURE_DIR`, `AVAILABLE_DOCS`, `LOCAL_EXECUTION_PROTOCOL`, `IMPLEMENT_BOOTSTRAP`, `TASKS_MANIFEST_BOOTSTRAP`, and `IMPLEMENT_ANCHOR_GATE`.
2. Treat `IMPLEMENT_BOOTSTRAP.analyze_readiness` as the primary analyze hard gate.
3. If `IMPLEMENT_BOOTSTRAP` is missing, malformed, or contradictory, perform one bounded fallback validation from latest `analyze-history.md` run block and current `spec.md` / `plan.md` / `tasks.md` SHA-256 values.
4. Parse optional runtime mode:
   - `mode: strict` (default)
   - `mode: adaptive`
5. Parse optional explicit waiver:
   - `waive-analyze-gate reason:<non-empty>`
   - in `strict` mode, `waive-analyze-gate` is forbidden
   - in `adaptive` mode, waiver requires non-empty `reason`
6. Runtime source preference:
   - use `tasks.manifest.json` when schema validation passes
   - prefer `TASKS_MANIFEST_BOOTSTRAP.validation` as the packaged manifest gate when available
   - in `strict` mode, invalid/missing manifest is a hard stop
   - in `adaptive` mode, fallback to `tasks.md` parsing is allowed when manifest is missing or invalid
7. Read `plan.md` only as control-plane context (`Shared Context Snapshot`, `Stage Queue`, `Artifact Status`, `Binding Projection Index`) and resolved artifact paths; do not treat it as a semantic source for architecture/contract/model requirements.
8. Read support artifacts only when required by active tasks (`contracts/`, `data-model.md`, `test-matrix.md`, `research.md`).
9. Read canonical repository-first baselines under `.specify/memory/repository-first/` for dependency/module-edge validation.
10. Treat `LOCAL_EXECUTION_PROTOCOL` as the constitution-derived run-local execution packet for repository discovery, repo inspection, and bounded helper execution during this run.
11. Treat `LOCAL_EXECUTION_PROTOCOL.runtime_tools` as the SDD core runtime inventory for this run: `specify-cli`, `git`, and `rg`.
12. If additional repository discovery is required, use only `LOCAL_EXECUTION_PROTOCOL.repo_search.list_files_cmd` and `LOCAL_EXECUTION_PROTOCOL.repo_search.search_text_cmd`; if `repo_search.available = false`, stop and report the blocker instead of trial-and-error across ad hoc CLIs.
13. If bounded Python helper execution is required, use only `LOCAL_EXECUTION_PROTOCOL.python.runner_cmd`; do not switch to user-managed interpreters, project-local virtual environments, or repo-local `uv run python`.
14. When a task requires build/test/lint commands, execute only completion anchors or repo-backed scripts/config entries; do not guess alternate package managers or install tooling in this command.
15. Treat `IMPLEMENT_ANCHOR_GATE.script_path` as the completion-anchor post-check helper and `IMPLEMENT_ANCHOR_GATE.history_path` as append-only implementation evidence target.

Manifest validation keys:

- top-level: `schema_version`, `generated_at`, `generated_from`, `tasks`
- `generated_from`: `plan_path`, `plan_source_fingerprint`, `contract_source_fingerprints`
- task keys: `task_id`, `dependencies`, `if_scope`, `refs`, `target_paths`, `completion_anchors`, `conflict_hints`, `topo_layer`, `status`

## Write Only

1. Execute ready tasks by DAG dependency closure.
2. Before marking tasks complete, run completion-anchor gate for completed tasks:
   - use `{LOCAL_EXECUTION_PROTOCOL.python.runner_cmd}` to run `IMPLEMENT_ANCHOR_GATE.script_path`
   - required args: `--feature-dir`, `--tasks`, `--tasks-manifest`
   - when `mode: strict`, pass `--strict-non-executable`
3. Update completion checkboxes in `tasks.md` only when completion-anchor gate returns `ready_for_task_completion_update = true`.
4. Preserve source task lineage in adaptive mode.
5. Emit progress signals (`start`, per-task transition, heartbeat, long-command before/after status).
6. Append one run block to `IMPLEMENT_ANCHOR_GATE.history_path` with exact sentinels:
   - `<!-- SDD_IMPLEMENT_RUN_BEGIN -->`
   - `<!-- SDD_IMPLEMENT_RUN_END -->`
   Include at minimum: `Run At (UTC)`, `Execution Mode`, `Analyze Gate Status`, `Manifest Validation`, `Anchor Gate`, `Completed Task IDs`.

## Stop Conditions

Stop immediately when any condition holds:

1. Required task artifacts are missing or non-consumable.
2. Runtime mode is `strict` and `waive-analyze-gate` is present.
3. Runtime mode is `adaptive`, `waive-analyze-gate` is present, and waiver reason is empty.
4. `IMPLEMENT_BOOTSTRAP.analyze_readiness.ready_for_implementation = false` and `waive-analyze-gate` is absent.
5. `IMPLEMENT_BOOTSTRAP` fallback validation cannot reconstruct a consumable analyze gate packet.
6. `IMPLEMENT_BOOTSTRAP.analyze_readiness.errors` contains blockers.
7. Runtime mode is `strict` and `TASKS_MANIFEST_BOOTSTRAP.validation.valid != true`.
8. Required DAG predecessors fail.
9. Completion-anchor gate returns `ready_for_task_completion_update = false`.
10. Required canonical repository-first evidence for affected scope is missing, stale, or non-traceable.
11. Runtime drift exceeds safe local adaptation in adaptive mode.
12. Active execution targets rely on `new` repo anchors without explicit rejection evidence for `existing` and `extended`.
13. Required repository discovery or helper execution is blocked because `LOCAL_EXECUTION_PROTOCOL` marks the capability unavailable.

When analyze gate is not ready and runtime mode is `adaptive` with valid `waive-analyze-gate reason:<non-empty>`, continue with explicit waiver notice.

Do not invent missing semantics in this command:

- no new external contracts
- no lifecycle model invention
- no conversion of `TODO(REPO_ANCHOR)` into executable semantics
- no bypass of repo-anchor strategy priority (`existing -> extended -> new`)
- no local CLI trial-and-error outside `LOCAL_EXECUTION_PROTOCOL` and repo-backed task anchors
- no cross-artifact final PASS/FAIL claim in this stage

## Final Output

Return a concise execution summary:

1. execution mode
2. analyze gate status (`IMPLEMENT_BOOTSTRAP` pass, fallback pass, or `waived`) and waiver reason (if waived)
3. manifest gate status (`TASKS_MANIFEST_BOOTSTRAP.validation`)
4. completion-anchor validation result (`ready_for_task_completion_update`, executed/failed/skipped counts)
5. completed / failed / blocked tasks
6. dependency-closure validation result
7. `Repository-first Validation Trace` with consumed canonical dependency and module-edge rows, formatted as **Repository-First Evidence Bundle (`RFEB`)** entries:
   - `fact -> conclusion`
   - `source_refs`
   - `signal_ids` and/or `module_edge_ids`
8. appended implement-history path and run-block status
9. follow-up remediation owner command when execution cannot continue

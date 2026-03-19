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

## Read Only

1. Run `{SCRIPT}` once and parse `FEATURE_DIR`, `AVAILABLE_DOCS`, `LOCAL_EXECUTION_PROTOCOL`, and `IMPLEMENT_BOOTSTRAP`.
2. Treat `IMPLEMENT_BOOTSTRAP.analyze_readiness` as the primary analyze hard gate.
3. If `IMPLEMENT_BOOTSTRAP` is missing, malformed, or contradictory, perform one bounded fallback validation from latest `analyze-history.md` run block and current `spec.md` / `plan.md` / `tasks.md` SHA-256 values.
4. Parse optional runtime mode:
   - `mode: strict` (default)
   - `mode: adaptive`
5. Parse optional explicit waiver: `waive-analyze-gate`.
6. Runtime source preference:
   - use `tasks.manifest.json` when schema validation passes
   - fallback to `tasks.md` parsing when manifest is missing or invalid
7. Read `plan.md` only as control-plane context (`Shared Context Snapshot`, `Stage Queue`, `Artifact Status`, `Binding Projection Index`) and resolved artifact paths; do not treat it as a semantic source for architecture/contract/model requirements.
8. Read support artifacts only when required by active tasks (`contracts/`, `data-model.md`, `test-matrix.md`, `research.md`).
9. Read canonical repository-first baselines under `.specify/memory/repository-first/` for dependency/module-edge validation.
10. Treat `LOCAL_EXECUTION_PROTOCOL` as the constitution-derived run-local execution packet for repository discovery, repo inspection, and bounded helper execution during this run.
11. Treat `LOCAL_EXECUTION_PROTOCOL.runtime_tools` as the SDD core runtime inventory for this run: `specify-cli`, `git`, and `rg`.
12. If additional repository discovery is required, use only `LOCAL_EXECUTION_PROTOCOL.repo_search.list_files_cmd` and `LOCAL_EXECUTION_PROTOCOL.repo_search.search_text_cmd`; if `repo_search.available = false`, stop and report the blocker instead of trial-and-error across ad hoc CLIs.
13. If bounded Python helper execution is required, use only `LOCAL_EXECUTION_PROTOCOL.python.runner_cmd`; do not switch to user-managed interpreters, project-local virtual environments, or repo-local `uv run python`.
14. When a task requires build/test/lint commands, execute only completion anchors or repo-backed scripts/config entries; do not guess alternate package managers or install tooling in this command.

Manifest validation keys:

- top-level: `schema_version`, `generated_at`, `generated_from`, `tasks`
- `generated_from`: `plan_path`, `plan_source_fingerprint`, `contract_source_fingerprints`
- task keys: `task_id`, `dependencies`, `if_scope`, `refs`, `target_paths`, `completion_anchors`, `conflict_hints`, `topo_layer`, `status`

## Write Only

1. Execute ready tasks by DAG dependency closure.
2. Update completion checkboxes in `tasks.md` for completed tasks.
3. Preserve source task lineage in adaptive mode.
4. Emit progress signals (`start`, per-task transition, heartbeat, long-command before/after status).

## Stop Conditions

Stop immediately when any condition holds:

1. Required task artifacts are missing or non-consumable.
2. `IMPLEMENT_BOOTSTRAP.analyze_readiness.ready_for_implementation = false` and `waive-analyze-gate` is absent.
3. `IMPLEMENT_BOOTSTRAP` fallback validation cannot reconstruct a consumable analyze gate packet.
4. `IMPLEMENT_BOOTSTRAP.analyze_readiness.errors` contains blockers.
5. Required DAG predecessors fail.
6. Required canonical repository-first evidence for affected scope is missing, stale, or non-traceable.
7. Runtime drift exceeds safe local adaptation in adaptive mode.
8. Active execution targets rely on `new` repo anchors without explicit rejection evidence for `existing` and `extended`.
9. Required repository discovery or helper execution is blocked because `LOCAL_EXECUTION_PROTOCOL` marks the capability unavailable.

When gate is not ready and `waive-analyze-gate` is present, continue with explicit waiver notice.

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
2. analyze gate status (`IMPLEMENT_BOOTSTRAP` pass, fallback pass, or `waived`)
3. completed / failed / blocked tasks
4. dependency-closure validation result
5. completion-anchor validation result
6. `Repository-first Validation Trace` with consumed canonical dependency and module-edge rows
7. follow-up remediation owner command when execution cannot continue

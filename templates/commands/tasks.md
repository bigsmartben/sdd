---
description: Generate an executable, dependency-ordered tasks.md from the current feature branch plan.md, organized by GLOBAL and interface delivery units keyed by IF Scope as execution work packages.
handoffs:
  - label: Analyze For Consistency
    agent: sdd.analyze
    prompt: Run a project analysis for consistency before implementation
    send: true
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --task-preflight
  ps: scripts/powershell/check-prerequisites.ps1 -Json -TaskPreflight
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Argument Parsing

Treat all `$ARGUMENTS` as scoped runtime context.
Resolve `PLAN_FILE` from current feature branch using `{SCRIPT}` defaults.

## Goal

`/sdd.tasks` owns execution decomposition only.

1. Convert approved planning outputs into executable tasks.
2. Emit a dependency-safe `Task DAG` and aligned `tasks.manifest.json`.
3. Keep semantics in authoritative upstream artifacts; do not redesign in this command.

## Read Only

1. Run `{SCRIPT}` once from repo root.
2. Parse `FEATURE_DIR`, `AVAILABLE_DOCS`, `LOCAL_EXECUTION_PROTOCOL`, and `TASKS_BOOTSTRAP`.
3. Treat `TASKS_BOOTSTRAP.execution_readiness` as the primary hard gate.
4. If `TASKS_BOOTSTRAP.execution_readiness.ready_for_task_generation = true`, do not recompute full hard gates by re-deriving complete `plan.md` tables.
5. If `TASKS_BOOTSTRAP` is missing, malformed, or contradictory, perform one bounded fallback validation from `plan.md` control-plane fields.
6. Read only authoritative inputs for the active generation unit:
   - `plan.md` control plane (`Shared Context Snapshot`, `Binding Projection Index`, `Artifact Status`)
   - required refs from `spec.md`, `data-model.md`, `test-matrix.md`, and selected `contracts/` slices
   - canonical repository-first baselines under `.specify/memory/repository-first/`
7. Use `LOCAL_EXECUTION_PROTOCOL` as the default local shell contract for repository discovery and repo inspection during this run.
8. If additional repository discovery is required, use only `LOCAL_EXECUTION_PROTOCOL.repo_search.list_files_cmd` and `LOCAL_EXECUTION_PROTOCOL.repo_search.search_text_cmd`; if `repo_search.available = false`, stop and report the blocker instead of trial-and-error across ad hoc CLIs.
9. Do not install missing tools, mutate PATH, or guess alternate package managers/CLIs in this command.

## Write Only

1. Generate `tasks.md` using `.specify/templates/tasks-template.md`.
2. Generate `tasks.manifest.json` from the same run-local execution graph used to render `tasks.md`.
3. Keep fixed decomposition units:
   - `GLOBAL` shared prerequisites
   - one `IF Scope` unit at a time
   - cross-interface finalization
4. Enforce deterministic mapping rules during task generation:
   - one work package maps to exactly one `operationId` or one shared prerequisite objective
   - one work package maps to exactly one target path cluster or one command target
   - one work package maps to exactly one primary completion anchor
5. Keep contract projection authoritative for the current run.
6. On projection drift, emit upstream writeback actions only:
   - `/sdd.specify` for spec drift
   - `/sdd.plan.test-matrix` for test-matrix drift
7. Do not re-parse the just-written markdown to construct the manifest.
8. Invalidate run-local derived views after write/report.

Manifest requirements:

- Top-level keys: `schema_version`, `generated_at`, `generated_from`, `tasks`
- `generated_from` keys: `plan_path`, `plan_source_fingerprint`, `contract_source_fingerprints`

## Stop Conditions

Stop immediately when any condition holds:

1. Resolved branch-derived `PLAN_FILE` is missing or invalid.
2. `TASKS_BOOTSTRAP.execution_readiness.ready_for_task_generation = false`.
3. `TASKS_BOOTSTRAP` fallback validation cannot build a consumable gate packet.
4. `TASKS_BOOTSTRAP.execution_readiness.errors` contains blockers.
5. Required canonical repository-first evidence for affected scope is missing, stale, or non-traceable.
6. Active executable tuples select `new` repo anchors but lack explicit rejection evidence for `existing` and `extended` in authoritative upstream artifacts.
7. Required repository discovery is blocked because `LOCAL_EXECUTION_PROTOCOL.repo_search.available = false`.

Hard execution safety gates in this command are limited to:

- input availability and consumability
- repository-anchored tuple executability
- repo-anchor strategy evidence completeness for executable tuples
- DAG schedulability
- task-line completeness

`/sdd.tasks` does **not** own comprehensive audit concerns (coverage completeness, ambiguity sweeps, contradiction analysis). Route those to `/sdd.analyze`.

## Final Output

Return a concise execution summary:

1. resolved `PLAN_FILE`
2. generated artifact paths: `tasks.md`, `tasks.manifest.json`
3. task totals (`GLOBAL` and each `IF-###`)
4. DAG schedulability result
5. manifest/task alignment result
6. Repository-first explainable evidence: list only decision-relevant dependency/governance facts in `fact -> conclusion` format (path-level refs by default; add line refs only when ambiguity/conflict requires precision)
7. Module-edge explainable evidence: list only decision-relevant invocation-governance facts in `fact -> conclusion` format (path-level refs by default; add line refs only when ambiguity/conflict requires precision)
8. upstream alignment repair actions (if any)
9. analyze handoff note

## Hook Dispatch Protocol

Use this protocol whenever the Outline asks to execute extension hooks for a phase (`before_tasks` or `after_tasks`):

- If `.specify/extensions.yml` is missing or invalid, skip silently.
- Filter hooks to `enabled: true`.
- Do not evaluate hook `condition` expressions in this command.
- Optional hooks are announced only; mandatory hooks are emitted as `EXECUTE_COMMAND` actions.
- Hook dispatch here is phase-boundary execution only. Do not introduce alternative task-generation flows.

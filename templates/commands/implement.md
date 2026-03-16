---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

### Execution Mode Selection

- Parse optional mode hints from user input:
  - `mode: strict` (default)
  - `mode: adaptive`
- If no mode is explicitly provided, use `strict`.
- Mode intent:
  - `strict`: maximize determinism; execute exactly against `tasks.md` and `Task DAG`.
  - `adaptive`: preserve dependency safety and completion intent while allowing bounded runtime task adaptation.

### Progress Signaling

- `/sdd.implement` is often long-running. Emit visible progress throughout execution.
- Required signals:
  - Emit an initial `Execution Start Banner` before heavy work begins.
  - Emit progress on each task transition (`Task Start` / `Task Complete`).
  - Emit heartbeat updates when there is no visible completion (typically every ~1-2 minutes).
  - For long-running commands (build/test/install/migration), emit status before and after execution.
- Heartbeat updates SHOULD be concise and include at least one of: current task/phase, completed/total progress, blocking reason, next expected update checkpoint.

## Hook Dispatch Protocol

Use this protocol whenever the Outline asks to execute extension hooks for a phase (`before_implement` or `after_implement`):

- Check if `.specify/extensions.yml` exists in the project root. If absent, skip silently.
- Parse YAML and read entries under `hooks.<phase>`. If YAML is invalid, skip silently.
- Filter hooks to `enabled: true`.
- Do not evaluate hook `condition` expressions:
  - If `condition` is missing/null/empty, treat the hook as executable.
  - If `condition` is non-empty, skip it and leave condition handling to HookExecutor.
- For each executable hook:
  - Optional (`optional: true`) output:

    ```text
    ## Extension Hooks

    **Optional Hook ({phase})**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

  - Mandatory (`optional: false`) output:

    ```text
    ## Extension Hooks

    **Automatic Hook ({phase})**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```

## Responsibility Boundary (Scope Guard)

Terminology note (compatibility, non-normative):

- In this command, **Hard Gates** means the existing "hard pre-execution gates" set (same semantics, alias only).
- This alias is for cross-command readability and does not change ownership, checks, or blocking behavior.

- `/sdd.implement` owns task consumption and execution only.
- Keep pre-execution gating minimal and execution-oriented: required artifact presence, runtime-source consumability, DAG dependency safety, and blocking missing inputs.
- Comprehensive cross-artifact auditing remains owned by `/sdd.analyze`.
- Analyze-first is a blocking reminder by default: if current task artifacts have no completed `/sdd.analyze` pass, stop and route the user to `/sdd.analyze` unless the user explicitly waives that audit step for this run.

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. Execute `before_implement` hooks using the Hook Dispatch Protocol.

3. **Enforce hard pre-execution gates only**:
   - **Required artifact presence**: confirm `tasks.md` exists and prerequisite command output (`FEATURE_DIR`, `AVAILABLE_DOCS`) is available.
   - **Analyze-first blocking reminder**: if there is no evidence this feature has completed `/sdd.analyze` for the current `tasks.md`, stop and route the user to `/sdd.analyze` before continuing. Continue only if the user explicitly waives the audit step for this run.
   - **Manifest probe (preferred runtime source)**: check for `tasks.manifest.json` in the same directory as `tasks.md`.
   - **Manifest validation (when present)**: validate parseability and required task keys: `task_id`, `dependencies`, `if_scope`, `refs`, `target_paths`, `completion_anchors`, `conflict_hints`, `status`.
   - **Fallback trigger**: if manifest is missing or validation fails, switch to `tasks.md` parsing for this run and report the fallback reason.
   - **`tasks.md` consumability** (fallback path): confirm `tasks.md` includes the required consumable sections:
      - `Upstream Inputs (Execution References)`
      - `Execution Ordering Model` (including `Task DAG`)
      - `Shared Foundation`
      - `Interface Delivery Units` (treated as IF-scoped execution work packages)
      - `Cross-Interface Finalization`
   - **DAG dependency safety**: confirm dependency data from the selected runtime source is parseable and dependency-safe for execution (no predecessor violations, no unresolved required predecessors, no obvious cycle/closure break).
   - **Blocking missing inputs**: if ready-to-run tasks reference required inputs/artifacts that are absent, treat as blocking and stop.
   - **Blocking behavior**: if any hard gate fails (required artifacts missing, missing analyze pass without explicit waiver, runtime source non-consumable, DAG invalid, or blocking inputs missing), stop and report the exact missing/invalid item; route task-structure/dependency repair to `/sdd.tasks` before retrying `/sdd.implement`. Route comprehensive semantic uncertainty to `/sdd.analyze`.

4. Load the execution context needed for the current run:
   - Prefer `tasks.manifest.json` as the runtime execution metadata source. If missing or invalid, fall back to parsing `tasks.md` and report the fallback reason.
   - `tasks.md` remains the human-review and execution-orchestration authority; manifest is a machine-readable projection and MUST NOT introduce new semantics.
   - Build the in-memory scheduling graph exactly once per run from the selected runtime source, then reuse that graph for scheduling/checkpoints/completion validation.
   - Treat `Task DAG` as baseline dependency authority (`strict`: follow exactly; `adaptive`: allow local resequencing only when dependency safety is preserved, completion anchors remain satisfiable, and adaptations are reported).
   - Treat `[Pre:T###,...]` as inline dependency mirror only.
   - Read `plan.md` for tech stack, architecture, and file structure.
   - Load supporting artifacts only when needed for a ready task or its completion anchor:
      - `interface-details/` for per-interface behavior/sequencing
      - `data-model.md` for entity/lifecycle context
      - `contracts/` for interface semantics/contract checks
      - `test-matrix.md` for feature verification anchors referenced by tasks
      - `research.md` for implementation constraints/decisions
      - `.specify/memory/repository-first/technical-dependency-matrix.md` for dependency-governance execution baseline
      - `.specify/memory/repository-first/domain-boundary-responsibilities.md` for ownership/collaboration execution baseline
      - `.specify/memory/repository-first/module-invocation-spec.md` for invocation direction/layering execution baseline
   - Treat runtime batching notes, ready-task summaries, and local execution shortcuts as derived views only.
   - If local execution notes conflict with authoritative artifacts, use the authoritative artifact for semantics; if unresolved safely, stop and route upstream repair.
   - Treat `TODO(REPO_ANCHOR)` as forward-looking notes only; execute only repository-anchored semantics.
   - Repository-first execution discipline:
      - dependency changes MUST be validated against `.specify/memory/repository-first/technical-dependency-matrix.md`
      - ownership/boundary changes MUST be validated against `.specify/memory/repository-first/domain-boundary-responsibilities.md`
      - invocation-direction/layering changes MUST be validated against `.specify/memory/repository-first/module-invocation-spec.md`
      - feature-local copies are derived views only and MUST NOT replace canonical baseline semantics
      - if required canonical repository-first evidence is missing/stale/non-traceable, stop affected execution scope and route repair to `/sdd.constitution` or `/sdd.analyze` (do not infer semantics from docs/plans/summaries in `/sdd.implement`)

5. Generate an execution strategy summary before modifying code:
   - Produce a short `Execution Strategy Summary` that states:
     - planned execution batches/layers from DAG
     - candidate file-path conflicts
     - verify-before-interface opportunities
     - in `adaptive` mode, any proposed local resequencing/merge/split decisions and rationale
   - In `strict` mode, this summary is descriptive only.
   - In `adaptive` mode, include any expected runtime adaptation notes.
   - Also print a concise `Execution Start Banner` in this format:

     ```text
     ## Implement Run Started
     Mode: {strict|adaptive}
     Total Tasks: {N}
     Ready Now: {T###, ...}
     Heartbeat Interval: 60-90s
     ```

6. Parse the selected runtime source exactly once and extract:
   - **Execution scopes**: `GLOBAL` and `IF-###` units
   - **Task DAG**: adjacency list and topological execution layers
   - **Task metadata**: `TaskID`, `Type`, `Scope`, `Role` (when present), `Pre`, description, file paths or command targets, completion anchors (when present)
   - **Reference metadata** (when present): `operationId`, requirement refs, verification refs
   - **Execution flow**: DAG-driven order and file-level conflict constraints
   - **Single-parse rule**: after this extraction step, reuse the in-memory scheduling graph and metadata cache; do not re-run full markdown parsing loops during the same `/sdd.implement` run.

7. Execute implementation following the task plan:
   - **DAG-first execution**: Schedule tasks strictly by `Task DAG` dependency satisfaction
   - **Scope-aware flow**: Execute `GLOBAL` foundation tasks and IF-scoped execution work packages (`IF-###` units) according to DAG, not section order alone
   - **GLOBAL foundation first when required by DAG**: complete shared infra/bootstrap/config prerequisites before dependent IF tasks
   - **Interface-unit delivery**: for each `IF-###`, execute verify + implementation work using task `Role` when present, or task description when `Role` is omitted
   - **Cross-cutting/finalization last when DAG-scheduled**: run docs/final validation/cross-interface tasks after prerequisite IF/GLOBAL tasks complete
   - **Parallel eligibility**: Tasks in the same DAG-ready layer may execute in parallel only when they have no shared file-path conflicts
   - **Verify-before-Interface preference**: Prefer running `Type:Verify` tasks before corresponding `Type:Interface` tasks when DAG allows
   - **Validation checkpoints**: Verify completion anchors and dependency closure before advancing to downstream DAG layers
   - **Adaptive execution bounds** (`mode: adaptive` only):
     - MAY split a task into smaller executable steps when this reduces file conflict or de-risks delivery
     - MAY merge same-layer tasks when they target the same artifact and share completion anchors
     - MAY locally resequence same-layer tasks when no dependency/file-conflict rule is violated
     - MUST keep original task IDs traceable (do not erase source task lineage)
     - MUST update task checkboxes and report adaptations in execution output
   - **No new normative semantics in implement**: Do not turn `TODO(REPO_ANCHOR)` into runtime semantics and do not create new external contracts, lifecycle stable states, or `INV-*` definitions during `/sdd.implement`; send unresolved semantic gaps upstream.
   - **No repository-first backfill in implement**: do not reconstruct dependency matrix facts, boundary ownership semantics, or invocation governance rules inside `/sdd.implement`; consume upstream projections and route evidence gaps upstream.
   - **Progress signaling**: report task progress, heartbeat on quiet periods, and before/after status for long-running commands.
   - **Error handling**:
     - Halt execution if any required DAG predecessor task fails
     - For parallel-eligible DAG-ready tasks, continue successful tasks, report failed ones, and skip newly blocked descendants
     - In `adaptive` mode, if runtime drift exceeds safe local adaptation (unexpected file structure/API drift, missing upstream detail, conflicting contract expectation), stop and point the user to upstream artifact repair or `/sdd.analyze` before continuing
     - Provide clear error messages with context for debugging
     - On recoverable stalls (tooling/network/build wait), print explicit status + wait reason + estimated next update time
     - Suggest next steps if implementation cannot proceed
   - **IMPORTANT**: for completed tasks, mark the task as `[X]` in `tasks.md`.

8. Completion validation:
   - Verify all reachable required DAG tasks are completed or explicitly waived by user
   - Verify `Task DAG` dependency closure (no completed task missing required predecessors)
   - Verify each interface unit (`IF-###`) reaches the task-defined completion anchors that exist for that unit
   - Verify task-defined validation commands, tests, or contract checks passed for completed work
   - Confirm tasks.md checkboxes accurately reflect execution results
   - In `adaptive` mode, summarize adaptations and their dependency impact in final output
   - Report final status with summary of completed work, blocked items, and remediation follow-ups
   - If unresolved drift remains, recommend upstream artifact repair or `/sdd.analyze`

9. Execute `after_implement` hooks using the Hook Dispatch Protocol.

Note: This command assumes a complete, DAG-usable task breakdown exists. Preferred runtime input is `tasks.manifest.json` (when valid), with `tasks.md` as authoritative orchestration source and fallback parse target. If required sections are missing, no current `/sdd.analyze` pass exists and the user does not explicitly waive it, DAG is invalid, manifest validation fails without safe fallback, or task rows are incomplete, suggest running `/sdd.tasks` or `/sdd.analyze` first before retrying `/sdd.implement`.

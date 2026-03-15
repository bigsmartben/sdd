---
description: Generate an executable, dependency-ordered tasks.md organized by GLOBAL and interface delivery units keyed by IF Scope as execution work packages.
handoffs:
  - label: Analyze For Consistency
    agent: sdd.analyze
    prompt: Run a project analysis for consistency before implementation
    send: true
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Hook Dispatch Protocol

Use this protocol whenever the Outline asks to execute extension hooks for a phase (`before_tasks` or `after_tasks`):

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
- In this command, **Hard Gates** means the existing "hard execution safety gates" set (same semantics, alias only).
- This alias is for cross-command readability and does not change ownership, checks, or blocking behavior.

- `/sdd.tasks` owns executable task generation and DAG-oriented orchestration of approved planning outputs only.
- `Interface Delivery Units` are IF-scoped execution work packages, not a second design stage.
- Keep checks in this command limited to a **P0-frozen set of hard execution safety gates only**: input availability, repository-anchored tuple executability for generated tasks, DAG schedulability, and task-line completeness.
- `/sdd.tasks` may fail when execution-critical inputs are missing or non-consumable, but it does **not** own coverage completeness, ambiguity sweeps, terminology/diagram drift detection, repo-anchor misuse audits, audit hygiene checks, or cross-artifact contradiction analysis.
- This runtime scheduling guidance is execution-only. It MUST NOT change artifact authority.
- Any tuple indexes, execution maps, or working summaries created during `/sdd.tasks` are derived views only.
- Handoff all non-mainline comprehensive audit concerns to `/sdd.analyze`.
- Runtime guidance in this command MUST NOT substitute for the centralized comprehensive audit in `/sdd.analyze`.

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. Execute `before_tasks` hooks using the Hook Dispatch Protocol.

3. **Build the runtime task-generation queue before broad reads**:
   - Use bounded units in fixed order: `GLOBAL inventory and foundation -> one IF Scope at a time -> final DAG synthesis and document assembly`.
   - Keep only three context tiers active: **Bootstrap packet**, **Unit workset**, and **Task card**.
   - **Task card**: exactly one active generation target at a time.
   - Before opening each unit, declare required authoritative inputs, expected output, and stop condition.
   - Keep only one active generation target at a time; carry forward only stable execution anchors (`IF Scope`, `operationId`, refs, target paths, completion anchors, predecessor edges, blockers).

4. **Load design documents (required + on-demand)**: Read from FEATURE_DIR:
   - **Required**: `plan.md`, `spec.md`, `data-model.md`, `test-matrix.md`, `contracts/`, `interface-details/`.
   - Consume only the slices needed for the active generation unit. Prefer section-level or row-level rereads over whole-file replay.
   - **On-demand only**: `research.md` when constraints/decisions materially affect the active unit.

5. **Execute task generation workflow**:
   - Treat `plan.md` as a planning summary / structure guide, not as a replacement for canonical requirement, contract, model, or verification semantics.
   - Read `plan.md` and `spec.md` for bootstrap extraction only (tech stack, structure, constraints, requirement/story refs for execution mapping).
   - Convert approved planning artifacts into executable work packages plus a dependency-safe DAG; do not redesign upstream semantics in `/sdd.tasks`.
   - Use the fixed loop `Discover -> Generate -> Compress` for every generation unit.
   - Between `Generate` and `Compress`, run **hard execution safety gates only** for the active unit: required anchor presence, prevention of promoting `TODO(REPO_ANCHOR)` into executable semantics, local mapping completeness, and dependency-safe schedulability.
   - **GLOBAL inventory and foundation unit**:
      - Load `data-model.md` and capture shared global object baselines required by tasks.
      - Derive only truly cross-interface prerequisites; do not use `GLOBAL` as overflow for interface-local work.
      - Compress to stable shared anchors before moving to `IF Scope` units.
   - **IF Scope units (sequential; one active at a time)**:
      - Map verification refs from `test-matrix.md` (`TM-*` / `TC-*`) using stable tuple keys (`Operation ID`, `Boundary Anchor`, `IF Scope`).
      - Use `contracts/` as canonical interface semantics for implementation/verification task targets.
      - Map `IF Scope -> operationId -> detail doc path` from `interface-details/` and validate tuple alignment.
      - If contracts define interface operations but required interface-detail docs are missing, stop and request upstream completion.
      - For the active `IF Scope`, read only matching contract/detail slices, relevant `TM/TC` rows, relevant `data-model.md` anchors, and required `spec.md` refs.
      - Consume only repository-anchored contract/interface tuples as executable semantics; treat `TODO(REPO_ANCHOR)` as blocker/note only.
      - When artifacts overlap, keep semantics authoritative in upstream artifacts (`spec.md`, `contracts/`, `data-model.md`, `test-matrix.md`); `tasks.md` maps execution only.
      - Generate one IF-scoped delivery unit at a time, then compress before loading the next.
      - After each unit is compressed, discard its detailed local working set and carry forward only stable delivery anchors.
   - **Final DAG synthesis and document assembly**:
      - Keep execution refs at task level inside GLOBAL/IF task definitions.
      - Build local predecessor edges per unit, then synthesize the full **Task DAG** adjacency list from the compressed unit outputs.
      - Add adaptation caution note only when task graph/file layout indicates extra `adaptive` risk.
      - Ensure each task line is executable with concrete path/command/completion signal where relevant.
      - Generate tasks grouped by **GLOBAL** and **Interface Delivery Units** keyed by `IF Scope`.

6. **Generate tasks.md**: Use `templates/tasks-template.md` as structure, fill with:
   - Correct feature name from plan.md
   - A complete execution mapping that satisfies the template's required sections and canonical task format
   - Clear file paths, command targets, or completion signals where relevant

7. **Generate/refresh `tasks.manifest.json` sidecar (same directory as `tasks.md`)**:
   - Generate immediately after `tasks.md` so both outputs stay synchronized for the same run
   - Treat manifest as a **machine-readable projection** of `tasks.md` execution metadata only; it MUST NOT introduce new semantics beyond authoritative artifacts
   - If an older manifest exists, refresh it from the just-generated `tasks.md` (do not patch incrementally from stale state)
   - At minimum, each task entry MUST include keys: `task_id`, `dependencies`, `if_scope`, `refs`, `target_paths`, `completion_anchors`, `conflict_hints`, `status` (initialize to `pending`).

8. **Report (Execution Summary + Analyze Handoff Only)**: Output a concise summary only:
   - Generated artifact paths: `tasks.md`, `tasks.manifest.json`
   - Total task count and count split by `GLOBAL` and each interface unit (`IF-###`)
   - DAG schedulability result (dependency-safe / blockers detected)
   - Manifest alignment result (task count and task IDs aligned with `tasks.md`)
   - Analyze handoff note: direct non-mainline comprehensive audit concerns to `/sdd.analyze`

9. Execute `after_tasks` hooks using the Hook Dispatch Protocol.

Context for task generation: {ARGS}

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

## Task Generation Rules

**CRITICAL**: Tasks MUST be organized by execution scope: `GLOBAL` + interface delivery units keyed by `IF Scope` (`IF-###`).
`Interface Delivery Units` are IF-scoped execution work packages. They do not reopen planning-stage design.

`tasks.md` is an execution orchestration artifact. Do not duplicate interface semantics, data-model semantics, or test prose from upstream docs.
Contract semantics come from `contracts/` only.
Feature verification semantics come from `test-matrix.md`.
Use `templates/tasks-template.md` as the authoritative source for document structure, required sections, and canonical task line format.

Additional generation constraints:

- Map each interface detail / contract to one interface delivery unit keyed by `IF Scope`.
- Treat interface delivery units as execution mapping only.
- Each interface delivery unit SHOULD include at least one `Verify` task and one `Interface` task (document exceptions explicitly).
- Tasks may refine operation-level mappings but MUST NOT rewrite approved global object semantics.
- Task execution targets MUST reference anchored tuples only. `TODO(REPO_ANCHOR)` items MUST NOT be converted into executable interface semantics, completion anchors, or implementation objectives.
- Use deterministic refs (`operationId`, `CaseID`, `TM-*`, `TC-*`) only when they help execution or completion checking.
- Keep Task DAG dependency-safe and minimally sufficient (avoid speculative over-constraint).
- Keep `[Pre:T###,...]` consistent with the DAG while recognizing it is an inline mirror.
- Prefer intent-oriented `Role` labels when they help execution, but retain architecture-bound roles when the project structure confirms them.
- Use deterministic completion anchors when they are needed to prove task completion.

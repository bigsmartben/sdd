---
description: Generate an executable, dependency-ordered tasks.md organized by GLOBAL and interface delivery units keyed by IF Scope as execution work packages.
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

- Hook dispatch here is phase-boundary execution only. Do not let hook handling introduce extra audit passes, repository rediscovery loops, or alternative task-generation flows inside `/sdd.tasks`.

## Responsibility Boundary (Scope Guard)

Terminology note (compatibility, non-normative):

- In this command, **Hard Gates** means the existing "hard execution safety gates" set (same semantics, alias only).
- This alias is for cross-command readability and does not change ownership, checks, or blocking behavior.

- `/sdd.tasks` owns executable task generation and DAG-oriented orchestration of approved planning outputs only.
- `/sdd.tasks` is the execution decomposition step for completed `plan`-stage detailed design. It projects approved design into work packages; it does not supplement missing design.
- `Interface Delivery Units` are IF-scoped execution work packages, not a second design stage.
- Keep checks in this command limited to a **P0-frozen set of hard execution safety gates only**: input availability, repository-anchored tuple executability for generated tasks, DAG schedulability, and task-line completeness.
- `/sdd.tasks` MUST NOT supplement design details, verification semantics, target paths, completion anchors, or dependency meaning that are not already traceable to authoritative upstream artifacts.
- If required execution anchors are missing from `Binding Projection Index`, completed `Artifact Status` rows, `contracts/`, `interface-details/`, or `test-matrix.md`, fail fast and route back to the relevant `/sdd.plan.*` command; do not emit placeholder execution tasks.
- `/sdd.tasks` may fail when execution-critical inputs are missing or non-consumable, but it does **not** own coverage completeness, uncovered MUST requirement analysis, ambiguity sweeps, terminology/diagram drift detection, repo-anchor misuse audits, helper-doc leakage checks, audit hygiene checks, or cross-artifact contradiction analysis.
- This runtime scheduling guidance is execution-only. It MUST NOT change artifact authority.
- Any tuple indexes, execution maps, or working summaries created during `/sdd.tasks` are derived views only.
- Temporary derived views created during `/sdd.tasks` are run-local only; discard them after artifact write/report and rebuild from authoritative inputs on the next run.
- Do not create `blocked`, `todo`, placeholder, or compensating execution rows to mask upstream design gaps.
- Handoff all non-mainline comprehensive audit concerns to `/sdd.analyze`.
- Runtime guidance in this command MUST NOT substitute for the centralized comprehensive audit in `/sdd.analyze`.

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse `FEATURE_DIR`, `AVAILABLE_DOCS`, and `TASKS_BOOTSTRAP`. All paths must be absolute. `TASKS_BOOTSTRAP` is an optional derived run-local control-plane projection extracted from `plan.md`; treat `plan.md` as the authority if bootstrap is null, missing, or fails validation. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. Execute `before_tasks` hooks using the Hook Dispatch Protocol.

3. **Build the runtime task-generation queue before broad reads**:
   - Create one bounded **Bootstrap packet** for the run from `TASKS_BOOTSTRAP` first: feature identity, absolute paths, plan control-plane pointers, authoritative artifact inventory, and unresolved blockers.
   - Use bounded units in fixed order: `GLOBAL inventory and foundation -> one IF Scope at a time -> final DAG synthesis and document assembly`.
   - Keep only three context tiers active: **Bootstrap packet**, **Unit workset**, and **Task card**.
   - **Task card**: exactly one active generation target at a time.
   - Before opening each unit, declare required authoritative inputs, expected output, and stop condition.
   - Keep only one active generation target at a time; carry forward only stable execution anchors (`IF Scope`, `operationId`, refs, target paths, completion anchors, predecessor edges, blockers).
   - Build run-local derived views only as needed (`tuple-index`, `global-anchor-summary`, `unit-task-cards`, `dag-seed`); never promote them to new artifact authority.
   - Prefer `TASKS_BOOTSTRAP.unit_inventory` and `TASKS_BOOTSTRAP.ready_unit_inventory` over reparsing `Binding Projection Index` / `Artifact Status` tables. Re-open `plan.md` control-plane tables only when bootstrap data is missing, invalid, or contradictory.

4. **Load design documents (required + on-demand)**: Read from FEATURE_DIR:
   - **Required**: `plan.md`, `spec.md`, `data-model.md`, `test-matrix.md`, `contracts/`, `interface-details/`.
   - First validate `TASKS_BOOTSTRAP.required_sections`, `TASKS_BOOTSTRAP.stage_queue`, and `TASKS_BOOTSTRAP.unit_inventory`. If valid, use them as the default bounded control-plane packet for this run.
   - Consume only the slices needed for the active generation unit. Prefer section-level or row-level rereads over whole-file replay.
   - **On-demand only**: `research.md` when constraints/decisions materially affect the active unit.
   - Treat `plan.md` as the planning control plane. It MUST contain:
     - `Shared Context Snapshot`
     - `Stage Queue`
     - `Binding Projection Index`
     - `Artifact Status`
   - Stop and route to `/sdd.plan` if these control-plane sections are missing or non-consumable.
   - Stop and route to the relevant `/sdd.plan.*` child command if:
     - any `Stage Queue` row required for planning completion is not `done`
     - any `Artifact Status` row for `contract` or `interface-detail` remains non-`done`
   - Stop and route to `/sdd.plan.test-matrix` if `test-matrix.md` is missing, non-consumable, or lacks the tuple keys needed for executable verification mapping.
   - Stop and route to `/sdd.plan.contract` if a required contract artifact/path is missing, non-consumable, or cannot be aligned to the selected binding tuple.
   - Stop and route to `/sdd.plan.interface-detail` if a required interface-detail artifact/path is missing, non-consumable, or cannot be aligned to the selected binding tuple.

5. **Execute task generation workflow**:
   - Treat `plan.md` as the planning control plane and binding projection ledger; it is still a planning summary / structure guide, not as a replacement for canonical requirement, contract, model, or verification semantics.
   - Prefer bootstrap extraction from `TASKS_BOOTSTRAP`. Read `plan.md` only to validate or repair missing bootstrap fields:
     - `Shared Context Snapshot`
     - `Binding Projection Index`
     - completed `Artifact Status` target paths
     - structure / constraint notes needed for execution mapping
   - Build one unique run-local `tuple-index` from `TASKS_BOOTSTRAP.unit_inventory` when available; otherwise derive it from `Binding Projection Index` plus completed `Artifact Status` rows. This is the sole execution inventory for task generation. Reuse it instead of rescanning the repository for target discovery.
   - Read `spec.md` only for the requirement/story refs needed by the active execution mapping unit.
   - Convert approved planning artifacts into executable work packages plus a dependency-safe DAG; do not redesign upstream semantics in `/sdd.tasks`.
   - Output execution mapping conclusions only; do not emit design explanations, semantic supplements, or compensating rationale for missing upstream detail.
   - Repository-first consumption discipline:
     - Use canonical baseline files under `.specify/memory/repository-first/` only:
       - `.specify/memory/repository-first/technical-dependency-matrix.md` for dependency-governance task projection
       - `.specify/memory/repository-first/domain-boundary-responsibilities.md` for boundary ownership/collaboration task projection
       - `.specify/memory/repository-first/module-invocation-spec.md` for invocation-direction and layering-governance task projection
     - Feature-local copies are derived views only and MUST NOT replace canonical baseline semantics.
     - Do not derive dependency matrix / boundary responsibilities / invocation governance semantics from `README.md`, `docs/**`, planning narratives, or generated summaries.
     - If required canonical repository-first evidence is missing, stale, or non-traceable, stop task generation for affected scope and route repair to `/sdd.constitution` or `/sdd.analyze`.
   - Use the fixed loop `Discover -> Generate -> Compress` for every generation unit.
   - Use deterministic mechanical mapping rules during `Generate`:
     - one work package maps to exactly one `operationId` or one shared prerequisite objective
     - one work package maps to exactly one target path cluster or one command target
     - one work package maps to exactly one primary completion anchor
     - do not merge multiple operations, unrelated file clusters, or distinct validation objectives into one task
   - Between `Generate` and `Compress`, run **hard execution safety gates only** for the active unit: required anchor presence, prevention of promoting `TODO(REPO_ANCHOR)` into executable semantics, local mapping completeness, and dependency-safe schedulability.
   - **GLOBAL inventory and foundation unit**:
      - Load `data-model.md` and capture shared global object baselines required by tasks.
      - Build a run-local `global-anchor-summary` from the minimum shared anchors and invariants needed for cross-interface prerequisites.
      - Derive only truly cross-interface prerequisites consumed by multiple `IF Scope` units; do not use `GLOBAL` as overflow for interface-local work.
      - Treat any attempted `GLOBAL` overflow as a hard generation error that must be fixed upstream or by per-IF decomposition.
      - Compress to stable shared anchors before moving to `IF Scope` units.
   - **IF Scope units (sequential; one active at a time)**:
      - Build IF-scoped unit inventory from `TASKS_BOOTSTRAP.ready_unit_inventory` first; if bootstrap is unavailable, fall back to `Binding Projection Index`. Do not discover execution units by repository scan.
      - Map verification refs from `test-matrix.md` (`TM-*` / `TC-*`) using stable tuple keys projected in `Binding Projection Index` (`Operation ID`, `Boundary Anchor`, `IF Scope`).
      - Use `contracts/` as canonical interface semantics for implementation/verification task targets.
      - Resolve `contract` and `interface-detail` target paths from the completed `Artifact Status` rows in `plan.md`, then validate tuple alignment against the authoritative artifacts.
      - If contracts define interface operations but required interface-detail docs are missing, stop and request upstream completion.
      - For the active `IF Scope`, read only matching contract/detail slices, relevant `TM/TC` rows, relevant `data-model.md` anchors, and required `spec.md` refs.
      - Use `interface-details/` as the authoritative internal handoff design for execution targeting; extract `Implementation Entry Anchor` and repo-backed participating components when placing implementation tasks.
      - When `Boundary Anchor` and `Implementation Entry Anchor` differ, keep `Boundary Anchor` for verification/binding refs but anchor implementation tasks to the internal entry/collaborator path defined in `interface-details/`.
      - Do not target implementation work at the external boundary alone when the detail doc defines a narrower repo-backed internal handoff entry.
      - Consume only repository-anchored contract/interface tuples as executable semantics; treat `TODO(REPO_ANCHOR)` as blocker/note only.
      - Build work packages only from the active scope's matching contract/interface-detail/test tuples. If multiple operations share one `IF Scope`, keep them as separate work packages rather than one composite task.
      - When artifacts overlap, keep semantics authoritative in upstream artifacts (`spec.md`, `contracts/`, `data-model.md`, `test-matrix.md`); `tasks.md` maps execution only.
      - Generate one IF-scoped delivery unit at a time, then compress before loading the next.
      - After each unit is compressed, discard its detailed local working set and carry forward only stable delivery anchors.
   - **Final DAG synthesis and document assembly**:
      - Keep execution refs at task level inside GLOBAL/IF task definitions.
      - Build local predecessor edges per unit, then synthesize the full **Task DAG** adjacency list from the compressed unit outputs.
      - Add predecessor edges only when they are traceable to shared prerequisites, same-unit verify -> implement -> completion flow, or explicit upstream cross-unit dependency evidence. Do not infer new business ordering, responsibility boundaries, or implementation strategy.
      - Accumulate compressed unit outputs into one run-local execution graph and metadata cache; this graph is the single source for task numbering, DAG synthesis, `tasks.md` rendering, and manifest projection during the run.
      - Add adaptation caution note only when task graph/file layout indicates extra `adaptive` risk.
      - Ensure each task line is executable with concrete path/command/completion signal where relevant.
      - Generate tasks grouped by **GLOBAL** and **Interface Delivery Units** keyed by `IF Scope`.

6. **Generate tasks.md**: Use `.specify/templates/tasks-template.md` as structure. If the runtime template is missing or non-consumable, stop and report the blocker. Do not substitute `templates/tasks-template.md` or any other template location. Fill with:
   - Correct feature name from plan.md
   - A complete execution mapping that satisfies the template's required sections and canonical task format
   - Clear file paths, command targets, or completion signals where relevant
   - Explicit single-target work packages only; do not emit composite tasks, design rationale paragraphs, or placeholder blocker rows
   - Render from the run-local execution graph built in Step 5; do not regenerate task content by rereading completed unit prose

7. **Generate/refresh `tasks.manifest.json` sidecar (same directory as `tasks.md`)**:
   - Generate immediately after `tasks.md` so both outputs stay synchronized for the same run
   - Treat manifest as a **machine-readable projection** of `tasks.md` execution metadata only; it MUST NOT introduce new semantics beyond authoritative artifacts
   - Project manifest data from the same run-local execution graph used to render `tasks.md`; do not re-parse the just-written markdown to construct the manifest
   - If an older manifest exists, replace it from the current run-local execution graph (do not patch incrementally from stale state)
   - At minimum, each task entry MUST include keys: `task_id`, `dependencies`, `if_scope`, `refs`, `target_paths`, `completion_anchors`, `conflict_hints`, `status` (initialize to `pending`).
   - After write/report, invalidate run-local derived views (`tuple-index`, `global-anchor-summary`, `unit-task-cards`, `dag-seed`, execution graph cache`) so the next run rebuilds from authoritative artifacts

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
Use `.specify/templates/tasks-template.md` as the authoritative source for document structure, required sections, and canonical task line format.

Additional generation constraints:

- Map each interface detail / contract to one interface delivery unit keyed by `IF Scope`.
- Treat interface delivery units as execution mapping only.
- Use `Binding Projection Index` from `plan.md` as the execution-unit inventory source; if it is missing or incomplete, stop and route to `/sdd.plan.test-matrix`.
- Use the completed `Artifact Status` rows plus `Binding Projection Index` to resolve the only allowed contract/detail target paths for task generation.
- Each interface delivery unit SHOULD surface the contract binding plus the `Implementation Entry Anchor` when it differs from the contract boundary.
- Each interface delivery unit SHOULD include at least one `Verify` task and one `Interface` task (document exceptions explicitly).
- Each task MUST project exactly one execution target: one `operationId` or one shared prerequisite objective, one explicit target path cluster or command target, and one primary completion anchor.
- If a target path, command target, completion anchor, or predecessor edge cannot be stated explicitly from upstream artifacts, stop rather than infer it.
- A single task MUST NOT cover multiple operations, multiple unrelated file clusters, or multiple distinct validation objectives.
- Tasks may refine operation-level mappings but MUST NOT rewrite approved global object semantics.
- Interface implementation tasks SHOULD target the repo-backed `Implementation Entry Anchor` or directly participating collaborators from `interface-details/`; verification tasks SHOULD keep contract/test anchors explicit.
- If multiple operations share an `IF Scope`, keep them as separate work packages inside that IF unit; do not merge them into a synthetic combined task.
- `GLOBAL` is limited to prerequisites shared by multiple IF units. Using `GLOBAL` as overflow for one-scope work is a hard error.
- Repository-first projection artifacts in `.specify/memory/repository-first/` are complementary and MUST NOT replace one another (`.specify/memory/repository-first/technical-dependency-matrix.md` = dependency facts, `.specify/memory/repository-first/domain-boundary-responsibilities.md` = business boundary ownership, `.specify/memory/repository-first/module-invocation-spec.md` = invocation constraints).
- Task execution targets MUST reference anchored tuples only. `TODO(REPO_ANCHOR)` items MUST NOT be converted into executable interface semantics, completion anchors, or implementation objectives.
- Do not emit `blocked`, `todo`, placeholder, or compensating tasks to represent missing upstream design anchors.
- Use deterministic refs (`operationId`, `CaseID`, `TM-*`, `TC-*`) only when they help execution or completion checking.
- Keep Task DAG dependency-safe and minimally sufficient (avoid speculative over-constraint).
- Task DAG edges may come only from shared prerequisites, same-unit verification/implementation/completion flow, and explicit upstream cross-unit dependency evidence.
- `/sdd.tasks` must not infer new business ordering, responsibility boundaries, or implementation strategy.
- Keep `[Pre:T###,...]` consistent with the DAG while recognizing it is an inline mirror.
- Prefer intent-oriented `Role` labels when they help execution, but retain architecture-bound roles when the project structure confirms them.
- Use deterministic completion anchors whenever a task is emitted; if no primary completion anchor can be projected, do not generate the task.

---
description: Generate an executable, dependency-ordered tasks.md organized by GLOBAL and interface delivery units keyed by IF Scope.
handoffs: 
  - label: Analyze For Consistency
    agent: sdd.analyze
    prompt: Run a project analysis for consistency
    send: true
  - label: Implement Project
    agent: sdd.implement
    prompt: Start the implementation in phases
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

## Pre-Execution Checks

**Check for extension hooks (before tasks generation)**:

- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_tasks` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter to only hooks where `enabled: true`
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):

    ```text
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

  - **Mandatory hook** (`optional: false`):

    ```text
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    
    Wait for the result of the hook command before proceeding to the Outline.
    ```

- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load design documents (required + on-demand)**: Read from FEATURE_DIR:
   - **Required**: `plan.md`, `spec.md`, `data-model.md`, `test-matrix.md`, `contracts/`, `interface-details/`
   - **Load on-demand when needed for concrete task generation**: `research.md`
   - Do not preload beyond the required planning artifacts and the specific supporting context needed to generate executable tasks with clear file-level anchors.

3. **Execute task generation workflow**:
   - Load plan.md and extract tech stack, project structure, and implementation constraints that affect execution mapping
   - Load spec.md and extract requirement/user-story references for task mapping (not as primary task grouping)
   - Load `data-model.md` and identify global object baselines that tasks must reference (without rewriting semantics)
   - Load `test-matrix.md` and map feature verification refs (`TM-*` / `TC-*`) using stable tuple keys (`Operation ID`, `Boundary Anchor`, `IF Scope`)
   - Load contracts/ as the canonical interface semantics source for implementation and verification task targets
   - Map `IF Scope -> operationId -> detail doc path` from `interface-details/`, validating `Operation ID` / `Boundary Anchor` / `IF Scope` tuple alignment
   - If interface operations exist in contracts but required interface detail docs are missing, stop and ask for upstream completion first (do not backfill Stage 4 in `/sdd.tasks`)
   - Apply reference precedence when multiple artifacts mention similar scenarios:
     - requirement semantics from `spec.md`
     - contract semantics from `contracts/`
     - global model semantics from `data-model.md`
     - feature verification semantics from `test-matrix.md`
     - `tasks.md` only maps execution and must not redefine the above semantics
   - Treat `plan.md` as a planning summary / structure guide, not as a replacement for canonical requirement, contract, model, or verification semantics owned by the authoritative upstream artifacts above.
   - Any tuple indexes, execution maps, or working summaries created during `/sdd.tasks` are derived views only and MUST be rebuilt if they drift from the authoritative artifacts they summarize.
   - Load `research.md` only when implementation constraints or prior decisions materially affect task generation
   - Generate a lightweight execution mapping by keeping task-level refs inside IF/global task definitions
   - Generate **Task DAG** as adjacency list and use it as the baseline dependency source for execution order
   - Add a brief adaptation note only when the task graph or file layout suggests that `adaptive` mode needs special caution beyond normal dependency safety
   - Ensure each task line is concrete enough for execution while preserving room for bounded runtime adaptation
   - Generate tasks grouped by **GLOBAL** and **Interface Delivery Units** keyed by `IF Scope` (see Task Generation Rules below)
   - Validate task completeness: each IF unit has implementable tasks; each task has a concrete path, command target, or completion signal when relevant

4. **Generate tasks.md**: Use `templates/tasks-template.md` as structure, fill with:
   - Correct feature name from plan.md
   - A complete execution mapping that satisfies the template's required sections and canonical task format
   - Clear file paths, command targets, or completion signals where relevant

5. **Report**: Output path to generated tasks.md and summary:
   - Total task count
   - Task count per interface unit (`IF-###`) and `GLOBAL`
   - DAG sanity check summary (e.g., missing predecessors or obvious cycles)
   - Format validation: confirm ALL tasks follow the canonical task format closely enough for direct execution

6. **Check for extension hooks**: After tasks.md is generated, check if `.specify/extensions.yml` exists in the project root.
   - If it exists, read it and look for entries under the `hooks.after_tasks` key
   - If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
   - Filter to only hooks where `enabled: true`
   - For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
     - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
     - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
   - For each executable hook, output the following based on its `optional` flag:
     - **Optional hook** (`optional: true`):

       ```text
       ## Extension Hooks

       **Optional Hook**: {extension}
       Command: `/{command}`
       Description: {description}

       Prompt: {prompt}
       To execute: `/{command}`
       ```

     - **Mandatory hook** (`optional: false`):

       ```text
       ## Extension Hooks

       **Automatic Hook**: {extension}
       Executing: `/{command}`
       EXECUTE_COMMAND: {command}
       ```

   - If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

Context for task generation: {ARGS}

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

## Task Generation Rules

**CRITICAL**: Tasks MUST be organized by execution scope: `GLOBAL` + interface delivery units keyed by `IF Scope` (`IF-###`).

`tasks.md` is an execution orchestration artifact. Do not duplicate interface semantics, data-model semantics, or test prose from upstream docs.
Contract semantics come from `contracts/` only.
Feature verification semantics come from `test-matrix.md`.
Use `templates/tasks-template.md` as the authoritative source for document structure, required sections, and canonical task line format.

Additional generation constraints:

- Map each interface detail / contract to one interface delivery unit keyed by `IF Scope`.
- Each interface delivery unit SHOULD include at least one `Verify` task and one `Interface` task (document exceptions explicitly).
- Tasks may refine operation-level mappings but MUST NOT rewrite approved global object semantics.
- Use deterministic refs (`operationId`, `CaseID`, `TM-*`, `TC-*`) only when they help execution or completion checking.
- Keep Task DAG dependency-safe and minimally sufficient (avoid speculative over-constraint).
- Keep `[Pre:T###,...]` consistent with the DAG while recognizing it is an inline mirror.
- Prefer intent-oriented `Role` labels when they help execution, but retain architecture-bound roles when the project structure confirms them.
- Use deterministic completion anchors when they are needed to prove task completion.

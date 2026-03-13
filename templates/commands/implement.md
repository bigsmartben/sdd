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

### Long-Running Execution Visibility (Anti-Stall UX)

- `/speckit.implement` is often long-running. To avoid "no output / maybe stuck" confusion, the agent MUST emit visible progress signals throughout execution.
- Required visibility behaviors (minimal and implementation-agnostic):
  - Emit an initial `Execution Start Banner` before heavy work begins.
  - Emit progress on each task transition (`Task Start` / `Task Complete`).
  - If there is no visible completion for a while, emit periodic `still running` heartbeat updates (typically every ~1-2 minutes).
  - For obviously long-running commands (build/test/install/migration), emit status before and after command execution.
- Heartbeat updates SHOULD be concise and include at least one of:
  - current task or current phase
  - completed/total progress
  - blocking reason (if waiting)
  - next expected update checkpoint

## Pre-Execution Checks

**Check for extension hooks (before implementation)**:

- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_implement` key
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

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Check checklists status** (if FEATURE_DIR/checklists/ exists):
   - Scan all checklist files in the checklists/ directory
   - For each checklist, count:
     - Total items: All lines matching `- [ ]` or `- [X]` or `- [x]`
     - Completed items: Lines matching `- [X]` or `- [x]`
     - Incomplete items: Lines matching `- [ ]`
   - Create a status table:

     ```text
     | Checklist | Total | Completed | Incomplete | Status |
     |-----------|-------|-----------|------------|--------|
     | ux.md     | 12    | 12        | 0          | ✓ PASS |
     | test.md   | 8     | 5         | 3          | ✗ FAIL |
     | security.md | 6   | 6         | 0          | ✓ PASS |
     ```

   - Calculate overall status:
     - **PASS**: All checklists have 0 incomplete items
     - **FAIL**: One or more checklists have incomplete items

   - **If any checklist is incomplete**:
     - Display the table with incomplete item counts
     - **STOP** and ask: "Some checklists are incomplete. Do you want to proceed with implementation anyway? (yes/no)"
     - Wait for user response before continuing
     - If user says "no" or "wait" or "stop", halt execution
     - If user says "yes" or "proceed" or "continue", proceed to step 3

   - **If all checklists are complete**:
     - Display the table showing all checklists passed
     - Automatically proceed to step 3

3. Load and analyze the implementation context:
   - **REQUIRED**: Read tasks.md as the runtime execution orchestration source
   - **REQUIRED**: Consume these sections from tasks.md:
     - `Upstream Inputs (Execution References)`
     - `Execution Ordering Model` (especially `Task DAG`)
     - `Shared Foundation`
     - `Interface Delivery Units (IFxx)`
     - `Cross-Interface Finalization`
   - **REQUIRED**: Treat `Task DAG` as the baseline dependency authority for runtime scheduling
   - **REQUIRED**: In `strict` mode, follow `Task DAG` exactly as written.
   - **REQUIRED**: In `adaptive` mode, local resequencing is allowed only when all conditions below hold:
     - Dependency safety is preserved (no predecessor violation)
     - Final completion anchors remain satisfiable
     - Runtime adaptation notes are reported in execution output
   - **REQUIRED**: Treat `[Pre:T###,...]` only as an inline dependency mirror (consistency check), not as dependency authority
   - **REQUIRED**: Read plan.md for tech stack, architecture, and file structure
   - **IF EXISTS**: Read interface-details/ for per-interface detailed design projection (contract-bound behavior, field-level class refinement from data-model, and method-level sequencing details)
   - **IF EXISTS**: Read data-model.md for entities and relationships
   - **IF EXISTS**: Read contracts/ for API specifications and test requirements
   - **IF EXISTS**: Read research.md for technical decisions and constraints
   - **IF EXISTS**: Read quickstart.md for integration scenarios

4. Generate an execution strategy summary before modifying code:
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

5. Parse tasks.md structure and extract:
   - **Execution scopes**: `GLOBAL` and `IFxx` units
   - **Task DAG**: adjacency list and topological execution layers
   - **Task metadata**: `TaskID`, `Type`, `Scope`, `Role`, `Pre`, description, file paths, completion anchors
   - **Reference metadata** (when present): `operationId`, requirement refs, verification refs
   - **Execution flow**: DAG-driven order and file-level conflict constraints

6. Execute implementation following the task plan:
   - **DAG-first execution**: Schedule tasks strictly by `Task DAG` dependency satisfaction
   - **Scope-aware flow**: Execute `GLOBAL` foundation tasks and `IFxx` unit tasks according to DAG, not section order alone
   - **Parallel eligibility**: Tasks in the same DAG-ready layer may execute in parallel only when they have no shared file-path conflicts
   - **Verify-before-Interface preference**: Prefer running `Type:Verify` tasks before corresponding `Type:Interface` tasks when DAG allows
   - **Validation checkpoints**: Verify completion anchors and dependency closure before advancing to downstream DAG layers
   - **Adaptive execution bounds** (`mode: adaptive` only):
     - MAY split a task into smaller executable steps when this reduces file conflict or de-risks delivery
     - MAY merge same-layer tasks when they target the same artifact and share completion anchors
     - MAY locally resequence same-layer tasks when no dependency/file-conflict rule is violated
     - MUST keep original task IDs traceable (do not erase source task lineage)
     - MUST update task checkboxes and report adaptations in execution output

7. Implementation execution rules:
   - **GLOBAL foundation first when required by DAG**: Complete shared infra/bootstrap/config prerequisites before dependent IF tasks
   - **Interface-unit delivery**: For each `IFxx`, execute verify + implementation work using task `Role` (e.g., contract, handler, service, persistence, wiring, smoke)
   - **Reference-preserving execution**: For each task, keep linkage to available operation/requirement/verification refs
   - **Cross-cutting/finalization last when DAG-scheduled**: Run docs/final validation/cross-interface tasks after prerequisite IF/GLOBAL tasks complete

8. Progress tracking and error handling:
   - Report progress after each completed task
   - Emit periodic heartbeat updates when execution has no visible completion for a while (typically every ~1-2 minutes)
   - Halt execution if any required DAG predecessor task fails
   - For parallel-eligible DAG-ready tasks, continue successful tasks, report failed ones, and skip newly blocked descendants
   - In `adaptive` mode, if adaptation is required due to runtime reality (unexpected file structure/API drift), propose minimal safe adaptation and request confirmation before continuing
   - Provide clear error messages with context for debugging
   - On recoverable stalls (tooling/network/build wait), print explicit status + wait reason + estimated next update time
   - Suggest next steps if implementation cannot proceed
   - **IMPORTANT** For completed tasks, make sure to mark the task off as [X] in the tasks file.

9. Completion validation:
   - Verify all reachable required DAG tasks are completed or explicitly waived by user
   - Verify `Task DAG` dependency closure (no completed task missing required predecessors)
   - Verify each interface unit (`IFxx`) meets its Definition of Done and completion anchors
   - Verify completed tasks still map to available requirement/verification refs
   - Check that implemented features match the original specification
   - Validate that tests pass and coverage meets requirements
   - Confirm the implementation follows the technical plan
   - Confirm tasks.md checkboxes accurately reflect execution results
   - In `adaptive` mode, summarize adaptations and their dependency impact in final output
   - Report final status with summary of completed work, blocked items, and remediation follow-ups

Note: This command assumes a complete, DAG-usable tasks breakdown exists in tasks.md. If required sections are missing, DAG is invalid, or task rows are incomplete, suggest running `/speckit.tasks` first to regenerate the task list.

### Progress Output Examples (Non-Normative)

Any concise, consistent, human-readable style is acceptable. Example:

```text
Started implementation (mode=adaptive, total=37)
Task T012 started: implement submit handler
Still running: waiting on build lock, next update in <= 2m
Command finished: npm test -- submit_session (exit=0)
Task T012 completed (Completion Anchor: CaseID C-017 pass)
```

1. **Check for extension hooks**: After completion validation, check if `.specify/extensions.yml` exists in the project root.
    - If it exists, read it and look for entries under the `hooks.after_implement` key
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

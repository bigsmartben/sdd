---
description: Generate an executable, dependency-ordered tasks.md organized by GLOBAL and IFxx delivery units.
handoffs: 
  - label: Analyze For Consistency
    agent: speckit.analyze
    prompt: Run a project analysis for consistency
    send: true
  - label: Implement Project
    agent: speckit.implement
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
   - **Required**: `plan.md`, `spec.md`, `contracts/` (canonical contract semantics)
   - **Load on-demand when needed for concrete task generation**: `data-model.md`, `interface-details/`, `test-matrix.md`, `research.md`, `quickstart.md`
   - Do not preload every optional artifact; load only what is needed to generate executable tasks with clear file-level anchors.

3. **Execute task generation workflow**:
   - Load plan.md and extract tech stack, project structure, and interface references (IFxx/operationId when available)
   - Load spec.md and extract requirement/user-story references for task mapping (not as primary task grouping)
   - Load contracts/ as the canonical interface semantics source for implementation and verification task targets
   - If interface-details/ exists: map `IFxx -> operationId -> detail doc path`
   - If test-matrix.md exists: map verification refs (`CaseID` / `TM-*` / `TC-*`) to interfaces or global behaviors
   - If data-model.md exists: identify global object baselines that tasks must reference (without rewriting semantics)
   - Generate **Task Mapping Index** (`TaskID -> IFxx|GLOBAL -> operationId -> requirement/test refs -> source refs`)
   - Generate **Task DAG** as adjacency list and use it as the dependency source for execution order
   - Generate tasks grouped by **GLOBAL** and **Interface Delivery Units (IFxx)** (see Task Generation Rules below)
   - Validate task completeness: each IF unit has implementable tasks and verifiable completion criteria; each task has concrete path + completion anchor when relevant

4. **Generate tasks.md**: Use `templates/tasks-template.md` as structure, fill with:
   - Correct feature name from plan.md
   - Upstream reference index (IF registry, interface details, data-model baseline, test-matrix refs)
   - Task mapping index
   - Execution ordering model with **Task DAG**
   - Global foundation tasks (cross-interface prerequisites)
   - Interface delivery units (`IFxx`) with verify + implementation tasks
   - Final cross-cutting/finalization tasks
   - All tasks must follow the strict checklist format (see Task Generation Rules below)
   - Clear file paths and completion anchors

5. **Report**: Output path to generated tasks.md and summary:
   - Total task count
   - Task count per interface unit (`IFxx`) and `GLOBAL`
   - DAG sanity check summary (e.g., missing predecessors or obvious cycles)
   - Format validation: confirm ALL tasks follow the checklist format (checkbox, ID, type, role, path)

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

**CRITICAL**: Tasks MUST be organized by execution scope: `GLOBAL` + `Interface Delivery Units (IFxx)`.

`tasks.md` is an execution orchestration artifact. Do not duplicate interface semantics, data-model semantics, or test prose from upstream docs.
Contract semantics come from `contracts/` only.

### Checklist Format (REQUIRED)

Every task MUST strictly follow this format:

```text
- [ ] T### [Type:Research|Interface|Verify|Infra|Docs] [IFxx?] [Role:...] [Pre:T###,...] Description with file path
```

**Format Components**:

1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
2. **Task ID**: Sequential number (T001, T002, T003...) in execution order
3. **Type**: MUST be one of `Research | Interface | Verify | Infra | Docs`
4. **[IFxx] scope tag**:
   - Include when task belongs to an interface delivery unit
   - Omit only for true cross-interface/global tasks
5. **[Role:...]**: REQUIRED execution role (e.g., `contract`, `handler`, `service`, `persistence`, `wiring`, `smoke`, `manual-check`)
6. **[Pre:T###,...]**: Optional inline dependency mirror; Task DAG remains authority
7. **Description**: Clear action with exact file path and completion anchor where relevant

**Examples**:

- ✅ CORRECT: `- [ ] T001 [Type:Infra] [Role:bootstrap] Initialize service scaffolding in backend/src/app.py`
- ✅ CORRECT: `- [ ] T007 [Type:Verify] [IF01] [Role:contract] [Pre:T006] Validate submitGushiwenPracticeSession contract in tests/contract/test_submit_session.py`
- ✅ CORRECT: `- [ ] T009 [Type:Interface] [IF01] [Role:handler] [Pre:T007] Implement submit handler in backend/src/handlers/submit_session.py (Completion Anchor: CaseID C-017 pass)`
- ❌ WRONG: `- [ ] Create handler` (missing ID/type/role/path)
- ❌ WRONG: `- [ ] T010 [IF01] Implement handler` (missing Type and Role)
- ❌ WRONG: `- [ ] T011 [Type:Interface] Implement handler` (missing Role and path)

### Task Organization

1. **By Execution Scope (PRIMARY ORGANIZATION)**:
   - Global prerequisites and shared infra tasks under `GLOBAL`
   - Interface implementation and verification under `IFxx` units
   - Cross-cutting/finalization tasks in final section

2. **From Interface Artifacts**:
   - Map each interface detail / contract to one IF unit
   - Each IF unit SHOULD include at least one `Verify` task and one `Interface` task (document exceptions explicitly)

3. **From Data Model Baseline**:
   - Tasks may refine operation-level mappings
   - Tasks MUST NOT rewrite approved global object semantics

4. **From Verification Artifacts**:
   - Use deterministic refs (`operationId`, `CaseID`, `TM-*`, `TC-*`) for verify task targeting
   - Verification semantics come from upstream artifacts; tasks only reference and execute

### Required Sections in Generated tasks.md

- Upstream Reference Index
- Task Mapping Index
- Execution Ordering Model (`Task DAG` as dependency source)
- Global Foundation Tasks
- Interface Delivery Units (`IFxx`)
- Cross-Cutting and Finalization

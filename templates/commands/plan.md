---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
handoffs: 
  - label: Create Tasks
    agent: speckit.tasks
    prompt: Break the plan into tasks
    send: true
  - label: Create Checklist
    agent: speckit.checklist
    prompt: Create a checklist for the following domain...
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load context**: Read FEATURE_SPEC and `/memory/constitution.md`. Load IMPL_PLAN template (already copied).

3. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Stage 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Stage 1: Generate data-model.md, contracts/, quickstart.md (include business state machine in data-model when lifecycle exists)
   - Stage 2: Refine and enhance spec-stage UIF and complete normal/exception scenario coverage (e.g., test-matrix.md when applicable)
   - Stage 3: Produce interface detailed design with method-call-level sequence diagrams, strictly referencing contracts semantics (e.g., interface-details/)
   - Stage 3: Update agent context by running the agent script
   - Re-evaluate Constitution Check after Stage 3

4. **Stop and report**: Command ends after Stage 3 planning. Report branch, IMPL_PLAN path, and generated artifacts.

## Stages

### Stage 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:

   ```text
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]
   - Repository Support: [exact in-repo evidence with concrete symbols, e.g., `ClassName.methodName`, `path:Class#method`, API operationId/schema ref]
   - Support Status: [`Supported` / `Partially Supported` / `Unsupported`]
   - Certainty: [`Certain` / `Suspected` / `Missing`]

4. **Repository support evidence rule (mandatory)**:
   - For every key conclusion, provide direct repository support evidence with concrete source anchors.
   - Prefer `类.方法` (or equivalent symbol-level anchors) over generic module descriptions.
   - If implementation symbol is unavailable, explicitly mark `NEEDS CLARIFICATION` and include the closest verifiable anchor.

**Output**: research.md with all NEEDS CLARIFICATION resolved

### Stage 1: Data Model & Contracts

**Prerequisites:** `research.md` complete

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable (business state machine required when lifecycle exists)

2. **Define interface contracts** (mandatory) → `/contracts/`:
   - Identify what interfaces the project exposes to users or other systems
   - Document the contract format appropriate for the project type
   - Use **contracts terminology and contracts semantics** as the single source for downstream references
   - Examples: public APIs for libraries, command schemas for CLI tools, endpoints for web services, grammars for parsers, UI contracts for applications

**Output**: data-model.md, /contracts/*, quickstart.md

### Stage 2: Test (UIF Refinement & Exception Coverage)

**Prerequisites:** `research.md`, `data-model.md`, and contracts complete

1. **Refine UIF in spec**:
   - Expand key user interaction flows and states
   - Ensure UIF references align with FR/UC and contracts
   - This is **spec-stage refinement and enhancement within current planning stage**, not a backward rewrite workflow

2. **Complete test coverage design**:
   - Cover normal scenario paths end-to-end
   - Cover exception/error/degraded scenarios comprehensively
   - Produce or update `test-matrix.md` (or project-equivalent coverage artifact)

**Output**: UIF refinement in spec and test coverage artifact(s)

### Stage 3: Interface Detailed Design

**Prerequisites:** Stage 1 and Stage 2 outputs complete

1. **Produce per-interface detailed design artifacts**:
   - Add/update interface detail docs (e.g., `interface-details/*.md`)
   - Keep detailed design consistent with contracts and data model
   - Downstream artifacts must reference contracts; do not redefine contract semantics in detailed design

2. **Design notation requirements**:
   - UML class at this stage is detailed-design/full-class level
   - Sequence diagrams must be method-call-level granularity

3. **Contract reference rule**:
   - Use contracts semantics as canonical; treat all contract artifacts under `contracts/` as representations, not independent semantic sources

4. **Agent context update**:
   - Run `{AGENT_SCRIPT}`
   - These scripts detect which AI agent is in use
   - Update the appropriate agent-specific context file
   - Add only new technology from current plan
   - Preserve manual additions between markers

**Output**: interface detailed design artifact(s), agent-specific file

## Key rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications

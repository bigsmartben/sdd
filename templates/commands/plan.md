---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
handoffs: 
  - label: Create Tasks
    agent: sdd.tasks
    prompt: Break the plan into tasks
    send: true
  - label: Create Checklist
    agent: sdd.checklist
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
   - Evaluate constitution-aligned constraints (stop if critical violations are unresolved)
   - Stage 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Stage 1: Generate data-model.md, contracts/, quickstart.md (include business state machine in data-model when lifecycle exists; provide stable model anchors such as invariant IDs / transition IDs when applicable for Stage 3 references)
   - Stage 2: Generate test-matrix.md as verification design input from spec-stage UIF (without rewriting `spec.md`), then complete normal/exception coverage and case anchors (as input for Stage 3 interface design)
   - Stage 3: Generate interface detailed design artifacts as contract-bound semantic projections with field-level UML class design refined from data-model and method-call-level sequence diagrams, strictly referencing contracts semantics and projecting upstream semantics for downstream consumption (e.g., interface-details/, one detail doc per interface operation)
   - Stage 4: Update agent context by running the agent script
   - Re-evaluate Constitution Check after Stage 3

4. **Stop and report**: Command ends after Stage 4 planning. Report branch, IMPL_PLAN path, and generated artifacts.

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
   - Entity / value object / lifecycle policy candidates
   - Entity name, fields, relationships
   - Validation rules and business invariants from requirements
   - State transitions if applicable (business state machine required when lifecycle exists)
   - Prefer stable reference anchors for downstream stages when applicable:
     - invariant IDs (e.g., `INV-*`)
     - transition IDs (e.g., `T-*`)

2. **Define interface contracts** (mandatory) → `/contracts/`:
   - Identify what interfaces the project exposes to users or other systems
   - Document the contract format appropriate for the project type
   - Use **contracts terminology and contracts semantics** as the single source for downstream references
   - Examples: public APIs for libraries, command schemas for CLI tools, endpoints for web services, grammars for parsers, UI contracts for applications

**Output**: data-model.md, /contracts/*, quickstart.md

### Stage 2: Test-Matrix Generation (UIF Refinement & Exception Coverage)

**Prerequisites:** `research.md`, `data-model.md`, and contracts complete

1. **Derive verification-oriented UIF refinement from spec**:
   - Integrate UC-local UIF and cross-UC global flow into a verification-oriented execution view
   - Expand key user interaction flows and states
   - Ensure UIF references align with FR/UC and contracts
   - This is **verification-oriented projection within current planning stage**, not a backward rewrite workflow of `spec.md`

2. **Generate `test-matrix.md` and complete test coverage design**:
   - Cover normal scenario paths end-to-end
   - Cover exception/error/degraded scenarios comprehensively
   - Use refined global UIF execution paths as key input for case design (`CaseID` / `TM-*` / `TC-*` anchors)
   - Keep case traceability reference-oriented for verification use; avoid governance-only mapping payloads
   - Produce `test-matrix.md` (or project-equivalent coverage artifact)

**Output**: `test-matrix.md` (or project-equivalent coverage artifact) with UIF-based verification paths, case anchors, and normal/exception coverage

### Stage 3: Interface Detailed Design

**Prerequisites:** Stage 1 and Stage 2 outputs complete

1. **Produce per-interface detailed design artifacts**:
   - Add/update interface detail docs (e.g., `interface-details/*.md`)
   - Each interface detail doc MUST map to exactly one contract operation (prefer operationId-aligned naming)
   - File naming SHOULD be operationId-aligned and stable (e.g., `<operationId>.md`) unless the project has an explicit naming convention
   - Each interface detail doc MUST project only the interface-relevant subset of `data-model.md`; avoid restating the full global model
   - Carry forward interface-relevant main/exception interaction paths from `test-matrix.md` into interface-level detailed behavior
   - Each interface detail doc SHOULD map main path and major exception paths to `CaseID` / `TM-*` / `TC-*` anchors (keep it practical)
   - Keep detailed design consistent with contracts and data model
   - Treat `interface-details/` as the per-interface detailed design projection consumed by downstream `/sdd.tasks` and `/sdd.implement`
   - Downstream artifacts must reference contracts; do not redefine contract semantics in detailed design
   - For each interface detail artifact, identify which normal and exception paths from `test-matrix.md` are realized by the bound operation and reflect them in behavior/sequence design
   - Keep Stage 3 anchors aligned with upstream artifacts where available; if some anchors are unavailable, record concise clarifications without blocking progress

2. **Minimum required content per interface detail doc**:
   - Stable section skeleton (keep section names and order stable for reviewability):
     - `## Contract Binding`
     - `## Scope & Projection`
     - `## Invariants & Transition Responsibilities`
     - `## Preconditions / Postconditions`
     - `## Behavior Paths`
     - `## Sequence Diagram`
     - `## UML Class Design`
     - `## Traceability Mapping`
   - If a required section is not applicable, keep the section and provide explicit rationale (do not silently remove sections)
   - Contract binding: explicit operationId (or equivalent unique contract operation anchor)
   - Operation semantic projection from `data-model.md`, including:
     - entities / value objects / FSMs in scope
     - field projection (read / write / output / internal use)
     - source anchors for projected fields (e.g., `Entity.field`) when helpful
     - relationship projection relevant to the operation
     - projection depth sufficient for implementation (avoid ultra-thin 1-2 field summaries unless justified)
   - Invariant responsibility mapping:
     - identify which global invariants are established, validated, preserved, or not applicable in this operation
     - identify where enforcement occurs (application / domain / repository / other component)
     - include invariant meaning and contract-visible failure behavior when invariant checks fail
     - avoid opaque placeholders (e.g., bare `N/A`); if not applicable, provide explicit reason
   - Lifecycle transition binding (when relevant state machine exists):
     - transition IDs (or equivalent transition anchors)
     - guards / constraints
     - contract-visible guard-failure behavior
   - Field-level UML class design refined from `data-model.md` (include interface-relevant fields/relationships/constraints)
   - Preconditions and postconditions aligned with contracts/data model and written as verifiable conditions
   - Main success path and numbered key exception/error path behavior at interface level
   - Consistency boundary / side-effect notes when operation crosses persistence or external interaction boundaries
   - Method-call-level sequence diagram (participants + call order + key exception/guard-failure branches)
   - Concise path/case mapping to spec / data-model / contracts / test-matrix references (avoid heavy traceability overhead)

3. **Markdown formatting contract (mandatory)**:
   - Use clean CommonMark-compatible Markdown; do not indent headings, tables, lists, or fenced code blocks with leading spaces unless nested by design
   - Keep heading levels stable and ordered (H1 title once, then H2/H3 as needed); avoid heading level jumps
   - Every list item must start on its own line; do not merge multiple numbered/bulleted items into a single wrapped line
   - Tables must keep a valid header separator row and one logical record per row (no accidental line breaks inside a row)
   - Diagrams must use Mermaid syntax and be fenced with plain triple backticks and `mermaid` language tag
   - Before finalizing, normalize spacing (single blank line between sections, no trailing indentation)

4. **Stage 3 quality gate (mandatory before finalizing)**:
   - Contract operation binding is one-to-one and unambiguous
   - Required section skeleton is preserved; non-applicable sections include explicit rationale
   - No required section is empty or filled with unqualified placeholders
   - Field projection, invariant mapping, transition mapping, and traceability all have concrete anchors
   - Main path and key exception paths are both represented in behavior and sequence design
   - UML class diagram includes interface-relevant concrete fields/relationships (not only layer names)
   - Sequence diagram uses method-call-level granularity and concrete method names, including key exception/guard-failure branches
   - Main and major exception paths include concise case mapping (`CaseID` / `TM-*` / `TC-*`)
   - Key anchors are aligned with upstream artifacts (`contracts/`, `data-model.md`, `test-matrix.md`) where available
   - Markdown rendering is structurally correct (headings/lists/tables/code blocks display normally in preview)

5. **Design notation requirements**:
   - UML class at this stage is detailed-design/full-class level with concrete field-level definitions
   - Sequence diagrams must be method-call-level granularity

6. **Contract reference rule**:
   - Use contracts terminology and semantics consistently across downstream artifacts

7. **Data-model reference rule**:
   - Use `data-model.md` as canonical source for global object semantics, invariants, relationships, and lifecycle definitions
   - Interface detailed design may refine/project these semantics for one bound operation, but must not redefine or contradict them
   - Prefer explicit anchors (entity names, invariant IDs, transition IDs) over free-text paraphrase when available

8. **Test-matrix reference rule**:
   - Use `test-matrix.md` as the planning-stage source for coverage and verification anchors (e.g., `CaseID` / `TM-*` / `TC-*`)
   - `test-matrix.md` may refine scenario coverage from spec/UIF for verification purposes, but must not redefine requirement semantics from `spec.md`
   - Treat Stage 2 global UIF refinement as key case-design input and map selected main/exception paths explicitly at operation level
   - Keep traceability lightweight and design-serving
   - Interface detailed design should consume test-matrix paths as validation-path input, then map operation-level realization explicitly

**Output**: interface detailed design artifact(s)

### Stage 4: Agent Context Update

**Prerequisites:** Stage 3 outputs complete

1. **Update agent context**:
   - This stage is a repository-level context synchronization action after design outputs are produced
   - Run `{AGENT_SCRIPT}`
   - These scripts detect which AI agent is in use
   - Update the appropriate agent-specific context file
   - Add only new technology from current plan
   - Preserve manual additions between markers

**Output**: agent-specific context file

## Key rules

- Use absolute paths
- Stop on unresolved critical constraints or unresolved clarifications

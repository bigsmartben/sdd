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
   - Stage 2: Generate test-matrix.md as a verification design input from spec-stage UIF, focusing on actionable normal/exception scenarios and any case anchors that help downstream verification (without rewriting `spec.md`)
   - Stage 3: Generate interface detailed design artifacts as contract-bound design projections that support implementation, using field-level UML class design refined from data-model and method-call-level sequence diagrams while referencing upstream artifacts only where they clarify behavior, enforcement, or verification
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
   - Repository Support (when available): [relevant in-repo evidence such as symbol, path, API operationId, or nearby implementation anchor]
   - Notes (optional): [certainty, gaps, or follow-up items only when they materially affect the plan]

4. **Repository support evidence rule**:
   - Add direct repository support evidence when the repo already contains a relevant implementation, contract, or pattern worth following.
   - Prefer concrete anchors over generic module descriptions when such anchors are easy to identify.
   - If no useful in-repo support exists, record the decision without forcing placeholder evidence.

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

### Stage 2: Test-Matrix Generation (Verification Design)

**Prerequisites:** `research.md`, `data-model.md`, and contracts complete

1. **Derive verification-oriented UIF refinement from spec**:
   - Integrate UC-local UIF and cross-UC global flow into a verification-oriented execution view
   - Expand key user interaction flows and states
   - Ensure UIF references align with FR/UC and contracts
   - This is **verification-oriented projection within current planning stage**, not a backward rewrite workflow of `spec.md`

2. **Generate `test-matrix.md` as a verification design artifact**:
   - Capture the normal scenario paths needed for downstream verification
   - Capture the exception/error/degraded scenarios that materially affect implementation or validation
   - Use refined global UIF execution paths as key input for case design and add `CaseID` / `TM-*` / `TC-*` anchors only when they help downstream verification
   - Keep the artifact verification-serving and scenario-oriented; avoid turning it into a coverage audit ledger
   - Produce `test-matrix.md` (or project-equivalent coverage artifact)

**Output**: `test-matrix.md` (or project-equivalent coverage artifact) with UIF-based verification paths, actionable scenarios, and any case anchors needed downstream

### Stage 3: Interface Detailed Design

**Prerequisites:** Stage 1 and Stage 2 outputs complete

1. **Produce per-interface detailed design artifacts**:
   - Add/update interface detail docs (e.g., `interface-details/*.md`)
   - Each interface detail doc MUST map to exactly one contract operation (prefer operationId-aligned naming)
   - File naming SHOULD be operationId-aligned and stable (e.g., `<operationId>.md`) unless the project has an explicit naming convention
   - Each interface detail doc MUST project only the interface-relevant subset of `data-model.md`; avoid restating the full global model
   - Carry forward interface-relevant main/exception interaction paths from `test-matrix.md` into interface-level detailed behavior
   - Include `CaseID` / `TM-*` / `TC-*` anchors only when they materially clarify behavior or verification intent
   - Keep detailed design consistent with contracts and data model
   - Treat `interface-details/` as the per-interface detailed design projection consumed by downstream `/sdd.tasks` and `/sdd.implement`
   - Downstream artifacts must reference contracts; do not redefine contract semantics in detailed design
   - Reflect the normal and exception paths from `test-matrix.md` that are actually realized by the bound operation in behavior/sequence design
   - Add concise upstream references only where they clarify behavior, enforcement, or verification; do not turn the doc into an audit table
   - For diagram generation, use strict source precedence: `contracts/` for contract semantics, `data-model.md` for domain objects/fields/invariants/relationships/transitions, and `test-matrix.md` for main/exception execution paths
   - If relevant repository symbols already exist, reuse participant / class / method names verbatim in prose and diagrams
   - If no relevant repository symbols exist, choose one stable planned name per role for the bound operation and reuse it across prose, sequence diagram, and UML
   - Do not introduce multiple synonymous participants or classes for the same responsibility within one interface detail doc

2. **Minimum required content per interface detail doc**:
   - Stable section skeleton (keep section names and order stable for reviewability):
     - `## Contract Binding`
     - `## Scope & Projection`
     - `## Invariants & Transition Responsibilities`
     - `## Preconditions / Postconditions`
     - `## Behavior Paths`
     - `## Sequence Diagram`
     - `## UML Class Design`
     - `## Upstream References`
   - If a required section is not applicable, keep the section and provide explicit rationale (do not silently remove sections)
   - `## Behavior Paths` is the authoritative local source for sequence-diagram message flow
   - `## Scope & Projection` plus `## Invariants & Transition Responsibilities` are the authoritative local source for UML class/member selection
   - Contract binding: explicit operationId (or equivalent unique contract operation anchor)
   - Operation semantic projection from `data-model.md`, including:
     - entities / value objects / FSMs in scope
     - field projection (read / write / output / internal use)
     - source anchors for projected fields (e.g., `Entity.field`) when helpful
     - relationship projection relevant to the operation
     - projection depth sufficient for implementation (avoid ultra-thin 1-2 field summaries unless justified)
   - Invariant responsibility mapping:
     - identify which global invariants are established, validated, preserved, or not applicable in this operation when invariants materially affect the behavior
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
   - Concise upstream references listing the contract anchor plus only the spec / data-model / test-matrix refs actually used by the operation

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
   - Main path and key exception paths relevant to the operation are represented in behavior and sequence design
   - UML class diagram includes interface-relevant concrete fields/relationships (not only layer names)
   - Sequence diagram uses method-call-level granularity and concrete method names, including key exception/guard-failure branches
   - `## Behavior Paths` is reflected in sequence design without missing contract-visible exception or guard-failure branches
   - Each sequence participant has an explicit operation role and comes from an allowed participant bucket
   - Guard / invariant / transition checks appear before the protected side effects they gate
   - UML class diagram includes only operation-relevant classes, each with concrete members/constraints and a clear reason to appear
   - No class/member contradicts `data-model.md` and no diagram branch contradicts contract-visible failure behavior
   - Existing repo symbols are reused verbatim when available; otherwise planned names stay stable across prose and diagrams
   - The design stays consistent with `contracts/` and `data-model.md`
   - Upstream references stay concise and only include refs that support behavior, enforcement, or verification
   - Markdown rendering is structurally correct (headings/lists/tables/code blocks display normally in preview)

5. **Design notation requirements**:
   - UML class at this stage is detailed-design/full-class level with concrete field-level definitions
   - Sequence diagrams must be method-call-level granularity

6. **Diagram source-of-truth and naming rule**:
   - Contract semantics come only from `contracts/`
   - Domain objects, fields, invariants, relationships, and transitions come only from `data-model.md`
   - Main and exception execution paths come only from `test-matrix.md`
   - If relevant repository symbols already exist, reuse them verbatim for participant, class, and method names
   - If no relevant repository symbols exist, choose one stable planned name per role for the bound operation and reuse it consistently across prose, sequence diagram, and UML
   - Do not introduce multiple synonymous participants or classes for the same responsibility within a single interface detail doc

7. **Sequence diagram derivation rule**:
   - Participants may be selected only from the buckets actually used by the operation: external actor/caller, interface boundary/handler/controller/command entrypoint, application/service orchestrator, domain entity/value object/policy, persistence adapter/repository, external system/gateway
   - Message order must be derived from `## Behavior Paths`, not invented independently
   - Every main success path must appear once in the success flow
   - Every key exception/guard-failure path listed in `## Behavior Paths` that materially affects contract-visible behavior must appear as an `alt` branch
   - Guard / invariant / transition checks must appear before the side effect they protect
   - Cross-boundary side effects must be shown as explicit calls to repository / gateway / external participants
   - Use Mermaid `sequenceDiagram` with `autonumber`
   - Message labels must use concrete method or operation names; avoid generic verbs like `process()` unless the exact name is anchored upstream or already exists in-repo

8. **UML class derivation rule**:
   - Include only interface-relevant classes from these buckets: contract DTO/request/response/error types, domain entities/value objects/policies from `data-model.md`, and application/service/repository/gateway classes that participate in the bound operation
   - Each class shown must have an operation-level reason to appear tied to field projection, invariant/transition enforcement, method participation in the sequence, or cross-boundary side effect
   - Fields must be included only when the operation uses them as input, validation, read, write, output, or internal state
   - Methods shown must align with sequence-diagram messages or invariant/transition enforcement responsibilities
   - Relationships must be limited to ones relevant to the bound operation
   - If a state machine exists, affected classes must show the relevant state field and transition-related constraints for this operation
   - Layer-only placeholder boxes are invalid; each class must include concrete members or constraints

9. **Contract reference rule**:
   - Use contracts terminology and semantics consistently across downstream artifacts

10. **Data-model reference rule**:
    - Use `data-model.md` as canonical source for global object semantics, invariants, relationships, and lifecycle definitions
    - Interface detailed design may refine/project these semantics for one bound operation, but must not redefine or contradict them
    - Prefer explicit anchors (entity names, invariant IDs, transition IDs) over free-text paraphrase when available

11. **Test-matrix reference rule**:
    - Use `test-matrix.md` as the planning-stage source for verification scenarios and anchors when those scenarios materially inform implementation or validation
    - `test-matrix.md` may refine scenario coverage from spec/UIF for verification purposes, but must not redefine requirement semantics from `spec.md`
    - Treat Stage 2 global UIF refinement as key case-design input and carry forward only the paths that matter to the bound operation
    - Keep references lightweight and design-serving; do not build audit ledgers in interface detail docs
    - Interface detailed design should consume test-matrix paths as validation-path input, then reference them concisely where useful

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

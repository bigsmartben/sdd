---
description: Perform a non-destructive cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Run the dedicated pre-implementation audit across the three core artifacts (`spec.md`, `plan.md`, `tasks.md`) after `/sdd.tasks`. Identify inconsistencies, ambiguities, uncovered MUST requirements, execution gaps, and unnecessary traceability payload before `/sdd.implement`.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Output a structured audit report. Offer an optional remediation plan (user must explicitly approve before any follow-up editing commands would be invoked manually).

**Constitution Authority**: The project constitution (`/memory/constitution.md`) is **non-negotiable** within this analysis scope. Constitution conflicts are automatically CRITICAL and require adjustment of the spec, plan, or tasks—not dilution, reinterpretation, or silent ignoring of the principle. If a principle itself needs to change, that must occur in a separate, explicit constitution update outside `/sdd.analyze`.

## Execution Steps

### 1. Initialize Analysis Context

Run `{SCRIPT}` once from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS. Derive absolute paths:

- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md

Abort with an error message if any required file is missing (instruct the user to run missing prerequisite command).
For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Load Artifacts (Progressive Disclosure)

Load only the minimal necessary context from each artifact:

**From spec.md:**

- Overview/Context
- Functional Requirements
- Non-Functional Requirements
- User Stories
- Edge Cases (if present)

**From plan.md:**

- Architecture/stack choices
- Contract / data-model / verification design references when present
- Phases
- Technical constraints

**From tasks.md:**

- Task IDs
- Execution scopes (`GLOBAL`, `IFxx`)
- `Task DAG`
- Descriptions and completion anchors
- Referenced requirement / verification refs when present
- Referenced file paths

**From supporting planning artifacts (load only when needed for Stage 3 consistency checks):**

- `contracts/` for canonical interface semantics
- `data-model.md` for global object / invariant / transition semantics
- `test-matrix.md` for main/exception path anchors
- `interface-details/` for per-operation behavior text, sequence diagrams, and UML class diagrams

**From constitution:**

- Load `/memory/constitution.md` for principle validation

### 3. Build Semantic Models

Create internal representations (do not include raw artifacts in output):

- **Requirements inventory**: Each functional + non-functional requirement with a stable key (derive slug based on imperative phrase; e.g., "User can upload file" → `user-can-upload-file`)
- **User story/action inventory**: Discrete user actions with acceptance criteria
- **Task coverage mapping**: Map each task to one or more requirements or stories (inference by keyword / explicit reference patterns like IDs or key phrases)
- **Constitution rule set**: Extract principle names and MUST/SHOULD normative statements

### 4. Detection Passes (Token-Efficient Analysis)

Focus on high-signal findings. Limit to 50 findings total; aggregate remainder in overflow summary.

#### A. Duplication Detection

- Identify near-duplicate requirements
- Mark lower-quality phrasing for consolidation

#### B. Ambiguity Detection

- Flag vague adjectives (fast, scalable, secure, intuitive, robust) lacking measurable criteria
- Flag unresolved placeholders (TODO, TKTK, ???, `<placeholder>`, etc.)

#### C. Underspecification

- Requirements with verbs but missing object or measurable outcome
- User stories missing acceptance criteria alignment
- Tasks referencing files or components not defined in spec/plan

#### D. Constitution Alignment

- Any requirement or plan element conflicting with a MUST principle
- Missing mandated sections or quality gates from constitution

#### E. Coverage Gaps

- Requirements with zero associated tasks
- Tasks with no mapped requirement/story
- Non-functional requirements not reflected in tasks (e.g., performance, security)

#### F. Inconsistency

- Terminology drift (same concept named differently across files)
- Data entities referenced in plan but absent in spec (or vice versa)
- Task ordering contradictions (e.g., integration tasks before foundational setup tasks without dependency note)
- Conflicting requirements (e.g., one requires Next.js while other specifies Vue)

#### G. Audit Hygiene

- Unnecessary traceability payload embedded in design/execution artifacts
- Repeated audit requirements that should be handled in `/sdd.analyze`, not in plan or implement instructions
- Optional references presented as blocking requirements without execution need

#### H. Stage 3 Diagram Drift

- Invented participant / class / method symbols in `interface-details/` despite available repository anchors
- Sequence diagrams missing required exception / guard-failure branches from `Behavior Paths` when they affect contract-visible behavior
- UML diagrams containing only layered placeholders or classes with no operation-relevant members / constraints
- Diagram content contradicting `contracts/`, `data-model.md`, or `test-matrix.md`
- Interface detail prose and diagrams disagreeing on method names, participants, or responsibilities

### 5. Severity Assignment

Use this heuristic to prioritize findings and separate blocking issues from optional cleanliness work:

- **Blocking**: Missing execution-critical inputs, contract contradictions, constitution MUST violations, or uncovered MUST requirements that block baseline functionality
- **Non-Blocking**: Naming drift, missing optional references, over-verbose traceability sections, or minor wording/structure issues
- **CRITICAL**: Violates constitution MUST, contract contradiction, diagram contradiction that changes contract-visible behavior, missing execution-critical input, or uncovered MUST requirement blocking baseline functionality
- **HIGH**: Duplicate or conflicting requirement, ambiguous security/performance attribute, untestable acceptance criterion, missing required Stage 3 exception/guard branch, or task model contradiction that can derail implementation
- **MEDIUM**: Terminology drift, missing non-functional task coverage, underspecified edge case, placeholder Stage 3 diagrams, or over-verbose traceability payload
- **LOW**: Style/wording improvements, optional reference cleanup, minor redundancy not affecting execution order

### 6. Produce Compact Analysis Report

Output a Markdown report (no file writes) with the following structure:

## Specification Analysis Report

| ID | Category | Impact | Severity | Location(s) | Summary | Recommendation |
|----|----------|--------|----------|-------------|---------|----------------|
| A1 | Duplication | Non-Blocking | HIGH | spec.md:L120-134 | Two similar requirements ... | Merge phrasing; keep clearer version |

(Add one row per finding; generate stable IDs prefixed by category initial.)

**Coverage Summary Table:**

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|

**Constitution Alignment Issues:** (if any)

**Unmapped Tasks:** (if any)

**Metrics:**

- Total Requirements
- Total Tasks
- Coverage % (requirements with >=1 task)
- Ambiguity Count
- Duplication Count
- Critical Issues Count

### 7. Provide Next Actions

At end of report, output a concise Next Actions block:

- If CRITICAL issues exist: Recommend resolving before `/sdd.implement`
- If only LOW/MEDIUM: User may proceed, but provide improvement suggestions
- Provide explicit command suggestions: e.g., "Run `/sdd.specify` with refinement", "Run `/sdd.plan` to adjust architecture", "Manually edit `tasks.md` to add coverage for 'performance-metrics'"
- Frame this command as the dedicated audit pass before implementation, not as a generic extra validation step

### 8. Offer Remediation

Ask the user: "Would you like me to suggest concrete remediation edits for the top N issues?" (Do NOT apply them automatically.)

## Operating Principles

### Context Efficiency

- **Minimal high-signal tokens**: Focus on actionable findings, not exhaustive documentation
- **Progressive disclosure**: Load artifacts incrementally; don't dump all content into analysis
- **Token-efficient output**: Limit findings table to 50 rows; summarize overflow
- **Deterministic results**: Rerunning without changes should produce consistent IDs and counts

### Analysis Guidelines

- **NEVER modify files** (this is read-only analysis)
- **NEVER hallucinate missing sections** (if absent, report them accurately)
- **Prioritize constitution violations** (these are always CRITICAL)
- **Treat this command as the single concentrated audit step** for cross-artifact drift and duplicated governance overhead
- **Use examples over exhaustive rules** (cite specific instances, not generic patterns)
- **Report zero issues gracefully** (emit success report with coverage statistics)

## Context

{ARGS}

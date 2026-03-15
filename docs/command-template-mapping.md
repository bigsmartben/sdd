# Command-Template Mapping

## Purpose

This document is the sole consolidated description of:

- command versus template responsibility split
- main-flow artifact ownership
- vertical command ownership for audit and checklist work

This document replaces the prior refactor baseline document.

## Core Principles

- Commands orchestrate workflow, load context, and enforce stage boundaries.
- Templates define artifact shape, section structure, and writing constraints.
- One command may consume multiple templates.
- Main-flow artifacts must not absorb audit, traceability, or checklist responsibilities.
- Authoritative artifacts own semantics; summaries, projection notes, inline mappings, caches, and other derived views are disposable navigation aids only.
- When a derived view conflicts with or lags behind its source artifact, commands must return to the authoritative source slice before producing downstream output.
- Responsibilities must not expand across stage boundaries.
- Prompts should stay concise and effective; remove material that biases downstream work.

## Authority Model

| Artifact / View | Primary Role | Authority Level |
| --- | --- | --- |
| `memory/constitution.md` | Project-wide principles, terminology boundaries, governance rules | Authoritative |
| `spec.md` | Feature business semantics and user-visible requirements | Authoritative |
| `research.md`, `data-model.md`, `test-matrix.md`, `contracts/`, `interface-details/` | Planning-stage design semantics within their defined scopes | Authoritative within scope |
| `plan.md` | Planning summary and downstream projection ledger | Derived view |
| `tasks.md` | Execution mapping and DAG scheduling authority | Authoritative for execution order; derived for upstream semantics |
| internal extraction tables / tuple maps / caches / summaries | Context reduction and navigation | Derived view |

Authority rules:

- Derived views may speed retrieval or navigation, but they MUST NOT redefine upstream semantics.
- `Task DAG` remains the execution authority inside `tasks.md`; task prose and inline predecessor mirrors do not outrank it.
- `plan.md` does not supersede the stage artifacts it summarizes.
- `tasks.md` does not supersede `spec.md`, `contracts/`, `data-model.md`, or `test-matrix.md` for semantics.

## Mapping Overview

| Command | Command Role | Template(s) | Primary Output(s) |
| --- | --- | --- | --- |
| `/sdd.specify` | Generate and refine business-facing specifications | `spec-template.md` | `spec.md` |
| `/sdd.plan` | Orchestrate staged planning | `plan-template.md` plus `research-template.md`, `data-model-template.md`, `test-matrix-template.md`, `contract-template.md`, and `interface-detail-template.md` | `plan.md`, `research.md`, `data-model.md`, `test-matrix.md`, `contracts/`, `interface-details/` |
| `/sdd.tasks` | Convert approved planning artifacts into executable work mapping | `tasks-template.md` | `tasks.md` |
| `/sdd.implement` | Execute tasks against the approved design set | N/A | Implementation progress and completion output |
| `/sdd.checklist` | Generate vertical checklist output | `checklist-template.md` | `checklists/*.md` |
| `/sdd.analyze` | Run vertical audit and consistency analysis | N/A | Analysis report output |

## /sdd.specify

- Command role: generate and refine the business-facing specification.
- Template role: `spec-template.md` defines the structure of the specification artifact.
- Output role: `spec.md` holds business semantics and user-visible requirements.
- Exclusion: no technical planning, no audit payload, and no implementation choreography.

## /sdd.plan

- Command role: orchestrate staged planning.
- Template role:
  - `plan-template.md` defines the generated `plan.md` skeleton.
  - `research-template.md` defines `research.md`.
  - `data-model-template.md` defines `data-model.md`.
  - `test-matrix-template.md` defines `test-matrix.md`.
  - `contract-template.md` defines each contract artifact in `contracts/`.
  - `interface-detail-template.md` defines each per-operation detail artifact in `interface-details/`.
- Planning outputs:
  - `plan.md`
  - `research.md`
  - `data-model.md`
  - `test-matrix.md`
  - `contracts/`
  - `interface-details/`

Planning rules:

- `test-matrix.md` remains in the planning flow.
- `test-matrix.md` is software test design refinement for `spec.md`.
- `test-matrix.md` is not an audit, traceability, or governance ledger.
- `data-model.md` is UML-first.
- `interface-details` is centered on field semantics, sequence diagrams, and UML class diagrams.

## Planning Artifact Traits

### `research.md`

- records decisions
- records reuse anchors
- records constraints
- records only blocking open questions

### `data-model.md`

- UML-first backbone artifact with concrete reusable semantics, not abstract placeholder prose
- explicitly defines scope/non-goals for Stage 1 boundaries
- includes a domain inventory of shared elements with kind, repository anchors, global responsibility, and globally stable fields only
- groups backbone responsibilities and relationships by domain/subdomain (ownership, composition, projection, derivation, dependency)
- defines cross-operation shared invariants as normative `INV-###` rules with applicability and anchors
- captures aggregate/entity lifecycle anchors using state field, stable states, allowed transitions, and forbidden transitions
- includes backbone UML that shows core classes/interfaces, key stable fields, and labeled relationships
- concrete enough to support downstream `contract-template.md` and `interface-detail-template.md` reuse
- remains backbone-only: no per-operation spillover, no field-complete DTO modeling, no implementation-layer expansion, no persistence schema design

### `test-matrix.md`

- scenario-oriented software test design supplement
- covers main, branch, exception, and degraded scenarios
- contains no audit tables
- contains no traceability expansion

### `contracts/`

- minimum external I/O only
- defines success and failure semantics
- defines preconditions, postconditions, and visible side effects
- contains no internal projections or sequence/UML design

### `interface-details/`

- defines field semantics
- defines sequence diagrams
- defines UML class design
- defines upstream references
- reuses and extends `data-model.md` vocabulary in UML
- does not expand into behavior ledgers or verification notes

## /sdd.tasks

- Command role: turn approved planning artifacts into executable work mapping.
- Template role: `tasks-template.md` defines the structure of the task document.
- Output role: `tasks.md` is execution mapping only.
- Rule: it consumes upstream semantics but must not redefine them.
- Rule: it may consume `test-matrix.md` as test-design input, not as audit material.

## /sdd.implement

- Command role: execute tasks against the approved upstream design set.
- No template split is required here in this document.
- Rule: it must not backfill missing design-stage responsibilities.
- Rule: it consumes `tasks.md` plus upstream artifacts, but does not redefine planning outputs.

## /sdd.checklist

- Command role: vertical checklist generation.
- It owns checklist-style verification work.
- It remains outside the main planning flow.
- It must not push checklist burden back into `spec.md`, `plan.md`, `data-model.md`, `contracts/`, or `interface-details/`.

## /sdd.analyze

- Command role: vertical audit and consistency analysis.
- It owns:
  - traceability checks
  - drift detection
  - contradiction checks
  - boundary violations
- It remains the place where audit concerns are centralized.
- Those concerns must not be embedded back into the main planning artifacts.

## Non-Goals

- no command aliases
- no compatibility shims
- no navigation or supporting-doc sync in this slice
- no prompt or template edits in this slice
- no test updates in this slice
- no expansion of responsibilities across stages

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
- Repo semantic evidence for `/sdd.plan` comes from source anchors plus engineering assembly facts; constitution is rule authority and MUST NOT be treated as component-boundary evidence.
- Repository-first projections are canonical only under `.specify/memory/repository-first/`; feature-local copies are derived views only.
- Authoritative artifacts own semantics; summaries, projection notes, inline mappings, caches, and other derived views are disposable navigation aids only.
- When a derived view conflicts with or lags behind its source artifact, commands must return to the authoritative source slice before producing downstream output.
- Responsibilities must not expand across stage boundaries.
- Prompts should stay concise and effective; remove material that biases downstream work.

## Authority Model

| Artifact / View | Primary Role | Authority Level |
| --- | --- | --- |
| `.specify/memory/constitution.md` | Project-wide principles, terminology boundaries, governance rules (rule authority, not component-boundary evidence) | Authoritative |
| `.specify/memory/repository-first/*` | Canonical repository-first dependency/boundary/invocation projections | Authoritative |
| `spec.md` | Feature business semantics and user-visible requirements | Authoritative |
| `research.md`, `data-model.md`, `test-matrix.md`, `contracts/`, `interface-details/` | Planning-stage design semantics within their defined scopes | Authoritative within scope |
| `plan.md` | Planning summary and downstream projection ledger | Derived view |
| `tasks.md` | Execution mapping and DAG scheduling authority | Authoritative for execution order; derived for upstream semantics |
| `tasks.manifest.json` | machine-readable sidecar projection of `tasks.md` runtime metadata | Derived view |
| internal extraction tables / tuple maps / caches / summaries | Context reduction and navigation | Derived view |

Authority rules:

- Derived views may speed retrieval or navigation, but they MUST NOT redefine upstream semantics.
- `Task DAG` remains the execution authority inside `tasks.md`; task prose and inline predecessor mirrors do not outrank it.
- `plan.md` does not supersede the stage artifacts it summarizes.
- `tasks.md` does not supersede `spec.md`, `contracts/`, `data-model.md`, or `test-matrix.md` for semantics.
- `tasks.manifest.json` is generated from `tasks.md` and must not become an independent semantic source.

## Mapping Overview

| Command | Command Role | Template(s) | Primary Output(s) |
| --- | --- | --- | --- |
| `/sdd.constitution` | Update constitution rules and refresh project-level repository-first baseline | `constitution-template.md` plus repository-first projection templates | `.specify/memory/constitution.md`, `.specify/memory/repository-first/technical-dependency-matrix.md`, `.specify/memory/repository-first/domain-boundary-responsibilities.md`, `.specify/memory/repository-first/module-invocation-spec.md` |
| `/sdd.specify` | Generate and refine business-facing specifications | `spec-template.md` | `spec.md` |
| `/sdd.plan` | Orchestrate staged planning | `plan-template.md` plus `research-template.md`, `data-model-template.md`, `test-matrix-template.md`, `contract-template.md`, `interface-detail-template.md`, and repository-first projection templates as structural contracts | `plan.md`, `research.md`, `data-model.md`, `test-matrix.md`, `contracts/`, `interface-details/` |
| `/sdd.tasks` | Convert approved planning artifacts into executable work mapping | `tasks-template.md` | `tasks.md`, `tasks.manifest.json` |
| `/sdd.implement` | Execute tasks against the approved design set | N/A | Implementation progress and completion output |
| `/sdd.checklist` | Generate vertical checklist output | `checklist-template.md` | `checklists/*.md` |
| `/sdd.analyze` | Run vertical audit and consistency analysis | N/A | Analysis report output |

## Recommended Main Flow & Gates

Recommended sequence:

`/sdd.specify` -> `/sdd.clarify` -> `/sdd.plan` -> `/sdd.tasks` -> `/sdd.analyze` -> `/sdd.implement`

Gate rules:

- Clarification-first gate: `/sdd.specify` should hand off to `/sdd.clarify` first; skipping clarification is allowed only with explicit user intent and risk warning.
- Analyze-first gate: `/sdd.tasks` should hand off to `/sdd.analyze` as the default pre-implementation step.
- Implementation block gate: if `/sdd.analyze` reports CRITICAL issues, `/sdd.implement` should be treated as blocked until those issues are resolved or explicitly waived.

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
  - feature-local derived copies may include `technical-dependency-matrix.md`, `domain-boundary-responsibilities.md`, and `module-invocation-spec.md` (canonical authority remains under `.specify/memory/repository-first/`)

Planning rules:

- `test-matrix.md` remains in the planning flow.
- `test-matrix.md` is software test design refinement for `spec.md`.
- `test-matrix.md` is not an audit, traceability, or governance ledger.
- `plan.md` carries planning-stage summary and downstream projection only; it must not absorb audit, coverage-accounting, or traceability payload.
- `data-model.md` is UML-first.
- `interface-details` is centered on field semantics, sequence diagrams, and UML class diagrams.
- `/sdd.constitution` owns creation/refresh of repository-first canonical projections in `.specify/memory/repository-first/`.
- dependency-matrix canonical baseline is built from build-manifest auto-detection (`pom.xml`, `package.json`, `pyproject.toml` + requirements/lock hints, `go.mod`).
- `/sdd.plan` MUST consume canonical repository-first projections and fail-fast to `/sdd.constitution` when they are missing/stale.

## Planning Artifact Traits

### `research.md`

- records decisions
- records source-code reuse anchors only
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
- keeps only minimum downstream binding references
- contains no internal projections or sequence/UML design
- contains no audit or traceability ledger

### `interface-details/`

- defines field semantics
- defines sequence diagrams
- defines UML class design
- defines upstream references
- reuses and extends `data-model.md` vocabulary in UML
- does not expand into behavior ledgers or verification notes

## /sdd.tasks

- Command role: turn approved planning artifacts into executable work mapping, Task DAG synthesis, and manifest projection.
- Template role: `tasks-template.md` defines the structure of the task document.
- Output role: `tasks.md` is execution mapping and DAG scheduling authority only; `tasks.manifest.json` is its machine-readable runtime projection.
- `GLOBAL` and `Interface Delivery Units` are execution packages; interface delivery units are IF-scoped work packages.
- Rule: generation loop is `Discover -> Generate -> Compress`; checks inside `/sdd.tasks` are limited to hard execution safety gates required for schedulable task output.
- Rule: `tasks.manifest.json` must be generated/refreshed together with `tasks.md` and must not add independent semantics.
- Rule: it consumes upstream semantics but must not redefine them.
- Rule: it may consume `test-matrix.md` as test-design input, not as audit material.
- Rule: it must not reopen research, data-model, contract, or interface-detail design.
- Rule: it must not absorb comprehensive implementation-readiness audit responsibilities (coverage completeness, ambiguity sweeps, terminology/diagram drift detection, repo-anchor misuse, audit hygiene, or cross-artifact contradiction analysis).
- Rule: it must not absorb comprehensive audit responsibilities.
- Rule: default handoff should route to `/sdd.analyze` before implementation.

## /sdd.implement

- Command role: execute tasks against the approved upstream design set.
- No template split is required here in this document.
- Rule: it must not backfill missing design-stage responsibilities.
- Rule: it prefers `tasks.manifest.json` for runtime scheduling metadata and falls back to `tasks.md` when manifest is missing/invalid.
- Rule: it consumes `tasks.md` plus upstream artifacts, but does not redefine planning outputs.
- Rule: when no evidence of a completed `/sdd.analyze` run exists for current task artifacts, implementation should emit an analyze-first blocking warning and route the user back to `/sdd.analyze`.

## /sdd.checklist

- Command role: vertical checklist generation.
- It owns checklist-style verification work.
- It remains outside the main planning flow.
- It must not push checklist burden back into `spec.md`, `plan.md`, `data-model.md`, `contracts/`, or `interface-details/`.

## /sdd.analyze

- Command role: vertical implementation-readiness audit and consistency analysis.
- It owns comprehensive non-mainline implementation-readiness/audit responsibilities, including:
- It owns comprehensive non-mainline audit responsibilities.
  - coverage completeness checks
  - ambiguity sweeps
  - terminology/diagram drift detection
  - repo-anchor misuse checks
  - helper-doc leakage checks
  - audit-payload / audit hygiene checks
  - cross-artifact contradiction checks
  - boundary violations
- It remains the place where audit concerns are centralized.
- Those concerns must not be embedded back into `/sdd.tasks` or other main-flow generation artifacts.
- CRITICAL findings from `/sdd.analyze` act as a pre-implementation blocking signal until resolved or explicitly waived.

## Non-Goals

- no command aliases
- no compatibility shims
- no navigation or supporting-doc sync in this slice
- no prompt or template edits in this slice
- no test updates in this slice
- no expansion of responsibilities across stages

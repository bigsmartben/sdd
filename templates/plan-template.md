# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

## Summary

[Brief summary of the feature, technical direction, and planning intent]

This document is the planning-stage summary only. Detailed authoring structure for `research.md`, `data-model.md`, `test-matrix.md`, `contracts/`, and `interface-details/` lives in the sibling planning templates under `templates/`. Use this file to compress stage outcomes into short downstream projection notes so later stages can reuse stable anchors without replaying full artifact bodies.

## Workflow Loop

- `Clarify`: [What needed clarification during planning]
- `Generate`: [What was produced from clarified inputs]
- `Boundary Check`: [How stage responsibilities were kept separate]
- `Compress`: [What downstream projection conclusions, stable terms, IDs, constraints, and blockers were carried forward]

## Technical Context

**Language/Version**: [e.g., Python 3.11, Java 21, TypeScript 5.x or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, Spring Boot, React or NEEDS CLARIFICATION]  
**Storage**: [e.g., PostgreSQL, files, N/A]  
**Testing**: [e.g., pytest, JUnit, Vitest or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, browser, mobile or NEEDS CLARIFICATION]  
**Project Type**: [e.g., web service, CLI, library, mobile app or NEEDS CLARIFICATION]  
**Performance Goals**: [domain-specific goals or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific constraints or NEEDS CLARIFICATION]  
**Scale/Scope**: [expected scale or NEEDS CLARIFICATION]

## Constitution Check

[Summarize constitution-aligned constraints and their planning impact]

## Stage 0 Research

### Inputs

- `spec.md`
- user input
- repository evidence
- constitution

### Outputs

- `research.md`

### Focus

[Research scope, decisions, and downstream constraints]

### Boundary Notes

[How this stage stayed within research scope]

### Downstream Projection

[3-7 bullets only: projected conclusions, canonical terms, stable IDs, hard constraints, and unresolved blockers needed by later stages]

## Stage 1 Data Model

### Inputs

- `spec.md`
- `research.md`

### Outputs

- `data-model.md`

### Focus

[Backbone-only but concrete: identify shared domain elements with repository anchors, globally stable fields only, grouped ownership/composition/projection/derivation/dependency relationships, cross-operation shared invariants (`INV-###`), and aggregate/entity lifecycle anchors (state field, stable states, allowed/forbidden transitions)]

### Boundary Notes

[Stayed backbone-only while still concrete enough for downstream reuse: no full DTO inventories, no implementation layering, no persistence schema/table/index design, and no per-operation behavior/sequence details]

### Downstream Projection

[3-7 bullets only: projected conclusions, canonical terms, stable IDs, invariants, lifecycle anchors, and blockers needed by later stages]

## Stage 2 Feature Verification Design

### Inputs

- `spec.md`
- `research.md`
- `data-model.md`

### Outputs

- `test-matrix.md`

### Focus

[Feature-level path coverage across main, branch, exception, and degraded paths]

### Boundary Notes

[How this stage stayed out of contract field design and interface internals]

### Downstream Projection

[3-7 bullets only: projected conclusions, stable tuple keys, scenario anchors, path coverage decisions, and blockers needed by later stages]

## Stage 3 Contracts

### Inputs

- `spec.md`
- `research.md`
- `data-model.md`
- `test-matrix.md`

### Outputs

- `contracts/`

### Focus

[Minimum external I/O, success/failure semantics, preconditions, postconditions, visible side effects]

### Boundary Notes

[How this stage stayed out of internal implementation detail]

### Downstream Projection

[3-7 bullets only: projected conclusions, stable contract bindings, visible semantics, and blockers needed by later stages]

## Stage 4 Interface Detailed Design

### Inputs

- `contracts/`
- `data-model.md`
- `test-matrix.md`
- `research.md`

### Outputs

- `interface-details/`

### Focus

[Per-operation detailed design with field semantics, sequence diagrams, UML class design, upstream references, and UML vocabulary that reuses/extends data-model terms]

### Boundary Notes

[How this stage preserved upstream artifact ownership]

### Downstream Projection

[3-7 bullets only: projected conclusions, task-relevant anchors, operation bindings, and unresolved blockers for downstream consumers]

## Project Structure

### Documentation (planning stage outputs)

```text
specs/[###-feature]/
├── plan.md
├── research.md
├── data-model.md
├── test-matrix.md
├── contracts/
└── interface-details/
```

### Source Code (repository root)

```text
[Replace with the real project structure relevant to this feature]
```

**Structure Decision**: [Describe the selected structure and why it fits this feature]

## Complexity Tracking

> Fill only if constitution check has violations that must be justified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., extra service boundary] | [reason] | [why simpler option failed] |

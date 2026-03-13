# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Stage Overview

| Stage | Name | Core Goal | Primary Outputs |
|------:|------|-----------|-----------------|
| 0 | Research | Resolve unknowns and record evidence-based decisions | `research.md` |
| 1 | Data Model & Contracts | Define core model + contracts semantics (including state machine) | `data-model.md`, `contracts/`, `quickstart.md` |
| 2 | Test-Matrix Generation | Generate `test-matrix.md` as a verification design input based on spec/UIF, including normal/exception coverage and case anchors (without rewriting `spec.md`) | `test-matrix.md` (or equivalent coverage artifact) |
| 3 | Interface Detailed Design | Produce per-operation semantic projection and interface-level detailed design by binding contracts to data-model fields, invariants, and lifecycle transitions | `interface-details/*.md` |
| 4 | Agent Context Update | Update agent-specific context from current plan outputs | repository-level agent-specific context file (outside `specs/[###-feature]/`) |

## Design Terminology Boundaries

- **Data Model UML Class (`data-model.md`)**: module-interface/core-class level. Focus on core entities, relationships, constraints, and lifecycle semantics.
- **Interface Detailed Design UML Class (`interface-details/*.md`)**: detailed-design/full-class level. Focus on per-interface collaboration and implementation-level structure.
- **Sequence diagrams in Stage 3** must use **method-call-level granularity**.
- Use `contracts` terminology uniformly in downstream artifacts.
- **Interface detailed design is semantic projection**: each `interface-details/*.md` doc projects and refines only the `data-model.md` subset required by exactly one contract operation.
- **Do not redefine global model semantics in interface details**: entity identity, field meaning, relationships, invariants, and lifecycle semantics stay anchored in `data-model.md`.
- **Operation accountability must be explicit**: each interface detail doc should state which data-model fields/invariants/transitions are consumed, validated, or triggered.
- **Stage 2 UIF refinement role**: refine spec-stage UIF and cross-UC flow into a verification-oriented view for case design (`CaseID` / `TM-*` / `TC-*`).
- **Test matrix boundary**: `test-matrix.md` serves coverage and verification design only. It must not redefine requirement semantics (`spec.md`), contract semantics (`contracts/`), or global model semantics (`data-model.md`).

## Stage 1 State Machine Requirement

- `data-model.md` MUST include the business state machine when domain lifecycle/state transition exists.
- At minimum, define states, transitions, and transition guards/constraints.
- State-machine semantics belong to model/design artifacts, not governance status snapshots.
- When a state machine exists, each affected `interface-details/*.md` doc MUST explicitly map operation-level transition usage, guards/constraints, and guard-failure contract behavior.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

Check constitution-aligned constraints before Stage 0 research, and re-check after Stage 3 design.

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Stage 0 output (/speckit.plan command)
├── data-model.md        # Stage 1 output (/speckit.plan command)
├── contracts/           # Stage 1 mandatory output (/speckit.plan command, canonical contracts semantics)
├── test-matrix.md       # Stage 2 output (/speckit.plan command, if applicable)
├── interface-details/   # Stage 3 output (/speckit.plan command, one doc per contract operation with operation binding, data-model projection, invariant/transition mapping, and method-level sequencing)
├── quickstart.md        # Optional output (/speckit.plan command)
└── tasks.md             # Next stage output (/speckit.tasks command - NOT created by /speckit.plan)
```

`agent-specific context file` is a repository-level auxiliary output of Stage 4 (`/speckit.plan`) and is not stored under `specs/[###-feature]/`.

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

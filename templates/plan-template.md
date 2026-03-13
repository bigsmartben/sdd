# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/sdd.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Stage Overview

| Stage | Name | Core Goal | Primary Outputs |
|------:|------|-----------|-----------------|
| 0 | Research | Resolve unknowns and record evidence-based decisions | `research.md` |
| 1 | Data Model & Contracts | Define core model + contracts semantics (including state machine) | `data-model.md`, `contracts/`, `quickstart.md` |
| 2 | Test-Matrix Generation | Generate `test-matrix.md` as a verification design input based on spec/UIF, capturing actionable normal/exception scenarios and any downstream-needed case anchors (without rewriting `spec.md`) | `test-matrix.md` (or equivalent coverage artifact) |
| 3 | Interface Detailed Design | Produce per-operation design projections that bind contracts to the relevant data-model fields, invariants, and lifecycle transitions without turning interface docs into audit reports | `interface-details/*.md` |
| 4 | Agent Context Update | Update agent-specific context from current plan outputs | repository-level agent-specific context file (outside `specs/[###-feature]/`) |

## Design Terminology Boundaries

- **Data Model UML Class (`data-model.md`)**: spec-wide backbone coverage at module-interface/core-class level. Focus on the full class inventory materially involved in this spec, stable repo symbols, material second-party references, relationships, constraints, and lifecycle semantics; prioritize breadth over per-interface implementation detail.
- **Interface Detailed Design UML Class (`interface-details/*.md`)**: detailed-design/full-class level. Focus on per-interface collaboration and implementation-level structure.
- **Sequence diagrams in Stage 3** must use **method-call-level granularity**.
- Use `contracts` terminology uniformly in downstream artifacts.
- **Diagram source precedence**: contract behavior and operation semantics come only from `contracts/`; domain objects, fields, invariants, relationships, and transitions come only from `data-model.md`; main/exception execution paths come only from `test-matrix.md`.
- **Repository symbol reuse first**: if relevant repository participants, classes, or methods already exist, reuse those names verbatim in prose and diagrams.
- **Greenfield naming fallback**: if no relevant repository symbols exist, choose one stable planned name per role for the bound operation and reuse it across prose, sequence diagram, and UML.
- **Interface detailed design is semantic projection**: each `interface-details/*.md` doc projects and refines only the `data-model.md` subset required by exactly one contract operation.
- **Do not redefine global model semantics in interface details**: entity identity, field meaning, relationships, invariants, and lifecycle semantics stay anchored in `data-model.md`.
- **Operation accountability must be explicit**: each interface detail doc should state which data-model fields/invariants/transitions are consumed, validated, or triggered.
- **Path accountability should be practical**: reference `CaseID` / `TM-*` / `TC-*` anchors only when they clarify behavior, enforcement, or verification intent.
- **Behavior Paths authority**: `## Behavior Paths` is the authoritative local source for sequence-diagram message flow.
- **Projection authority**: `## Scope & Projection` plus `## Invariants & Transition Responsibilities` are the authoritative local source for UML class/member selection; `## Scope & Projection` should flatten the projection into one list-style view rather than fragment it into mini-sections.
- **Stage 2 UIF refinement role**: refine spec-stage UIF and cross-UC flow into a verification-oriented view for case design (`CaseID` / `TM-*` / `TC-*`).
- **Test matrix boundary**: `test-matrix.md` serves coverage and verification design only. It must not redefine requirement semantics (`spec.md`), contract semantics (`contracts/`), or global model semantics (`data-model.md`).

## Stage 3 Interface Detail Anchors (Recommended)

For each `interface-details/*.md` doc, prefer concrete anchors only when they clarify behavior, enforcement, or verification (avoid opaque placeholders when possible):

- Contract anchor: `operationId` (or equivalent unique contract operation key)
- Data-model anchors: `Entity`, `Entity.field`, invariant IDs, transition IDs (when applicable)
- Test anchors: key `CaseID` / `TM-*` / `TC-*` for main and major exception paths
- References: related spec/contracts/data-model/test-matrix links

If a dimension is truly not applicable, provide explicit reason + nearest upstream anchor (instead of bare `N/A`).

## Stage 3 Interface Detail Content Depth Rules (Required)

For each `interface-details/*.md` doc, ensure content is implementation-informative (not only structural placeholders):

- **Field projection depth**: include operation-relevant key fields across input/validation/read/write/output/internal-use dimensions; avoid ultra-thin projection with only 1-2 superficial fields unless justified.
- **Projection presentation discipline**: keep `## Scope & Projection` as one flat bullet-list projection view. Do not split the same projection into local mini-sections such as `In-scope entities`, `Field projection`, and `Relationship projection` unless absolutely required for readability.
- **Invariant/transition accountability depth**: for each mapped invariant/transition, include responsibility type (establish/validate/preserve), enforcement location, and contract-visible failure behavior.
- **Pre/Post condition checkability**: preconditions and postconditions should be verifiable conditions (not vague summaries).
- **Behavior path completeness**: include main success path and numbered key exception/error paths.
- **Path mapping clarity**: include case anchors only when they materially aid implementation or verification.
- **Concrete naming discipline**: reuse in-repo participant/class/method names verbatim when available; otherwise keep one stable planned name per role across text and diagrams.
- **Sequence participant discipline**: include only operation-used participants from these buckets: external actor/caller, interface boundary/entrypoint, application/service orchestrator, domain entity/value object/policy, persistence adapter/repository, external system/gateway.
- **Sequence flow derivation**: derive call order from `## Behavior Paths`; include each main success path once; render contract-visible exception/guard-failure paths as `alt` branches; place guard checks before protected side effects; show cross-boundary side effects explicitly; use Mermaid `sequenceDiagram` with `autonumber`.
- **UML inclusion discipline**: include only operation-relevant contract DTOs, domain types, and participating application/service/repository/gateway classes.
- **UML member discipline**: fields appear only when used by the operation; methods align with sequence messages or invariant/transition enforcement; relationships stay operation-relevant; affected classes show the relevant state field and transition constraints when applicable.
- **No layered placeholder UML**: UML class design must include interface-relevant concrete fields/methods/relationships/constraints, not only layer names.
- **Sequence exception branches**: sequence design must reflect key guard-failure/error branches in addition to success flow.

## Stage 3 Interface Detail Section Skeleton (Required)

For each `interface-details/*.md` doc, use a stable section skeleton to keep outputs complete and reviewable:

1. `## Contract Binding` (operationId + contract anchor)
2. `## Scope & Projection` (single flat bullet-list view covering class/object role, relevant fields/methods/relationships, and anchors)
3. `## Invariants & Transition Responsibilities` (INV/T anchors + responsibility + failure behavior)
4. `## Preconditions / Postconditions` (checkable conditions)
5. `## Behavior Paths` (main path + numbered key exception paths; authoritative local source for sequence flow)
6. `## Sequence Diagram` (Mermaid `sequenceDiagram` with `autonumber`, method-call-level, derived from `## Behavior Paths`, includes key exception/guard-failure branches)
7. `## UML Class Design` (field-level, interface-relevant concrete structure derived from `## Scope & Projection` plus `## Invariants & Transition Responsibilities`)
8. `## Upstream References` (contract anchor plus only the spec/model/test refs actually used by the operation)

If a section is truly not applicable, keep the section and provide explicit rationale with nearest upstream anchor (never remove required sections silently).

Within `## Scope & Projection`, prefer a single flat bullet list. Each bullet should inline the projected class/object, operation role, relevant fields/methods/relationships, and anchor or source reason.

## Stage 3 Markdown Formatting Rules (Required)

- Use CommonMark-compatible Markdown with clean structure.
- Do not prepend unintended leading spaces to headings, tables, lists, and fenced code blocks.
- Keep heading levels ordered and stable; avoid heading jumps.
- Keep one list item per line; do not collapse multi-step items into wrapped mixed lines.
- Keep table structure valid (`header` + `separator` + data rows) and avoid broken rows.
- Use Mermaid for all diagrams, fenced with triple backticks and `mermaid` language tag.
- Normalize spacing before finalization (single blank line between sections, no trailing indentation).

## Stage 1 State Machine Requirement

- `data-model.md` MUST include the business state machine when domain lifecycle/state transition exists.
- At minimum, define states, transitions, and transition guards/constraints.
- State-machine semantics belong to model/design artifacts, not governance status snapshots.
- When a state machine exists, each affected `interface-details/*.md` doc MUST explicitly map operation-level transition usage, guards/constraints, and guard-failure contract behavior.

## Stage 1 Data Model Coverage Requirement

- `data-model.md` MUST include a `## UML Class Diagram` section using Mermaid `classDiagram`.
- The Stage 1 UML class diagram is the spec-wide backbone view: it MUST cover the full set of classes materially involved in this spec, not only the subset used by one interface.
- Coverage MUST include:
  - spec-defined domain entities / value objects / policies / lifecycle carriers
  - stable contract/request/response/DTO classes when they are already canonical in contracts or existing repo symbols
  - relevant first-party repository symbols already present in the codebase (for example PO/DTO/VO/service/repository/gateway names) when they anchor the planned design
  - material second-party referenced classes / facades / gateways / services that this feature depends on across module boundaries
- Breadth-first rule: Stage 1 UML should show why each class exists and how classes relate, but it should not expand every operation into Stage 3 full-class design detail.
- Do not add a standalone `## Relationships` section when the UML class diagram already expresses the relationships clearly; add concise prose notes only for relationship semantics the diagram cannot express well.
- If business naming differs from stable repo symbols, record a one-to-one mapping in `data-model.md` and keep diagram naming consistent across downstream artifacts.

## Stage 3 Quality Gate (Before Finalizing Plan Outputs)

- One interface detail doc binds to one contract operation, unambiguously.
- Required sections are present and non-empty.
- Main success path and key exception paths are reflected in both behavior text and sequence design.
- UML class is field-level and interface-relevant (not only layered placeholders).
- Sequence diagram is method-call-level with concrete method names and key exception/guard-failure branches.
- Existing repo symbols are reused verbatim when available; otherwise greenfield names stay stable across prose and diagrams.
- Sequence participants are limited to real operation roles and allowed participant buckets.
- `Behavior Paths` is fully reflected in sequence design, including key exception/guard-failure branches that alter contract-visible behavior.
- Guard / invariant / transition checks appear before the protected side effects they gate.
- UML includes only operation-relevant classes with concrete members/constraints and clear reasons to appear.
- No class/member contradicts `data-model.md`; no diagram branch contradicts contract-visible failure behavior.
- Required section skeleton is preserved; non-applicable sections include explicit rationale + nearest upstream anchor.
- Upstream references stay concise and only include refs that help implementation, enforcement, or verification.
- Markdown structure renders correctly in preview (headings/lists/tables/code fences).

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
├── plan.md              # This file (/sdd.plan command output)
├── research.md          # Stage 0 output (/sdd.plan command)
├── data-model.md        # Stage 1 output (/sdd.plan command)
├── contracts/           # Stage 1 mandatory output (/sdd.plan command, canonical contracts semantics)
├── test-matrix.md       # Stage 2 output (/sdd.plan command, if applicable)
├── interface-details/   # Stage 3 output (/sdd.plan command, one doc per contract operation with implementation-serving design projection and concise upstream references)
├── quickstart.md        # Optional output (/sdd.plan command)
└── tasks.md             # Next stage output (/sdd.tasks command - NOT created by /sdd.plan)
```

`agent-specific context file` is a repository-level auxiliary output of Stage 4 (`/sdd.plan`) and is not stored under `specs/[###-feature]/`.

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

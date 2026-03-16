# Module Invocation Spec: [PROJECT]

**Projection Type**: Repository-First Projection  
**Canonical Path**: `.specify/memory/repository-first/module-invocation-spec.md`  
**Primary Inputs**: Real module layering + governance signals from `.specify/memory/repository-first/technical-dependency-matrix.md`

Use this artifact to define module invocation constraints.
Rules in this document MUST use normative language (`MUST`/`SHOULD`/`MUST NOT`).

## Allowed Direction

Define allowed invocation directions according to real module layering
(`web/service/manager/dao/api/common` or repository-equivalent).

| From Module Layer | To Module Layer | Rule | Rationale |
|-------------------|-----------------|------|-----------|
| [web] | [service] | [MUST invoke only through service boundary] | [Layering constraint] |
| [service] | [manager] | [SHOULD use manager for orchestration paths] | [Orchestration constraint] |
| [manager] | [dao] | [MUST use dao for persistence access] | [Persistence boundary] |
| [service] | [api/common] | [MAY use shared contracts/utilities with stable boundary] | [Shared contract rationale] |

## Forbidden Direction

Define invocation directions that are prohibited.

| From Module Layer | To Module Layer | Rule | Violation Risk |
|-------------------|-----------------|------|----------------|
| [web] | [dao] | [MUST NOT bypass service/manager boundary] | [Boundary collapse / transaction inconsistency] |
| [dao] | [web] | [MUST NOT depend on presentation layer] | [Inverted dependency] |
| [common] | [web/service/manager/dao] | [SHOULD avoid upward business coupling] | [Shared layer contamination] |

## Dependency Governance Rules

These rules MUST consume version-divergence and `unresolved` signals from `.specify/memory/repository-first/technical-dependency-matrix.md`.

| Rule ID | Trigger Signal (from matrix) | Governance Rule | Required Action |
|---------|------------------------------|-----------------|-----------------|
| [DG-001] | [version-divergence on dependency G:A] | [MUST prevent new cross-layer invocations that increase divergence surface] | [Unify version source or document exception] |
| [DG-002] | [`unresolved` version source] | [MUST block dependency-driven invocation expansion until resolved] | [Resolve manifest source and re-validate] |
| [DG-003] | [high-risk scope usage across boundary] | [SHOULD constrain invocation to approved adapter boundary] | [Add explicit adapter path and justification] |

## Boundary Notes

- This artifact defines invocation governance only; it does not replace dependency facts from `.specify/memory/repository-first/technical-dependency-matrix.md`.
- This artifact does not redefine domain responsibilities from `.specify/memory/repository-first/domain-boundary-responsibilities.md`.

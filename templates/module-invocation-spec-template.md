# Module Invocation Spec: [PROJECT]

**Projection Type**: Repository-First Projection  
**Canonical Path**: `.specify/memory/repository-first/module-invocation-spec.md`  
**Primary Inputs**: Real module layering + governance signals from `.specify/memory/repository-first/technical-dependency-matrix.md`

## Artifact Quality Signals

- Must: read like concrete module-governance rules for the real repository.
- Must not: drift into speculative future edges, abstract layer essays, or dependency-fact duplication.
- Strictly: every rule must map to a concrete module edge or existing matrix signal.

Use this artifact to define module invocation constraints.
Rules in this document MUST use normative language (`MUST`/`SHOULD`/`MUST NOT`).
Allowed and forbidden direction tables MUST cover the concrete first-party module edges found in the target runtime repo.
Do not collapse unmatched edges into broad grouped rows unless every covered edge shares the same rule and rationale.

## Allowed Direction

Define allowed invocation directions according to real module layering
(`web/service/manager/dao/api/common` or repository-equivalent).

| From Module | To Module | Layer View | Rule | Rationale |
|-------------|-----------|------------|------|-----------|
| [aidm-web] | [aidm-service] | [web -> service] | [MUST invoke only through service boundary] | [Layering constraint] |
| [aidm-service] | [aidm-manager] | [service -> manager] | [SHOULD use manager for orchestration paths] | [Orchestration constraint] |
| [aidm-manager] | [aidm-dao] | [manager -> dao] | [MUST use dao for persistence access] | [Persistence boundary] |
| [aidm-service] | [aidm-api] | [service -> api] | [MAY use shared contracts through a stable boundary] | [Shared contract rationale] |

## Forbidden Direction

Define invocation directions that are prohibited.
Every observed first-party cross-module edge MUST be represented as allowed or forbidden.

| From Module | To Module | Layer View | Rule | Violation Risk |
|-------------|-----------|------------|------|----------------|
| [aidm-web] | [aidm-dao] | [web -> dao] | [MUST NOT bypass service/manager boundary] | [Boundary collapse / transaction inconsistency] |
| [aidm-dao] | [aidm-web] | [dao -> web] | [MUST NOT depend on presentation layer] | [Inverted dependency] |
| [aidm-common] | [aidm-service] | [common -> service] | [SHOULD avoid upward business coupling] | [Shared layer contamination] |

## Dependency Governance Rules

These rules MUST consume version-divergence and `unresolved` signals from `.specify/memory/repository-first/technical-dependency-matrix.md`.
Every governance rule MUST reference an existing `SIG-*` row from the matrix or an explicit matrix fact summary; do not emit speculative future-signal rows.
Use concise reasoning facts (`trigger fact -> governance action`) and avoid restating full matrix content.

| Rule ID | Trigger Signal (from matrix) | Governance Rule | Required Action |
|---------|------------------------------|-----------------|-----------------|
| [DG-001] | [existing `SIG-*` row] | [MUST prevent new cross-layer invocations that increase divergence surface] | [Unify version source or document exception] |

## Boundary Notes

- This artifact defines invocation governance only; it does not replace dependency facts from `.specify/memory/repository-first/technical-dependency-matrix.md`.

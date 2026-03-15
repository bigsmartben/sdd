# Data Model: [FEATURE]

**Stage**: Stage 1 Data Model
**Inputs**: `spec.md`, `research.md`

Use this artifact to define the reusable global backbone model for planning outputs. It should explain what shared domain elements exist, how they relate, which rules and lifecycle anchors govern them, and what downstream authors must treat as globally stable. The content must be concrete enough to support downstream `contracts/` and `interface-details/` authoring while remaining backbone-only.

## Model Overview

Use this section to establish the overall shape of the model before filling in details.

### This file should answer

- What shared domain elements and vocabulary must remain consistent across operations
- Which globally stable fields, relationships, and derivations form the backbone model
- What cross-operation invariants and lifecycle anchors downstream artifacts must respect
- Which core classes/interfaces should appear in the backbone UML

### This file defines

- Shared domain elements and vocabulary reused across operations
- Backbone ownership/composition/projection/derivation/dependency relationships
- Cross-operation invariants in normative rule form (`INV-###`)
- Aggregate/entity lifecycle anchors needed for global semantic consistency
- Core UML classes/interfaces with globally stable fields and labeled relationships

### This file does not define

- Full DTO field inventories or per-operation request/response payload details
- Implementation-layer decomposition (service/repository/module/class internals)
- Persistence schema/table/index mappings
- Operation-local behavior flows, sequence-level logic, or verification matrix design

## Domain Inventory

List only elements that carry shared planning semantics. Prefer existing repository symbols as anchors when available. Capture only globally stable fields here.

| Domain Element | Kind | Repository Anchor | Global Responsibility | Globally Stable Fields Only |
|----------------|------|-------------------|-----------------------|-----------------------------|
| `[OrderAggregate]` | `Aggregate` | ``src/domain/order.py::OrderAggregate`` | [Backbone responsibility shared across operations] | `[id, customerId, status, version]` |
| `[PaymentPolicy]` | `Domain Service / Policy` | ``src/domain/payment_policy.py::PaymentPolicy`` | [Global policy responsibility] | `[policyId, policyVersion, decisionType]` |
| `[OrderSnapshotView]` | `Projection / View` | `[No anchor yet - planned in specs/[###-feature]/]` | [Shared read-model responsibility] | `[orderId, state, updatedAt]` |

## Backbone Structure

Expand the model by describing only globally significant responsibilities and links. Group by backbone domain area or subdomain.

### [Backbone Group / Subdomain A]

- **Composition**: `[AggregateA]` composes `[EntityA1, EntityA2]` because [global ownership boundary].
- **Ownership**: `[AggregateA]` owns lifecycle authority for `[EntityA1]`; external modules must not mutate `[stateField]` directly.
- **Projection**: `[ProjectionA]` is derived from `[AggregateA]` via [shared projection rule].
- **Dependency**: `[AggregateA]` depends on `[PolicyA Interface]` for [cross-operation decision semantics].

### [Backbone Group / Subdomain B]

- **Derivation**: `[DerivedValueB]` is computed from `[StableFieldX, StableFieldY]` under [global rule].
- **Association**: `[AggregateB]` references `[AggregateA]` by `[stableIdentifier]` only (no deep embedding).
- **Boundary rule**: [What can/cannot cross this group boundary at backbone level].

## Shared Invariants

Write normative rules with stable identifiers and references. Prefer rules that downstream contracts and interface details can reuse directly.

### INV-001: [Short invariant title]

- **Rule**: [Normative statement using MUST / MUST NOT / MAY]
- **Applies To**: `[Element(s) / Relationship(s)]`
- **Rationale**: [Why this is globally required]
- **Source Anchors**: `[spec.md#...], [research.md#...], [repo symbol if applicable]`

### INV-002: [Short invariant title]

- **Rule**: [Normative statement]
- **Applies To**: `[Element(s) / Relationship(s)]`
- **Rationale**: [Global semantic reason]
- **Source Anchors**: `[spec/research/repository anchors]`

## Lifecycle Anchors

Describe each globally shared lifecycle as its own section. Include only states and transitions that must remain stable across planning outputs.

### Lifecycle: [Aggregate / Entity Name]

- **State field**: `[status | phase | lifecycleState]`
- **Stable states**: `[Draft, Active, Suspended, Closed]`
- **Allowed transitions**:
  - `[Draft -> Active]` on [event/condition]
  - `[Active -> Suspended]` on [event/condition]
- **Forbidden transitions**:
  - `[Closed -> Active]` (forbidden because [global reason])
  - `[Draft -> Closed]` unless [explicit global exception]

### Lifecycle: [Second Aggregate / Entity Name]

- **State field**: `[stateField]`
- **Stable states**: `[StateA, StateB, StateC]`
- **Allowed transitions**:
  - `[StateA -> StateB]` on [event/condition]
- **Forbidden transitions**:
  - `[StateC -> StateA]` (forbidden because [global reason])

## Backbone UML

Show core classes/interfaces plus globally stable fields and labeled relationships. Keep the diagram aligned with the sections above rather than introducing new model elements here.

```mermaid
classDiagram
    class AggregateA {
        +id: UUID
        +status: AggregateAStatus
        +version: int
    }

    class EntityA1 {
        +id: UUID
        +state: EntityState
    }

    class ProjectionA {
        +aggregateAId: UUID
        +status: AggregateAStatus
        +updatedAt: Instant
    }

    class PolicyA {
        <<interface>>
        +evaluate(input): Decision
    }

    AggregateA *-- EntityA1 : composes
    ProjectionA ..> AggregateA : projects-from
    AggregateA ..> PolicyA : depends-on
```

## Model Closure

Use this final section to confirm that the backbone model is coherent, complete, and ready for downstream reuse.

- Ensure the model covers the shared elements, stable fields, labeled relationships, invariants, and lifecycle anchors required by `spec.md` and `research.md`.
- Ensure the content remains backbone-only and does not expand into full DTO inventories, endpoint-by-endpoint contracts, implementation layers, persistence schema design, or interface-level sequence behavior.
- Ensure terminology, invariants, and lifecycle definitions are consistent with downstream `contract-template.md` and `interface-detail-template.md` expectations without duplicating their scope.
- If anything is still uncertain, record the gap as a source anchor or explicit assumption rather than leaving backbone semantics ambiguous.

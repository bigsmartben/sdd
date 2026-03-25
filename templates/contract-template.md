# Northbound Interface Design: [BindingRowID]

**Stage**: Stage 4 Binding-Level Interface Design Closure
**BindingRowID (Required)**: [BR-###]
**Operation ID (Required)**: [operationId]
**IF Scope (Required)**: [IF-### or N/A]
**Boundary Anchor (Required)**: [HTTP `METHOD /path` \| `event.topic` \| `Facade.method` \| `cli command` \| `ConcreteBoundary.method` \| `TODO(REPO_ANCHOR)`]
**Anchor Status (Required)**: [`existing` \| `extended` \| `new` \| `todo`]
**Boundary Anchor Strategy Evidence (Required)**: [`existing rejected: ...; extended rejected: ...` \| `N/A` when `Anchor Status (Required) != new`]
**Implementation Entry Anchor (Required)**: [`path/to/file.ext::Symbol` \| `ConcreteEntry.method` \| `TODO(REPO_ANCHOR)`]
**Implementation Entry Anchor Status (Required)**: [`existing` \| `extended` \| `new` \| `todo`]
**Implementation Entry Anchor Strategy Evidence (Required)**: [`existing rejected: ...; extended rejected: ...` \| `N/A` when `Implementation Entry Anchor Status (Required) != new`]

## Artifact Quality Signals (Normative)

- Must: be strong enough for implementation to start without reopening basics.
- Strictly: Concrete anchors only; no placeholder labels in final artifact.
- Strictly: Every major section MUST include at least one concrete evidence pointer (`spec.md` / `test-matrix.md` / `data-model.md` / repo anchor).
- Strictly: Generic claims without evidence pointers are invalid.
- `contract` is responsible for first-time production of `Boundary Anchor`, `Implementation Entry Anchor`, request/response surface, UML closure, sequence closure, and test projection for this binding.

Angle-bracket labels in the examples below are template scaffolding only and MUST be replaced before the artifact can be `done`.

This artifact is the single authoritative interface-design closure for one `BindingRowID`.
Its core outputs are fixed:

- `Interface Definition`
- `UML Class Design`
- `Sequence Design`
- `Test Projection`

`Operation ID (Required)` MUST be concrete for this binding and MUST NOT be `N/A`.

## Northbound Entry Rules (Normative)

- Allowed normative boundary-anchor forms are exactly: HTTP `METHOD /path`, event topic `event.topic`, RPC/Façade method `Facade.method`, CLI `command`, concrete boundary name `ConcreteBoundary.method`, or explicit `TODO(REPO_ANCHOR)`.
- `Boundary Anchor` MUST represent the first client-callable entry for this interaction, not an internal service/manager/mapper hop.
- If clients call an HTTP route directly, use HTTP `METHOD /path` as `Boundary Anchor` and the owning controller method as `Implementation Entry Anchor`.
- For HTTP-facing bindings, treat `Boundary Anchor` and `Implementation Entry Anchor` as two aligned views of one northbound boundary semantic: external consumer entry vs internal realization handoff.
- If clients call a stable RPC/Façade surface, use repo-backed `Facade.method` as `Boundary Anchor`.
- If both controller/HTTP and façade exist, select the consumer-visible first callable entry as normative `Boundary Anchor`.
- For first-party internal `new` anchors, prefer repository-style names such as `*Controller.method`, `*Service.method`, or `*ServiceImpl.method`; do not use `Facade` unless the anchor is explicitly modeling an adapter/external integration surface.
- `BA-*` labels are not valid normative boundary anchors.
- Apply anchor decision order `existing -> extended -> new -> todo`.
- `new` \| `todo` is only valid after explicit rejection of `existing` and `extended` with evidence.
- `extended` is valid only for same-entity field/state expansion.
- `new` is normative only when selected `spec.md` / `data-model.md` / `test-matrix.md` slices plus bounded repo reads fully close the binding design and this stage can assign one concrete repository-facing boundary/entry target for implementation.
- `new` anchors are design-final implementation targets for this binding run; they are not automatic proof that the symbol already exists in the repository at contract-generation time.
- For `new` anchors whose concrete repo symbol is not yet present in bounded repo evidence, prefer concrete design-target naming (for example `ConcreteEntry.method`) or `TODO(REPO_ANCHOR)` instead of fabricating repo file anchors.
- Use `path/to/file.ext::Symbol` for `new` anchors only when bounded repo evidence closes that path/symbol landing for this binding.
- When `Anchor Status (Required) = new`, `Boundary Anchor Strategy Evidence (Required)` MUST include explicit rejection evidence for both `existing` and `extended`.
- When `Implementation Entry Anchor Status (Required) = new`, `Implementation Entry Anchor Strategy Evidence (Required)` MUST include explicit rejection evidence for both `existing` and `extended`.
- When an anchor status is not `new`, set the corresponding strategy evidence field to `N/A`.
- If bounded evidence cannot close `existing`, `extended`, or one concrete `new` target, set the corresponding anchor field to `TODO(REPO_ANCHOR)` and status to `todo`.

## Binding Context

Purpose: fix exactly which upstream requirement-projection unit this contract closes.
Keep this section locator-oriented; do not restate full upstream prose.
Treat upstream packet scope-reference fields as binding-range inputs only. This stage finalizes `Operation ID`, boundary landing, concrete DTO naming, and realization design.
`Binding Packets` in `test-matrix.md` is the semantic authority for this section.
Do not reinterpret packet meaning locally; copy locator fields deterministically and resolve only contract-local closure fields.

| Field | Value |
|-------|-------|
| `Binding Packet Source` | [`test-matrix.md` `Binding Packets` row for selected `BindingRowID`] |
| `BindingRowID` | [BR-###] |
| `Operation ID` | [operationId] |
| `IF Scope` | [IF-### or N/A] |
| `User Intent` | [Northbound action summary] |
| `Trigger Ref(s)` | [UIP / UIF / UC refs] |
| `Request Semantics` | [Input semantics only; no DTO naming] |
| `Visible Result` | [Visible result semantics] |
| `Side Effect` | [Create / update / read / authorize / none] |
| `Boundary Notes` | [Idempotent / permission-gated / state-transitioning / N/A] |
| `Repo Landing Hint` | [Existing entry family or bounded repo hint] |
| `UIF Path Ref(s)` | [UIF path refs] |
| `UDD Ref(s)` | [UDD refs or `N/A`] |
| `Primary TM IDs` | [TM-###, TM-###] |
| `TM IDs` | [TM-###, TM-###] |
| `TC IDs` | [TC-###, TC-###] |
| `Test Scope` | [binding-scoped test coverage summary] |
| `Spec Ref(s)` | [UC / FR / UIF / UDD refs] |
| `Scenario Ref(s)` | [TM / SC refs] |
| `Success Ref(s)` | [success refs] |
| `Edge Ref(s)` | [edge / EC refs or `N/A`] |

## Interface Definition

This section is the contract authority for request/response shape and field-level semantics.
Generate it in this order:

1. `UDD Ref(s)` for user-visible field meaning
2. `data-model.md` for shared owner/source/lifecycle/invariant constraints
3. bounded repo evidence for landed naming and concrete shape

### Contract Summary

| Aspect | Definition |
|--------|------------|
| External Input | [behavior-significant external input surface] |
| Success Output | [contract-visible success output surface] |
| Failure Output | [contract-visible failure output surface] |
| Preconditions | [preconditions that must hold before execution] |
| Postconditions | [state/result guarantees after successful completion] |
| Visible Side Effects | [externally visible state change, event, or notification] |

### Shared Semantic Reuse

If the selected `BindingRowID` has no shared-semantic dependency, keep one explicit `N/A` row.

| Shared Semantic Ref | Constraint Type (Required Enum) | Applied To | Impact on Contract |
|---------------------|---------------------------------|------------|--------------------|
| [`SSE-*` / `OSA-*` / `SFV-*` / `LC-*` / `INV-*` / `DCC-*` / `N/A`] | [`shared-semantic-element` / `owner-source-alignment` / `shared-field-vocabulary` / `lifecycle-invariant` / `downstream-contract-constraint` / `none`] | [request / response / owner field / behavior path / collaborator / `N/A`] | [what must be reused and what must not be invented locally] |

### Full Field Dictionary (Operation-scoped)

This is the only authoritative field-level contract surface for the operation.
It MUST cover request DTO fields, response DTO fields, and all owner/source fields that the operation reads, writes, projects, validates, defaults, or uses for state decisions.
Classify each row as `Dictionary Tier = operation-critical|owner-residual`; list `operation-critical` rows first.
Fields not used by this operation MUST remain listed with `Used in [operationId] = no`.
If a field cannot be fully confirmed, keep the row with an explicit gap marker rather than shrinking the contract.

| Field | Owner Class | Dictionary Tier | Direction | Required/Optional | Default | Validation/Enum | Persisted | Contract-visible | Used in [operationId] | Source Anchor |
|-------|-------------|-----------------|-----------|-------------------|---------|-----------------|-----------|------------------|-----------------------|---------------|
| [fieldPath] | [RequestModel / ResponseModel / StateOwner] | [`operation-critical` / `owner-residual`] | [input / output / state / derived] | [required / optional / conditional] | [default / derivation / none / gap] | [validation rule / enum vocabulary / gap] | [yes / no / derived / gap] | [yes / no / indirect] | [yes / no] | [`path/to/file.ext::Symbol` / `new concrete field/method name` / `SSE-*` / `OSA-*` / `SFV-*` / `LC-*` / `INV-*` / `TODO(REPO_ANCHOR)`] |

## UML Class Design

This section MUST describe both class ownership and two-party package relation closure.

Mandatory rules:

- UML MUST cover `Boundary Anchor`, `Implementation Entry Anchor`, request/response models, key entity/value object ownership, and required collaborators.
- UML MUST include explicit two-party package relations; class-only diagrams are insufficient.
- UML MUST keep first-party executable participants at method-level anchors.
- Every first-party sequence participant MUST appear in UML with at least one mapped method anchor.
- For contract-visible request/response and behavior-significant fields, each field MUST have explicit UML ownership.
- Any newly introduced field/method/call not already in anchored sources MUST be explicitly marked as `new`.
- If `Boundary Anchor` / `Implementation Entry Anchor` are `new` but reuse an `existing` realization chain downstream, render both layers explicitly instead of replacing the design anchor with the nearest existing class.
- Any `new` entity/value object/state holder MUST identify owner, creator, reader, and writer closure somewhere in UML notes or field ownership rows before the artifact can be `done`.

### Resolved Type Inventory

| Role | Concrete Name | Resolution | Source / Evidence | Notes |
|------|---------------|------------|-------------------|-------|
| [`boundary-entry` / `implementation-entry` / `request-dto` / `response-dto` / `entity` / `value-object` / `service` / `collaborator` / `middleware` (when anchored) / `external-dependency`] | [`path/to/file.ext::Symbol` or concrete new name] | [`existing` / `extended` / `new`] | [spec ref / data-model ref / repo anchor / contract-local rationale] | [why this concrete name is final for this contract run] |

Use `Notes` to make layering explicit whenever `new` and `existing` types coexist in the same design:

- mark northbound design anchors as `new boundary` / `new entry`
- mark reused downstream classes as `existing realization`
- mark any operation-scoped holder such as a new set/state/value object with owner + creator + reader + writer closure

### Class Diagram

If middleware is present as a concrete first-party call anchor in Sequence, include the same middleware type and call edge in UML.

#### UML Variant A (Boundary != Entry)

```mermaid
classDiagram
    class ConcreteBoundary {
        +method(request)
    }
    class ConcreteEntry {
        +execute()
    }
    class Collaborator {
        +perform()
    }
    ConcreteBoundary --> ConcreteEntry
    ConcreteEntry --> Collaborator
```

#### UML Variant B (Boundary == Entry)

```mermaid
classDiagram
    class ConcreteBoundary {
        +method(request)
    }
    class Collaborator {
        +perform()
    }
    ConcreteBoundary --> Collaborator
```

### Two-Party Package Relations

This subsection is required.
Model the first-party package/module ownership and dependency direction explicitly.

Minimum closure requirements:

- When `Boundary Anchor != Implementation Entry Anchor`, include at least one row for `Boundary package -> Entry package` and at least one row for `Entry package -> mandatory collaborator package`.
- When `Boundary Anchor == Implementation Entry Anchor`, include at least one row for `Boundary/Entry package -> mandatory collaborator package`.

| From Package | To Package | Relation Type | Covered Classes | Reason |
|--------------|------------|---------------|-----------------|--------|
| [package/module A] | [package/module B] | [`depends-on` / `calls` / `owns-model` / `crosses-boundary`] | [Boundary / Entry / DTO / Entity / Collaborator classes] | [why this 2-party package relation is required] |

## Sequence Design

This section MUST describe the executable method-level call chain, including mandatory second-party and third-party calls, and middleware only when anchored.

Mandatory rules:

- Sequence MUST start from consumer/client entry and keep first-party hops at method-level anchors.
- When `Boundary Anchor != Implementation Entry Anchor`, the first-party handoff from boundary to entry MUST be explicit and contiguous.
- Sequence MUST be end-to-end contiguous: no broken hops, no orphan participants, and no disconnected request/response segments.
- Sequence MUST explicitly represent every mandatory second-party call anchor on the main path.
- Sequence MUST explicitly represent every mandatory third-party call anchor on the main path.
- Middleware traversal MUST appear only when a concrete middleware call anchor exists in bounded repo evidence; do not insert middleware as a default participant.
- Sequence MUST NOT merge multiple mandatory collaborators/dependencies into one synthetic participant label.
- When `new` boundary/entry anchors hand off to an `existing` realization chain, the first hop MUST remain the new anchor and the reused repo-backed chain MUST appear as a subsequent explicit handoff.
- Do not substitute the nearest `existing` controller/service for a `new` boundary when the new northbound interaction semantics are not identical.
- `opt` blocks are valid only for truly conditional branches; mandatory main-path calls MUST remain outside `opt`.
- Main success path and key failure path MUST be traceable to `Primary TM IDs` / `TM IDs` / `TC IDs`.

### Behavior Paths

| Path | Trigger | Key Steps | Outcome | Contract-Visible Failure | Sequence Ref | TM/TC Anchor |
|------|---------|-----------|---------|--------------------------|--------------|--------------|
| Main | [Trigger] | [Essential interaction steps] | [Success outcome] | [N/A or failure mode] | [S1] | [TM-### / TC-###] |
| Failure | [Trigger / branch condition] | [Essential failure steps] | [N/A] | [Failure outcome] | [Sx] | [TM-### / TC-###] |

### Sequence Diagram

#### Sequence Variant A (Boundary != Entry)

##### A1. With Anchored Middleware (Optional)

```mermaid
sequenceDiagram
    participant Initiator as "<ClientOrCaller>"
    participant Boundary as "ConcreteBoundary.method"
    participant Middleware as "<AnchoredMiddlewareSymbol>"
    participant Entry as "ConcreteEntry.method"
    participant SecondParty as "<AnchoredSecondPartyCollaborator>"
    participant ThirdParty as "<AnchoredThirdPartyDependency>"

    Initiator->>Boundary: [operation request] (S1)
    Boundary->>Middleware: ingress / middleware traversal (S2)
    Middleware->>Entry: handoff to implementation entry (S3)
    Entry->>SecondParty: required second-party call (S4)
    SecondParty->>ThirdParty: required third-party call (S5)
    ThirdParty-->>SecondParty: third-party result / ack (S6)
    SecondParty-->>Entry: second-party result / ack (S7)
    alt failure
        Entry-->>Boundary: mapped error/result handoff (S8)
        Boundary-->>Initiator: contract error response (S9)
    else success
        Entry-->>Boundary: contract response handoff (S10)
        Boundary-->>Initiator: success response (S11)
    end
```

##### A2. Without Middleware Anchor

```mermaid
sequenceDiagram
    participant Initiator as "<ClientOrCaller>"
    participant Boundary as "ConcreteBoundary.method"
    participant Entry as "ConcreteEntry.method"
    participant SecondParty as "<AnchoredSecondPartyCollaborator>"
    participant ThirdParty as "<AnchoredThirdPartyDependency>"

    Initiator->>Boundary: [operation request] (S1)
    Boundary->>Entry: method-level handoff to implementation entry (S2)
    Entry->>SecondParty: required second-party call anchor (S3)
    SecondParty->>ThirdParty: required third-party call anchor (S4)
    ThirdParty-->>SecondParty: third-party result / ack (S5)
    SecondParty-->>Entry: second-party result / ack (S6)
    alt failure
        Entry-->>Boundary: mapped error/result handoff (S7)
        Boundary-->>Initiator: contract error response (S8)
    else success
        Entry-->>Boundary: contract response handoff (S9)
        Boundary-->>Initiator: success response (S10)
    end
```

#### Sequence Variant B (Boundary == Entry)

##### B1. With Anchored Middleware (Optional)

```mermaid
sequenceDiagram
    participant Initiator as "<ClientOrCaller>"
    participant Boundary as "ConcreteBoundary.method"
    participant Middleware as "<AnchoredMiddlewareSymbol>"
    participant SecondParty as "<AnchoredSecondPartyCollaborator>"
    participant ThirdParty as "<AnchoredThirdPartyDependency>"

    Initiator->>Boundary: [operation request] (S1)
    Boundary->>Middleware: ingress / middleware traversal (S2)
    Middleware->>Boundary: continue execution (S3)
    Boundary->>SecondParty: required second-party call (S4)
    SecondParty->>ThirdParty: required third-party call (S5)
    ThirdParty-->>SecondParty: third-party result / ack (S6)
    SecondParty-->>Boundary: second-party result / ack (S7)
    alt failure
        Boundary-->>Initiator: contract error response (S8)
    else success
        Boundary-->>Initiator: success response (S9)
    end
```

##### B2. Without Middleware Anchor

```mermaid
sequenceDiagram
    participant Initiator as "<ClientOrCaller>"
    participant Boundary as "ConcreteBoundary.method"
    participant SecondParty as "<AnchoredSecondPartyCollaborator>"
    participant ThirdParty as "<AnchoredThirdPartyDependency>"

    Initiator->>Boundary: [operation request] (S1)
    Boundary->>SecondParty: required second-party call anchor (S2)
    SecondParty->>ThirdParty: required third-party call anchor (S3)
    ThirdParty-->>SecondParty: third-party result / ack (S4)
    SecondParty-->>Boundary: second-party result / ack (S5)
    alt failure
        Boundary-->>Initiator: contract error response (S6)
    else success
        Boundary-->>Initiator: success response (S7)
    end
```

## Test Projection

This section is the normalized downstream testing slice for `/sdd.tasks` and `/sdd.implement`.
`Main Pass Anchor` and `Branch/Failure Anchor(s)` are generated here from `Primary TM IDs`, `TM IDs`, `TC IDs`, `Scenario Ref(s)`, `Success Ref(s)`, `Edge Ref(s)`, and the realized interface design.

### Test Projection Slice

| IF Scope | Operation ID | Test Scope | Primary TM IDs | TM ID(s) | TC ID(s) | Main Pass Anchor | Branch/Failure Anchor(s) | Command / Assertion Signal |
|----------|--------------|------------|----------------|----------|----------|------------------|--------------------------|----------------------------|
| [IF-### or N/A] | [operationId] | [`Contract` / `Integration` / `E2E` / `Mixed`] | [TM-###, TM-###] | [TM-###, TM-###] | [TC-###, TC-###] | [primary success check inferred here] | [failure/branch checks inferred here] | [test command or assertion signal] |

### Cross-Interface Smoke Candidate (Required)

Keep exactly one row for the selected operation.
If this operation does not participate in feature-level smoke flow, keep `Candidate Role = none` with explicit `N/A` values.

| Smoke Candidate ID | IF Scope | Operation ID | Candidate Role | Depends On Candidate ID(s) | Trigger | Main Pass Anchor | Branch/Failure Anchor(s) | Command / Assertion Signal |
|--------------------|----------|--------------|----------------|----------------------------|---------|------------------|--------------------------|----------------------------|
| [SMK-###] | [IF-### or N/A] | [operationId] | [`entry` / `middle` / `exit` / `none`] | [SMK-###, SMK-### or `N/A`] | [cross-interface trigger or `N/A`] | [cross-interface success signal or `N/A`] | [degraded/failure signal or `N/A`] | [smoke command/assertion signal or `N/A`] |

## Closure Check

Keep this section short and explicit.

| Check Item | Required Evidence | Evidence Pointer(s) | Status |
|------------|-------------------|---------------------|--------|
| Interface-definition closure | request/response surface + full field dictionary + shared semantic reuse are all present | [Contract Summary rows, Field Dictionary rows, Shared Semantic Reuse rows] | [ok / gap] |
| UML closure | class diagram and two-party package relations are present, and sequence participants/method anchors are mapped consistently | [Class Diagram refs, Two-Party Package Relations rows, Resolved Type Inventory rows] | [ok / gap] |
| Sequence closure | success/failure paths are contiguous, include mandatory second-party and third-party call anchors, and include middleware only when anchored | [Behavior Paths rows, Sequence Sx refs, repo anchor evidence] | [ok / gap] |
| Test closure | `TM/TC`, pass/failure anchors, and command/assertion signal are present | [Test Projection Slice row, Smoke Candidate row, TM/TC refs] | [ok / gap] |

## Upstream References

- `spec.md`: [canonical source for UC / FR / UIF / UDD / scenario refs]
- `test-matrix.md`: [TM / TC / scenario / success / edge refs captured above]
- `data-model.md`: [shared semantic elements, owner/source alignment, field vocabulary, lifecycle/invariant, downstream contract constraints]
- repo anchors: [boundary / entry / request-response model / collaborator / dependency symbols / middleware (when anchored)]

## Boundary Notes

- Keep field completeness in `Full Field Dictionary (Operation-scoped)`.
- Keep shared owner/source/lifecycle/invariant definitions upstream in `data-model.md`; reuse them here instead of re-declaring them.
- `contract` is responsible for first-time production of `Boundary Anchor`, `Implementation Entry Anchor`, request/response surface, UML closure, sequence closure, and test projection for this binding.
- If repo evidence is insufficient for `existing` or `extended`, this stage may design concrete `new` operation-scoped boundary/entry/DTO/collaborator/dependency surfaces when they remain bounded to this binding; include middleware only when a concrete middleware anchor is available.
- `new` anchors are planning-final for this binding and MUST stay concrete, uniquely named, and consistent across Interface Definition, UML, Sequence, and Test Projection.
- If `new` anchors reuse `existing` repo-backed implementation, keep the design anchor and reused realization chain distinct instead of collapsing both into one symbol.
- Any `new` operation-scoped holder/state class must close owner, creator, reader, and writer responsibilities before the binding can be treated as design-final.
- the first hop MUST remain the new anchor and the reused repo-backed chain MUST appear as a subsequent explicit handoff.
- Sequence and UML MUST stay aligned at method-level anchors for first-party participants.
- owner, creator, reader, and writer closure MUST be explicit for any new holder/state class.
- render both layers explicitly instead of replacing the design anchor with the nearest existing class.
- If a gap is truly shared-semantic, route upstream to `/sdd.plan.data-model`.
- Do not use helper docs (`README.md`, `docs/**`, `specs/**`, generated artifacts) as repo semantic anchors.

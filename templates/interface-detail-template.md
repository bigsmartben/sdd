# Interface Detail: [operationId]

**Stage**: Stage 4 Interface Detailed Design
**Operation ID (Required)**: [operationId]
**IF Scope (Required)**: [IF-### or N/A]
**Boundary Anchor (Required)**: [HTTP `METHOD /path` \| `event.topic` \| `Facade.method` \| `cli command` \| `N/A`]
**Boundary Anchor Status (Required)**: [`existing` \| `extended` \| `new` \| `todo`]
**Implementation Entry Anchor (Required)**: [repo-backed internal handoff entry such as `Controller.method` or `Facade.method`]
**Implementation Entry Anchor Status (Required)**: [`existing` \| `extended` \| `new` \| `todo`]
**Contract Artifact (Required)**: `[contracts/<artifact>]`
**Contract Binding Row (Required)**: [Operation ID + Boundary Anchor + IF Scope tuple from contract]

Contract tuple enforcement:

- `Operation ID`, `Boundary Anchor`, and `IF Scope` MUST match the Stage 3 contract binding row exactly (value and granularity).
- `Boundary Anchor` MUST be a single normative anchor value. Do not use disjunctive wording such as `A or B`.
- Apply repo-anchor decision order `existing -> extended -> new -> todo` for both boundary/implementation entry statuses.
- `extended` is valid only for same-entity field/state expansion.
- `new` is normative only when explicit `path::symbol` target evidence is provided.
- `Implementation Entry Anchor` is an interface-detail-only internal handoff anchor and MUST be repo-backed unless explicitly blocked with `TODO(REPO_ANCHOR)` (`Implementation Entry Anchor Status = todo`).
- `Implementation Entry Anchor` may differ from `Boundary Anchor`, but it must be reachable from the contract-visible entry path.

Use one detail document per contract operation. Prefer the file name `<operationId>.md` whenever the operation has a stable identifier.
Keep this document operation-local and minimal: include only contract-visible or state-transition-relevant fields, materially distinct behavior paths, and the smallest complete handoff set needed to explain how the contract entry is realized.

## Upstream References

- `spec.md`: [relevant FR / UC / UIF refs]
- `contracts/`: [contract artifact and operation binding; tuple must match exactly]
- `data-model.md`: [shared entities, invariants, lifecycle anchors]
- `test-matrix.md`: [TM / TC refs using the same Operation ID / Boundary Anchor / IF Scope]
- `research.md`: [constraints or reuse anchors]

## Contract Binding

- Consumer-visible interaction: [summary]
- Operation ID: [operationId; must match header and contract]
- Boundary anchor: [must match header and contract]
- Boundary anchor status: [`existing` | `extended` | `new` | `todo`]
- IF scope: [must match header and contract]
- Implementation entry anchor: [repo-backed internal handoff entry; for HTTP entry typically `Controller.method`, for RPC/facade entry typically `Facade.method`]
- Implementation entry anchor status: [`existing` | `extended` | `new` | `todo`]
- Participating components: [reuse anchored source-code symbols from controller/facade, service implementation, manager, and other repo-backed collaborators that affect contract-visible output/failure]
- Use anchored symbols when they exist; do not replace them with layered placeholders such as `*BoundaryAdapter`, `*Service`, `*Policy`, `*Assembler`, or pseudo-symbols such as `AnchoredMapper`, `queryOrUpdate(...)`, or bare role labels like `Caller`.

## Field Semantics

List only fields that affect contract-visible behavior, validation, authorization, projection, or state transitions. Do not restate pass-through fields that add no behavioral meaning beyond the contract.
If anchored client-entry signature surface (HTTP route/controller or facade/RPC method) and request/response DTOs exist, preserve that signature surface and DTO structure (field names, nesting, and anchored enum/status vocabulary).
Field semantics may add business meaning for anchored fields, but must not rename fields, flatten nesting, split anchored fields into new fields, or add UI-confirmation-only flow fields unless those fields already exist on the anchored interface.
Use `Direction = input` / `output` only for contract-visible request/response fields or their anchored DTO-owned subfields. Use `Direction = state` only for persisted or domain state that directly changes contract-visible outcomes, failure semantics, or lifecycle legality.
If the contract already captures the external payload shape, do not duplicate full request/response prose here; record only the behavior-significant fields, ownership implications, and mapping rules that are needed for detailed design.

| Field | Direction | Meaning | Required / Optional | Rules | Source |
|-------|-----------|---------|---------------------|-------|--------|
| [field] | [input / output / state] | [semantic meaning] | [required / optional] | [validation, invariant, or projection rule] | [contract / model ref] |

## Preconditions / Postconditions

- Preconditions:
  - [Operation-local guard or prerequisite]
- Postconditions:
  - [Observable or model-level outcome]

## Behavior Paths

Keep only materially distinct paths. Merge paths that differ only in internal mechanics when the trigger, contract-visible outcome, and failure semantics are the same.

Define only the paths that matter to contract-visible outcomes. Each path should map to at least one interaction segment in the sequence diagram.

| Path | Trigger | Key Steps | Outcome | Contract-Visible Failure | Sequence Ref | TM/TC Anchor |
|------|---------|-----------|---------|--------------------------|--------------|--------------|
| Main | [Trigger] | [Essential interaction steps] | [Success outcome] | [N/A or failure mode] | [S1] | [TM-### / TC-###] |

## Sequence Diagram

Include participants and interactions whenever they influence contract-visible outcomes, key state changes, key side effects, auth/validation decisions, or critical failure paths.
Do not expand into exhaustive two-party/three-party call enumeration that has no contract-visible impact.
Use short step labels (for example `S1`, `S2`) so behavior paths can reference sequence segments.
Sequence MUST start from consumer/client entry and reach `Implementation Entry Anchor` within the first two request hops.
If both controller and facade exist for this operation, show both participants in order and keep their handoff explicit.
If `Boundary Anchor` and `Implementation Entry Anchor` resolve to the same repo-backed symbol, reuse one participant instead of inventing a fake handoff hop.
When `Boundary Anchor` and `Implementation Entry Anchor` differ, show both forward and return handoff messages explicitly; do not collapse the response directly from deeper collaborators back to the contract boundary.
Prefer confirmed source-code symbols for participant names.
Only when repo anchors truly do not exist may placeholders remain forward-looking; in that case set `Boundary Anchor Status = todo` and/or `Implementation Entry Anchor Status = todo`, keep explicit `TODO(REPO_ANCHOR)`, and avoid pseudo-symbol or layered placeholder collaborators.
Do not imply event publication paths unless a repo-backed anchor explicitly supports that path.

```mermaid
sequenceDiagram
    participant Initiator as "<ClientOrCaller>"
    participant Boundary as "<ContractBoundaryAnchor>"
    %% Declare Entry only when it differs from Boundary.
    participant Entry as "<ImplementationEntryAnchor>"
    participant Coordinator as "<AnchoredCoordinatorSymbol>"
    participant Dependency as "<AnchoredDependencySymbol>"

    Initiator->>Boundary: [operation request] (S1)
    alt boundary anchor already is implementation entry
        Boundary->>Coordinator: validate + execute (S2)
        alt auth/validation fails
            Coordinator-->>Boundary: rejection reason (S3)
            Boundary-->>Initiator: contract error response (S4)
        else success
            opt optional repo-backed dependency interaction
                Coordinator->>Dependency: [anchored side effect] (S5)
                Dependency-->>Coordinator: [result/ack] (S6)
            end
            Coordinator-->>Boundary: success result or mapped response (S7)
            Boundary-->>Initiator: success response (S8)
        end
    else boundary hands off to distinct implementation entry
        Boundary->>Entry: handoff to internal entry (S2)
        Entry->>Coordinator: validate + execute (S3)
        alt auth/validation fails
            Coordinator-->>Entry: rejection reason (S4)
            Entry-->>Boundary: mapped error/result handoff (S5)
            Boundary-->>Initiator: contract error response (S6)
        else success
            opt optional repo-backed dependency interaction
                Coordinator->>Dependency: [anchored side effect] (S7)
                Dependency-->>Coordinator: [result/ack] (S8)
            end
            Coordinator-->>Entry: success result or mapped response (S9)
            Entry-->>Boundary: contract response handoff (S10)
            Boundary-->>Initiator: success response (S11)
        end
    end
```

## UML Class Design

Use this section for an operation-level static collaboration view for this contract binding. It should complement the sequence diagram by showing which classes/interfaces hold the responsibilities behind the behavior paths and contract-visible outcomes.

- **Target artifact**: a per-operation UML class diagram focused on static collaborators for this operation only.
- **Minimum complete handoff set**:
  - key operation-local classes or interfaces for boundary entry, implementation entry, coordination, decision, and output-assembly responsibilities
  - request/response DTOs and nested DTOs at field level for all contract-visible input/output fields
  - repo-backed DO/entity/enum/status vocabulary that directly influences mapping, recommendation/availability decisions, or failure semantics
  - labeled relationships with type and direction where relevant such as association, dependency, composition, or realization
  - operation-local constraints or notes needed to explain validation, state change authority, emitted side effects, or failure decisions
- **Traceability**:
  - keep names consistent with the contract binding, field semantics, preconditions/postconditions, and behavior paths
  - ensure each important collaborator supports at least one sequence segment or contract-visible rule in this document
  - use this diagram to explain static responsibility placement, not to replay interaction order already covered by the sequence diagram
  - collapse `ContractBoundaryEntry` and `ImplementationEntry` into one class/interface when they resolve to the same repo-backed symbol
  - prefer source-code symbols for classes/interfaces; only when repo anchors are unavailable may forward-looking placeholders be used, and they must remain explicit non-anchored/non-normative with `TODO(REPO_ANCHOR)`
  - do not use reused planning terminology to imply a repo-backed collaborator model when no anchor exists
- **Boundary**:
  - reuse `data-model.md` entities, invariants, and lifecycle vocabulary when they apply, but do not redraw the full backbone model here
  - keep scope to the smallest complete handoff set needed to explain this operation; avoid turning this into a feature-wide domain model or implementation decomposition
- **Exclude**:
  - persistence schema, ORM/table mappings, and repository internals that do not influence contract-visible mapping/failure
  - package/module structure and deployment/component layout
  - utility/helper/cache/optimization classes with no contract-visible impact
  - language/framework-specific implementation details that do not affect operation semantics

Use placeholder names below as structure-only anchors, not implementation recommendations. Replace them with repo-backed symbols whenever such anchors exist.

```mermaid
classDiagram
    %% Collapse ContractBoundaryEntry and ImplementationEntry into one class when both anchors resolve to the same symbol.
    class ContractBoundaryEntry["<ContractBoundaryEntry>"] {
        +[consumerEntry](requestDto): responseDto
    }

    class ImplementationEntry["<ImplementationEntryAnchor>"] {
        +[handle](requestDto): responseDto
    }

    class RequestDTO["<RequestDTO>"] {
        +[requestFieldA]: [Type]
        +[requestFieldB]: [Type]
    }

    class ResponseDTO["<ResponseDTO>"] {
        +[responseFieldA]: [Type]
        +[status]: [StatusEnum]
    }

    class DomainEntity["<DomainEntityOrDO>"] {
        +[domainField]: [Type]
        +[state]: [StatusEnum]
    }

    class StatusEnum["<StatusEnum>"] {
        <<enumeration>>
        [ACTIVE]
        [REJECTED]
    }

    ContractBoundaryEntry --> ImplementationEntry : hands-off-to
    ImplementationEntry --> RequestDTO : consumes
    ImplementationEntry --> ResponseDTO : produces
    ImplementationEntry --> DomainEntity : reads/writes
    ResponseDTO --> StatusEnum : uses
    DomainEntity --> StatusEnum : stores
```

## Runtime Correctness Check

Use this as a required operation-local traceability aid during drafting and handoff. Centralized blocking validation is owned by `/sdd.analyze`.
All required rows in this section must be present; each row may remain `ok` or `gap` with explicit evidence.

- If an item is unresolved, keep it explicit as `TODO(REPO_ANCHOR)`, set the associated `Boundary Anchor Status` and/or `Implementation Entry Anchor Status` to `todo`, and keep it non-normative.
- `ok` means the mapping is complete and anchored; `gap` means further analysis is required before normative validation paths.

| Runtime Check Item | Required Evidence | Anchor | Status |
|--------------------|-------------------|--------|--------|
| Boundary-to-entry reachability | Sequence reaches `Implementation Entry Anchor` from consumer/client entry within the first two request hops | [boundary/entry anchors + sequence steps] | [ok / gap] |
| Behavior-path closure | `Behavior Paths` trigger/outcome/failure is fully covered by `Sequence Ref` steps | [path + sequence steps + TM/TC] | [ok / gap] |
| Failure consistency | Sequence failure steps map exactly to contract `Failure Output` semantics | [contracts/<artifact> failure rows] | [ok / gap] |
| State-transition legality | Every sequence step that reads/writes lifecycle state maps to a valid lifecycle transition and invariant | [data-model lifecycle + INV-*] | [ok / gap] |
| Message callability | Every contract-visible sequence message maps to a callable boundary/collaborator operation with UML ownership | [client-entry surface/DTO + UML operation/responsibility] | [ok / gap] |
| Field-ownership closure | Every contract-visible request/response field and every behavior-significant `Field Semantics` row has an explicit owning UML class/interface | [contract I/O + field semantics + UML ownership] | [ok / gap] |

## Boundary Notes

- Reuse and extend `data-model.md` vocabulary; do not redefine global model semantics.
- You may extend data-model vocabulary, but do not invent repo-backed collaborators, DTO fields, or lifecycle states without anchoring evidence.
- If anchored client-entry signature surface (HTTP route/controller or facade/RPC method) and request/response DTOs exist, keep that signature surface and DTO nesting intact across sequence, field semantics, and UML references.
- Do not duplicate the contract's `Request / Input`, `Success Output`, or `Failure Output` prose here; extend only the behavior-significant field meaning, ownership, mapping, and failure-propagation details needed for internal handoff design.
- For UML, ensure every contract-visible request/response field and every behavior-significant field in `Field Semantics` has an explicit owning class.
- Do not use `README.md`, `docs/**`, `specs/**`, or generated artifacts as repo anchors in this document.

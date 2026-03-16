# Contract: [BOUNDARY OR OPERATION]

**Stage**: Stage 3 Contracts
**Scope**: [operation, endpoint, event, command, or external boundary]
**IF Scope (Required)**: [IF-### or N/A]
**Operation ID (Required)**: [operationId or N/A]
**Boundary Anchor (Required)**: [HTTP `METHOD /path` \| `event.topic` \| `Facade.method` \| `cli command` \| `N/A`]
**Anchor Status (Required)**: [`existing` \| `extended` \| `new` \| `todo`]

Keep this artifact minimal and binding-stable. It is the external contract handoff into interface-level detailed design.
For UIF-scoped operations, anchor the first consumer-callable boundary rather than internal implementation hops.

## Boundary Anchor Rules (Normative)

- Allowed normative boundary-anchor forms are exactly: HTTP `METHOD /path`, event topic `event.topic`, RPC/Façade method `Facade.method`, CLI `command`, or explicit `N/A`.
- `Boundary Anchor` MUST represent the first client-callable entry for this operation/interaction, not an internal service/manager/mapper hop.
- If clients call an HTTP route directly, prefer HTTP `METHOD /path` as `Boundary Anchor`; do not skip to internal layers.
- If clients call a stable RPC/Façade surface, use repo-backed `Facade.method` as `Boundary Anchor`.
- If both controller/HTTP and façade exist, select the consumer-visible first callable entry as normative `Boundary Anchor`; model the remaining chain in interface detail.
- `BA-*` labels are not valid normative boundary anchors. If used, treat them as local shorthand notes only and never as authoritative binding keys.
- Apply repo-anchor decision order `existing -> extended -> new -> todo`.
- `extended` is valid only for same-entity field/state expansion.
- `new` is normative only when explicit `path::symbol` target evidence is provided.
- If explicit target evidence is missing, set `Repo Anchor` to `TODO(REPO_ANCHOR)` and `Anchor Status` to `todo`; treat that tuple as non-normative forward-looking only.

## Contract Binding

- External boundary: [HTTP / event / RPC / CLI / other]
- Operation or interaction name: [name]
- Operation ID: [operationId or N/A]
- Boundary anchor: [same value as header field above; must follow one allowed normative form]
- IF scope: [same value as header field above; must be explicit `N/A` when not interface-scoped]
- Anchor Status: [`existing` | `extended` | `new` | `todo`]
- Repo Anchor: [existing source-code symbol proving this binding] or `TODO(REPO_ANCHOR)` when unresolved
- Visible consumer / caller: [actor or system]
- Detailed design handoff target: `[interface-details/<operationId>.md]` or [N/A]
- Client entry rationale: [why this `Boundary Anchor` is the first consumer-callable entry]

## Minimal Binding References

Use stable IDs and short references only. Keep this section focused on the minimum downstream binding required for interface design and execution; do not expand it into a traceability ledger.

| Operation ID | Boundary Anchor | Operation / Interaction | IF Scope | Anchor Status | Repo Anchor | Upstream Ref(s) | Data Model Ref(s) | Detail Target |
|--------------|-----------------|-------------------------|----------|--------------------|-------------|-----------------|-------------------|---------------|
| [operationId or N/A] | [HTTP `METHOD /path` / `event.topic` / `Facade.method` / `cli command` / `N/A`] | [name] | [IF-### or N/A] | [`existing` / `extended` / `new` / `todo`] | [`path/to/file.ext::Symbol` or `TODO(REPO_ANCHOR)`] | [UC/FR/UIF/TM/TC refs needed downstream] | [Entity / INV / Lifecycle anchor ref] | `[interface-details/<operationId>.md]` or [N/A] |

## External I/O Summary

Keep this to minimum external I/O only.
Read the anchored client-entry signature surface (HTTP route/controller or façade/RPC method) and anchored request/response DTO first.
Request / Success Output / Failure Output MUST align with that anchored signature and DTO structure, including field names, nesting, and status vocabulary. Do not flatten, rename, split, or otherwise reshape anchored external I/O.

| Aspect | Definition |
|--------|------------|
| Request / Input | [Minimum external input required] |
| Success Output | [Visible success response or effect] |
| Failure Output | [Visible error response or failure effect] |

## Preconditions

- [Condition that must hold before the interaction]

## Postconditions

- [State or guarantee after successful completion]

## Success Semantics

- [What success means externally]

## Failure Semantics

- [Contract-visible failure mode]

## Visible Side Effects

- [Externally visible state change, event, or notification]

## Upstream References

- `spec.md`: [canonical source for UC / FR / UIF refs captured above]
- `test-matrix.md`: [TM / TC refs captured above; keep `Operation ID` / `Boundary Anchor` / `IF Scope` aligned]
- `data-model.md`: [shared concepts, invariants, and lifecycle anchors referenced above]
- `interface-details/`: [detailed design documents that consume this contract binding]

## Boundary Notes

- Keep this artifact at the minimum external I/O boundary only.
- For UIF-scoped operations, model the consumer-visible entry; do not substitute internal service/manager/mapper entrypoints as `Boundary Anchor`.
- Do not expand into internal projections, persistence mappings, sequence diagrams, or UML class design here.
- Do not turn this artifact into an audit, traceability, or coverage-report ledger.
- Use the decision order `existing -> extended -> new -> todo` for `Anchor Status`.
- `extended` MUST remain same-entity field/state expansion; do not use it for brand-new entities.
- `new` is allowed in normative rows only with explicit `path::symbol` target evidence.
- Rows/fields or tuples with `Anchor Status = todo` are forward-looking notes only; they are not normative contract commitments.
- If anchored DTOs exist, contract field semantics may add business meaning but MUST NOT rename anchored fields, flatten anchored nesting, or introduce split fields absent from the anchored DTO.

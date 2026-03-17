# Contract: [BOUNDARY OR OPERATION]

**Stage**: Stage 3 Contracts
**Scope**: [operation, endpoint, event, command, or external boundary]
**IF Scope (Required)**: [IF-### or N/A]
**Operation ID (Required)**: [operationId or N/A]
**Boundary Anchor (Required)**: [HTTP `METHOD /path` \| `event.topic` \| `Facade.method` \| `cli command` \| `N/A`]

This template is format-agnostic. The final artifact may be represented as Markdown, JSON, YAML, or another contract-friendly syntax, but it MUST preserve the semantics captured below.
This artifact should provide the minimum stable binding from approved planning artifacts into interface-level detailed design.

## Boundary Anchor Rules (Normative)

- Allowed normative boundary-anchor forms are exactly: HTTP `METHOD /path`, event topic `event.topic`, RPC/Façade method `Facade.method`, CLI `command`, or explicit `N/A`.
- `BA-*` labels are not valid normative boundary anchors. If used, treat them as local shorthand notes only and never as authoritative binding keys.
- `Repo Anchor` MUST default to an existing source-code symbol for the binding tuple. If unresolved, set `Repo Anchor` to `TODO(REPO_ANCHOR)` and treat that tuple as non-normative forward-looking only.

## Contract Binding

- External boundary: [HTTP / event / RPC / CLI / other]
- Operation or interaction name: [name]
- Operation ID: [operationId or N/A]
- Boundary anchor: [same value as header field above; must follow one allowed normative form]
- IF scope: [same value as header field above; must be explicit `N/A` when not interface-scoped]
- Repo Anchor: [existing source-code symbol proving this binding] or `TODO(REPO_ANCHOR)` when unresolved
- Visible consumer / caller: [actor or system]
- Detailed design handoff target: `[interface-details/<operationId>.md]` or [N/A]

## Minimal Binding References

Use stable IDs and short references only. Keep this section focused on the minimum downstream binding required for interface design and execution; do not expand it into a traceability ledger.

| Operation ID | Boundary Anchor | Operation / Interaction | IF Scope | Repo Anchor | Upstream Ref(s) | Data Model Ref(s) | Detail Target |
|--------------|-----------------|-------------------------|----------|-------------|-----------------|-------------------|---------------|
| [operationId or N/A] | [HTTP `METHOD /path` / `event.topic` / `Facade.method` / `cli command` / `N/A`] | [name] | [IF-### or N/A] | [`path/to/file.ext:Symbol` or `TODO(REPO_ANCHOR)`] | [UC/FR/UIF/TM/TC refs needed downstream] | [Entity / INV / Lifecycle anchor ref] | `[interface-details/<operationId>.md]` or [N/A] |

## External I/O Summary

Keep this to minimum external I/O only. `minimum` does not permit abstracting away from an existing repo-backed interface surface.
Before filling this section, read the anchored facade/RPC method signature and anchored request/response DTO.
Request / Success Output / Failure Output MUST align with the anchored signature and DTO structure (including field names, nesting, and anchored status vocabulary).
Do not flatten, rename, split, or otherwise reshape anchored external I/O for readability.

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
- `Minimum` does not justify re-modeling or abstracting away from an existing repo-backed interface surface.
- Do not expand into internal projections, persistence mappings, sequence diagrams, or UML class design here.
- Do not turn this artifact into an audit, traceability, or coverage-report ledger.
- Use an existing source-code symbol whenever available for `Repo Anchor`; use `TODO(REPO_ANCHOR)` only when unresolved.
- Rows/fields or tuples that remain `TODO(REPO_ANCHOR)` are forward-looking notes only and MUST NOT be treated as normative contract commitments.
- A contract with unresolved repo anchors is not a fully anchored external-interface commitment.
- If anchored DTOs exist, contract field semantics may add business meaning but MUST NOT rename anchored fields, flatten anchored nesting, or introduce split fields absent from the anchored DTO.

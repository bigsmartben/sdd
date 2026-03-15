# Contract: [BOUNDARY OR OPERATION]

**Stage**: Stage 3 Contracts
**Scope**: [operation, endpoint, event, command, or external boundary]
**IF Scope (Required)**: [IF-### or N/A]
**Operation ID (Required)**: [operationId or N/A]
**Boundary Anchor (Required)**: [HTTP method+path \| event topic \| RPC method \| CLI command \| N/A]

This template is format-agnostic. The final artifact may be represented as Markdown, JSON, YAML, or another contract-friendly syntax, but it MUST preserve the semantics captured below.
This artifact should provide the minimum stable binding from `spec.md` intent and plan artifacts into interface-level detailed design.

## Contract Binding

- External boundary: [HTTP / event / RPC / CLI / other]
- Operation or interaction name: [name]
- Operation ID: [operationId or N/A]
- Boundary anchor: [same value as header field above]
- IF scope: [same value as header field above; must be explicit `N/A` when not interface-scoped]
- Visible consumer / caller: [actor or system]
- Detailed design handoff target: `[interface-details/<operationId>.md]` or [N/A]

## Traceability Anchors (Minimal Binding)

Use stable IDs and short references only. Do not reproduce full spec prose or expand into a full traceability matrix.

| Operation ID | Boundary Anchor | Operation / Interaction | UC Ref | FR Ref(s) | UIF / Scenario Ref | TM Ref(s) | IF Scope | Data Model Ref(s) |
|--------------|-----------------|-------------------------|--------|-----------|--------------------|-----------|----------|-------------------|
| [operationId or N/A] | [HTTP method+path / event topic / RPC method / CLI command / N/A] | [name] | [UC-###] | [FR-###, FR-###] | [UIF-### / Scenario] | [TM-### / TC-###] | [IF-### or N/A] | [Entity / INV / Lifecycle anchor ref] |

## External I/O Summary

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
- Do not expand into internal projections, persistence mappings, sequence diagrams, or UML class design here.

# Feature Verification Design: [FEATURE]

**Stage**: Stage 2 Feature Verification Design
**Inputs**: `spec.md`

Use this artifact to define scenario-oriented software test design for the feature. Cover main, branch, exception, and degraded behavior without turning the document into an audit ledger.
Keep the matrix minimal-but-sufficient: merge pure permutations with identical observable outcomes, and add a new row only when path semantics, preconditions, or expected outcomes materially differ.

## Coverage Strategy

- [Coverage scope: which spec paths must be verified and why]
- [Path decomposition: which main / branch / failure / degraded paths must stay distinct]
- [Verification goals and observability signals for each path family]
- [How the selected strategy seeds downstream `Binding Contract Packets` and bounded contract reads]
- [How `spec.md` scenarios are translated into verifiable paths]
- [Which spec-declared interface bindings make each path executable]

## Stable Binding Keys (Required)

- Keep `TM ID` and `TC ID` stable once referenced downstream.
- For every scenario/case row, populate `Operation ID`, `Boundary Anchor`, `IF Scope`, `Repo Anchor`, `Repo Anchor Role`, and `Anchor Status` (use explicit `N/A` when not interface-scoped).
- `Boundary Anchor` is normative only when it is one of: HTTP `METHOD /path`, `event.topic`, RPC/Façade method, CLI command, or explicit `N/A`.
- `Boundary Anchor` MUST identify the first consumer-callable entry used for contract binding; do not project internal service/manager/mapper handoff symbols here.
- `Operation ID` captures feature-level operation semantics; multiple `Operation ID` values MAY share the same spec-declared `Boundary Anchor`.
- `Repo Anchor` is optional traceability context only and MUST NOT replace or redefine `Boundary Anchor`.
- If the consumer enters through HTTP, prefer `HTTP METHOD /path`; if the consumer enters through a stable RPC/Façade surface, use `Facade.method`.
- A normative `Boundary Anchor` MUST be explicitly consumer-callable in spec context; do not replace declared HTTP/controller entries with abstract facade operation names.
- `BA-*` labels are invalid as normative boundary anchors and may appear only as non-normative helper labels.
- Apply repo-anchor decision order `existing -> extended -> new`.
- `extended` is valid only for same-entity field/state expansion.
- `new` is normative only when explicit `path::symbol` target evidence is provided.
- If explicit target evidence is missing, set `Anchor Status = todo` and keep the row non-normative forward-looking only.
- `Repo Anchor Role` must be one of: `boundary-owner`, `state-source`, `projection-source`, `transport-carrier`, `context-carrier`, `partial-lineage`.
- Keep `Operation ID` / `Boundary Anchor` / `IF Scope` values stable; `/sdd.plan.contract` MUST consume these tuple keys verbatim and MUST NOT redefine them.
- `Implementation Entry Anchor` MUST NOT be added to `Scenario Matrix` or `Verification Case Anchors` tuple keys.
- `Implementation Entry Anchor` is allowed only in `Binding Contract Packets` as a contract-seed field for `/sdd.plan.contract`.
- For HTTP-facing bindings, `Boundary Anchor` MUST stay `HTTP METHOD /path`, `Implementation Entry Anchor` MUST stay the owning controller method, and downstream service/facade symbols MUST remain collaborators only.
- `Request DTO Anchor` and `Response DTO Anchor` MAY remain `TODO(REPO_ANCHOR)` only as explicit contract gap sources; they MUST NOT trigger a fallback back to minimal-field contract output.
- Do not define shared-semantic ownership/classes/lifecycle vocabulary here; keep this artifact focused on spec-driven verification tuples.
- Main-path verification binding MUST use tuples with `Anchor Status = existing|extended|new`. Rows with `Anchor Status = todo` MUST NOT enter primary verification path rows.

## Scenario Matrix

| TM ID | Operation ID | Boundary Anchor | IF Scope | Repo Anchor | Repo Anchor Role | Anchor Status | Path Type | Scenario | Preconditions | Expected Outcome | Related Ref |
|-------|--------------|-----------------|----------|-------------|------------------|---------------|-----------|----------|---------------|------------------|-------------|
| TM-001 | [operationId or N/A] | [HTTP `METHOD /path` \| `event.topic` \| `Facade.method` \| `cli command` \| `N/A`] | [IF-### or N/A] | [`path/to/file.ext::Symbol` or `TODO(REPO_ANCHOR)`] | [`boundary-owner` \| `state-source` \| `projection-source` \| `transport-carrier` \| `context-carrier` \| `partial-lineage`] | [`existing` \| `extended` \| `new` \| `todo`] | Main | [Scenario] | [State or setup] | [Observable result] | [UC / UIF / FR] |

## Verification Case Anchors

| TC ID | TM ID | Operation ID | Boundary Anchor | IF Scope | Repo Anchor | Repo Anchor Role | Anchor Status | Verification Goal | Observability / Signal |
|-------|-------|--------------|-----------------|----------|-------------|------------------|---------------|-------------------|------------------------|
| TC-001 | TM-001 | [operationId or N/A] | [same as scenario row or N/A] | [IF-### or N/A] | [same as scenario row] | [same as scenario row] | [same as scenario row] | [What this case proves] | [Assertion, signal, or check] |

## Binding Contract Packets

Use this section to emit the authoritative per-binding contract seed packet consumed by `/sdd.plan.contract`.
Keep the packet compact and tuple-oriented; do not restate scenario prose or realization-design narrative here.
This packet scopes the operation-scoped `Full Field Dictionary` and the minimum targeted contract reads in `contracts/`; it does not claim field-level closure on its own, and it does not authorize a fallback to minimal-field contract output.
When either anchor status is `new`, the packet MUST carry concise strategy evidence showing why `existing` was rejected and why `extended` was rejected or unsafe.

| BindingRowID | Operation ID | IF Scope | Boundary Anchor | Boundary Anchor Status | Boundary Anchor Strategy Evidence | Implementation Entry Anchor | Implementation Entry Anchor Status | Implementation Entry Anchor Strategy Evidence | Request DTO Anchor | Response DTO Anchor | Primary Collaborator Anchor | TM ID | TC IDs | Spec Ref(s) | Scenario Ref(s) | Success Ref(s) | Edge Ref(s) | Main Pass Anchor | Branch/Failure Anchor(s) |
|--------------|--------------|----------|-----------------|------------------------|-----------------------------------|-----------------------------|------------------------------------|-----------------------------------------------|--------------------|--------------------|-----------------------------|-------|--------|-------------|-----------------|----------------|-------------|------------------|--------------------------|
| BR-001 | [operationId or N/A] | [IF-### or N/A] | [HTTP `METHOD /path` \| `event.topic` \| `Facade.method` \| `cli command` \| `N/A`] | [`existing` \| `extended` \| `new` \| `todo`] | [`existing: ...; extended: ...` or `N/A`] | [`path/to/file.ext::Symbol` or `TODO(REPO_ANCHOR)`] | [`existing` \| `extended` \| `new` \| `todo`] | [`existing: ...; extended: ...` or `N/A`] | [`path/to/file.ext::Symbol` or `N/A` or `TODO(REPO_ANCHOR)`] | [`path/to/file.ext::Symbol` or `N/A` or `TODO(REPO_ANCHOR)`] | [`path/to/file.ext::Symbol` or `N/A` or `TODO(REPO_ANCHOR)`] | [TM-001] | [TC-001, TC-002] | [UC / UIF / FR refs] | [SC / scenario refs] | [success refs] | [edge / EC refs] | [primary success check] | [branch or failure checks] |

### Packet Field Semantics (Mandatory)

- `BindingRowID`: unique stable packet id; must map 1:1 to one downstream contract unit
- `Operation ID`: operation token carried from spec path semantics
- `IF Scope`: interface scope token (`IF-###` or `N/A`) aligned to the operation
- `Boundary Anchor`: client-facing boundary token used as contract binding key
- `Boundary Anchor Status`: strategy status for boundary token only (`existing|extended|new|todo`)
- `Boundary Anchor Strategy Evidence`: mandatory when boundary status is `new`
- `Implementation Entry Anchor`: realization handoff entry token (`path::symbol` or `TODO(REPO_ANCHOR)`)
- `Implementation Entry Anchor Status`: independent strategy status for implementation entry (`existing|extended|new|todo`)
- `Implementation Entry Anchor Strategy Evidence`: mandatory when implementation-entry status is `new`
- `Request DTO Anchor`: request payload anchor used by downstream contract (`path::symbol`, `N/A`, or `TODO(REPO_ANCHOR)`)
- `Response DTO Anchor`: response payload anchor used by downstream contract (`path::symbol`, `N/A`, or `TODO(REPO_ANCHOR)`)
- `Primary Collaborator Anchor`: first mandatory collaborator anchor (`path::symbol` or `N/A`)
- `TM ID`: owning scenario-matrix row id
- `TC IDs`: ordered verification-case ids linked to the same packet
- `Spec Ref(s)`: explicit `UC/UIF/FR` references proving spec traceability
- `Scenario Ref(s)`: scenario references that materialize the tuple
- `Success Ref(s)`: success-path references proving main expected behavior
- `Edge Ref(s)`: edge/failure references proving non-happy paths
- `Main Pass Anchor`: canonical success assertion/check id
- `Branch/Failure Anchor(s)`: canonical branch/failure assertion/check ids

## Boundary Notes

- Keep this artifact in the planning flow as feature-level test design only.
- Prefer the smallest scenario/case set that still preserves meaningful path coverage and stable downstream bindings.
- Emit one `Binding Contract Packets` row for every stable binding row that will enter the contract queue.
- Keep tuple-key status semantics explicit: packet `Boundary Anchor Status` and `Implementation Entry Anchor Status` must be projected separately; do not collapse them into one ambiguous status token.
- If either packet anchor status is `new`, the matching strategy-evidence column MUST explicitly mention both `existing` and `extended` rejection evidence; do not leave the cell empty or reduce it to a bare target path.
- Bind TM/TC rows to tuples with `Anchor Status = existing|extended|new` for normative verification; keep rows with `Anchor Status = todo` out of the main validation path.
- Treat `Boundary Anchor` as the client-facing contract entry only; keep internal implementation handoff anchors for contract realization design sections.
- For HTTP-facing bindings, keep the controller method in `Implementation Entry Anchor` and the first downstream service/facade hop in `Primary Collaborator Anchor`.
- If later contract generation surfaces tuple drift, repair this packet via `/sdd.plan.test-matrix`; do not let downstream commands rewrite Stage 2 tuple seeds.
- `Primary Collaborator Anchor` MAY be `N/A`, but it MUST NOT be used to disguise an unknown boundary or implementation entry.
- Contract-seed coverage is operation-scoped and bounded: it identifies request/response surfaces, collaborator surfaces, and test anchors the contract must preserve without duplicating the full field dictionary.
- Treat `BA-*` as non-normative shorthand only; never use it as a normative tuple key.
- Do not redefine contract fields, interface internals, audit tables, traceability ledgers, or shared-semantic ownership here.

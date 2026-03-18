# Feature Verification Design: [FEATURE]

**Stage**: Stage 2 Feature Verification Design
**Inputs**: `spec.md`, `research.md`, `data-model.md`

Use this artifact to define scenario-oriented software test design for the feature. Cover main, branch, exception, and degraded behavior without turning the document into an audit ledger.
Keep the matrix minimal-but-sufficient: merge pure permutations with identical observable outcomes, and add a new row only when path semantics, preconditions, or expected outcomes materially differ.

## Coverage Strategy

- [How `spec.md` scenarios are translated into verifiable paths]
- [Where shared invariants, lifecycle, or role boundaries affect coverage]

## Stable Binding Keys (Required)

- Keep `TM ID` and `TC ID` stable once referenced downstream.
- For every scenario/case row, populate `Operation ID`, `Boundary Anchor`, `IF Scope`, `Repo Anchor`, and `Anchor Status` (use explicit `N/A` when not interface-scoped).
- `Boundary Anchor` is normative only when it is one of: HTTP `METHOD /path`, `event.topic`, RPC/Façade method, CLI command, or explicit `N/A`.
- `Boundary Anchor` MUST identify the first consumer-callable entry used for contract binding; do not project internal service/manager/mapper handoff symbols here.
- If the consumer enters through HTTP, prefer `HTTP METHOD /path`; if the consumer enters through a stable RPC/Façade surface, use `Facade.method`.
- `BA-*` labels are invalid as normative boundary anchors and may appear only as non-normative helper labels.
- Apply repo-anchor decision order `existing -> extended -> new -> todo`.
- `extended` is valid only for same-entity field/state expansion.
- `new` is normative only when explicit `path::symbol` target evidence is provided.
- If explicit target evidence is missing, set `Anchor Status = todo` and keep the row non-normative forward-looking only.
- Keep `Operation ID` / `Boundary Anchor` / `IF Scope` values textually consistent with `contracts/`.
- `Implementation Entry Anchor` MUST NOT be added to `Scenario Matrix` or `Verification Case Anchors` tuple keys.
- `Implementation Entry Anchor` is allowed only in `Binding Contract Packets` as a contract-seed field for `/sdd.plan.contract`.
- For HTTP-facing bindings, `Boundary Anchor` MUST stay `HTTP METHOD /path`, `Implementation Entry Anchor` MUST stay the owning controller method, and downstream service/facade symbols MUST remain collaborators only.
- `Request DTO Anchor`, `Response DTO Anchor`, and `State Owner Anchor(s)` MAY remain `TODO(REPO_ANCHOR)` only as explicit contract gap sources; they MUST NOT trigger a fallback back to minimal-field contract output.
- Main-path verification binding MUST use tuples with `Anchor Status = existing|extended|new`. Rows with `Anchor Status = todo` MUST NOT enter primary verification path rows.

## Scenario Matrix

| TM ID | Operation ID | Boundary Anchor | IF Scope | Repo Anchor | Anchor Status | Path Type | Scenario | Preconditions | Expected Outcome | Related Ref |
|-------|--------------|-----------------|----------|-------------|---------------|-----------|----------|---------------|------------------|-------------|
| TM-001 | [operationId or N/A] | [HTTP `METHOD /path` \| `event.topic` \| `Facade.method` \| `cli command` \| `N/A`] | [IF-### or N/A] | [`path/to/file.ext::Symbol` or `TODO(REPO_ANCHOR)`] | [`existing` \| `extended` \| `new` \| `todo`] | Main | [Scenario] | [State or setup] | [Observable result] | [UC / UIF / FR] |

## Verification Case Anchors

| TC ID | TM ID | Operation ID | Boundary Anchor | IF Scope | Repo Anchor | Anchor Status | Verification Goal | Observability / Signal |
|-------|-------|--------------|-----------------|----------|-------------|---------------|-------------------|------------------------|
| TC-001 | TM-001 | [operationId or N/A] | [same as scenario row or N/A] | [IF-### or N/A] | [same as scenario row] | [same as scenario row] | [What this case proves] | [Assertion, signal, or check] |

## Binding Contract Packets

Use this section to emit the authoritative per-binding contract seed packet consumed by `/sdd.plan.contract`.
Keep the packet compact and tuple-oriented; do not restate scenario prose or realization-design narrative here.
This packet seeds the operation-scoped `Full Field Dictionary` in `contracts/`; it does not authorize a fallback to minimal-field contract output.

| BindingRowID | Operation ID | IF Scope | Boundary Anchor | Boundary Anchor Status | Implementation Entry Anchor | Implementation Entry Anchor Status | Request DTO Anchor | Response DTO Anchor | Primary Collaborator Anchor | State Owner Anchor(s) | TM ID | TC IDs | Spec Ref(s) | Scenario Ref(s) | Success Ref(s) | Edge Ref(s) | Main Pass Anchor | Branch/Failure Anchor(s) |
|--------------|--------------|----------|-----------------|------------------------|-----------------------------|------------------------------------|--------------------|--------------------|-----------------------------|-----------------------|-------|--------|-------------|-----------------|----------------|-------------|------------------|--------------------------|
| BR-001 | [operationId or N/A] | [IF-### or N/A] | [HTTP `METHOD /path` \| `event.topic` \| `Facade.method` \| `cli command` \| `N/A`] | [`existing` \| `extended` \| `new` \| `todo`] | [`path/to/file.ext::Symbol` or `TODO(REPO_ANCHOR)`] | [`existing` \| `extended` \| `new` \| `todo`] | [`path/to/file.ext::Symbol` or `N/A` or `TODO(REPO_ANCHOR)`] | [`path/to/file.ext::Symbol` or `N/A` or `TODO(REPO_ANCHOR)`] | [`path/to/file.ext::Symbol` or `N/A` or `TODO(REPO_ANCHOR)`] | [[`path/to/file.ext::Symbol`, `path/to/file.ext::Symbol`] or `N/A` or `TODO(REPO_ANCHOR)`] | [TM-001] | [TC-001, TC-002] | [UC / UIF / FR refs] | [SC / scenario refs] | [success refs] | [edge / EC refs] | [primary success check] | [branch or failure checks] |

## Boundary Notes

- Keep this artifact in the planning flow as feature-level test design only.
- Prefer the smallest scenario/case set that still preserves meaningful path coverage and stable downstream bindings.
- Emit one `Binding Contract Packets` row for every stable binding row that will enter the contract queue.
- Keep tuple-key status semantics explicit: packet `Boundary Anchor Status` and `Implementation Entry Anchor Status` must be projected separately; do not collapse them into one ambiguous status token.
- Bind TM/TC rows to tuples with `Anchor Status = existing|extended|new` for normative verification; keep rows with `Anchor Status = todo` out of the main validation path.
- Treat `Boundary Anchor` as the client-facing contract entry only; keep internal implementation handoff anchors for contract realization design sections.
- For HTTP-facing bindings, keep the controller method in `Implementation Entry Anchor` and the first downstream service/facade hop in `Primary Collaborator Anchor`.
- `State Owner Anchor(s)` MUST identify the owner classes that this operation reads, writes, projects, or uses for state/default/validation decisions; do not substitute the collaborator list here.
- `Primary Collaborator Anchor` MAY be `N/A`, but `State Owner Anchor(s)` MUST NOT be replaced by `Primary Collaborator Anchor`.
- Contract-seed coverage is operation-scoped: request DTO fields, response DTO fields, state-owner fields, and the directly read/write/project/validate/default-driving fields that the contract must preserve.
- Treat `BA-*` as non-normative shorthand only; never use it as a normative tuple key.
- Do not redefine contract fields, interface internals, audit tables, or traceability ledgers here.

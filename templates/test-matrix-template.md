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
- Keep `Operation ID` / `Boundary Anchor` / `IF Scope` values textually consistent with `contracts/` and `interface-details/`.
- `Implementation Entry Anchor` belongs only in `interface-details/`; do not encode internal handoff entrypoints in TM/TC tuple keys.
- Main-path verification binding MUST use tuples with `Anchor Status = existing|extended|new`. Rows with `Anchor Status = todo` MUST NOT enter primary verification path rows.

## Scenario Matrix

| TM ID | Operation ID | Boundary Anchor | IF Scope | Repo Anchor | Anchor Status | Path Type | Scenario | Preconditions | Expected Outcome | Related Ref |
|-------|--------------|-----------------|----------|-------------|---------------|-----------|----------|---------------|------------------|-------------|
| TM-001 | [operationId or N/A] | [HTTP `METHOD /path` \| `event.topic` \| `Facade.method` \| `cli command` \| `N/A`] | [IF-### or N/A] | [`path/to/file.ext::Symbol` or `TODO(REPO_ANCHOR)`] | [`existing` \| `extended` \| `new` \| `todo`] | Main | [Scenario] | [State or setup] | [Observable result] | [UC / UIF / FR] |

## Verification Case Anchors

| TC ID | TM ID | Operation ID | Boundary Anchor | IF Scope | Repo Anchor | Anchor Status | Verification Goal | Observability / Signal |
|-------|-------|--------------|-----------------|----------|-------------|---------------|-------------------|------------------------|
| TC-001 | TM-001 | [operationId or N/A] | [same as scenario row or N/A] | [IF-### or N/A] | [same as scenario row] | [same as scenario row] | [What this case proves] | [Assertion, signal, or check] |

## Boundary Notes

- Keep this artifact in the planning flow as feature-level test design only.
- Prefer the smallest scenario/case set that still preserves meaningful path coverage and stable downstream bindings.
- Bind TM/TC rows to tuples with `Anchor Status = existing|extended|new` for normative verification; keep rows with `Anchor Status = todo` out of the main validation path.
- Treat `Boundary Anchor` as the client-facing contract entry only; keep internal implementation handoff anchors for Stage 4 interface detail.
- Treat `BA-*` as non-normative shorthand only; never use it as a normative tuple key.
- Do not redefine contract fields, interface internals, audit tables, or traceability ledgers here.

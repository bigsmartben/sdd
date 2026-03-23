---
description: Generate exactly one blocked-or-pending contract artifact from plan.md.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

Treat all `$ARGUMENTS` as optional scoped user context.
Resolve `PLAN_FILE` using `{SCRIPT}` defaults.

## Goal

Generate exactly one unified northbound interface design artifact by consuming the first `blocked` or `pending` `contract` row from `PLAN_FILE`.
Use `.specify/templates/contract-template.md` only.

`/sdd.plan.contract` owns one `BindingRowID` per run:
- Northbound interface landing in the current repo.
- External boundary and internal implementation handoff point.
- Request / response semantics and realization design.
- Reuse of shared semantics from `data-model.md`.
- do not rewrite upstream planning artifacts from this command.

**MUST NOT** redefine binding cuts; `test-matrix` is the authority for binding projection.

## Selection Rules

1. Run `{SCRIPT}` to resolve `FEATURE_DIR` and `PLAN_FILE`.
2. If no pending or blocked contract row exists, stop and report that the contract queue is complete.
3. Prerequisite Check: `test-matrix` and `data-model` stage rows MUST be `done`; if either is not `done`, stop and route back to the failing stage before selecting a row.
4. Find the first `contract` row in `Artifact Status` with `Status = blocked|pending`.
5. Attempt to resolve one selected binding packet in `test-matrix.md` by the same `BindingRowID`; if absent, stop and route back to `/sdd.plan.test-matrix`.
6. Treat the matched `Binding Projection Index` row as a minimal locator ledger only — do not treat it as a complete design seed.
7. Treat the selected packet as the semantic authority for binding meaning in this run.
8. Copy packet locator fields deterministically into contract `Binding Context`; do not reinterpret packet meaning locally.
9. Treat the selected packet as demand projection only through the end of bounded repo closure.
10. If inconsistencies found, stop and route back to `/sdd.plan.test-matrix`.

## Governance / Authority

- **Authority rule**: `PLAN_FILE` is authoritative only for queue state; `spec.md`, `test-matrix.md`, and `data-model.md` are the semantic authorities.
- **Stage boundary rule**: No re-partitioning or re-modeling; only implementation-facing interface design.
- **Shared protocol rule**: Apply **Unified Repository-First Gate Protocol (URFGP)**.
- Use the repo-anchor decision protocol in `.specify/templates/contract-template.md` as the authority for this stage.

## Allowed Inputs

- `.specify/templates/contract-template.md` (structure)
- `PLAN_FILE` (queue state and shared snapshot)
- `test-matrix.md` (binding packet and scenario matrix)
- `FEATURE_SPEC` (UC/FR/UIF/UDD authority)
- `data-model.md` (shared semantics authority)
- Bounded repo evidence (boundary/entry/DTO/collaborator targets)

**Prohibited**: `research.md`, broad symbol scans, or non-resolved artifact reads.

## Semantic Reconstruction

Reconstruct request / response meaning from `UC`, `FR`, `UIF`, `UDD`, and scenario refs before reading repo evidence.
Use the selected `Binding Packets` row as binding semantic authority; resolve ambiguity by routing upstream instead of local reinterpretation.

Required scope for bounded repo reads:
- required collaborators and middleware
- required owner/source symbols
- `existing` boundary/entry anchors

Keep repo-backed verification bounded to the selected `BindingRowID` and active blockers.

If repo-backed verification finds a binding-projection error or shared-semantic gap, stop and route to the appropriate upstream command.

## Realization Rules

- MAY refine operation-scoped VO/DTO/field mappings within this binding.
- MUST NOT mint new shared-semantic classes, owners/sources, lifecycle vocabulary, or invariants.
- Sequence design MUST explicitly render every mandatory repo-backed collaborator hop.
- Sequence design MUST NOT collapse multiple mandatory collaborators/dependencies into one synthetic participant label.
- `opt` blocks are valid only for truly conditional branches.
- UML request/response class labels should use anchored symbols or repository boundary naming conventions; do not synthesize placeholder DTO labels.

## Concrete Naming Closure (Mandatory)

Apply the anchor decision order `existing -> extended -> new -> todo`.

- Bounded repo closure MUST end with one explicit boundary/entry decision: `existing`, `extended`, `new`, or `todo`.
- MUST evaluate one concrete `new` anchor set before stopping.
- Do not mark the row `blocked` only because no existing repo entry anchor was found.
- Do not route upstream only because no existing repo entry was found after evaluating `existing -> extended -> new -> todo` with bounded evidence.
- freeze that naming for this run and finish the contract instead of reopening anchor search loops.
- After bounded reads, stop anchor hunting and transition to closure output for this run.
- If `existing` and `extended` are both insufficient, design concrete `new` anchors — this stage may produce concrete `new` anchors when bounded repo evidence closes the naming.
- `new` anchors are design-final implementation targets for this binding run; they are not automatic proof that the symbol already exists in the repository.
- If a `new` anchor symbol is not yet present in bounded repo evidence, do not fabricate repo file anchors; prefer concrete design-target naming (for example `ConcreteEntry.method`) or `TODO(REPO_ANCHOR)` when landing cannot be closed.
- Use `path/to/file.ext::Symbol` for `new` anchors only when bounded repo evidence closes that landing path/family for this binding.

## Stop Local Refinement Rules

Stop local refinement and route upstream when continuing would require a new upstream shared semantic — specifically:
- new shared semantic owner/source, a new backbone semantic element, a new cross-operation stable owner field, new shared lifecycle/invariant vocabulary.

## Feature-Level Smoke Readiness (Queue-Complete Gate)

After each run, check whether all `contract` rows are done. If so:
- Emit the queue-complete `Handoff Decision` with `Next Command = /sdd.tasks`.
- Cross-Interface Smoke Candidate (Required) — confirm at least one smoke candidate is designated across the completed contracts.

## Reasoning Order

1. **Requirement Projection**: Lock demand from selected binding packet and spec refs.
2. **Spec Semantics**: Reconstruct I/O and outcome meaning from `spec.md`.
3. **Shared Semantic Reuse**: Inherit owner/source/vocabulary from `data-model.md`.
4. **Repo Closure**: Land design using `existing -> extended -> new -> todo` priority.

## Artifact Quality Contract

- Must: close one `BindingRowID` with concrete names, anchors, field semantics, realization, and test projection.
- Strictly: `Operation ID` MUST be concrete (not `N/A`).

## Writeback Contract

- Generate or refresh exactly one contract artifact for the selected `BindingRowID`.
- Update only the selected `Artifact Status` row in `PLAN_FILE`: `Target Path`, `Status`, `Blocker`.
- `Status = done` only when `Operation ID` is concrete and key field gaps are resolved.
- Do not modify `Stage Queue`, `Binding Projection Index`, or unrelated `Artifact Status` rows.
- **MUST NOT** rewrite `spec.md`, `plan.md` stage queue, or unrelated artifacts.

## Output Contract

- **Operation ID**: MUST be concrete (not `N/A`).
- **Full Field Dictionary**: MUST cover all I/O fields present in the selected binding packet's UC/FR/UIF/UDD refs; classify each as `operation-critical` (field required for the operation to succeed) or `owner-residual` (field owned by a shared semantic class, not this operation).
- **Anchor Strategy**: If `new`, MUST provide explicit rejection evidence for `existing` and `extended`.
- **Sequence Design**: MUST be end-to-end contiguous, starting from client entry.
- **UML Class Design**: MUST cover all sequence participants and methods.
- **Test Projection**: Derive `Main Pass Anchor` and smoke candidates from `test-matrix.md`.

## Handoff Decision

Emit exactly these fields:
- If any `contract` rows remain `blocked`, `Next Command = /sdd.plan.contract`.
- Otherwise, if any `contract` rows remain `pending`, `Next Command = /sdd.plan.contract`.
- Otherwise, if all required planning rows (`research`, `test-matrix`, `data-model`, and all queued `contract` rows) are complete, `Next Command = /sdd.tasks`.
- `Decision Basis`: Cite post-update `Artifact Status` state.
- `Selected BindingRowID`: selected unit.
- `Ready/Blocked`: Local readiness only.

---
description: Generate the pending data-model.md artifact selected from the current feature branch plan.md.
handoffs:
  - label: Continue Contract Queue
    agent: sdd.plan.contract
    prompt: Run /sdd.plan.contract with the same active feature branch context.
    send: true
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --data-model-preflight
  ps: scripts/powershell/check-prerequisites.ps1 -Json -DataModelPreflight
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Argument Parsing

Treat all `$ARGUMENTS` as optional scoped user context.
Resolve `PLAN_FILE` from the current feature branch using `{SCRIPT}` defaults.

## Goal

Generate exactly one `data-model.md` artifact by consuming the first pending `data-model` row from `PLAN_FILE`.
This command is single-unit only and MUST NOT perform any other planning stage work.
This stage performs shared semantic alignment for the selected `BindingRowID` set, not interface predesign.
For this command, `selected BindingRowID set` means all currently projected `BindingRowID` rows in `PLAN_FILE` `Binding Projection Index` for this run-local snapshot.
Primary semantic inputs are `spec.md`, `test-matrix.md`, and bounded repo semantic landing evidence:

- `Interface Partition Decisions` explain why bindings were split and which semantics stay interface-local
- `Binding Packets` are the default downstream-demand projection input, including scope reference fields such as `User Intent`, `Request Semantics`, `Visible Result`, `Side Effect`, `Boundary Notes`, and `Repo Landing Hint`
- `Scenario Matrix` / `Verification Case Anchors` are required verification inputs for confirming whether semantics are shared or binding-local
- bounded repo semantic landing evidence is mandatory when this stage materializes a final semantic owner, lifecycle owner, or UML/class node

`research.md` is optional clarification input only and MUST NOT be treated as the primary semantic source for this stage.
The output MUST define only the shared, stable, reusable semantics that downstream `contract` work must reuse across bindings: shared entities, value objects, projections, owner/source alignment, lifecycle vocabulary, invariants, and any necessary new shared classes.
Repo-first remains mandatory as the landing strategy for any final semantic owner, lifecycle owner, or UML/class node emitted by this artifact: apply `existing -> extended -> new`. If `existing` and `extended` cannot safely close a confirmed shared semantic, this stage MUST explicitly choose `new` here rather than leaving the ownership decision to `/sdd.plan.contract`.
Do not define HTTP routes, controller/service/DTO names, request/response shapes, operation-scoped command/result models, or repo interface-anchor placement here; those belong to `/sdd.plan.contract`.
Use `.specify/templates/data-model-template.md` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or other `data-model.md` outputs.

## Selection Rules

1. Run `{SCRIPT}` once from repo root and parse `FEATURE_DIR`, `AVAILABLE_DOCS`, and `DATA_MODEL_BOOTSTRAP`
2. Treat `DATA_MODEL_BOOTSTRAP.generation_readiness` as the primary queue/readiness gate for resolved paths, selected row, and output-path consistency
3. If `DATA_MODEL_BOOTSTRAP.generation_readiness.ready_for_generation = true`, reuse the selected stage row, resolved `plan.md` / `spec.md` / `test-matrix.md` / `data-model.md` paths, `FEATURE_DIR`, and `state_machine_policy` from `DATA_MODEL_BOOTSTRAP`; do not rescan for alternate pending rows
4. If `DATA_MODEL_BOOTSTRAP` is missing, malformed, contradictory, or unavailable, stop immediately and report the runtime bootstrap blocker
5. When `ready_for_generation = false`, report blocking `generation_readiness.errors[].code/message/details` directly in runtime output; do not replace them with generic failure text

## Stage Packet (Data-Model Unit)

Build one bounded run-local packet for the selected `data-model` row from:

- selected `Stage Queue` row in resolved `PLAN_FILE`
- `Shared Context Snapshot` in resolved `PLAN_FILE`
- `Repository-First Consumption Slice` in resolved `PLAN_FILE`
- resolved `FEATURE_SPEC` path
- resolved `test-matrix.md` path, with these mandatory sections:
  - `Interface Partition Decisions`
  - `UIF Full Path Coverage Graph (Mermaid)`
  - `UIF Path Coverage Ledger`
  - `Scenario Matrix`
  - `Verification Case Anchors`
  - `Binding Packets`
- `Scenario Matrix` / `Verification Case Anchors` as required verification anchors for confirming whether a semantic is shared across bindings or remains binding-local
- bounded repo semantic landing evidence referenced by the selected feature slice
- optional `research.md` path only when `spec.md` + `test-matrix.md` wording leaves the shared-semantic boundary ambiguous
- selected row source/output fingerprint fields

Use this packet as the default context for generation.
Do not load additional artifacts unless the selected-row blocker cannot be resolved from those bounded inputs.

Apply the constitution-derived lifecycle applicability policy from `DATA_MODEL_BOOTSTRAP.state_machine_policy` while writing lifecycle sections:

- For each declared lifecycle, count distinct stable states as `N`
- Count unique effective transitions (`FromState -> ToState`) as `T`
- If `N > 3` or `T >= 2N`, emit a full FSM package: transition table, transition pseudocode, and state diagram
- Otherwise keep the lifecycle lightweight: state field definition, allowed transitions, forbidden transitions, and key invariants
- If you still choose a full FSM below threshold, record explicit justification in the lifecycle section

## Stop Conditions

Stop immediately when any condition holds:

1. Resolved branch-derived `PLAN_FILE` is missing or invalid
2. `DATA_MODEL_BOOTSTRAP.generation_readiness.ready_for_generation = false`
3. `DATA_MODEL_BOOTSTRAP` is missing, malformed, contradictory, or unavailable
4. Any required `test-matrix.md` section is missing, or any projected `BindingRowID` packet is missing/non-consumable/incomplete
5. Shared-semantic boundary or lifecycle evidence required by the selected unit cannot be resolved from the allowed inputs

## Plan Control-Plane Input Path (Mandatory)

Use only the resolved `PLAN_FILE` from `{SCRIPT}` as planning control plane.
Ignore alternate `plan.md` paths from environment variables or repository discovery.
Non-`plan.md` user files are allowed only when already listed in `Allowed Inputs`; they never redefine control-plane state.
If `PLAN_FILE` is missing or non-consumable, stop and report a blocker.

## Path Constraints

- Stay inside the resolved `FEATURE_DIR` plus the explicit files listed in `Allowed Inputs`
- Derive shared semantic elements from `FEATURE_SPEC` and `test-matrix.md` first
- Use `Interface Partition Decisions` plus `Binding Packets` as the default downstream-demand projection input; use packet scope reference fields primarily to exclude interface-local detail from the shared model, and use `Scenario Matrix` / `Verification Case Anchors` as required verification anchors for shared-vs-local checks
- Apply shared-semantic alignment across the full projected `BindingRowID` set for this run-local snapshot; do not narrow to ad hoc subsets unless a runtime blocker explicitly requires upstream repair first
- Treat `research.md` as optional clarification only; do not let it override `spec.md` or `test-matrix.md`
- Apply repo-first only as the landing strategy for final semantic owners, lifecycle owners, and UML/class nodes; it is not the primary semantic input source for this stage, but bounded repo landing evidence is still required when such nodes are materialized
- Finish row selection and prerequisite checks before any broader reads; do not scan the repository for additional context, alternate `plan.md` paths, or other feature folders
- Do not use any existing `data-model.md` outside the current target artifact path as an input or style source
- Prefer section-level reads of `spec.md` and `test-matrix.md` that are relevant to the selected unit; avoid whole-file replay unless the selected row is blocked by missing local context

## Shared-Semantic Alignment Rules (Mandatory)

- Output only shared, stable, reusable semantics
- Do not treat "used by two or more `BindingRowID` values" as sufficient proof of shared-semantic status by itself
- A semantic used by two or more `BindingRowID` values SHOULD enter `data-model.md` only when it remains business-stable across those bindings and is not merely trigger-local, request-local, side-effect-local, or interface-partition-local detail
- A semantic used by only one `BindingRowID` SHOULD stay in `/sdd.plan.contract` unless it is a globally stable business object, stable projection, or stable lifecycle that downstream contracts must not redefine independently
- Include shared owner/source/lifecycle/invariant/projection vocabulary when contract runs would otherwise drift
- If a shared semantic is materialized as a class, semantic owner, lifecycle owner, or UML node, it MUST follow repo-first landing order `existing -> extended -> new`
- If `existing` and `extended` are both insufficient, `new` is the required outcome for this stage; do not defer that class/owner decision downstream
- Do not include interface-partition-only trigger semantics, request semantics, side-effect descriptions, single-binding request/response shapes, controller/service/facade naming, operation-specific DTO/command/result models, single-interface local validation detail, or realization-level collaborator chains
- Treat `User Intent`, `Request Semantics`, `Visible Result`, `Side Effect`, `Boundary Notes`, and `Repo Landing Hint` as downstream scope-reference helpers only; they may justify exclusion from the shared model but they do not become shared semantics by themselves
- Shared semantics that are confirmed by `spec.md` + `test-matrix.md` MUST be closed here at owner/source/lifecycle level; use `gap` only for genuine input/evidence blockers, not for unresolved ownership of an already-confirmed shared semantic

## Shared-Semantic Consistency Checks (Lightweight)

Before writing `done` status for the selected row, validate:

- Every shared semantic element cites primary `UDD` / spec refs and the `BindingRowID(s)` that consume it
- Every semantic elevated from `test-matrix.md` is justified as business-stable shared meaning rather than as repeated interface-partition metadata
- Packet scope reference fields are used only to explain why a semantic stayed local or became shared; they are not copied verbatim into shared owner/source/vocabulary rows unless grounded by stable business semantics
- Every owner/source alignment row resolves who owns the semantic and whether the downstream field/concept is authoritative, derived, or projected
- Shared field vocabulary stays vocabulary-only; do not expand it into a full per-contract field dictionary
- Lifecycle and invariant sections appear only when the state semantics are shared or globally stable for downstream reuse
- Every final UML/class landing decision remains repo-first and MUST end in `existing`, `extended`, or explicit `new`; do not leave a confirmed shared semantic without a closed landing decision
- `Downstream Contract Constraints` makes explicit which shared semantic refs each `BindingRowID` must reuse in `/sdd.plan.contract`
- If a required shared semantic cannot be closed only because authoritative input or evidence is missing, keep the blocker explicit in `data-model.md` and set the selected row `Blocker` instead of letting later stages backfill the model

If any gate fails, do not mark the `data-model` row `done`; keep it non-done and populate `Blocker` with the exact missing shared-semantic evidence.

## Allowed Inputs

Read only:

- `.specify/templates/data-model-template.md` for output structure
- selected `Stage Queue` row from the resolved `PLAN_FILE` only
- `Shared Context Snapshot` from the resolved `PLAN_FILE` only
- `Repository-First Consumption Slice` from the resolved `PLAN_FILE` only
- resolved `FEATURE_SPEC`
- resolved `test-matrix.md` (`Interface Partition Decisions`, `UIF Full Path Coverage Graph (Mermaid)`, `UIF Path Coverage Ledger`, `Scenario Matrix`, `Verification Case Anchors`, and `Binding Packets` required)
- bounded repo semantic landing evidence referenced by the selected feature slice
- optional `research.md`

### Conditional Inputs

Read additional files only when the selected-row blocker cannot be resolved from the stage packet.
When conditional reads are required, prefer section-level rereads over whole-file replay.

`data-model.md` remains the authoritative output for backbone shared semantics.
`PLAN_FILE` remains queue state plus binding projection state only.

## Required Writeback

After generating `data-model.md`, update only:

- selected `data-model` stage row `Status`, `Output Path`, `Source Fingerprint`, `Output Fingerprint`, `Blocker`
- affected `Artifact Status` rows only when alignment output changes contract-scoped readiness; keep writeback minimal to blocker/fingerprint fields
- do not rewrite `Binding Projection Index` rows or reopen `test-matrix` rows for this alignment path

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`: `/sdd.plan.contract`
- `Decision Basis`: Stage 2 interface partition decisions and binding packets remain authoritative for binding identity and test semantics; once shared semantic refs and constraints are aligned here, continue contract generation directly without rerunning `test-matrix`
- `Selected Stage ID`: selected `data-model` stage row id
- `Ready/Blocked`: `Ready` when the selected row is updated to `done`; otherwise `Blocked`

`Ready/Blocked` is stage-local readiness only and MUST NOT be treated as cross-artifact final PASS/FAIL; centralized final gating belongs to `/sdd.analyze`.

## Final Output

Report:

- resolved `PLAN_FILE`
- selected stage row id
- `data-model.md` path
- updated stage status
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected Stage ID`, and `Ready/Blocked`

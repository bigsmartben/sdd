---
description: Generate exactly one blocked-or-pending northbound interface design artifact selected from the current feature branch plan.md.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
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

Generate exactly one unified northbound interface design artifact by consuming the first `blocked` `contract` row from `PLAN_FILE` `Artifact Status`; if none exists, consume the first `pending` row.
This command MUST NOT generate multiple contract files in one run.
Use `.specify/templates/contract-template.md` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or prior generated artifacts.

`/sdd.plan.contract` is the first stage that performs repository-facing interface design reasoning.
Treat one `BindingRowID` as the single design unit for this run.
Treat the matched `Binding Projection Index` row as a minimal locator ledger only, not as a predesigned contract seed.
This stage must close:

- which northbound interface the selected `BindingRowID` lands on in the current repository
- what the external boundary is and where the internal implementation handoff begins
- how request / response semantics land as contract surface
- which shared semantics must be reused from `data-model.md`
- how realization design closes to executable implementation

This stage MUST NOT redefine how the binding was cut from `spec.md`; binding projection remains upstream `test-matrix` authority.

## Selection Rules

1. Run `{SCRIPT}` once from repo root. Resolve `FEATURE_DIR` and planning preflight context.
2. Resolve `PLAN_FILE` as `<FEATURE_DIR>/plan.md` and `FEATURE_SPEC` as `<FEATURE_DIR>/spec.md`; during row selection and prerequisite checks, read only the resolved `PLAN_FILE` (after selection, consume `Allowed Inputs`)
3. In `Artifact Status`, find the first row where:
   - `Unit Type = contract`
   - `Status = blocked`
4. If no blocked contract row exists, find the first row where:
   - `Unit Type = contract`
   - `Status = pending`
5. If no pending or blocked contract row exists, stop and report that the contract queue is complete
   - Note: `Artifact Status` contract rows are seeded by `/sdd.plan.test-matrix`; if `Artifact Status` contains no contract rows while the `test-matrix` stage row is `done`, this indicates a missing writeback — route back to `/sdd.plan.test-matrix` to repair before proceeding
6. Resolve the matching `BindingRowID` row in `Binding Projection Index`
7. Require `test-matrix` stage row to be `done`
8. Require `data-model` stage row to be `done`; if not, stop and route back to `/sdd.plan.data-model`
9. Attempt to resolve one selected binding packet in `test-matrix.md` by the same `BindingRowID`; if absent, stop and route back to `/sdd.plan.test-matrix`
10. Resolve the selected packet's `Primary TM IDs`, `TM IDs`, and `TC IDs` in `test-matrix.md`; if they are missing or inconsistent, stop and route back to `/sdd.plan.test-matrix`
11. Resolve the selected packet's `Spec Ref(s)`, `Scenario Ref(s)`, `Success Ref(s)`, and `Edge Ref(s)`; if they are missing or inconsistent with the same `BindingRowID`, stop and route back to `/sdd.plan.test-matrix`

## Plan Control-Plane Input Path (Mandatory)

Use only the resolved `PLAN_FILE` from `{SCRIPT}` as planning control plane.
Ignore alternate `plan.md` paths from environment variables or repository discovery.
Non-`plan.md` user files are allowed only when already listed in `Allowed Inputs`; they never redefine control-plane state.
If `PLAN_FILE` is missing or non-consumable, stop and report a blocker.

## Reasoning Strategy (Mandatory)

- Stay inside the resolved `FEATURE_DIR` plus the explicit files listed in `Allowed Inputs`.
- Complete `BindingRowID` selection and prerequisite validation from the resolved `PLAN_FILE` before reading `test-matrix.md`, `spec.md`, `data-model.md`, or repo anchors.
- Before that point, do not open repository files, generated artifacts, or run repository-wide discovery/search.
- Build one run-local `Selected Binding Context` from:
  - selected `Artifact Status` row
  - matching `Binding Projection Index` row
  - selected `Binding Packet`
  - selected `Scenario Matrix` rows
  - selected `Verification Case Anchors` rows
  - resolved spec slices addressed by the selected refs
  - binding-scoped shared-semantic slices from `data-model.md`
- `Selected Binding Context` is runtime working state only. Do not write it back into `plan.md`, and do not treat it as a new semantic authority.
- Use this fixed four-step reasoning order:
  1. requirement projection
  2. spec semantics
  3. shared semantic reuse
  4. repo closure

### Requirement Projection

- Treat the selected packet as demand projection only through `BindingRowID`, `IF Scope`, `User Intent`, `Trigger Ref(s)`, `Request Semantics`, `Visible Result`, `Side Effect`, `Boundary Notes`, `Repo Landing Hint`, `UIF Path Ref(s)`, `UDD Ref(s)`, `Primary TM IDs`, `TM IDs`, `TC IDs`, `Spec Ref(s)`, `Scenario Ref(s)`, `Success Ref(s)`, and `Edge Ref(s)`.
- Treat `Scenario Matrix` and `Verification Case Anchors` as the observable behavior boundary the contract must preserve.
- Treat the selected packet as a downstream scope-reference packet, not as a predesigned contract seed.
- `Operation ID` is finalized in this stage; it is not required as a precise upstream packet field.

### Spec Semantics

- `spec.md` is the authority for user trigger, external I/O semantics, UDD-visible data, and success/failure meaning behind the selected binding.
- Reconstruct request / response meaning from `UC`, `FR`, `UIF`, `UDD`, and scenario refs before reading repo evidence.

### Shared Semantic Reuse

- `data-model.md` is the authority for shared owner/source alignment, field vocabulary, lifecycle/invariant vocabulary, and downstream contract constraints reused by this binding.
- Reuse shared semantics here; do not mint new shared-semantic classes, owners/sources, lifecycle vocabulary, or invariants locally.

### Repo Closure

- Repo evidence is mandatory for evaluating `existing`, `extended`, and `new` closure and for landing any repo-backed symbols used by the selected design.
- Keep repo-backed verification bounded to the selected `BindingRowID` and active blockers; if ambiguity remains, keep unresolved items explicit as `todo` / `gap` instead of widening scope.
- Do not assume the selected packet already contains boundary/entry/DTO/collaborator closure; infer those surfaces here from requirement projection, shared semantics, and bounded repo evidence.
- Bounded repo closure MUST end with one explicit boundary/entry decision: `existing`, `extended`, `new`, or `todo`; do not keep searching for alternate entry chains after the bounded read set is exhausted.

## Unified Design Requirements

- Use `BindingRowID` as the only design unit for the run.
- Read requirement projection first, then shared semantic constraints, then land the design in repository evidence.
- `Contract Summary` is reader-oriented only: summarize external request/response, visible outcomes, and side effects without competing with field-level contract authority.
- `Full Field Dictionary (Operation-scoped)` is the only authoritative field-level contract surface: it MUST cover request DTO fields, response DTO fields, selected state-owner fields, and the fields directly used for reads, writes, projections, validation, defaults, or state decisions.
- `Full Field Dictionary (Operation-scoped)` MUST classify rows using `Dictionary Tier = operation-critical|owner-residual`, and list `operation-critical` rows first.
- `contract` is the first stage that MUST produce:
  - `Operation ID`
  - `Boundary Anchor`
  - `Implementation Entry Anchor`
  - request / response surface
  - full field dictionary
  - collaborator chain
  - sequence / UML realization design
  - downstream execution projection
- `Operation ID` MUST be concrete and MUST NOT be `N/A`.
- `collaborator chain` closure MUST be explicit in `UML Class Design` + `Sequence Design` (optionally with a dedicated collaborator table).
- This stage MAY design concrete `new` operation-scoped boundary/entry/DTO/collaborator surfaces when the selected semantic slices fully close the binding and one implementation-facing target can be named.
- If bounded repo reads cannot close `existing` or `extended` boundary/entry anchors, this stage MUST evaluate one concrete `new` anchor set before stopping.
- If `Anchor Status (Required) = new`, `Boundary Anchor Strategy Evidence (Required)` MUST include explicit rejection evidence for both `existing` and `extended`.
- If `Implementation Entry Anchor Status (Required) = new`, `Implementation Entry Anchor Strategy Evidence (Required)` MUST include explicit rejection evidence for both `existing` and `extended`.
- If an anchor status is not `new`, set the corresponding strategy evidence field to `N/A`.
- Do not mark the row `blocked` only because no existing repo entry anchor was found when a concrete `new` anchor set can be named and fully closed in this run.
- For first-party internal `new` anchors, choose repository-style names (`*Controller`, `*Service`, `*ServiceImpl`) unless the selected boundary is explicitly an adapter/facade surface.
- This stage MAY refine operation-scoped VO/DTO/field mappings from upstream shared semantics, but it MUST NOT mint new shared-semantic classes, owners/sources, lifecycle vocabulary, or invariants.
- Do not delete owner fields that this operation does not use; keep them in the field dictionary with `Used in <Operation ID> = no`.
- Realization design scope is delivery-ready: internal handoff, failure propagation, sequence closure, UML ownership, and southbound dependency chain.
- Fill `Test Projection` with one executable slice for the selected `IF Scope` / `Operation ID`.
- Derive `Main Pass Anchor` and `Branch/Failure Anchor(s)` in this stage from `Primary TM IDs`, `TM IDs`, `TC IDs`, `Scenario Ref(s)`, `Success Ref(s)`, `Edge Ref(s)`, and the landed interface design; do not require `test-matrix.md` to pre-close them.
- Fill `Cross-Interface Smoke Candidate (Required)` with exactly one row for the selected operation.
- `Cross-Interface Smoke Candidate (Required)` row MUST declare one `Candidate Role` in `entry|middle|exit|none`.
- If `Candidate Role != none`, `Main Pass Anchor` and `Command / Assertion Signal` MUST be explicit and executable.
- If `Candidate Role = none`, keep the row with explicit `N/A` values instead of omitting the section.
- Sequence design MUST start from consumer/client entry and reach the internal implementation entry within the first two request hops.
- Sequence design MUST remain end-to-end contiguous at current document granularity; no disconnected hops, orphan participants, or broken return chains.
- Each declared behavior path MUST map to one contiguous ordered sequence step chain from trigger entry to contract-visible outcome/failure.
- Sequence design MUST explicitly render every mandatory repo-backed collaborator hop in the selected behavior path, including second-party/third-party call-chain segments when present.
- Sequence design MUST NOT collapse multiple mandatory collaborators/dependencies into one synthetic participant label.
- `opt` blocks are valid only for truly conditional branches; mandatory main-path collaborator/dependency calls MUST NOT be rendered as optional.
- If inferred `Boundary Anchor` and `Implementation Entry Anchor` resolve to the same repo-backed symbol, do not invent a relay hop; reuse one participant/class in sequence and UML.
- UML MUST cover all executable sequence participants at this document granularity.
- Every sequence call MUST map to an owning UML method with directed caller/callee relationship.
- UML request/response class labels should use anchored symbols or repository boundary naming conventions; do not synthesize placeholder DTO labels.
- Any newly introduced field/method/call MUST be explicitly marked as new and connected to owner/consumer or caller/callee.
- If the selected design uses `new` northbound anchors plus reused `existing` downstream implementation, keep those layers explicit in UML and sequence instead of collapsing them into one entry symbol.
- Any `new` operation-scoped holder/state class MUST close owner, creator, reader, and writer responsibilities before the row can be marked `done`.

## Concrete Naming Closure (Mandatory)

- Every class/type/callable name that appears in the generated contract MUST be concrete before the row can be marked `done`; do not leave angle-bracket placeholders such as `<BoundaryRequestModel>` or `<ContractBoundaryEntry>` in the final artifact.
- Apply the anchor decision order `existing -> extended -> new -> todo`.
- A contract may define operation-scoped classes/types in this stage when upstream has not already fixed them, but those names MUST be concrete, uniquely named, and MUST stay inside the selected operation boundary.
- `new` is legal only when Interface Definition, Full Field Dictionary, Sequence, UML, and Test Projection all close on the same concrete names for this binding.
- When `new` operation-scoped anchors are selected, freeze that naming for this run and finish the contract instead of reopening anchor search loops.
- If continuing would require inventing a new shared-semantic class/owner/source rather than an operation-scoped contract detail, stop and route upstream to `/sdd.plan.data-model`.

## Repo Anchor Decision Protocol (Mandatory)

- Use the repo-anchor decision protocol in `.specify/templates/contract-template.md` as the authority for this stage.
- In this command, apply that protocol only for bounded verification and routing; do not widen the semantic scope of the selected binding.

## Allowed Inputs

Read only these inputs:

- `.specify/templates/contract-template.md` for output structure
- selected control-plane rows from the resolved `PLAN_FILE`
  - selected `Artifact Status` row
  - matching `Binding Projection Index` row
  - `Shared Context Snapshot`
- semantic inputs
  - selected binding packet from `test-matrix.md`
  - selected `Scenario Matrix` rows from `test-matrix.md`
  - selected `Verification Case Anchors` rows from `test-matrix.md`
  - resolved `FEATURE_SPEC`
  - binding-scoped shared semantic slices from `data-model.md`
- bounded repo closure inputs
  - inferred boundary entry target
  - inferred implementation entry target
  - inferred request / response DTO surface
  - required collaborators and middleware
  - required owner/source symbols
  - required package/module relation evidence

Do not read `research.md` in this stage.

### Repo Closure Limits

- Do not run repository-wide discovery or broad symbol scans.
- Read only the minimum repo-backed targets required to close the selected binding.
- After bounded reads, stop anchor hunting and transition to closure output for this run: either concrete `new` anchors or explicit blocker evidence.
- If required evidence is still missing after bounded reads:
  - set missing anchor to `TODO(REPO_ANCHOR)` when neither bounded repo evidence nor one concrete `new` closure can supply the required anchor token
  - keep explicit gap rows in `Full Field Dictionary (Operation-scoped)` instead of shrinking the contract
  - set `Artifact Status` blocker details precisely instead of widening scope

After generation, the selected artifact under `contracts/` becomes the authoritative source for interface semantics and realization design semantics for that binding.
`PLAN_FILE` remains queue state plus stable binding keys only.

## Block And Route Upstream

Stop local refinement and route upstream when continuing would require a new upstream shared semantic:

- `/sdd.plan.data-model` when the contract would need a new shared semantic owner/source, a new backbone semantic element, a new cross-operation stable owner field, new shared lifecycle/invariant vocabulary, downstream contract constraints that are not yet declared, or a field would drift across bindings if invented locally
- `/sdd.plan.test-matrix` only when the selected `BindingRowID`, `IF Scope`, `User Intent`, `Trigger Ref(s)`, `Request Semantics`, `Visible Result`, `Side Effect`, `Boundary Notes`, `Repo Landing Hint`, `UIF Path Ref(s)`, `UDD Ref(s)`, `Primary TM IDs`, `TM IDs`, `TC IDs`, `Spec Ref(s)`, `Scenario Ref(s)`, `Success Ref(s)`, or `Edge Ref(s)` are missing, inconsistent, or projected to the wrong binding

Do not route upstream for boundary/entry/DTO/collaborator inference, operation-scoped field selection, VO/DTO projection shape, default/validation detail, or realization-design detail that can be derived from the existing upstream boundary.
Do not route upstream only because no existing repo entry was found; when shared semantics are stable, close locally with one concrete `new` anchor set.

## Required Writeback

Update only the selected contract row in `Artifact Status`:

- `Target Path`
- `Status`
- `Blocker`

If repo-backed verification finds a binding-projection error or shared-semantic gap, keep it explicit in the generated contract and route repair to `/sdd.plan.test-matrix` or `/sdd.plan.data-model`; do not rewrite upstream planning artifacts from this command.

Set `Artifact Status` row `Status = blocked` when `Full Field Dictionary (Operation-scoped)` still contains key gaps, when shared-semantic reuse cannot be closed, or when the selected binding projection is inconsistent.
Set `Artifact Status` row `Status = blocked` when `Operation ID` is missing, placeholder-like, or `N/A`.
Set `Artifact Status` row `Status = blocked` when closure still fails after evaluating `existing -> extended -> new -> todo` with bounded evidence.
Set `Artifact Status` row `Status = done` only when `Operation ID` is concrete and the field dictionary is present with key gaps resolved.

Do not modify unrelated `BindingRowID` rows.
Do not modify `Binding Projection Index` or `Stage Queue`.
Do not write contract/design prose or tuple corrections into `PLAN_FILE`.

## Feature-Level Smoke Readiness (Queue-Complete Gate)

After selected-row status update, if no `contract` rows remain `blocked` or `pending`, treat cross-interface smoke input as planning-complete required output:

- All completed contract artifacts MUST contain `Cross-Interface Smoke Candidate (Required)` with one row each.
- At least one completed contract artifact MUST declare `Candidate Role != none`.
- If either condition fails, keep routing to `/sdd.plan.contract` with `Ready/Blocked = Blocked` and explicit blocker details.

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`
- `Decision Basis`
- `Selected BindingRowID`: selected `BindingRowID`
- `Ready/Blocked`

`Ready/Blocked` is stage-local readiness only and MUST NOT be treated as cross-artifact final PASS/FAIL; centralized final gating belongs to `/sdd.analyze`.

Determine `Next Command` from the resolved `PLAN_FILE` state only after the selected contract row status update:

- If any `contract` rows remain `blocked`, `Next Command = /sdd.plan.contract`
- Otherwise, if any `contract` rows remain `pending`, `Next Command = /sdd.plan.contract`
- Otherwise, if all required planning rows (`research`, `test-matrix`, `data-model`, and all queued `contract` rows) are complete, `Next Command = /sdd.tasks`
- Otherwise, if queue state is inconsistent with either condition, keep `Next Command` empty and set `Ready/Blocked = Blocked`

`Decision Basis` MUST cite the post-update `Artifact Status` state and planning-complete check that produced the routing decision.

## Final Output

Report:

- resolved `PLAN_FILE`
- selected `BindingRowID`
- generated contract path
- updated contract row status
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected BindingRowID`, and `Ready/Blocked`

---
description: Generate the pending data-model.md artifact selected from the current feature branch plan.md.
handoffs:
  - label: Continue Test Matrix Queue
    agent: sdd.plan.test-matrix
    prompt: Run /sdd.plan.test-matrix with the same active feature branch context.
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
`spec.md` + `research.md` define model semantics; repo anchors are correction/traceability evidence only.
The output MUST define the full spec-scoped backbone semantics set and stable boundary that downstream planning stages are allowed to reuse; introduce classes only when a stable owner or reusable contract boundary exists.
Use `.specify/templates/data-model-template.md` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or other `data-model.md` outputs.

## Selection Rules

1. Run `{SCRIPT}` once from repo root and parse `FEATURE_DIR`, `AVAILABLE_DOCS`, and `DATA_MODEL_BOOTSTRAP`.
2. Treat `DATA_MODEL_BOOTSTRAP.generation_readiness` as the primary hard gate.
3. If `DATA_MODEL_BOOTSTRAP.generation_readiness.ready_for_generation = true`, reuse the selected stage row, resolved `plan.md` / `spec.md` / `research.md` / `data-model.md` paths, and `state_machine_policy` from `DATA_MODEL_BOOTSTRAP`; do not rescan for alternate pending rows.
4. If `DATA_MODEL_BOOTSTRAP` is missing, malformed, or contradictory, perform one bounded fallback validation from `plan.md` control-plane fields plus current `spec.md` / `research.md` availability.
5. In fallback mode only, read the resolved `IMPL_PLAN`, find the first `Stage Queue` row where `Stage ID = data-model` and `Status = pending`, require the `research` row to be `done`, and stop on any blocker.

## Stage Packet (Data-Model Unit)

Build one bounded run-local packet for the selected `data-model` row from:

- selected `Stage Queue` row in resolved `PLAN_FILE`
- `Shared Context Snapshot` in resolved `PLAN_FILE`
- resolved `FEATURE_SPEC` path
- resolved `research.md` path
- selected row source/output fingerprint fields

Use this packet as the default context for generation.
Do not load additional artifacts unless the selected-row blocker or lifecycle constraints require them.

Apply the constitution-derived lifecycle applicability policy from `DATA_MODEL_BOOTSTRAP.state_machine_policy` while writing lifecycle sections:

- For each declared lifecycle, count distinct stable states as `N`.
- Count unique effective transitions (`FromState -> ToState`) as `T`.
- If `N > 3` or `T >= 2N`, emit a full FSM package: transition table, transition pseudocode, and state diagram.
- Otherwise keep the lifecycle lightweight: state field definition, allowed transitions, forbidden transitions, and key invariants.
- If you still choose a full FSM below threshold, record explicit justification in the lifecycle section.

## Stop Conditions

Stop immediately when any condition holds:

1. Resolved branch-derived `PLAN_FILE` is missing or invalid.
2. `DATA_MODEL_BOOTSTRAP.generation_readiness.ready_for_generation = false`.
3. `DATA_MODEL_BOOTSTRAP` fallback validation cannot reconstruct a consumable stage packet.
4. `DATA_MODEL_BOOTSTRAP.generation_readiness.errors` contains blockers.
5. Required targeted repo-anchor evidence for the selected unit cannot be resolved with bounded selected-unit reads.

## Plan Control-Plane Input Path (Mandatory)

Use only the resolved `PLAN_FILE` from `{SCRIPT}` as planning control plane.
Ignore alternate `plan.md` paths from environment variables or repository discovery.
Non-`plan.md` user files are allowed only when already listed in `Allowed Inputs`; they never redefine control-plane state.
If `PLAN_FILE` is missing or non-consumable, stop and report a blocker.

## Path Constraints

- Stay inside the resolved `FEATURE_DIR` plus the explicit files listed in `Allowed Inputs`.
- Derive entity/relationship/invariant semantics from `FEATURE_SPEC` and `research.md` first.
- Repo anchors are limited to naming correction, lifecycle vocabulary correction, and traceability.
- Lifecycle anchors MUST come from symbols/files explicitly referenced by `Shared Context Snapshot` or by a concrete blocker in the selected row.
- Finish row selection and prerequisite checks before broader repo reads; do not scan the repository for additional context, alternate `plan.md` paths, or other feature folders.
- Do not use any existing `data-model.md` outside the current target artifact path as an input or style source.
- Prefer section-level reads of `spec.md` and `research.md` that are relevant to the selected unit; avoid whole-file replay unless the selected row is blocked by missing local context.

## Repo Anchor Decision Protocol (Mandatory)

- Apply strict decision order for every repo-anchor choice: `existing -> extended -> new`.
- `extended` is valid only when the anchor already owns the same business identity and most globally stable fields/states.
- `new` is allowed in normative sections only when explicit `path::symbol` target evidence is provided.
- Transport wrappers, request/response DTOs, controller params, and context carriers are not normative same-entity anchors unless they already own materially aligned identity, lifecycle, and stable fields.
- If the closest repo evidence is carrier-only, keep the element `new` or `todo` and describe the carrier relationship narratively; do not upgrade anchor strength.
- Every selected `new` anchor in normative content MUST record:
  - why `existing` cannot satisfy the required semantics
  - why `extended` is insufficient or unsafe
  - the target repo-backed `path::symbol`
  - required upstream synchronization actions
- A planned-but-missing file path is not sufficient evidence for normative `new`; if the target file/symbol cannot be confirmed from allowed repo-backed reads, downgrade the item to `todo` and move it out of normative content.
- When reusing an anchored enum/state owner via `extended`, keep `Stable states` aligned to the anchored vocabulary; user-visible or mapped terms may be noted separately, but MUST NOT replace the anchored state names inside normative `Stable states`.
- If explicit `path::symbol` target evidence is missing, set status to `todo` and keep the item forward-looking/non-normative.
- Do not use repo anchors to invent business semantics; they only correct naming/lifecycle terms and provide traceability.

## Normative Consistency Checks (Lightweight)

Before writing `done` status for the selected row, validate:

- Normative anchors use strategy states `{existing, extended, new}`; `todo` remains forward-looking only.
- Every normative `new` anchor includes explicit rejection evidence for both `existing` and `extended`.
- Every globally stable projection, derivation, counter, badge, role label, or lifecycle guard identifies the owner class/field/state that sustains it; downstream `test-matrix.md` and `contracts/` MUST NOT invent missing state owners or owner fields that Stage 1 failed to declare.
- If a shared semantic depends on a missing owner field/state, keep the gap explicit in `data-model.md` and set the selected row `Blocker` instead of letting later stages backfill the model.

If any gate fails, do not mark the `data-model` row `done`; keep it non-done and populate `Blocker` with the exact missing anchor evidence.

## Allowed Inputs

Read only:

- `.specify/templates/data-model-template.md` for output structure
- selected `Stage Queue` row from the resolved `PLAN_FILE` only
- `Shared Context Snapshot` from the resolved `PLAN_FILE` only
- resolved `FEATURE_SPEC`
- `research.md`
- targeted lifecycle repo anchors required for stable states and invariants

### Conditional Inputs

Read additional files only when the selected-row blocker cannot be resolved from the stage packet.
When conditional reads are required, prefer section-level rereads over whole-file replay.

### Repo Anchor Input Limits

Keep repo-backed reads bounded to the selected unit and lifecycle/invariant blockers.
If bounded reads are insufficient, keep unresolved lifecycle/invariant evidence explicit in `data-model.md` and set row `Blocker` instead of expanding scope.

`data-model.md` remains the authoritative output for backbone semantics.
`PLAN_FILE` remains queue state plus binding projection state only.

## Required Writeback

After generating `data-model.md`, update the selected `Stage Queue` row only:

- `Status`
- `Output Path`
- `Source Fingerprint`
- `Output Fingerprint`
- `Blocker`

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`: `/sdd.plan.test-matrix`
- `Decision Basis`: `Stage Queue` shows the selected `data-model` row is complete and the fixed next pending stage is `test-matrix`
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

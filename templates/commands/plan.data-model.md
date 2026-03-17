---
description: Generate the pending data-model.md artifact selected from an explicit plan.md path.
handoffs:
  - label: Continue Test Matrix Queue
    agent: sdd.plan.test-matrix
    prompt: Run /sdd.plan.test-matrix <path/to/plan.md> with the same absolute plan.md path.
    send: true
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

1. Parse the first positional token from `$ARGUMENTS` as `PLAN_FILE`
2. `PLAN_FILE` is mandatory and MUST resolve from repo root to an existing file named `plan.md`
3. `PLAN_FILE` MUST stay under `repo/specs/**`
4. Any remaining text after removing `PLAN_FILE` is optional scoped user context

If `PLAN_FILE` is missing or invalid, stop immediately and report the required invocation:

`/sdd.plan.data-model <path/to/plan.md> [context...]`

## Goal

Generate exactly one `data-model.md` artifact by consuming the first pending `data-model` row from `PLAN_FILE`.
This command is single-unit only and MUST NOT perform any other planning stage work.
`spec.md` + `research.md` define model semantics; repo anchors are correction/traceability evidence only.
Use `.specify/templates/data-model-template.md` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or other `data-model.md` outputs.

## Selection Rules

1. Run `{SCRIPT} --plan-file <PLAN_FILE>` once and resolve `FEATURE_DIR`, `FEATURE_SPEC`, and `IMPL_PLAN`
2. Read only the resolved `IMPL_PLAN`
3. Find the first `Stage Queue` row where:
   - `Stage ID = data-model`
   - `Status = pending`
4. Require the `research` row to be `done`
5. If the required row does not exist or prerequisites are not done, stop and report the blocker

## Stage Packet (Data-Model Unit)

Build one bounded run-local packet for the selected `data-model` row from:

- selected `Stage Queue` row in explicit `PLAN_FILE`
- `Shared Context Snapshot` in explicit `PLAN_FILE`
- resolved `FEATURE_SPEC` path
- resolved `research.md` path
- selected row source/output fingerprint fields

Use this packet as the default context for generation.
Do not load additional artifacts unless the selected-row blocker or lifecycle constraints require them.

## Plan Control-Plane Input Path (Mandatory)

Use only the explicit `PLAN_FILE` resolved through `{SCRIPT}` as planning control plane.
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

- Apply strict decision order for every repo-anchor choice: `existing -> extended -> new -> todo`.
- `extended` is valid only for same-entity field/state expansion.
- `new` is allowed in normative sections only when explicit `path::symbol` target evidence is provided.
- If explicit `path::symbol` target evidence is missing, set status to `todo` and keep the item forward-looking/non-normative.
- Do not use repo anchors to invent business semantics; they only correct naming/lifecycle terms and provide traceability.

## Allowed Inputs

Read only:

- `.specify/templates/data-model-template.md` for output structure
- selected `Stage Queue` row from the explicit `PLAN_FILE` only
- `Shared Context Snapshot` from the explicit `PLAN_FILE` only
- resolved `FEATURE_SPEC`
- `research.md`
- targeted lifecycle repo anchors required for stable states and invariants

### Conditional Inputs

Read additional files only when the selected-row blocker cannot be resolved from the stage packet.
When conditional reads are required, prefer section-level rereads over whole-file replay.

### Repo Anchor Input Limits

Read at most five repo-backed files per data-model run.
If that cap is insufficient, keep unresolved lifecycle/invariant evidence explicit in `data-model.md` and set row `Blocker` instead of expanding scope.

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

- `Next Command`: `/sdd.plan.test-matrix <absolute path to plan.md>`
- `Decision Basis`: `Stage Queue` shows the selected `data-model` row is complete and the fixed next pending stage is `test-matrix`
- `Selected Stage ID`: selected `data-model` stage row id
- `Ready/Blocked`: `Ready` when the selected row is updated to `done`; otherwise `Blocked`

## Final Output

Report:

- resolved `PLAN_FILE`
- selected stage row id
- `data-model.md` path
- updated stage status
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected Stage ID`, and `Ready/Blocked`

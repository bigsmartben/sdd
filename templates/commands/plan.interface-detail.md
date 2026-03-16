---
description: Generate exactly one pending interface detail artifact selected from an explicit plan.md path.
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

`/sdd.plan.interface-detail <path/to/plan.md> [context...]`

## Goal

Generate exactly one minimum interface-detail artifact by consuming the first pending `interface-detail` row from `PLAN_FILE` `Artifact Status`.
This command MUST NOT generate multiple interface-detail files in one run.
Use `.specify/templates/interface-detail-template.md` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or prior generated interface-detail files.

## Selection Rules

1. Run `{SCRIPT} --plan-file <PLAN_FILE>` once and resolve `FEATURE_DIR`, `FEATURE_SPEC`, and `IMPL_PLAN`
2. Read only the resolved `IMPL_PLAN`
3. In `Artifact Status`, find the first row where:
   - `Unit Type = interface-detail`
   - `Status = pending`
4. Resolve the matching `BindingRowID` row in `Binding Projection Index`
5. Require the matching contract row for the same `BindingRowID` to be `done`
6. If no pending interface-detail row exists, stop and report that the queue is complete

## Plan Control-Plane Input Path (Mandatory)

- Use only the explicit `PLAN_FILE` resolved through `{SCRIPT}` as planning control plane.
- Ignore alternate `plan.md` paths from environment variables or repository discovery. Non-`plan.md` user files are allowed only when they are already listed in `Allowed Inputs`; they never redefine control-plane state.
- If `PLAN_FILE` is missing or non-consumable, stop and report a blocker.

## Path Constraints

- Stay inside the resolved `FEATURE_DIR` plus the explicit files listed in `Allowed Inputs`.
- Complete `BindingRowID` selection, matching contract-row resolution, and prerequisite validation from the explicit `PLAN_FILE` before reading `research.md`, `data-model.md`, `test-matrix.md`, the matching contract artifact, or any repo anchors.
- Before that point, do not open repository files, generated artifacts, or run repository-wide discovery/search.
- After selection, read only the selected row's planning inputs, the matching contract artifact, and the targeted symbols/files required for that `BindingRowID`.

## Internal Handoff Design Requirements

- Treat this artifact as the detailed-design handoff of the selected contract row, not a restatement of contract prose.
- Keep `Operation ID` / `Boundary Anchor` / `IF Scope` aligned to the selected contract binding row.
- Add and anchor `Implementation Entry Anchor` to the first internal handoff entry that realizes the selected contract boundary.
- Keep contract restatement out: explain only behavior-significant field semantics, internal ownership/mapping, and failure propagation.
- Sequence design must start from client/consumer entry and reach `Implementation Entry Anchor` within the first two request hops.
- If both controller and facade exist, show both in sequence order and keep handoff explicit.
- Explain internal responsibility flow through the smallest complete handoff set that still explains contract-visible outcomes.
- Require UML field-level ownership for all contract-visible request/response fields and behavior-significant fields from `Field Semantics`.

## Allowed Inputs

Read only:

- `.specify/templates/interface-detail-template.md` for output structure
- selected `Artifact Status` row from the explicit `PLAN_FILE` only
- matching `BindingRowID` row from `Binding Projection Index` in the explicit `PLAN_FILE` only
- `Shared Context Snapshot` from the explicit `PLAN_FILE` only
- `research.md` when constraints materially affect this `BindingRowID`
- `data-model.md`
- `test-matrix.md`
- matching contract artifact
- targeted repo boundary/entry/DTO/collaborator anchors required for the selected `BindingRowID` (for example route/controller, facade, service, manager, mapper/gateway)

After generation, the selected artifact under `interface-details/` becomes the authoritative source for operation-local design semantics for that binding.
`PLAN_FILE` remains queue state plus stable binding keys only.

## Required Writeback

Update only the selected interface-detail row in `Artifact Status`:

- `Target Path`
- `Status`
- `Source Fingerprint`
- `Output Fingerprint`
- `Blocker`

Do not modify unrelated `BindingRowID` rows.
Do not write interface-detail prose into `PLAN_FILE`.

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`
- `Decision Basis`
- `Selected BindingRowID`: selected `BindingRowID`
- `Ready/Blocked`

Determine `Next Command` from the explicit `PLAN_FILE` state only after the selected interface-detail row writeback:

- If any `interface-detail` rows remain `pending`, `Next Command = /sdd.plan.interface-detail <absolute path to plan.md>`
- Otherwise, if all required planning rows are complete, `Next Command = /sdd.tasks`
- Otherwise, if queue state is inconsistent with either condition, keep `Next Command` empty and set `Ready/Blocked = Blocked`

`Decision Basis` MUST cite the post-writeback `Artifact Status` state and planning-complete check that produced the routing decision.

## Final Output

Report:

- resolved `PLAN_FILE`
- selected `BindingRowID`
- generated interface-detail path
- updated interface-detail row status
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected BindingRowID`, and `Ready/Blocked`

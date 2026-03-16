---
description: Generate exactly one pending contract artifact selected from an explicit plan.md path.
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

`/sdd.plan.contract <path/to/plan.md> [context...]`

## Goal

Generate exactly one minimum contract artifact by consuming the first pending `contract` row from `PLAN_FILE` `Artifact Status`.
This command MUST NOT generate multiple contract files in one run.
Use `.specify/templates/contract-template.md` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or prior generated contracts.

## Selection Rules

1. Run `{SCRIPT} --plan-file <PLAN_FILE>` once and resolve `FEATURE_DIR`, `FEATURE_SPEC`, and `IMPL_PLAN`
2. Read only the resolved `IMPL_PLAN`
3. In `Artifact Status`, find the first row where:
   - `Unit Type = contract`
   - `Status = pending`
4. Resolve the matching `BindingRowID` row in `Binding Projection Index`
5. Require `test-matrix` stage row to be `done`
6. If no pending contract row exists, stop and report that the contract queue is complete

## Plan Control-Plane Input Path (Mandatory)

- Use only the explicit `PLAN_FILE` resolved through `{SCRIPT}` as planning control plane.
- Ignore alternate `plan.md` paths from environment variables or repository discovery. Non-`plan.md` user files are allowed only when they are already listed in `Allowed Inputs`; they never redefine control-plane state.
- If `PLAN_FILE` is missing or non-consumable, stop and report a blocker.

## Path Constraints

- Stay inside the resolved `FEATURE_DIR` plus the explicit files listed in `Allowed Inputs`.
- Complete `BindingRowID` selection and prerequisite validation from the explicit `PLAN_FILE` before reading `spec.md`, `data-model.md`, `test-matrix.md`, or any repo anchors.
- Before that point, do not open repository files, generated artifacts, or run repository-wide discovery/search.
- After selection, read only the selected row's planning inputs and the targeted symbols/files required for that `BindingRowID`.

## Boundary Anchor Selection (Client Entry First)

- Treat this contract as the UIF/client-facing entry artifact for the selected binding.
- Select `Boundary Anchor` as the first consumer-callable entry, not an internal service/manager/mapper hop.
- If the operation is consumer-called via HTTP, prefer `HTTP METHOD /path` and keep any controller symbol as repo anchor evidence.
- If the operation is consumer-called via RPC/facade, use the anchored `Facade.method` surface.
- If both HTTP/controller and facade symbols exist, keep the actual consumer-visible first callable entry as normative `Boundary Anchor`; downstream internal handoff belongs in interface-detail.

## Allowed Inputs

Read only:

- `.specify/templates/contract-template.md` for output structure
- selected `Artifact Status` row from the explicit `PLAN_FILE` only
- matching `BindingRowID` row from `Binding Projection Index` in the explicit `PLAN_FILE` only
- `Shared Context Snapshot` from the explicit `PLAN_FILE` only
- resolved `FEATURE_SPEC`
- `data-model.md`
- `test-matrix.md`
- targeted repo boundary symbols (route/controller and/or façade as applicable), plus DTO anchors required for the selected `BindingRowID`

After generation, the selected artifact under `contracts/` becomes the authoritative source for interface semantics for that binding.
`PLAN_FILE` is queue state plus stable binding keys only.

## Required Writeback

Update only the selected contract row in `Artifact Status`:

- `Target Path`
- `Status`
- `Source Fingerprint`
- `Output Fingerprint`
- `Blocker`

Do not modify unrelated `BindingRowID` rows.
Do not write contract semantics into `PLAN_FILE`.

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`
- `Decision Basis`
- `Selected BindingRowID`: selected `BindingRowID`
- `Ready/Blocked`

Determine `Next Command` from the explicit `PLAN_FILE` state only after the selected contract row writeback:

- If any `contract` rows remain `pending`, `Next Command = /sdd.plan.contract <absolute path to plan.md>`
- Otherwise, if no `contract` rows remain `pending` and at least one `interface-detail` row is `pending`, `Next Command = /sdd.plan.interface-detail <absolute path to plan.md>`
- Otherwise, if queue state is inconsistent with either condition, keep `Next Command` empty and set `Ready/Blocked = Blocked`

`Decision Basis` MUST cite the post-writeback `Artifact Status` state that produced the routing decision.

## Final Output

Report:

- resolved `PLAN_FILE`
- selected `BindingRowID`
- generated contract path
- updated contract row status
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected BindingRowID`, and `Ready/Blocked`

---
description: Orchestrate the planning phase from an explicit spec.md path by generating plan.md control-plane state, Stage 0 shared context, and the full handoff queue.
handoffs:
  - label: Start Research Queue
    agent: sdd.plan.research
    prompt: Continue the planning queue by running /sdd.plan.research <path/to/plan.md> with the explicit plan.md path resolved in the previous step.
    send: true
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Argument Parsing

Parse `$ARGUMENTS` in this exact order before doing any planning work:

1. The first positional token is mandatory and is `SPEC_FILE`
2. `SPEC_FILE` MUST resolve from repo root to an existing file named `spec.md`
3. `SPEC_FILE` MUST stay under `repo/specs/**`
4. The optional second positional token may be the reserved uppercase literal `ALL`
5. Any remaining text after removing `SPEC_FILE` and optional `ALL` is user planning context

If the first positional token is missing or invalid, stop immediately and report the required invocation shape:

`/sdd.plan <path/to/spec.md> [ALL] [technical-context...]`

## Goal

`/sdd.plan` is the planning control-plane entrypoint.

Default mode responsibilities are limited to:

1. Build the Stage 0 `Shared Context Snapshot` inside `plan.md`
2. Initialize and refresh the planning queue, binding projection ledger, artifact status, and source-fingerprint tracking

When the reserved `ALL` token is present, `/sdd.plan` becomes the autonomous planning runner:

1. Initialize or refresh `plan.md` from `SPEC_FILE`
2. Continue the planning queue in current handoff order
3. Stop immediately on the first blocker or queue inconsistency

Without `ALL`, `/sdd.plan` does **not** generate downstream planning-stage artifacts directly.

## Setup

Run `{SCRIPT} --spec-file <SPEC_FILE>` once from repo root and parse JSON for `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR`, and `BRANCH`.
All paths must be absolute.

Treat the resolved `IMPL_PLAN` as the canonical `PLAN_FILE` for all downstream planning commands and runtime handoff output.

## Repository-First Inputs (Mandatory)

`/sdd.plan` MUST consume the canonical repository-first baseline produced by `/sdd.constitution`:

1. `.specify/memory/repository-first/technical-dependency-matrix.md`
2. `.specify/memory/repository-first/domain-boundary-responsibilities.md`
3. `.specify/memory/repository-first/module-invocation-spec.md`

Fail fast and route to `/sdd.constitution` if any canonical baseline artifact is missing, stale, or non-traceable.

## Stage 0 Shared Context Snapshot

Generate the `Shared Context Snapshot` section inside `plan.md` from these inputs only:

- resolved `SPEC_FILE`
- `.specify/memory/constitution.md`
- `.specify/memory/repository-first/*`
- remaining user planning context after argument parsing

Do **not** read or reuse `research.md`, `data-model.md`, `test-matrix.md`, `contracts/`, or `interface-details/` when building Stage 0.
Do **not** materialize a separate `shared-context.md` file.

The snapshot must remain bounded to shared bootstrap facts only:

- feature identity and scope anchors
- actors, in-scope / out-of-scope, stable UC/UIF/FR references
- constitution-level constraints that affect every downstream stage
- repository-first consumption slice relevant to this feature
- shared blockers and must-read anchors

Do **not** write long summaries, audit payload, planning-stage prose, or execution logs into the snapshot.

## Planning Control Plane Requirements

Use `.specify/templates/plan-template.md` as the structure source for `plan.md`. This runtime template path is mandatory; if the file is missing or non-consumable, stop and report the blocker. Do not substitute `templates/plan-template.md` or any other template location.
The generated `plan.md` is the sole planning control plane and MUST contain exactly these functional content dimensions:

1. downstream-consumption context: `Shared Context Snapshot`
2. orchestration context: `Stage Queue` and `Artifact Status`
3. binding-key context: `Binding Projection Index`

`plan.md` is a derived planning control plane. It is authoritative for planning queue state, binding-index rows, and source/output fingerprints only. It MUST NOT replace downstream planning artifacts as the semantic source of truth.
Queue rows, binding rows, fingerprints, and other control-plane restatements are derived views only; they MUST NOT override upstream artifacts or downstream stage artifacts.

## Queue Initialization Rules

Initialize or refresh `plan.md` with:

### Stage Queue

Seed exactly three stage rows in fixed order:

1. `research`
2. `data-model`
3. `test-matrix`

For each row include:

- stage id
- command name
- required inputs
- output path
- status (`pending`, `in_progress`, `done`, `blocked`)
- source fingerprint
- output fingerprint
- blocker

### Binding Projection Index

Initialize the table structure but leave it empty until `/sdd.plan.test-matrix` produces stable binding rows.

Required columns:

- `BindingRowID`
- `UC ID`
- `UIF ID`
- `FR ID`
- `IF ID / IF Scope`
- `TM ID`
- `TC IDs`
- `Operation ID`
- `Boundary Anchor`

### Artifact Status

Initialize the table structure but leave it empty until binding rows exist.

Required columns:

- `BindingRowID`
- `Unit Type`
- `Target Path`
- `Status`
- `Source Fingerprint`
- `Output Fingerprint`
- `Blocker`

## Handoff Model

Frontmatter `handoffs` are static advisory metadata only.
Use at most one unconditional handoff target in frontmatter.
If the next command depends on `plan.md` queue state, child commands MUST emit that result through `Handoff Decision` in the runtime output instead of encoding branching paths in frontmatter.

Child-command selection rules are non-negotiable:

- `/sdd.plan.research <path/to/plan.md>` takes the first `research` row in `Stage Queue` with status `pending`
- `/sdd.plan.data-model <path/to/plan.md>` takes the first `data-model` row in `Stage Queue` with status `pending`
- `/sdd.plan.test-matrix <path/to/plan.md>` takes the first `test-matrix` row in `Stage Queue` with status `pending`
- `/sdd.plan.contract <path/to/plan.md>` takes the first `Artifact Status` row where `Unit Type = contract` and `Status = pending`
- `/sdd.plan.interface-detail <path/to/plan.md>` takes the first `Artifact Status` row where `Unit Type = interface-detail`, `Status = pending`, and the matching contract row is `done`

Child commands MUST NOT scan the repository to invent the next target.
They MUST consume queue state from the explicit `PLAN_FILE` only.

## Runtime Rules

- Keep `/sdd.plan` orchestration-only when `ALL` is absent; do not generate downstream planning artifacts here.
- In `ALL` mode, execute the existing planning queue autonomously in this order only: `research -> data-model -> test-matrix -> contract* -> interface-detail*`.
- In `ALL` mode, after each writeback, recompute the next step from post-writeback `PLAN_FILE` queue state only.
- In `ALL` mode, never skip pending rows, never reorder unit selection, and never continue past a blocker.
- Keep queue rows and binding rows minimal and deterministic.
- Record source fingerprints from the direct authoritative inputs of each queue row.
- Record output fingerprints after each row completes.
- Allow only minimal child-command writeback: status, output path, blocker, source fingerprint, output fingerprint.
- Do not append long summaries or stage bodies back into `plan.md`.
- `README.md`, `docs/**`, `specs/**`, `tests/**`, `plans/**`, `templates/**`, demos, and generated artifacts are supporting inputs only and MUST NOT be promoted into repo semantic anchors.

## Stop Conditions

Stop immediately when any of the following occurs:

- `SPEC_FILE` is missing, invalid, outside `repo/specs/**`, or not named `spec.md`
- required repository-first canonical baseline files are missing or stale
- constitution-level constraints block downstream planning
- required shared bootstrap anchors cannot be stabilized from authoritative inputs
- `plan.md` cannot be initialized with the required control-plane sections
- `ALL` mode encounters a blocked queue row or inconsistent post-writeback routing state

## Final Output

Always write or refresh `plan.md` first, then report:

- branch
- resolved `SPEC_FILE` absolute path
- `plan.md` absolute path
- initialized `Stage Queue`
- initialized `Binding Projection Index` row count
- initialized `Artifact Status` row count

If `ALL` is absent, also report:

- explicit next command: `/sdd.plan.research <absolute path to plan.md>`
- explicit handoff order: `sdd.plan.research -> sdd.plan.data-model -> sdd.plan.test-matrix -> sdd.plan.contract -> sdd.plan.interface-detail`

If `ALL` is present, also report:

- autonomous mode status: `completed` or `blocked`
- last completed stage or binding row
- next required command with explicit file path when blocked

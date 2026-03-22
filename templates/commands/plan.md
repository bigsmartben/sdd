---
description: Orchestrate the planning phase from the current feature branch by generating plan.md control-plane state, Stage 0 shared context, the stage queue, and empty downstream ledgers.
handoffs:
  - label: Start Research Queue
    agent: sdd.plan.research
    prompt: Run /sdd.plan.research with the same active feature branch context.
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

Treat all `$ARGUMENTS` as user planning context.
Resolve `SPEC_FILE` from the current feature branch using `{SCRIPT}` defaults.

## Goal

`/sdd.plan` is the planning control-plane entrypoint.

Do only four things:

1. Build the Stage 0 `Shared Context Snapshot` inside `plan.md`
2. Seed the fixed `Stage Queue`
3. Initialize an empty `Binding Projection Index`
4. Initialize an empty `Artifact Status`

`/sdd.plan` does **not** generate downstream planning-stage artifacts directly.
`/sdd.plan` does **not** project binding rows, shared semantics, or interface-design conclusions.

## Governance Guardrails (Mandatory)

- **Authority rule**: `plan.md` is authoritative only for planning control-plane state (queue rows, binding-index projections, artifact status). It MUST NOT override semantic authority owned by `spec.md`, `research.md`, `data-model.md`, `test-matrix.md`, or `contracts/`.
- **Stage boundary rule**: `/sdd.plan` is orchestration-only. Do not emit downstream stage bodies, shared-semantic conclusions, implementation ownership semantics, or contract schema details.
- **Gate ownership rule**: `/sdd.plan` may report local orchestration readiness (`pending`, `in_progress`, `done`, `blocked`) only. Cross-artifact final PASS/FAIL is owned by `/sdd.analyze`.

## Planning Sharding Model (Mandatory)

Keep the two-layer sharding model for planning runs:

1. Stage sharding (fixed): delivery path `research -> test-matrix -> data-model`
2. Binding sharding (fixed): `/sdd.plan.contract` consumes one `BindingRowID` row per run

Do not collapse all planning work into one broad run.
Optimization target is packet-first consumption with bounded inputs per shard, not shard removal.
`contract` is not a `Stage Queue` row; it is a per-binding artifact queue unit derived from `Artifact Status`.

## Setup

Run `{SCRIPT}` once from repo root.
Parse JSON for `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR`, and `BRANCH`.
All paths must be absolute.

Treat the resolved `IMPL_PLAN` as the canonical `PLAN_FILE` for all downstream planning commands and runtime handoff output.

## Repository-First Inputs (Mandatory)

`/sdd.plan` MUST consume the canonical repository-first baseline produced by `/sdd.constitution`:
`/sdd.plan` uses **Unified Repository-First Gate Protocol (`URFGP`)** as the shared authority for repository-first gate routing, evidence minimality, and canonical path enforcement.

1. `.specify/memory/repository-first/technical-dependency-matrix.md`
2. `.specify/memory/repository-first/module-invocation-spec.md`

Fail fast and route to `/sdd.constitution` if any canonical baseline artifact is missing, stale, or non-traceable.

## Stage 0 Shared Context Snapshot

Build `Shared Context Snapshot` from these inputs only:

- resolved `SPEC_FILE`
- `.specify/memory/constitution.md`
- `.specify/memory/repository-first/*`
- remaining user planning context after argument parsing

Do **not** read or reuse `research.md`, `data-model.md`, `test-matrix.md`, or `contracts/` when building Stage 0.
Do **not** materialize a separate `shared-context.md` file.

Keep the snapshot to shared bootstrap facts only:

- feature identity and scope anchors
- actors, in-scope / out-of-scope, stable UC/UIF/FR references
- constitution-level constraints that affect every downstream stage
- repository-first consumption slice relevant to this feature, citing only concrete dependency usage rows, concrete module edges, existing `SIG-*` rows needed for planning, and bounded repo candidate anchors needed for later interface partitioning or shared-semantic landing
- shared blockers and must-read anchors

Do **not** write long summaries, audit payload, planning-stage prose, or execution logs into the snapshot.
Do **not** place `test-matrix` scenario decomposition, `data-model` owner/lifecycle conclusions, contract tuples, final boundary/DTO design, or audit conclusions into Stage 0.
Do **not** place unbounded repository dumps or free-form symbol inventories into Stage 0; bounded repo candidate anchors are allowed only as later-stage input hints, not as design conclusions.
Do **not** perform repository-first completeness or consistency audit here; `/sdd.analyze` owns that responsibility.

## Planning Control Plane Requirements

Use `.specify/templates/plan-template.md` as the structure source for `plan.md`. This runtime template path is mandatory; if the file is missing or non-consumable, stop and report the blocker. Do not substitute `templates/plan-template.md` or any other template location.
The generated `plan.md` is the sole planning control plane and MUST contain exactly these sections:

1. `Summary`
2. `Shared Context Snapshot`
3. `Stage Queue`
4. `Binding Projection Index`
5. `Artifact Status`
6. `Handoff Protocol`

`plan.md` is a derived planning control plane. It is authoritative for planning queue state and binding-index rows only. It MUST NOT replace downstream planning artifacts as the semantic source of truth.
Queue rows, binding rows, and other control-plane restatements are derived views only; they MUST NOT override upstream artifacts or downstream stage artifacts.

## Queue Initialization Rules

Initialize or refresh only these sections:

### Stage Queue

Seed exactly three stage rows in fixed order:

1. `research`
2. `test-matrix`
3. `data-model`

Treat the `data-model` row as fixed shared-semantic alignment work:

- keep the row queued in `Stage Queue`
- run it after `test-matrix`
- finish it before entering `contract`
- keep it scoped to shared semantic alignment for the selected `BindingRowID` set, not boundary/DTO/repo-interface predesign

For each row include:

- stage id
- command name
- required inputs
- output path
- status (`pending`, `in_progress`, `done`, `blocked`)
- blocker

### Binding Projection Index

Initialize the table structure but leave it empty until `/sdd.plan.test-matrix` produces stable binding rows.

Required columns:

- `BindingRowID`
- `UC ID`
- `UIF ID`
- `FR ID`
- `IF ID / IF Scope`
- `Trigger Ref(s)`
- `Primary TM IDs`
- `TC IDs`
- `UIF Path Ref(s)`
- `UDD Ref(s)`
- `Test Scope`

Do not add `Boundary Anchor`, `Implementation Entry Anchor`, anchor statuses, DTO anchors, collaborator anchors, or other contract-design fields here.
Do not mirror packet-level scope reference fields such as `User Intent`, `Request Semantics`, `Visible Result`, `Side Effect`, `Boundary Notes`, or `Repo Landing Hint` into this index; those remain authoritative only in `test-matrix.md`.

### Artifact Status

Initialize the table structure but leave it empty until binding rows exist.

Required columns:

- `BindingRowID`
- `Unit Type`
- `Target Path`
- `Status`
- `Blocker`

## Handoff Model

Frontmatter `handoffs` are static advisory metadata only.
Use at most one unconditional handoff target in frontmatter.
State-dependent routing belongs in runtime `Handoff Decision`, not frontmatter.

Child-command selection rules are non-negotiable:

- `/sdd.plan.research` takes the first `research` row in `Stage Queue` with status `pending`
- `/sdd.plan.test-matrix` takes the first `test-matrix` row in `Stage Queue` with status `pending`
- `/sdd.plan.data-model` takes the first `data-model` row in `Stage Queue` with status `pending`
- `/sdd.plan.contract` takes the first `Artifact Status` row where `Unit Type = contract` and `Status = blocked`; if no blocked row exists, take the first row with `Status = pending`
Child commands MUST NOT scan the repository to invent the next target.
Child commands MUST consume queue state from the resolved `PLAN_FILE` only.

## Runtime Rules

- Keep `/sdd.plan` orchestration-only; do not generate downstream planning artifacts here.
- Keep queue rows and binding rows minimal and deterministic.
- Allow only minimal child-command writeback:
  - `/sdd.plan.research`: selected `research` stage row only
  - `/sdd.plan.test-matrix`: selected `test-matrix` stage row, `Binding Projection Index`, and `Artifact Status`
  - `/sdd.plan.data-model`: selected `data-model` stage row and contract-readiness blocker updates in `Artifact Status` only
  - `/sdd.plan.contract`: selected `Artifact Status` row only
- Do not append long summaries or stage bodies back into `plan.md`.
- `README.md`, `docs/**`, `specs/**`, `tests/**`, `plans/**`, `templates/**`, demos, and generated artifacts are supporting inputs only and MUST NOT be promoted into repo semantic anchors.
- Do not claim cross-artifact final PASS/FAIL in this stage.

## Stop Conditions

Stop immediately when any of the following occurs:

- resolved branch-derived `SPEC_FILE` is missing or non-consumable
- required repository-first canonical baseline files are missing or stale
- constitution-level constraints block downstream planning
- required shared bootstrap anchors cannot be stabilized from authoritative inputs
- `plan.md` cannot be initialized with the required control-plane sections

## Final Output

Always write or refresh `plan.md` first, then report:

- branch
- resolved `SPEC_FILE` absolute path
- `plan.md` absolute path
- initialized `Stage Queue`
- initialized `Binding Projection Index` row count
- initialized `Artifact Status` row count
- explicit next command: `/sdd.plan.research`
- explicit handoff order: `sdd.plan.research -> sdd.plan.test-matrix -> sdd.plan.data-model -> sdd.plan.contract`

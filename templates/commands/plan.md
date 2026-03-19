---
description: Orchestrate the planning phase from the current feature branch by generating plan.md control-plane state, Stage 0 shared context, and the full handoff queue.
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

Do only two things:

1. Build the Stage 0 `Shared Context Snapshot` inside `plan.md`
2. Initialize or refresh queue state, binding rows, artifact status, and fingerprints

`/sdd.plan` does **not** generate downstream planning-stage artifacts directly.

## Governance Guardrails (Mandatory)

- **Authority rule**: `plan.md` is authoritative only for planning control-plane state (queue rows, binding-index projections, artifact status, fingerprints). It MUST NOT override semantic authority owned by `spec.md`, `research.md`, `data-model.md`, `test-matrix.md`, or `contracts/`.
- **Stage boundary rule**: `/sdd.plan` is orchestration-only. Do not emit downstream stage bodies, implementation ownership semantics (including `Repo Anchor Role` assignment), or contract schema details.
- **Gate ownership rule**: `/sdd.plan` may report local orchestration readiness (`pending`, `in_progress`, `done`, `blocked`) only. Cross-artifact final PASS/FAIL is owned by `/sdd.analyze`.

## Planning Sharding Model (Mandatory)

Keep the two-layer sharding model for planning runs:

1. Stage sharding (fixed): default delivery path `research -> test-matrix -> contract`; `data-model` remains a queued on-demand shared-semantic alignment shard
2. Binding sharding (fixed): `/sdd.plan.contract` consumes one `BindingRowID` row per run

Do not collapse all planning work into one broad run.
Optimization target is packet-first consumption with bounded inputs per shard, not shard removal.

## Setup

Run `{SCRIPT}` once from repo root.
Parse JSON for `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR`, and `BRANCH`.
All paths must be absolute.

Treat the resolved `IMPL_PLAN` as the canonical `PLAN_FILE` for all downstream planning commands and runtime handoff output.

## Repository-First Inputs (Mandatory)

`/sdd.plan` MUST consume the canonical repository-first baseline produced by `/sdd.constitution`:

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
- repository-first consumption slice relevant to this feature, citing only concrete dependency usage rows, concrete module edges, and existing `SIG-*` rows needed for planning
- shared blockers and must-read anchors

Do **not** write long summaries, audit payload, planning-stage prose, or execution logs into the snapshot.
Do **not** perform repository-first completeness or consistency audit here; `/sdd.analyze` owns that responsibility.

## Planning Control Plane Requirements

Use `.specify/templates/plan-template.md` as the structure source for `plan.md`. This runtime template path is mandatory; if the file is missing or non-consumable, stop and report the blocker. Do not substitute `templates/plan-template.md` or any other template location.
The generated `plan.md` is the sole planning control plane and MUST contain exactly these dimensions:

1. downstream-consumption context: `Shared Context Snapshot`
2. orchestration context: `Stage Queue` and `Artifact Status`
3. binding-key context: `Binding Projection Index`

`plan.md` is a derived planning control plane. It is authoritative for planning queue state, binding-index rows, and source/output fingerprints only. It MUST NOT replace downstream planning artifacts as the semantic source of truth.
Queue rows, binding rows, fingerprints, and other control-plane restatements are derived views only; they MUST NOT override upstream artifacts or downstream stage artifacts.

## Queue Initialization Rules

Initialize or refresh only these sections:

### Stage Queue

Seed exactly three stage rows in fixed order:

1. `research`
2. `data-model`
3. `test-matrix`

Treat the `data-model` row as optional-by-default alignment work:

- keep the row queued in `Stage Queue`
- do not require it on the default `research -> test-matrix -> contract` path
- use it only when a stage discovers a shared-semantic gap that cannot stay operation-scoped

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
- `Implementation Entry Anchor`
- `Boundary Anchor Status`
- `Implementation Entry Anchor Status`
- `Test Scope`

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
State-dependent routing belongs in runtime `Handoff Decision`, not frontmatter.

Child-command selection rules are non-negotiable:

- `/sdd.plan.research` takes the first `research` row in `Stage Queue` with status `pending`
- `/sdd.plan.data-model` takes the first `data-model` row in `Stage Queue` with status `pending`
- `/sdd.plan.test-matrix` takes the first `test-matrix` row in `Stage Queue` with status `pending`
- `/sdd.plan.contract` takes the first `Artifact Status` row where `Unit Type = contract` and `Status = blocked`; if no blocked row exists, take the first row with `Status = pending`
Child commands MUST NOT scan the repository to invent the next target.
They MUST consume queue state from the resolved `PLAN_FILE` only.

## Runtime Rules

- Keep `/sdd.plan` orchestration-only; do not generate downstream planning artifacts here.
- Keep queue rows and binding rows minimal and deterministic.
- Record source fingerprints from the direct authoritative inputs of each queue row.
- Record output fingerprints after each row completes.
- Allow only minimal child-command writeback: status, output path, blocker, source fingerprint, output fingerprint.
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
- explicit handoff order: default `sdd.plan.research -> sdd.plan.test-matrix -> sdd.plan.contract`; insert `sdd.plan.data-model` only when a queued blocker explicitly requires shared-semantic alignment

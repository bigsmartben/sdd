---
description: Perform the centralized pre-implementation semantic audit and gate decision across spec.md, plan.md, and tasks.md.
handoffs:
  - label: Proceed to Implementation
    agent: sdd.implement
    prompt: Proceed with implementation only after analyze findings are resolved or explicitly accepted
    send: true
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Run the unified audit entry before `/sdd.implement`: combine planning lint output with semantic analysis, then produce one compact report and one Gate Decision.

`/sdd.analyze` is the centralized audit entry and single concentrated audit step before `/sdd.implement`.

`/sdd.analyze` owns this centralized audit and summary authority. `/sdd.implement` should remain limited to hard execution gates only.

Mechanical output structure is governed by `.specify/templates/lint-report-template.md`; if that runtime template is missing or non-consumable, stop and report the blocker. Semantic output remains in this command's semantic report section.

## Constitution Authority

`.specify/memory/constitution.md` is non-negotiable in this scope. Any MUST-level conflict is CRITICAL and must be remediated in `spec.md`, `plan.md`, or `tasks.md` (or by a separate constitution update command outside `/sdd.analyze`).

## Artifact Authority

**Artifact Authority**

Authoritative artifacts: `spec.md`, `tasks.md`, `.specify/memory/constitution.md`, supporting planning artifacts (`research.md`, `data-model.md`, `test-matrix.md`, `contracts/`), and repository-first canonical baseline projections `.specify/memory/repository-first/technical-dependency-matrix.md` and `.specify/memory/repository-first/module-invocation-spec.md` when required by plan outputs.

`plan.md` is the planning control plane for queue state, binding-projection rows, and source/output fingerprints only. It is derived for planning semantics and MUST NOT supersede the stage artifacts it dispatches.

`/sdd.analyze` owns comprehensive implementation-readiness analysis and audit responsibilities.
CRITICAL/HIGH findings MUST cite the authoritative source artifact(s).
Treat task-local summaries or inline mirrors as derived views only.
Derived views (summaries, mirrors, projection notes, caches) are secondary evidence only.
Misuse of `README.md`, `docs/**`, `specs/**`, `tests/**`, `plans/**`, `templates/**`, demos, or generated artifacts as repo semantic anchors must be reported as `repo-anchor misuse`.

## Operating Constraints

- **Read-only**: do not modify files.
- Produce a compact report with findings, metrics, and next actions.
- Keep implementation-boundary reminder minimal: `/sdd.implement` enforces hard run gates; this command owns comprehensive audit synthesis.

## Execution Steps

### 1) Initialize Context

Run `{SCRIPT}` once from repo root and parse JSON for `FEATURE_DIR` and `AVAILABLE_DOCS`. Derive absolute paths:

- `SPEC = FEATURE_DIR/spec.md`
- `PLAN = FEATURE_DIR/plan.md`
- `TASKS = FEATURE_DIR/tasks.md`
- `CONSTITUTION = .specify/memory/constitution.md`

Abort with clear prerequisite error if required artifacts are missing.

### 2) Run Planning Lint

Attempt planning lint before semantic passes.

- Bash: `scripts/bash/run-planning-lint.sh --feature-dir <abs-path> --rules <abs-path> --json`
- PowerShell: `scripts/powershell/run-planning-lint.ps1 -FeatureDir <abs-path> -Rules <abs-path> -Json`
- Rules catalog path: `rules/planning-lint-rules.tsv`

Expected lint payload fields:

- `feature_dir`
- `rules_total`
- `rules_evaluated`
- `findings_total`
- `findings_by_severity`
- `findings[]` with: `rule_id`, `severity`, `source`, `file`, `line`, `message`, `remediation`

If lint is unavailable or execution fails:

- Continue semantic audit.
- Explicitly mark lint as unavailable in the report.
- Emit zero `Mechanical Findings` with explanatory note (not silent omission).

### 3) Load Minimal Artifact Context

Load only sections needed for semantic conclusions:

- From `spec.md`: `1.1 Actors`, `1.2 System Boundary`, `1.3 UI Data Dictionary (UDD)`, `2.1 Functional Requirements Index`, `2.2 Global UX Flow Overview`, per-UC `3.1 User Story & Acceptance Scenarios`, `3.2 UX — User Interaction Flow`, `3.3 Functional Requirements`, `3.4 UI — UI Element Definitions`, `3.5 Component-Data Dependency Overview`, `N.1 Success Criteria`, `N.2 Environment Edge Cases`, and `Assumptions / Open Questions` when present.
- From `research.md` when present: feature-local architecture, northbound placement, and module-layering decisions that constrain boundary or implementation-entry selection.
- From `plan.md`: `Shared Context Snapshot`, `Stage Queue`, `Binding Projection Index`, `Artifact Status`, and source/output fingerprints.
- From `tasks.md`: task IDs, scopes (`GLOBAL`, `IF-*`), DAG/dependencies, descriptions, referenced files/anchors.
- From supporting planning artifacts (only when needed):
  - `contracts/` for interface semantics
  - `data-model.md` for domain objects/invariants/lifecycle anchors
  - `test-matrix.md` for path anchors
  - `contracts/` realization-design sections for operation behavior, sequence, UML details
- From repository-first canonical baseline (required when plan outputs depend on repository-first projections):
  - `.specify/memory/repository-first/technical-dependency-matrix.md` for dependency evidence (`Dependency (G:A)`, `Version Source`, divergence/`unresolved` governance signals)
  - `.specify/memory/repository-first/module-invocation-spec.md` for invocation governance (`Allowed Direction`, `Forbidden Direction`, `Dependency Governance Rules`)
  - if expected canonical files are missing/stale, stop and route remediation to `/sdd.constitution`
- From constitution: MUST/SHOULD principles required for validation.

### 4) Build Semantic Models

Construct internal models (no raw artifact dump):

- requirement inventory (FR / SC / EC obligations plus stable user-visible data anchors)
- user action / acceptance inventory (user stories, scenarios, UIF paths, UI-triggered behaviors)
- task-to-requirement coverage mapping
- constitution principle map
- planning queue / binding projection / fingerprint inventory

### 5) Semantic Detection Passes

Focus on high-signal semantic issues and aggregate overflow beyond 50 findings.

- duplication and contradiction in requirements/intent
- ambiguity and unresolved placeholders with execution impact
- constitution MUST violations
- requirement/task coverage gaps
- cross-artifact terminology or meaning drift
- cross-artifact contradiction detection
- execution-order or dependency contradictions that create implementation blockers
- semantic conflicts between `spec.md`, `plan.md`, `tasks.md`, and required supporting artifacts
- domain semantic coverage vs interface-local technical traceability sufficiency
- stale planning outputs where `plan.md` source fingerprints no longer match the current upstream artifact state

Mandatory explicit semantic checks (do not skip even when lint is available):

- spec backbone consistency:
  - flag `Entity.field` references in FR/UIF/UI sections that are missing from `1.3 UI Data Dictionary (UDD)` or whose mandatory UDD columns are incomplete
  - flag `FR`, `Scenario`, `UIF`, `SC`, or `EC` references that drift across `spec.md`, `test-matrix.md`, `contracts/`, or `tasks.md`
  - flag UI element definitions or component-data dependency rows that introduce user-visible behavior, state, or data without anchored UDD / FR / scenario evidence
- boundary anchor legality and tuple authority:
  - flag any tuple using `BA-*` as normative `Boundary Anchor`
  - flag tuple rows in normative/main validation paths when `Repo Anchor = TODO(REPO_ANCHOR)`, `Anchor Status = todo`, or `Implementation Entry Anchor Status = todo`
  - flag `test-matrix.md`, `plan.md`, or `contracts/` tuple drift where `Boundary Anchor` is not the first consumer-callable entry for the bound interaction
  - flag `test-matrix.md`, `plan.md`, or `contracts/` tuple drift where `Boundary Anchor` / `Implementation Entry Anchor` contradict feature-local northbound placement or layering constraints stated in `research.md`
- repo-anchor decision protocol compliance:
  - flag missing required anchor-status fields for anchored tuples:
    - `Anchor Status` in `data-model.md` and `test-matrix.md`
    - `Anchor Status` (or legacy `Repo Anchor Status`) and `Implementation Entry Anchor Status` in `contracts/`
  - flag any repo anchor value (except `TODO(REPO_ANCHOR)` or explicit `N/A`) that is not in strict `path::symbol` format
  - flag any anchor-status value outside `existing`, `extended`, `new`, `todo`
  - flag `extended` anchors that do not represent same-entity field/state expansion
  - flag `new` anchors that do not provide explicit `path::symbol` target evidence
  - flag cases where `extended`/`new` anchors are used to invent business semantics instead of naming/lifecycle correction and traceability
- contract DTO drift:
  - flag contract `Request`/`Success`/`Failure` fields that drift from anchored client-entry signature surfaces or anchored request/response DTO structure
  - drift includes renaming anchored fields, flattening anchored nesting, or splitting into fields absent from anchored DTOs
- full-field contract coverage:
  - flag contracts missing `Full Field Dictionary (Operation-scoped)`
  - flag contract field-dictionary rows missing `Owner Class`, `Default`, `Validation/Enum`, `Persisted`, `Used in <Operation ID>`, or `Source Anchor`
  - flag field-dictionary drift between `contracts/` and `test-matrix.md` binding packet seeds (`Request DTO Anchor`, `Response DTO Anchor`, `State Owner Anchor(s)`)
- contract-projection drift governance:
  - compare each contract `Spec Projection Slice` against referenced `spec.md` rows (`UC/UIF/FR/SC/EC`)
  - compare each contract `Test Projection Slice` against referenced `test-matrix.md` rows (`TM/TC`, scope, pass/failure anchors)
  - when drift exists, treat contract projection as current downstream execution baseline and emit mandatory upstream writeback repairs rather than local semantic merge
  - route spec writeback repairs to `/sdd.specify`; route test-matrix writeback repairs to `/sdd.plan.test-matrix`
- runtime correctness (from unified contract realization design):
  - treat this pass as the single post-generation runtime correctness gate; require the unified contract `Runtime Correctness Check` section and required rows, while allowing per-row `ok`/`gap` status with explicit evidence
  - flag contract realization sections missing `Implementation Entry Anchor` or using `TODO(REPO_ANCHOR)` there without an explicit blocker path
  - flag sequence designs that do not reach `Implementation Entry Anchor` within the first two request hops from the consumer/client entry
  - flag HTTP-facing sequences that bypass the controller-layer implementation entry and start directly from a downstream service/facade symbol
  - flag HTTP-facing contracts that render `Sequence Variant B (Boundary == Entry)` or otherwise collapse controller-first entry into a downstream service/facade symbol
  - flag sequence designs with broken end-to-end continuity at declared granularity (disconnected hops, orphan participants, or broken return chains)
  - flag behavior paths that do not map to one contiguous ordered sequence step chain
  - flag cases where both contract boundary and implementation entry are repo-backed but the handoff is omitted, reversed, or implied by invented participants only
  - flag behavior-path closure gaps where `Behavior Paths` outcomes/failures are not fully covered by `Sequence Ref` steps
  - flag sequence failure steps that do not match contract `Failure Output` semantics
  - flag sequence state-transition steps that are not mapped to valid lifecycle transitions/invariants
  - flag contract-visible sequence messages that are not mapped to callable boundary/collaborator operations with UML ownership
  - flag UML ownership gaps where contract-visible request/response fields or behavior-significant `Field Semantics` fields do not have an explicit owning class/interface
  - flag sequence participants missing from UML static view or lacking mapped operation ownership
  - flag newly introduced fields/methods/calls that are not explicitly marked and connected by UML ownership/call relationships
- lifecycle anchor drift (high priority):
  - flag `data-model.md` lifecycle stable states that drift from anchored enum/state field/mapper status values
  - flag lifecycle states promoted from UX phase/page step/flow node
- state-machine applicability compliance (constitution-driven):
  - evaluate lifecycle modeling outputs against constitution applicability thresholds for Full FSM vs Lightweight State Model
  - when Full FSM is used below threshold, require explicit planning justification evidence (for example in plan complexity tracking); flag as finding when absent

- repository-first projection evidence checks:
  - dependency evidence check:
    - flag canonical dependency-matrix rows not traceable to engineering assembly facts
    - verify dependency extraction aligns with supported build-manifest auto-detection (`pom.xml`, `package.json`, `pyproject.toml` + requirements/lock hints, `go.mod`) when those files exist
    - verify dependency key normalization (`group:artifact` for Maven, `ecosystem:package_or_module` for Node/Python/Go)
    - flag missing/invalid `Version Source` values when dependency rows exist
    - flag silent normalization when version divergence or `unresolved` evidence should be preserved
  - invocation governance check:
    - flag `.specify/memory/repository-first/module-invocation-spec.md` missing any required section (`Allowed Direction`, `Forbidden Direction`, `Dependency Governance Rules`)
    - flag invocation rules not aligned to real module layering
    - flag dependency-governance rules that ignore divergence/`unresolved` signals from canonical `.specify/memory/repository-first/technical-dependency-matrix.md`

- planning control-plane stale checks:
  - compare each `Stage Queue` row `Source Fingerprint` against the current direct upstream artifact set for that row
  - compare each `Artifact Status` row `Source Fingerprint` against the current authoritative inputs for that `BindingRowID`
  - flag rows where fingerprints drift as stale planning outputs
  - route stale `research` rows to `/sdd.plan.research`
  - route stale `data-model` rows to `/sdd.plan.data-model`
  - route stale `test-matrix` rows or missing binding rows to `/sdd.plan.test-matrix`
  - route stale `contract` rows to `/sdd.plan.contract`

Mechanical checks delegated to planning lint (for example format-level tuple lint and diagram syntax issues) should be consumed from lint output instead of duplicating long rule prose here.

### 6) Produce Compact Analysis Report

Output Markdown (no file writes) with this structure:

## Specification Analysis Report

### Summary

- lint status: `available` or `unavailable`
- totals: requirements, tasks, coverage %, lint findings, semantic findings, blocking findings

### Mechanical Findings

Rows derived from lint output only, projected using `.specify/templates/lint-report-template.md` section semantics.

| ID | Source | Rule | Severity | Location | Summary | Remediation |
|----|--------|------|----------|----------|---------|-------------|

- `Source` must be `lint` for all rows in this section.

### Semantic Findings

Rows derived from semantic audit passes.

| ID | Source | Category | Severity | Location(s) | Summary | Recommendation |
|----|--------|----------|----------|-------------|---------|----------------|

- `Source` must be `semantic` for all rows in this section.

### Metrics

- Total Requirements
- Total Tasks
- Coverage % (requirements with >=1 mapped task)
- Mechanical Findings Count
- Mechanical Findings by Severity
- Semantic Findings Count
- Critical Issues Count

### Gate Decision (Required)

Assemble and output one decision:

- `PASS`: no remaining blocking findings.
- `FAIL`: at least one blocking finding remains.

When `FAIL`, provide blocker list with evidence and remediation owner command (`/sdd.constitution`, `/sdd.specify`, `/sdd.plan.*`, or `/sdd.tasks`).
Treat the following as blocking by default: normative use of `BA-*`, normative tuple rows with unresolved `TODO(REPO_ANCHOR)`, `Anchor Status = todo`, or `Implementation Entry Anchor Status = todo`, repo-anchor decision protocol violations (missing/invalid required anchor-status fields, non-`path::symbol` repo-anchor values, invalid `extended/new` evidence), contracts missing `Full Field Dictionary (Operation-scoped)` or carrying unresolved key field gaps, contract field drift from anchored DTOs/signatures or `test-matrix.md` field seeds, unresolved contract projection drift requiring upstream writeback (`/sdd.specify`, `/sdd.plan.test-matrix`), controller-first HTTP entry violations including illegal `Boundary == Entry` collapse, runtime correctness gaps in unified contract realization sections, lifecycle stable-state drift from anchored enum/state sources, missing/stale repository-first canonical baseline files, dependency-matrix evidence not traceable to engineering assembly facts, invocation-governance rules that drift from real module layering or ignore divergence/`unresolved` dependency governance signals, and stale planning control-plane rows where `Source Fingerprint` no longer matches current authoritative inputs.

### 7) Next Actions

Provide concise actions aligned to gate result:

- `FAIL`: resolve blockers before `/sdd.implement`.
- `PASS`: proceed, with optional follow-up improvements for non-blocking findings.
- Keep command suggestions explicit and short (`/sdd.constitution`, `/sdd.specify`, `/sdd.plan.*`, `/sdd.tasks`).

## Context

{ARGS}

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

Mechanical output structure is governed by `templates/lint-report-template.md`; semantic output remains in this command's semantic report section.

## Constitution Authority

`.specify/memory/constitution.md` is non-negotiable in this scope. Any MUST-level conflict is CRITICAL and must be remediated in `spec.md`, `plan.md`, or `tasks.md` (or by a separate constitution update command outside `/sdd.analyze`).

## Artifact Authority

**Artifact Authority**

Authoritative artifacts: `spec.md`, `plan.md`, `tasks.md`, `.specify/memory/constitution.md`, supporting planning artifacts (`research.md`, `data-model.md`, `test-matrix.md`, `contracts/`, `interface-details/`), and repository-first canonical baseline projections in `.specify/memory/repository-first/` (`technical-dependency-matrix.md`, `domain-boundary-responsibilities.md`, `module-invocation-spec.md`) when required by plan outputs.

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

- From `spec.md`: overview/context, functional & non-functional requirements, user stories, edge cases when present.
- From `plan.md`: architecture/stack choices, constraints, stage outputs, planning references.
- From `tasks.md`: task IDs, scopes (`GLOBAL`, `IF-*`), DAG/dependencies, descriptions, referenced files/anchors.
- From supporting planning artifacts (only when needed):
  - `contracts/` for interface semantics
  - `data-model.md` for domain objects/invariants/lifecycle anchors
  - `test-matrix.md` for path anchors
  - `interface-details/` for operation behavior, sequence, UML details
- From repository-first canonical baseline (required when plan outputs depend on repository-first projections):
  - `.specify/memory/repository-first/technical-dependency-matrix.md` for dependency evidence (`Dependency (G:A)`, `Version Source`, divergence/`unresolved` governance signals)
  - `.specify/memory/repository-first/domain-boundary-responsibilities.md` for source-anchored capability boundaries (`Core Entity Anchors` as `path::symbol`)
  - `.specify/memory/repository-first/module-invocation-spec.md` for invocation governance (`Allowed Direction`, `Forbidden Direction`, `Dependency Governance Rules`)
  - if expected canonical files are missing/stale, stop and route remediation to `/sdd.constitution`
- From constitution: MUST/SHOULD principles required for validation.

### 4) Build Semantic Models

Construct internal models (no raw artifact dump):

- requirement inventory (functional + non-functional, stable keys)
- user action / acceptance inventory
- task-to-requirement coverage mapping
- constitution principle map

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

Mandatory explicit semantic checks (do not skip even when lint is available):

- boundary anchor legality and tuple authority:
  - flag any tuple using `BA-*` as normative `Boundary Anchor`
  - flag tuple rows in normative/main validation paths when `Repo Anchor = TODO(REPO_ANCHOR)`
- contract/interface DTO drift:
  - flag contract or interface `Request`/`Success`/`Failure` fields that drift from anchored facade/RPC method signatures or anchored request/response DTO structure
  - drift includes renaming anchored fields, flattening anchored nesting, or splitting into fields absent from anchored DTOs
- runtime correctness (from Stage 4 interface details):
  - treat this pass as the single post-generation runtime correctness gate; do not require pre-filled check tables in Stage 4 docs
  - flag behavior-path closure gaps where `Behavior Paths` outcomes/failures are not fully covered by `Sequence Ref` steps
  - flag sequence failure steps that do not match contract `Failure Output` semantics
  - flag sequence state-transition steps that are not mapped to valid lifecycle transitions/invariants
  - flag contract-visible sequence messages that are not mapped to callable boundary/collaborator operations with UML ownership
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
  - boundary evidence check:
    - flag `domain-boundary-responsibilities.md` boundaries lacking source-anchor evidence
    - flag `Core Entity Anchors` values not in `path::symbol` form
    - flag misuse where `2nd-Party Collaboration Anchor` is used as dependency-matrix substitute
  - invocation governance check:
    - flag `module-invocation-spec.md` missing any required section (`Allowed Direction`, `Forbidden Direction`, `Dependency Governance Rules`)
    - flag invocation rules not aligned to real module layering
    - flag dependency-governance rules that ignore divergence/`unresolved` signals from canonical `technical-dependency-matrix.md`

Mechanical checks delegated to planning lint (for example format-level tuple lint and diagram syntax issues) should be consumed from lint output instead of duplicating long rule prose here.

### 6) Produce Compact Analysis Report

Output Markdown (no file writes) with this structure:

## Specification Analysis Report

### Summary

- lint status: `available` or `unavailable`
- totals: requirements, tasks, coverage %, lint findings, semantic findings, blocking findings

### Mechanical Findings

Rows derived from lint output only, projected using `templates/lint-report-template.md` section semantics.

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

When `FAIL`, provide blocker list with evidence and remediation owner command (`/sdd.specify`, `/sdd.plan`, or `/sdd.tasks`).
Treat the following as blocking by default: normative use of `BA-*`, normative tuple rows with unresolved `TODO(REPO_ANCHOR)`, contract/interface field drift from anchored DTOs/signatures, runtime correctness gaps in Stage 4 interface details, lifecycle stable-state drift from anchored enum/state sources, missing/stale repository-first canonical baseline files, dependency-matrix evidence not traceable to engineering assembly facts, boundary responsibilities not traceable to source anchors, and invocation-governance rules that drift from real module layering or ignore divergence/`unresolved` dependency governance signals.

### 7) Next Actions

Provide concise actions aligned to gate result:

- `FAIL`: resolve blockers before `/sdd.implement`.
- `PASS`: proceed, with optional follow-up improvements for non-blocking findings.
- Keep command suggestions explicit and short (`/sdd.specify`, `/sdd.plan`, `/sdd.tasks`).

## Context

{ARGS}

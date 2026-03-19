---
description: Perform the centralized pre-implementation semantic audit and cross-artifact gate decision, using spec.md/plan.md/tasks.md as mandatory core inputs.
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

`/sdd.analyze` is the centralized audit entry and single concentrated audit step before `/sdd.implement`.

1. Run planning lint and semantic audit.
2. Produce one compact report.
3. Produce one authoritative `Gate Decision`.

The latest run block in `analyze-history.md` is the only authoritative analyze gate input for `/sdd.implement`.

## Governance Guardrails (Mandatory)

- **Authority rule**: `/sdd.analyze` is the sole cross-artifact audit authority before implementation. It owns the final PASS/FAIL decision across mandatory core artifacts (`spec.md`, `plan.md`, `tasks.md`) and any existing planning artifacts required by the selected evidence path (`research.md`, `data-model.md`, `test-matrix.md`, `contracts/`).
- **Stage boundary rule**: `/sdd.analyze` reports findings and remediation owners only. It MUST NOT rewrite semantic source artifacts or locally "repair" drift by mutating planning/design outputs.
- **Gate ownership rule**: commands other than `/sdd.analyze` may emit local readiness checks, but cross-artifact final PASS/FAIL claims are valid only from this stage.

## Read Only

1. Run `{SCRIPT}` once and resolve:
   - `SPEC = FEATURE_DIR/spec.md`
   - `PLAN = FEATURE_DIR/plan.md`
   - `TASKS = FEATURE_DIR/tasks.md`
   - `CONSTITUTION = .specify/memory/constitution.md`
   - `ANALYZE_HISTORY = FEATURE_DIR/audits/analyze-history.md`
2. Run planning lint before semantic passes:
   - Bash: `scripts/bash/run-planning-lint.sh --feature-dir <abs-path> --rules <abs-path> --json`
   - PowerShell: `scripts/powershell/run-planning-lint.ps1 -FeatureDir <abs-path> -Rules <abs-path> -Json`
3. Load only the minimum slices needed for conclusions from:
   - `spec.md`, `plan.md`, `tasks.md`
   - optional support artifacts (`research.md`, `data-model.md`, `test-matrix.md`, `contracts/`)
4. When plan outputs depend on repository-first baselines, read canonical files only:
   - `.specify/memory/repository-first/technical-dependency-matrix.md`
   - `.specify/memory/repository-first/module-invocation-spec.md`
5. Repository-first evidence checks MUST use:
   - matrix dependency facts plus `SIG-*` governance signals including divergence, version-source-mix, and `unresolved`
   - minimal supporting facts for conclusions (path-level default; line-level only when ambiguity/conflict requires precision)
   - invocation governance using concrete module-to-module rows as the primary representation

## Write Only

1. Append one run record to `FEATURE_DIR/audits/analyze-history.md`.
2. Do not modify `spec.md`, `plan.md`, `tasks.md`, or planning artifacts.

## Semantic Checks

Run focused passes only (high-signal, bounded):

1. constitution MUST violations
2. requirement/task coverage gaps
3. contract-projection drift governance
4. repo-anchor misuse and tuple legality
5. repository-first baseline evidence integrity
6. stale planning outputs where `plan.md` source fingerprints no longer match the current upstream artifact state
7. repo-anchor strategy priority compliance (`existing -> extended -> new`) for active tuples and anchors

Mandatory stale-row routing:

- stale `research` -> `/sdd.plan.research`
- stale `data-model` -> `/sdd.plan.data-model`
- stale `test-matrix` or missing binding rows -> `/sdd.plan.test-matrix`
- stale `contract` -> `/sdd.plan.contract`

Projection drift routing:

- if `Binding Projection Index` differs from the selected `Binding Contract Packets` row for the same `BindingRowID`, route `/sdd.plan.test-matrix` to repair the upstream binding projection
- if a generated contract contradicts the selected packet or selected `data-model` constraints for the same `BindingRowID`, treat it as contract projection drift and repair the upstream owner first (`/sdd.plan.test-matrix` for binding projection errors, `/sdd.plan.data-model` for shared semantic errors), then regenerate `/sdd.plan.contract`
- if the generated contract only differs in inferred boundary/entry/DTO/collaborator realization while remaining consistent with binding projection and shared semantic constraints, treat it as contract-stage design output rather than upstream drift

CRITICAL/HIGH findings MUST cite the authoritative source artifact(s) with concise supporting facts.

## Gate Decision

Output exactly one decision:

- `PASS`: no blocking findings
- `FAIL`: one or more blocking findings remain

When `FAIL`, include blocker list with supporting facts and remediation owner command (`/sdd.constitution`, `/sdd.specify`, `/sdd.plan.*`, or `/sdd.tasks`).

Default blocking classes include unresolved normative anchors (`BA-*`, `TODO(REPO_ANCHOR)`, `Anchor Status = todo`, `Implementation Entry Anchor Status = todo`), unresolved placeholder class/type labels in contract artifacts, missing `Full Field Dictionary (Operation-scoped)`, unresolved contract projection drift, upstream binding-projection drift across `plan.md` / `test-matrix.md`, controller-first violations, repository-first baseline gaps, and stale control-plane fingerprints.

Additional blocking requirement: any active tuple selecting `new` anchors without explicit rejection evidence for both `existing` and `extended` is `FAIL` and must route to the relevant `/sdd.plan.*` owner command.

## Final Output

Return one compact report with:

1. Run Metadata:
   - `Run At (UTC):`
   - `Spec SHA256:`
   - `Plan SHA256:`
   - `Tasks SHA256:`
2. mechanical findings summary
3. semantic findings summary
4. metrics summary
5. `Gate Decision:`
6. next actions by owner command

## Persist Analyze History

Persist each run as append-only history in `ANALYZE_HISTORY` with exact sentinels:

- `<!-- SDD_ANALYZE_RUN_BEGIN -->`
- `<!-- SDD_ANALYZE_RUN_END -->`

If append fails, report a warning and continue returning the analysis report.

## Authority Notes

- `plan.md` is authoritative for planning queue state, binding-projection rows, and source/output fingerprints only.
- `spec.md`, `tasks.md`, constitution, planning artifacts, and canonical repository-first baselines own semantics.
- Derived views must not override authoritative artifacts.

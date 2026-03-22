---
description: Perform a centralized pre-implementation consistency audit and update analyze-history.md.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Execute a centralized audit entry and single concentrated audit step before `/sdd.implement`.
Update `analyze-history.md` with the gate decision (`PASS|FAIL`).

`/sdd.analyze` owns:
- Cross-artifact consistency gating.
- Detecting ambiguity, contradiction, or coverage drift.
- Verification of `new` repo anchor strategy evidence.

## Read Only

- All generated feature artifacts (`spec.md`, `plan.md`, `tasks.md`, `contracts/`, `data-model.md`, `test-matrix.md`)
- `.specify/memory/repository-first/*.md` (canonical baselines)

## Write Only

- `analyze-history.md` (append-only: one run block per invocation)

## Final Output

- One analyze run block appended to `ANALYZE_HISTORY`:

```
<!-- SDD_ANALYZE_RUN_BEGIN -->
...Gate Decision, Findings, Routing...
<!-- SDD_ANALYZE_RUN_END -->
```

## Governance / Authority

- **Authority rule**: Centralized validation authority for the feature branch.
- **Protocol rule**: **Unified Repository-First Gate Protocol (`URFGP`)** is the shared authority.
- **Stage boundary rule**: Audit only. never perform local repair in this stage. **MUST NOT** backfill or modify design/task semantics.

## Audit Scope

Evaluate in this order:
1. **repo-anchor strategy priority compliance (`existing -> extended -> new`)**: any active tuple selecting `new` anchors without explicit rejection evidence for both `existing` and `extended` is `FAIL`.
2. **Contract-projection drift governance**: check for upstream binding-projection drift across `plan.md` / `test-matrix.md`; check for unresolved placeholder class/type labels in contract artifacts.
3. **matrix dependency facts plus `SIG-*` governance signals including divergence, version-source-mix, and `unresolved`**: audit using concrete module-to-module rows as the primary representation.
4. **Coverage completeness**: all planned bindings have matching contract artifacts.

`CRITICAL/HIGH findings MUST cite the authoritative source artifact(s) with concise supporting facts.`

## Repository-First Protocol

Apply **Repository-First Evidence Bundle (`RFEB`)** format for all anchor-decision citations in findings.

## Projection Drift Routing

Projection drift routing:

- For upstream binding-projection drift across `plan.md` / `test-matrix.md`: route `/sdd.plan.test-matrix` to repair the upstream binding projection.
- For unresolved placeholder class/type labels in contract artifacts: regenerate `/sdd.plan.contract` for the affected `BindingRowID`.
- For spec-level drift: route `/sdd.specify`.

## Reasoning Order

1. **Coverage Audit**: Trace `spec.md` requirements through plan, design, and tasks.
2. **Consistency Audit**: Check for conflicting DTOs, anchors, or shared semantics; apply contract-projection drift governance.
3. **Anchor Validation**: Verify `new` anchor strategy evidence for affected scope.
4. **Gate Decision**: Assign exactly `PASS` or `FAIL` with clear Gate Decision text.

## Artifact Quality Contract

- Must: produce one action-ready audit with prioritized findings and one authoritative gate decision.
- Strictly: Append exactly one analyze run block to `ANALYZE_HISTORY`. Write only append-only audit history.

## Writeback Contract

- Append exactly one analyze run block to `ANALYZE_HISTORY` in `analyze-history.md`.
- **MUST NOT** rewrite `spec.md`, `plan.md`, `contracts/`, or `tasks.md`.

## Output Contract

- **Gate Decision**: MUST be exactly `PASS` or `FAIL`.
- **Reasoning**: Provide clear, traceable evidence for failures.
- **History Record**: Append exactly one run block using `<!-- SDD_ANALYZE_RUN_BEGIN -->` / `<!-- SDD_ANALYZE_RUN_END -->` markers.

## Stop Conditions

Stop immediately if:
1. Required task artifacts (`tasks.md`/`tasks.manifest.json`) are absent.
2. Any required planning row is not `done`.

## Handoff Decision

Emit exactly these fields:
- `Next Command`: `/sdd.implement` (if PASS) or context-derived repair command (if FAIL).
- `Decision Basis`: Gate decision summary.
- `Ready/Blocked`: Local readiness only.

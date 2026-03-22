# Implementation Task Context

## 1) Objective

Implement the de-fingerprinting refactor described in `@implementation_plan.md`: remove file fingerprint mechanisms from the full workflow (`plan.md` control plane, `tasks.manifest.json` generated provenance, `analyze-history.md` run metadata, and `implement` preflight freshness checks), while keeping orchestration and gate-decision flow valid.

## 2) Scope and Constraints

- Runtime authority first: prioritize behavior in `src/specify_cli/runtime_*.py` and `.specify` runtime contract semantics.
- Remove fingerprint fields, comparisons, and stale-hash checks end-to-end.
- Preserve:
  - queue progression logic
  - `Gate Decision` requirement for implementation
  - preflight hard-stop behavior for missing required artifacts/history blocks.
- Accept intentional behavior change: no post-analyze hash freshness mismatch detection.

## 3) Plan Navigation Commands

Use these commands to read plan sections during implementation:

```bash
# Read Overview section
sed -n '/\[Overview\]/,/\[Types\]/p' /home/ben/project-codex/sdd/implementation_plan.md | cat

# Read Types section
sed -n '/\[Types\]/,/\[Files\]/p' /home/ben/project-codex/sdd/implementation_plan.md | cat

# Read Files section
sed -n '/\[Files\]/,/\[Functions\]/p' /home/ben/project-codex/sdd/implementation_plan.md | cat

# Read Functions section
sed -n '/\[Functions\]/,/\[Classes\]/p' /home/ben/project-codex/sdd/implementation_plan.md | cat

# Read Classes section
sed -n '/\[Classes\]/,/\[Dependencies\]/p' /home/ben/project-codex/sdd/implementation_plan.md | cat

# Read Dependencies section
sed -n '/\[Dependencies\]/,/\[Testing\]/p' /home/ben/project-codex/sdd/implementation_plan.md | cat

# Read Testing section
sed -n '/\[Testing\]/,/\[Implementation Order\]/p' /home/ben/project-codex/sdd/implementation_plan.md | cat

# Read Implementation Order section
sed -n '/\[Implementation Order\]/,$p' /home/ben/project-codex/sdd/implementation_plan.md | cat
```

## 4) Implementation Steps

1. Update template and command contracts to remove fingerprint columns/keys/wording.
2. Refactor runtime payload builders (`runtime_data_model_bootstrap.py`, `runtime_tasks_manifest_bootstrap.py`, `runtime_implement_bootstrap.py`, `runtime_gate_protocol.py`) to remove fingerprint structures and checks.
3. Remove SHA helper callsites and delete `compute_sha256` if no remaining usage.
4. Update lint rules (`PLN-FP-001`) and related tests.
5. Update tests/docs/authority markers and keep behavior consistent with new protocol.

## 5) Verification and Completion Criteria

- All fingerprint-related schema assertions updated.
- Implement preflight still blocks on missing/invalid analyze run or non-PASS gate.
- Implement preflight no longer blocks due to hash mismatch.
- Lint/test markers no longer require fingerprint-specific text.
- Full test suite (or targeted impacted suites) passes.

Refer to `@implementation_plan.md` for a complete breakdown of task requirements and steps. Re-read this file periodically while implementing.

task_progress Items:

- [ ] Step 1: Remove fingerprint fields from plan/templates/command docs and align wording
- [ ] Step 2: Refactor runtime bootstrap payload schemas to remove fingerprint outputs
- [ ] Step 3: Remove analyze fingerprint parsing/comparison logic from implement preflight
- [ ] Step 4: Remove or retire fingerprint lint rule(s) and synchronize lint expectations
- [ ] Step 5: Update tests for new schema/gate behavior and fixture content
- [ ] Step 6: Update README/authority-marker wording to de-fingerprint protocol descriptions
- [ ] Step 7: Run impacted test suites and fix regressions until green

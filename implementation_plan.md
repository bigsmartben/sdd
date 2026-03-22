# Implementation Plan

[Overview]
Remove all file-fingerprint mechanisms across planning, task manifest provenance, analyze history, and implement preflight gating while preserving queue orchestration and gate-decision flow.

The current fingerprint mechanism is distributed across multiple layers: control-plane tables in `plan.md`, manifest provenance (`tasks.manifest.json.generated_from`), analyze run metadata (`Spec/Plan/Tasks SHA256`), and implement-stage stale detection. This means deletion is a protocol-level refactor rather than a field cleanup, and all runtime payload schemas, template contracts, and tests must be updated together.

The target state is a non-fingerprint workflow: planning keeps status/path/blocker state only, tasks manifest keeps minimal source path provenance, analyze history keeps run timestamp + gate decision, and implement preflight validates only analyze presence and `Gate Decision = PASS`. This intentionally removes post-analyze artifact freshness detection and should be documented as a behavior change.

[Types]
All runtime payload and document schemas will be reduced by removing fingerprint keys and columns.

Schema changes:

- `plan.md` table schemas:
  - `Stage Queue` from
    - `Stage ID | Command | Required Inputs | Output Path | Status | Source Fingerprint | Output Fingerprint | Blocker`
    - to `Stage ID | Command | Required Inputs | Output Path | Status | Blocker`
  - `Artifact Status` from
    - `BindingRowID | Unit Type | Target Path | Status | Source Fingerprint | Output Fingerprint | Blocker`
    - to `BindingRowID | Unit Type | Target Path | Status | Blocker`

- `tasks.manifest.json.generated_from` keys:
  - from `plan_path`, `plan_source_fingerprint`, `contract_source_fingerprints`
  - to minimal provenance keyset: `plan_path`

- `analyze-history.md` run metadata:
  - remove `Spec SHA256`, `Plan SHA256`, `Tasks SHA256`
  - keep `Run At (UTC)` and `Gate Decision`

- `IMPLEMENT_BOOTSTRAP` payload:
  - remove `current_fingerprints`
  - remove `latest_run.fingerprints`
  - remove fingerprint-specific errors/codes (`analyze_fingerprints_missing`, `analyze_fingerprint_mismatch`)

- `TASKS_MANIFEST_BOOTSTRAP` payload:
  - remove `current_fingerprints`
  - validate new reduced `generated_from` required keys

- `DATA_MODEL_BOOTSTRAP` payload:
  - remove `current_fingerprints`
  - remove per-stage `source_fingerprint` / `output_fingerprint` fields in selected-stage structures

- `repository_first_gate_protocol.baseline_freshness`:
  - remove `source_manifest_fingerprints` normalization and output block
  - keep `generated_at_utc` and `generator_version`

[Files]
The implementation modifies runtime authority modules, command/templates, lint rules, and regression tests that currently encode fingerprint semantics.

Existing files to modify:

- Runtime source (authoritative behavior)
  - `src/specify_cli/runtime_common.py`
  - `src/specify_cli/runtime_data_model_bootstrap.py`
  - `src/specify_cli/runtime_tasks_manifest_bootstrap.py`
  - `src/specify_cli/runtime_implement_bootstrap.py`
  - `src/specify_cli/runtime_gate_protocol.py`

- Templates and command contracts
  - `templates/plan-template.md`
  - `templates/tasks-template.md`
  - `templates/commands/plan.md`
  - `templates/commands/plan.research.md`
  - `templates/commands/plan.test-matrix.md`
  - `templates/commands/plan.data-model.md`
  - `templates/commands/plan.contract.md`
  - `templates/commands/tasks.md`
  - `templates/commands/analyze.md`
  - `templates/commands/implement.md`

- Lint rules
  - `rules/planning-lint-rules.tsv` (remove `PLN-FP-001`)

- Test suites (schema and wording synchronization)
  - `tests/test_task_preflight_script.py`
  - `tests/test_planning_lint_anchor_status.py`
  - `tests/test_tasks_decomposition_boundary.py`
  - `tests/test_artifact_authority_protocol.py`
  - `tests/test_release_packaging_authority_protocol.py`

- Supporting docs
  - `README.md`

No file moves are required. No new configuration files are required.

[Functions]
The change is primarily function reduction and validation-logic removal in runtime bootstrap builders.

Modified/removed functions:

- `src/specify_cli/runtime_common.py`
  - Remove `compute_sha256(path: Path) -> str` once callsites are eliminated.

- `src/specify_cli/runtime_data_model_bootstrap.py`
  - Modify `build_stage_row(...)` to drop fingerprint fields.
  - Modify `build_data_model_bootstrap_payload(...)` to remove `current_fingerprints` emission.

- `src/specify_cli/runtime_tasks_manifest_bootstrap.py`
  - Update `REQUIRED_GENERATED_FROM_KEYS`.
  - Modify `build_tasks_manifest_validation(...)` generated-from validation accordingly.
  - Modify `build_tasks_manifest_bootstrap_payload(...)` to remove `current_fingerprints`.

- `src/specify_cli/runtime_implement_bootstrap.py`
  - Modify `build_analyze_readiness(...)` to stop parsing/validating SHA markers.
  - Remove fingerprint mismatch computation and related findings.
  - Modify `build_implement_bootstrap_payload(...)` to remove fingerprint outputs and manifest freshness inputs.

- `src/specify_cli/runtime_gate_protocol.py`
  - Remove `_normalize_manifest_fingerprints(...)`.
  - Modify `build_repository_first_gate_protocol(...)` freshness payload shape.

[Classes]
No class additions or removals are required; this refactor is schema/logic-focused on module-level runtime functions and template contracts.

Any class-level behavior changes are indirect (test expectations around packaged command text), with no required inheritance or constructor changes.

[Dependencies]
No third-party dependency changes are needed.

Potential standard-library simplification:

- `hashlib` import in `runtime_common.py` can be removed if `compute_sha256` is fully removed and no fallback usage remains.

[Testing]
Testing must be updated to assert de-fingerprinted protocol behavior and preserve gate correctness.

Required test updates:

- Update fixtures and assertions expecting `Source/Output Fingerprint` columns in plan tables.
- Update tasks manifest assertions from 3 generated-from keys to reduced keyset.
- Update analyze-history fixture generation and implement preflight assertions to remove SHA lines and mismatch expectations.
- Remove or replace `PLN-FP-001` coverage tests.
- Update wording-marker tests that currently assert phrases like:
  - `source/output fingerprints only`
  - `stale control-plane fingerprints`
  - `Spec SHA256/Plan SHA256/Tasks SHA256`

Validation strategy:

1. Run targeted unit tests for modified runtime bootstrap modules.
2. Run template/document contract tests.
3. Run full pytest suite to confirm no stale fingerprint dependency remains.
4. Confirm intended behavior change: implement preflight no longer blocks on post-analyze artifact hash drift.

[Implementation Order]
Implement protocol-contract updates first, then runtime logic, then tests/docs, to keep schema transitions coherent.

1. Update template and command contract language/schemas (plan tables, manifest keys, analyze run metadata).
2. Update runtime builders and gate protocol payload shapes.
3. Remove SHA computation and all remaining callsites.
4. Update lint rules (`PLN-FP-001`) and related tests.
5. Update test fixtures and assertions for runtime payload and command wording.
6. Update README authority wording and any packaged-marker expectations.
7. Run full tests and fix residual mismatches.
8. Capture explicit release note: stale-hash freshness gate removed by design.

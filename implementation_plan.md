# Implementation Plan

## Overview
Refactor the planning pipeline so `Binding Packets` remain the single semantic SSOT and `plan.md` becomes an index-only control plane that points to packet rows instead of duplicating packet payload.

This change removes the current two-copy projection pattern that allows `Binding Projection Index` drift, simplifies downstream bootstraps, and makes the execution gate reason over stable packet references instead of comparing redundant semantic views. The target state keeps the existing planning stages intact, but sharply narrows the responsibilities of `plan.md` to queue state, artifact status, and packet lookup pointers.

The migration should preserve downstream compatibility where practical, but the end state must be clear: `test-matrix.md` owns binding meaning, `plan.md` owns selection and orchestration, and all later stages consume packet content by stable index rather than by copied projection fields.

## Types
Introduce a minimal registry model for the SSOT index and a packet-resolution shape that lets bootstraps load binding meaning by reference instead of by duplicated projection columns.

| Type | Location | Purpose | Shape / Fields | Validation Rules | Relationships |
|---|---|---|---|---|---|
| `BindingIndexEntry` | `src/specify_cli/runtime_context_models.py` (new or promoted helper) | Registry-only row for `plan.md` | `binding_row_id: str`, `packet_source: str`, `status_hint: str \| None = None`, `target_path: str \| None = None` | `binding_row_id` must be stable and unique; `packet_source` must resolve to exactly one row in `test-matrix.md`; no semantic payload fields may be copied into the index | One index entry maps to one binding packet row |
| `BindingPacket` | `test-matrix.md` / runtime packet loader | Authoritative semantic binding payload | `binding_row_id`, `if_scope`, `trigger_refs`, `uif_path_refs`, `udd_refs`, `primary_tm_ids`, `tc_ids`, `test_scope`, `spec_refs`, `scenario_refs`, `success_refs`, `edge_refs` | Existing required field set remains mandatory; packets must remain consumable by downstream stages without requiring `plan.md` mirrors | Source of truth for contract/data-model/tasks consumption |
| `PacketResolutionResult` | `src/specify_cli/runtime_task_bootstrap.py` and `runtime_data_model_bootstrap.py` (internal helper shape) | Captures how an index row resolves to a packet | `binding_row_id`, `packet_source`, `resolved: bool`, `packet: dict \| None`, `error_code: str \| None`, `error_details: dict \| None` | Must distinguish missing source, duplicate source, and malformed packet cases | Used internally by readiness checks and unit inventory construction |
| `SSOTIndexLookup` | `src/specify_cli/runtime_common.py` (helper) | Normalize and resolve packet source references | `binding_row_id`, `source_ref`, `resolved_path`, `resolved_row_selector` | Source references must be deterministic, stable, and parseable from plan rows | Shared by task/data-model bootstraps to avoid divergent lookup logic |

## Files
Retarget the planning templates, runtime bootstraps, and tests so the same SSOT-index rules are enforced from authoring through execution gating.

### New files to create
- `implementation_plan.md` — this plan document; it is the handoff artifact for the refactor work.

### Existing files to modify
- `templates/plan-template.md` — shrink `Binding Projection Index` into an index-only registry and introduce a packet source pointer column or equivalent stable lookup field; remove duplicated binding semantic columns from the plan table.
- `templates/commands/plan.md` — update the planning scaffold so `plan.md` is explicitly described as the control plane and registry, not a semantic projection store.
- `templates/test-matrix-template.md` — strengthen the SSOT contract for `Binding Packets` and state that downstream consumers must load meaning by index rather than copying fields into plan.
- `templates/commands/plan.test-matrix.md` — make packet generation and plan-index emission share one authoritative in-memory binding tuple; emit index pointers, not duplicated semantic payload.
- `templates/commands/plan.contract.md` — state that the matched plan row is a locator ledger only, and all contract semantics come from the packet row resolved by `BindingRowID`.
- `templates/commands/tasks.md` — update the hard gate language to treat packet-source resolution as authoritative and to stop on unresolved index lookups rather than field-diff drift.
- `src/specify_cli/runtime_common.py` — add shared helpers for parsing/normalizing packet source references and resolving them deterministically.
- `src/specify_cli/runtime_task_bootstrap.py` — replace duplicated projection comparison with index-to-packet resolution and packet-level completeness checks.
- `src/specify_cli/runtime_data_model_bootstrap.py` — align data-model readiness with the same SSOT lookup model so it consumes packet source references consistently.
- `src/specify_cli/runtime_context_models.py` — add or promote typed helper structures for index rows and packet-resolution state.
- `tests/test_plan_refactor_templates.py` — update template assertions to reflect index-only plan semantics and SSOT packet ownership.
- `tests/test_task_preflight_script.py` — replace projection-drift expectations with packet-resolution and packet-completeness expectations.
- `tests/test_tasks_decomposition_boundary.py` — update tasks command assertions so they describe source resolution, not duplicated projection comparison.
- `tests/test_artifact_authority_protocol.py` — adjust authority model expectations where plan is now explicitly a registry/control plane and not a semantic mirror.
- `README.md` and `spec-driven.md` — refresh the explanation of plan/test-matrix responsibilities if they still describe plan as a semantic projection store.

### Files to delete or move
- None in the first pass; keep the current file layout and migrate behavior in place to reduce branch risk.

### Configuration file updates
- None expected beyond template and test updates. No third-party package changes are required for the SSOT-index refactor.

## Functions
Refactor the bootstrap pipeline so it resolves binding packets by index and stops reasoning about duplicated plan fields.

### New functions
- `normalize_packet_source_ref(value: str) -> str` in `src/specify_cli/runtime_common.py` — normalize packet source tokens so plan entries resolve deterministically.
- `resolve_binding_packet_source(binding_row_id: str, packet_source: str, test_matrix_path: Path) -> dict[str, Any]` in `src/specify_cli/runtime_task_bootstrap.py` or `runtime_common.py` — load exactly one packet row or return a structured resolution error.
- `load_binding_index_entries(plan_document: str) -> list[dict[str, Any]]` in `src/specify_cli/runtime_task_bootstrap.py` — parse index-only rows from `plan.md`.

### Modified functions
- `build_task_bootstrap_payload(...)` in `src/specify_cli/runtime_task_bootstrap.py` — stop extracting semantic payload from `Binding Projection Index`; instead parse index rows, resolve packet sources, and pass only the resolved packet payload into readiness evaluation.
- `build_unit_inventory(...)` in `src/specify_cli/runtime_task_bootstrap.py` — construct units from resolved packets and contract artifacts; remove the `has_projection_drift` comparison path.
- `build_task_execution_readiness(...)` in `src/specify_cli/runtime_task_bootstrap.py` — replace `binding_projection_packet_drift` with source-resolution and packet-consumption failures such as missing packet source, unresolved packet row, or malformed packet.
- `load_binding_contract_packets(...)` in `src/specify_cli/runtime_task_bootstrap.py` — keep as the authoritative packet loader, but make its outputs the only semantic source used downstream.
- `build_generation_readiness(...)` in `src/specify_cli/runtime_data_model_bootstrap.py` — keep packet validation authoritative and align error wording with the index-only model.
- Any plan/template emitters that currently duplicate `UIF Path Ref(s)`, `UDD Ref(s)`, `Primary TM IDs`, `TC IDs`, or `Test Scope` into `plan.md` should be rewritten to emit source pointers only.

### Removed functions
- Remove no functions initially; the refactor should preserve entrypoints and change their internal semantics so existing scripts remain callable.

## Classes
Add a lightweight typed representation for index rows and keep the rest of the runtime model focused on authority packets and control-plane state.

### New classes
- `BindingIndexEntry` in `src/specify_cli/runtime_context_models.py` — a frozen dataclass for registry rows, with `to_dict()` support for deterministic rendering and validation of `binding_row_id` / `packet_source`.
- `PacketResolutionResult` in `src/specify_cli/runtime_context_models.py` or a nearby runtime helper module — a frozen dataclass capturing `resolved`, `packet`, and structured error details for index lookups.

### Modified classes
- `ContextControlPanel` in `src/specify_cli/runtime_context_models.py` — keep as the deterministic control-plane container, but ensure it can carry index lookup metadata if the plan/control-plane layer needs typed helpers for packet references.
- No changes are expected to the existing metadata-term/relation classes unless shared terminology needs a canonical label for the SSOT-index lookup model.

### Removed classes
- None in the first pass.

## Dependencies
No new external packages are required; the refactor should reuse the current Python 3.11 runtime and existing dependency set.

Implementation dependencies are internal and should be treated as layering, not package work:
- `templates/*` define the contract that `src/specify_cli/runtime_*.py` must enforce.
- `runtime_common.py` should own shared lookup/normalization helpers so task and data-model bootstraps do not diverge.
- `runtime_task_bootstrap.py` and `runtime_data_model_bootstrap.py` must share the same packet-resolution semantics to avoid a split-brain index model.
- Tests must be updated in lockstep with the runtime change so that the new SSOT-index rule is enforced as a single repository-wide convention.

## Testing
Update the regression suite so it validates SSOT-index lookup behavior, not duplicated projection equality.

Test coverage requirements:
- Template tests must verify that `plan.md` is now documented as a registry/control plane and that `Binding Projection Index` no longer mirrors packet semantics.
- Preflight tests must verify that a binding row resolves via `packet_source` / stable lookup and that readiness fails when the source is missing, duplicated, or malformed.
- Contract/task boundary tests must verify that downstream consumers read packet meaning from `Binding Packets` and treat plan rows as locators only.
- Add regression coverage for source lookup normalization, escaped pipe parsing, and duplicate `BindingRowID` / unresolved packet source handling.

Primary test files to update:
- `tests/test_plan_refactor_templates.py`
- `tests/test_task_preflight_script.py`
- `tests/test_tasks_decomposition_boundary.py`
- `tests/test_artifact_authority_protocol.py`

Validation strategy:
- Run focused tests first (`pytest -k "plan_refactor_templates or task_preflight or tasks_decomposition_boundary or artifact_authority_protocol"`).
- Then run the broader bootstrap and template suite to ensure no hidden reliance on duplicated plan semantics remains.

## Implementation Order
Apply the refactor in a compatibility-preserving sequence so the new SSOT-index behavior can land without breaking the entire planning pipeline at once.

1. Update the plan/test-matrix/contract templates and command docs so the target architecture is explicit: `test-matrix.md` owns binding meaning, `plan.md` is an index-only control plane.
2. Add shared packet-source normalization and resolution helpers in the runtime layer so both task and data-model bootstraps resolve packets in the same way.
3. Refactor `runtime_task_bootstrap.py` to stop comparing duplicated projection fields and instead consume resolved packet rows by `BindingRowID` / packet source.
4. Align `runtime_data_model_bootstrap.py` with the same resolution model so it can validate packet completeness without relying on duplicated plan semantics.
5. Update the runtime context models, if needed, to carry typed index rows and resolution results instead of ad hoc dict-only helpers.
6. Rewrite the targeted tests so they assert SSOT-index behavior, source resolution errors, and plan-as-registry semantics.
7. Refresh documentation where it still implies that `plan.md` is a semantic projection mirror.
8. Run the focused test slice, then the broader bootstrap/template slice, and only after that proceed to implementation work on the new branch.

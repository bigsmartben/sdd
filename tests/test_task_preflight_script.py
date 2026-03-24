import json
import os
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _env_with_specify_shim(repo_dir: Path) -> dict[str, str]:
    shim_dir = repo_dir / ".test-bin"
    shim_dir.mkdir(parents=True, exist_ok=True)

    python_exe = Path(sys.executable).as_posix()
    if len(python_exe) >= 3 and python_exe[1:3] == ":/":
        python_exe = f"/mnt/{python_exe[0].lower()}{python_exe[2:]}"
    repo_src = REPO_ROOT / "src"
    repo_src_posix = repo_src.as_posix()
    if len(repo_src_posix) >= 3 and repo_src_posix[1:3] == ":/":
        repo_src_posix = f"/mnt/{repo_src_posix[0].lower()}{repo_src_posix[2:]}"
    shim_path = shim_dir / "specify"
    with shim_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            "#!/usr/bin/env bash\n"
            f"""PYTHONPATH="{repo_src_posix}${{PYTHONPATH:+:$PYTHONPATH}}" "{python_exe}" -c 'import sys; sys.path.insert(0, "{repo_src_posix}"); import specify_cli; sys.argv[0] = "specify"; specify_cli.main()' "$@"\n"""
        )
    shim_path.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env['PATH']}"
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{repo_src}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(repo_src)
    shim_posix = shim_path.as_posix()
    if len(shim_posix) >= 3 and shim_posix[1:3] == ":/":
        shim_posix = f"/mnt/{shim_posix[0].lower()}{shim_posix[2:]}"
    env["SDD_SPECIFY_CMD"] = shim_posix
    return env


def _write_minimal_feature(
    feature_dir: Path,
    contract_text: str | None = None,
    contract_status: str = "done",
    *,
    boundary_anchor_status: str = "existing",
    implementation_entry_anchor: str = "src/app/tasks_controller.py::TasksController.create_task",
    implementation_entry_anchor_status: str = "existing",
    boundary_anchor_strategy_evidence: str = "N/A",
    implementation_entry_anchor_strategy_evidence: str = "N/A",
    test_scope: str = "Integration",
    include_binding_packet: bool = True,
) -> None:
    (feature_dir / "contracts").mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (feature_dir / "data-model.md").write_text("# Data Model\n", encoding="utf-8")
    if include_binding_packet:
        (feature_dir / "test-matrix.md").write_text(
            f"""# Test Matrix

## Interface Partition Decisions

| BindingRowID | User Intent | Trigger Ref(s) | Request Semantics | Visible Result | Side Effect | Repo Landing Hint | Split Rationale |
|--------------|-------------|----------------|-------------------|----------------|-------------|-------------------|-----------------|
| BindingRowID-001 | Create task | [UIF-001.trigger] | Input semantics only | Task created | create | task-entry-family | Single northbound action |

## UIF Full Path Coverage Graph (Mermaid)

```mermaid
flowchart TD
    Start --> Success
```

## UIF Path Coverage Ledger

| UIF Path Ref | Path Type | Included in Graph | Omission Reason |
|--------------|-----------|-------------------|-----------------|
| UIF-Path-001 | Happy | yes | N/A |

## Scenario Matrix

| TM ID | BindingRowID | Path Type | Scenario | Preconditions | Expected Outcome | Related Ref |
|-------|--------------|-----------|----------|---------------|------------------|-------------|
| TM-001 | BindingRowID-001 | Happy | Create task succeeds | Valid request | Task is created | [UC-001, FR-001] |

## Verification Case Anchors

| TC ID | BindingRowID | TM ID | Verification Goal | Observability / Signal | Related Ref |
|-------|--------------|-------|-------------------|------------------------|-------------|
| TC-001 | BindingRowID-001 | TM-001 | Verify success | Task created signal | [SC-001] |
| TC-002 | BindingRowID-001 | TM-001 | Verify failure handling | Error signal | [EC-001] |

## Binding Packets

| BindingRowID | IF Scope | User Intent | Trigger Ref(s) | Request Semantics | Visible Result | Side Effect | Boundary Notes | Repo Landing Hint | UIF Path Ref(s) | UDD Ref(s) | Primary TM IDs | TM IDs | TC IDs | Test Scope | Spec Ref(s) | Scenario Ref(s) | Success Ref(s) | Edge Ref(s) |
|--------------|----------|-------------|----------------|-------------------|----------------|-------------|----------------|-------------------|-----------------|------------|----------------|--------|--------|------------|-------------|-----------------|----------------|-------------|
| BindingRowID-001 | IF-001 | Create task | [UIF-001.trigger] | Input semantics only | Task created | create | permission-gated | task-entry-family | [UIF-Path-001] | [UDD-001] | [TM-001] | [TM-001] | [TC-001, TC-002] | {test_scope} | [UC-001, FR-001] | [S1] | [SC-001] | [EC-001] |
""",
            encoding="utf-8",
        )
    else:
        (feature_dir / "test-matrix.md").write_text("# Test Matrix\n", encoding="utf-8")
    if contract_text is None:
        contract_text = f"""# Northbound Interface Design: BindingRowID-001

**BindingRowID (Required)**: BindingRowID-001
**Operation ID (Required)**: createTask
**IF Scope (Required)**: IF-001
**Boundary Anchor (Required)**: HTTP POST /tasks
**Anchor Status (Required)**: `{boundary_anchor_status}`
**Boundary Anchor Strategy Evidence (Required)**: {boundary_anchor_strategy_evidence}
**Implementation Entry Anchor (Required)**: {implementation_entry_anchor}
**Implementation Entry Anchor Status (Required)**: `{implementation_entry_anchor_status}`
**Implementation Entry Anchor Strategy Evidence (Required)**: {implementation_entry_anchor_strategy_evidence}

## Binding Context

| Field | Value |
|-------|-------|
| `BindingRowID` | BindingRowID-001 |
| `Operation ID` | createTask |
| `IF Scope` | IF-001 |
| `UIF Path Ref(s)` | [UIF-Path-001] |
| `UDD Ref(s)` | [UDD-001] |
| `Primary TM IDs` | [TM-001] |
| `TM IDs` | [TM-001] |
| `TC IDs` | [TC-001, TC-002] |
| `Test Scope` | Integration |
| `Spec Ref(s)` | [UC-001, FR-001] |
| `Scenario Ref(s)` | [S1] |
| `Success Ref(s)` | [SC-001] |
| `Edge Ref(s)` | [EC-001] |

## Interface Definition

### Contract Summary

| Aspect | Definition |
|--------|------------|
| External Input | create-task request |
| Success Output | created task payload |
| Failure Output | error payload |

### Shared Semantic Reuse

| Shared Semantic Ref | Constraint Type | Applied To | Impact on Contract |
|---------------------|-----------------|------------|--------------------|
| N/A | none | N/A | No shared semantic dependency for this fixture |

## Full Field Dictionary (Operation-scoped)

| Field | Owner Class | Dictionary Tier | Direction | Required/Optional | Default | Validation/Enum | Persisted | Contract-visible | Used in createTask | Source Anchor |
|-------|-------------|-----------------|-----------|-------------------|---------|-----------------|-----------|------------------|--------------------|---------------|
| taskId | CreateTaskResponse | operation-critical | output | required | none | uuid | no | yes | yes | `src/app/contracts.py::CreateTaskResponse.taskId` |

## UML Class Design

### Resolved Type Inventory

| Role | Concrete Name | Resolution | Source / Evidence | Notes |
|------|---------------|------------|-------------------|-------|
| boundary-entry | src/app/tasks_controller.py::TasksController.create_task | existing | binding packet + repo anchor | controller-first HTTP entry |
| implementation-entry | {implementation_entry_anchor} | existing | binding packet | implementation handoff |
| request-dto | src/app/contracts.py::CreateTaskRequest | existing | binding packet | concrete request model |
| response-dto | src/app/contracts.py::CreateTaskResponse | existing | binding packet | concrete response model |

## Sequence Design

### Behavior Paths

| Path | Trigger | Key Steps | Outcome | Contract-Visible Failure | Sequence Ref | TM/TC Anchor |
|------|---------|-----------|---------|--------------------------|--------------|--------------|
| Main | [UIF-Path-001] create task | controller -> service | task created | N/A | S1 | TM-001 / TC-001 |
| Failure | [UIF-Path-001] create task invalid | controller -> service -> error | N/A | validation error | S2 | TM-001 / TC-002 |

## Test Projection

### Test Projection Slice

| IF Scope | Operation ID | Test Scope | Primary TM IDs | TM ID(s) | TC ID(s) | Main Pass Anchor | Branch/Failure Anchor(s) | Command / Assertion Signal |
|----------|--------------|------------|----------------|----------|----------|------------------|--------------------------|----------------------------|
| IF-001 | createTask | Integration | [TM-001] | [TM-001] | [TC-001, TC-002] | task create success | task create failure | pytest -k createTask |

### Cross-Interface Smoke Candidate (Required)

| Smoke Candidate ID | IF Scope | Operation ID | Candidate Role | Depends On Candidate ID(s) | Trigger | Main Pass Anchor | Branch/Failure Anchor(s) | Command / Assertion Signal |
|--------------------|----------|--------------|----------------|----------------------------|---------|------------------|--------------------------|----------------------------|
| SMK-001 | IF-001 | createTask | entry | N/A | create task | task create success | task create failure | pytest -k createTask |

## Closure Check

| Check Item | Required Evidence | Status |
|------------|-------------------|--------|
| Interface-definition closure | request/response surface + full field dictionary + shared semantic reuse are all present | ok |
| UML closure | class diagram and two-party package relations both present and consistent with sequence | ok |
| Sequence closure | success/failure paths include mandatory second-party, third-party, and middleware calls | ok |
| Test closure | `TM/TC`, pass/failure anchors, and command/assertion signal are present | ok |

## Upstream References

- repo anchors: [src/app/tasks_controller.py::TasksController.create_task, src/app/contracts.py::CreateTaskResponse]

## Boundary Notes

- Keep controller-first HTTP boundary and bounded task semantics for this fixture.
"""
    (feature_dir / "contracts" / "create-task.md").write_text(contract_text, encoding="utf-8")

    (feature_dir / "plan.md").write_text(
        f"""# Planning Control Plane: Demo

## Summary

Demo planning control plane.

## Shared Context Snapshot

- Feature: Demo

### Repository-First Consumption Slice

- Relevant dependency usage rows / `SIG-*`: [SIG-001]
- Relevant module-edge rules: [EDGE-001]
- Bounded repo candidate anchors: [`src/app/tasks_controller.py::TasksController.create_task`]

## Stage Queue

| Stage ID | Command | Required Inputs | Output Path | Status | Blocker |
|----------|---------|-----------------|-------------|--------|---------|
| research | `/sdd.plan.research` | `plan.md` | `research.md` | done | [none] |
| test-matrix | `/sdd.plan.test-matrix` | `plan.md` | `test-matrix.md` | done | [none] |
| data-model | `/sdd.plan.data-model` | `plan.md` | `data-model.md` | done | [none] |

## Binding Projection Index

| BindingRowID | Packet Source |
|--------------|---------------|
| BindingRowID-001 | test-matrix.md#Binding Packets:BindingRowID-001 |

## Artifact Status

| BindingRowID | Unit Type | Target Path | Status | Blocker |
|--------------|-----------|-------------|--------|---------|
| BindingRowID-001 | contract | `contracts/create-task.md` | {contract_status} | [none] |

## Handoff Protocol

- `/sdd.plan` initializes this file.
- `/sdd.plan.contract` advances one contract row at a time.
- `/sdd.tasks` starts only after required rows are done.
""",
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _write_tasks_and_analyze_history(feature_dir: Path, gate_decision: str = "PASS", *, mismatched_hashes: bool = False) -> None:
    (feature_dir / "tasks.md").write_text("# Tasks\n", encoding="utf-8")
    (feature_dir / "audits").mkdir(parents=True, exist_ok=True)

    spec_sha = _sha256_file(feature_dir / "spec.md")
    plan_sha = _sha256_file(feature_dir / "plan.md")
    tasks_sha = _sha256_file(feature_dir / "tasks.md")

    (feature_dir / "tasks.manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "generated_at": "2026-03-18T00:00:00Z",
                "generated_from": {
                    "plan_path": str(feature_dir / "plan.md"),
                },
                "presentation": {
                    "board_style": "enhanced",
                    "source_lineage": ["plan_path"],
                },
                "tasks": [
                    {
                        "task_id": "T001",
                        "dependencies": [],
                        "if_scope": "GLOBAL",
                        "refs": [],
                        "target_paths": [str(feature_dir / "tasks.md")],
                        "completion_anchors": ["tasks-md-updated"],
                        "conflict_hints": [],
                        "topo_layer": 0,
                        "status": "pending",
                    }
                ],
            },
            ensure_ascii=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    if mismatched_hashes:
        spec_sha = "0" * 64

    (feature_dir / "audits" / "analyze-history.md").write_text(
        f"""<!-- SDD_ANALYZE_RUN_BEGIN -->
Run At (UTC): 2026-03-18T00:00:00Z
Spec SHA256: {spec_sha}
Plan SHA256: {plan_sha}
Tasks SHA256: {tasks_sha}
Gate Decision: {gate_decision}
<!-- SDD_ANALYZE_RUN_END -->
""",
        encoding="utf-8",
    )


def _write_data_model_feature(
    feature_dir: Path,
    *,
    research_status: str = "done",
    test_matrix_status: str = "done",
    data_model_status: str = "pending",
    include_spec: bool = True,
    include_test_matrix: bool = True,
    include_research: bool = True,
    include_data_model: bool = False,
) -> None:
    feature_dir.mkdir(parents=True, exist_ok=True)
    if include_spec:
        (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    if include_test_matrix:
        (feature_dir / "test-matrix.md").write_text(
            """# Test Matrix

## Interface Partition Decisions

| BindingRowID | User Intent | Trigger Ref(s) | Request Semantics | Visible Result | Side Effect | Repo Landing Hint | Split Rationale |
|--------------|-------------|----------------|-------------------|----------------|-------------|-------------------|-----------------|
| BR-001 | Demo intent | [UIF-001.trigger] | Input semantics only | Visible demo result | none | demo-entry-family | Single binding |

## UIF Full Path Coverage Graph (Mermaid)

```mermaid
flowchart TD
    Start --> Success
```

## UIF Path Coverage Ledger

| UIF Path Ref | Path Type | Included in Graph | Omission Reason |
|--------------|-----------|-------------------|-----------------|
| UIF-Path-001 | Happy | yes | N/A |

## Scenario Matrix

| TM ID | BindingRowID | Path Type | Scenario | Preconditions | Expected Outcome | Related Ref |
|-------|--------------|-----------|----------|---------------|------------------|-------------|
| TM-001 | BR-001 | Happy | Demo success | Ready state | Demo visible | [UC-001] |

## Verification Case Anchors

| TC ID | BindingRowID | TM ID | Verification Goal | Observability / Signal | Related Ref |
|-------|--------------|-------|-------------------|------------------------|-------------|
| TC-001 | BR-001 | TM-001 | Verify demo payload | Demo signal | [FR-001] |

## Binding Packets

| BindingRowID | IF Scope | User Intent | Trigger Ref(s) | Request Semantics | Visible Result | Side Effect | Boundary Notes | Repo Landing Hint | UIF Path Ref(s) | UDD Ref(s) | Primary TM IDs | TM IDs | TC IDs | Test Scope | Spec Ref(s) | Scenario Ref(s) | Success Ref(s) | Edge Ref(s) |
|--------------|----------|-------------|----------------|-------------------|----------------|-------------|----------------|-------------------|-----------------|------------|----------------|--------|--------|------------|-------------|-----------------|----------------|-------------|
| BR-001 | IF-001 | Demo intent | [UIF-001.trigger] | Input semantics only | Demo visible | none | N/A | demo-entry-family | [UIF-Path-001] | [UDD-001] | [TM-001] | [TM-001] | [TC-001] | Integration | [UC-001, FR-001] | [S1] | [SC-001] | [EC-001] |
""",
            encoding="utf-8",
        )
    if include_research:
        (feature_dir / "research.md").write_text("# Research\n", encoding="utf-8")
    if include_data_model:
        (feature_dir / "data-model.md").write_text("# Data Model\n", encoding="utf-8")

    (feature_dir / "plan.md").write_text(
        f"""# Planning Control Plane: Demo

## Summary

Demo planning control plane.

## Shared Context Snapshot

- Feature: Demo

### Repository-First Consumption Slice

- Relevant dependency usage rows / `SIG-*`: [SIG-001]
- Relevant module-edge rules: [EDGE-001]
- Bounded repo candidate anchors: [`src/app/tasks_controller.py::TasksController.create_task`]

## Stage Queue

| Stage ID | Command | Required Inputs | Output Path | Status | Blocker |
|----------|---------|-----------------|-------------|--------|---------|
| research | `/sdd.plan.research` | `plan.md`, `spec.md` | `research.md` | {research_status} | [none] |
| test-matrix | `/sdd.plan.test-matrix` | `plan.md`, `spec.md` | `test-matrix.md` | {test_matrix_status} | [none] |
| data-model | `/sdd.plan.data-model` | `plan.md`, `spec.md`, `test-matrix.md` | `data-model.md` | {data_model_status} | [none] |

## Binding Projection Index

| BindingRowID | Packet Source |
|--------------|---------------|

## Artifact Status

| BindingRowID | Unit Type | Target Path | Status | Blocker |
|--------------|-----------|-------------|--------|---------|

## Handoff Protocol

- `/sdd.plan` initializes this file.
- `/sdd.plan.data-model` advances the data-model row.
""",
        encoding="utf-8",
    )


def test_task_preflight_helper_emits_contract_unit_inventory(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    assert payload["schema_version"] == "1.4"
    assert payload["required_sections"]["summary"] is True
    assert payload["required_sections"]["stage_queue"] is True
    assert payload["required_sections"]["handoff_protocol"] is True
    assert payload["incomplete_stage_ids"] == []
    assert payload["stage_queue_status_summary"]["done"] == 3
    assert payload["binding_row_count"] == 1
    assert payload["artifact_status_summary"]["contract"]["done"] == 1
    assert len(payload["unit_inventory"]) == 1
    assert len(payload["ready_unit_inventory"]) == 1
    assert payload["execution_readiness"]["ready_for_task_generation"] is True
    assert payload["execution_readiness"]["error_count"] == 0
    unit = payload["ready_unit_inventory"][0]
    assert unit["binding_row_id"] == "BindingRowID-001"
    assert unit["operation_id"] == "createTask"
    assert unit["if_scope"] == "IF-001"
    assert unit["uif_path_refs"] == ["UIF-Path-001"]
    assert unit["udd_refs"] == ["UDD-001"]
    assert unit["binding_packet"]["present"] is True
    assert unit["binding_packet"]["resolution_error"] == ""
    assert unit["packet_source"] == "test-matrix.md#Binding Packets:BindingRowID-001"
    assert unit["contract"]["target_path"] == "contracts/create-task.md"
    assert unit["contract"]["exists"] is True
    assert unit["contract"]["binding_context_section_present"] is True
    assert unit["contract"]["interface_definition_section_present"] is True
    assert unit["contract"]["full_field_dictionary_present"] is True
    assert unit["contract"]["field_dictionary_tier_present"] is True
    assert unit["contract"]["resolved_type_inventory_present"] is True
    assert unit["contract"]["test_projection_section_present"] is True
    assert unit["contract"]["upstream_references_section_present"] is True
    assert unit["contract"]["boundary_notes_section_present"] is True
    assert unit["contract"]["cross_interface_smoke_candidate_present"] is True
    assert unit["contract"]["cross_interface_smoke_candidate_row_count"] == 1
    assert unit["contract"]["closure_check_section_present"] is True
    assert unit["contract"]["interface_definition_closure_check_present"] is True
    assert unit["contract"]["uml_closure_check_present"] is True
    assert unit["contract"]["sequence_closure_check_present"] is True
    assert unit["contract"]["test_closure_check_present"] is True
    assert unit["contract"]["has_unresolved_field_gaps"] is False
    assert "interface_detail" not in unit


def test_task_preflight_helper_excludes_missing_contract_from_ready_inventory(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    (feature_dir / "contracts" / "create-task.md").unlink()

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    assert len(payload["unit_inventory"]) == 1
    assert payload["unit_inventory"][0]["contract"]["exists"] is False
    assert payload["ready_unit_inventory"] == []
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    assert payload["execution_readiness"]["error_count"] >= 1
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "done_contract_target_missing" in error_codes


def test_task_preflight_helper_accepts_h3_field_dictionary_heading(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    contract_path = feature_dir / "contracts" / "create-task.md"
    contract_text = contract_path.read_text(encoding="utf-8")
    contract_path.write_text(
        contract_text.replace(
            "## Full Field Dictionary (Operation-scoped)",
            "### Full Field Dictionary (Operation-scoped)",
            1,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["execution_readiness"]["ready_for_task_generation"] is True
    assert payload["ready_unit_inventory"][0]["contract"]["full_field_dictionary_present"] is True


def test_task_preflight_helper_treats_empty_contract_status_as_not_done(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir, contract_status="")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "contract_rows_not_done" in error_codes


def test_task_preflight_helper_flags_status_without_contract_target_path(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)

    plan_path = feature_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(
        plan_text.replace(
            "| BindingRowID-001 | contract | `contracts/create-task.md` | done | [none] |",
            "| BindingRowID-001 | contract |  | done | [none] |",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ready_unit_inventory"] == []
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "contract_target_path_missing" in error_codes


def test_task_preflight_helper_surfaces_incomplete_stage_queue_blocker(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)

    plan_path = feature_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(plan_text.replace("| test-matrix | `/sdd.plan.test-matrix` | `plan.md` | `test-matrix.md` | done | [none] |", "| test-matrix | `/sdd.plan.test-matrix` | `plan.md` | `test-matrix.md` | pending | [none] |"), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["incomplete_stage_ids"] == ["test-matrix"]
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "incomplete_stage_queue" in error_codes


def test_task_preflight_helper_requires_pending_data_model_stage(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)

    plan_path = feature_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(
        plan_text.replace(
            "| data-model | `/sdd.plan.data-model` | `plan.md` | `data-model.md` | done | [none] |",
            "| data-model | `/sdd.plan.data-model` | `plan.md` | `data-model.md` | pending | [none] |",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["data_model_required"] is True
    assert payload["required_stage_ids_for_tasks"] == ["data-model", "research", "test-matrix"]
    assert payload["incomplete_stage_ids"] == ["data-model"]
    assert payload["execution_readiness"]["ready_for_task_generation"] is False


def test_task_preflight_helper_ignores_data_model_blocker_when_stage_is_done(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)

    plan_path = feature_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(
        plan_text.replace(
            "| data-model | `/sdd.plan.data-model` | `plan.md` | `data-model.md` | done | [none] |",
            "| data-model | `/sdd.plan.data-model` | `plan.md` | `data-model.md` | done | shared_semantic_alignment_required |",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["data_model_required"] is True
    assert payload["required_stage_ids_for_tasks"] == ["data-model", "research", "test-matrix"]
    assert payload["incomplete_stage_ids"] == []
    assert payload["execution_readiness"]["ready_for_task_generation"] is True


def test_task_preflight_helper_blocks_missing_full_field_dictionary(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir, contract_text="# Contract\n")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ready_unit_inventory"] == []
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "full_field_dictionary_missing" in error_codes


def test_task_preflight_helper_blocks_missing_contract_required_sections(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    contract_path = feature_dir / "contracts" / "create-task.md"
    contract_path.write_text(
        """# Northbound Interface Design: BindingRowID-001

## Full Field Dictionary (Operation-scoped)

| Field | Owner Class | Direction | Required/Optional | Default | Validation/Enum | Persisted | Contract-visible | Used in createTask | Source Anchor |
|-------|-------------|-----------|-------------------|---------|-----------------|-----------|------------------|--------------------|---------------|
| taskId | CreateTaskResponse | output | required | none | uuid | no | yes | yes | `src/app/contracts.py::CreateTaskResponse.taskId` |
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ready_unit_inventory"] == []
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "binding_context_section_missing" in error_codes
    assert "interface_definition_section_missing" in error_codes
    assert "resolved_type_inventory_missing" in error_codes
    assert "cross_interface_smoke_candidate_missing" in error_codes
    assert "upstream_references_section_missing" in error_codes
    assert "boundary_notes_section_missing" in error_codes
    assert "contract_units_not_execution_ready" in error_codes
    warning_codes = [entry["code"] for entry in payload["execution_readiness"]["warnings"]]
    assert "field_dictionary_tier_missing" in warning_codes
    assert "test_projection_section_missing" in warning_codes
    assert "closure_check_section_missing" in warning_codes
    assert "closure_check_rows_missing" in warning_codes


def test_task_preflight_helper_warns_unresolved_contract_field_gaps(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    contract_path = feature_dir / "contracts" / "create-task.md"
    contract_text = contract_path.read_text(encoding="utf-8")
    contract_path.write_text(
        contract_text.replace(
            "| taskId | CreateTaskResponse | operation-critical | output | required | none | uuid | no | yes | yes | `src/app/contracts.py::CreateTaskResponse.taskId` |",
            "| taskId | CreateTaskResponse | operation-critical | output | required | gap | gap | gap | yes | yes | TODO(REPO_ANCHOR) |",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ready_unit_inventory"] == []
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "contract_units_not_execution_ready" in error_codes
    warning_codes = [entry["code"] for entry in payload["execution_readiness"]["warnings"]]
    assert "contract_field_gap_unresolved" in warning_codes


def test_task_preflight_helper_warns_http_controller_first_violation(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    contract_path = feature_dir / "contracts" / "create-task.md"
    contract_text = contract_path.read_text(encoding="utf-8")
    contract_path.write_text(
        contract_text.replace(
            "**Implementation Entry Anchor (Required)**: src/app/tasks_controller.py::TasksController.create_task",
            "**Implementation Entry Anchor (Required)**: src/app/task_service.py::TaskService.create_task",
        ).replace(
            "| implementation-entry | src/app/tasks_controller.py::TasksController.create_task | existing | binding packet | implementation handoff |",
            "| implementation-entry | src/app/task_service.py::TaskService.create_task | existing | binding packet | implementation handoff |",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert len(payload["ready_unit_inventory"]) == 1
    assert payload["execution_readiness"]["ready_for_task_generation"] is True
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "contract_anchor_inventory_mismatch" not in error_codes
    assert "contract_units_not_execution_ready" not in error_codes
    warning_codes = [entry["code"] for entry in payload["execution_readiness"]["warnings"]]
    assert "controller_first_violation" not in warning_codes


def test_task_preflight_helper_blocks_unresolved_contract_placeholder_names(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(
        feature_dir,
        contract_text="""# Northbound Interface Design: BindingRowID-001

**BindingRowID (Required)**: BindingRowID-001
**Operation ID (Required)**: createTask
**IF Scope (Required)**: IF-001
**Boundary Anchor (Required)**: HTTP POST /tasks
**Anchor Status (Required)**: `existing`
**Implementation Entry Anchor (Required)**: src/app/tasks_controller.py::TasksController.create_task
**Implementation Entry Anchor Status (Required)**: `existing`

## Binding Context

| Field | Value |
|-------|-------|
| `BindingRowID` | BindingRowID-001 |
| `Operation ID` | createTask |
| `IF Scope` | IF-001 |
| `UIF Path Ref(s)` | [UIF-Path-001] |
| `Primary TM IDs` | [TM-001] |
| `TM IDs` | [TM-001] |
| `TC IDs` | [TC-001, TC-002] |

## Interface Definition

### Contract Summary

| Aspect | Definition |
|--------|------------|
| External Input | create-task request |
| Success Output | created task payload |
| Failure Output | error payload |

## UML Class Design

### Resolved Type Inventory

| Role | Concrete Name | Resolution | Source / Evidence | Notes |
|------|---------------|------------|-------------------|-------|
| request-dto | <BoundaryRequestModel> | new | contract-local rationale | unresolved placeholder should block |

## Full Field Dictionary (Operation-scoped)

| Field | Owner Class | Dictionary Tier | Direction | Required/Optional | Default | Validation/Enum | Persisted | Contract-visible | Used in createTask | Source Anchor |
|-------|-------------|-----------------|-----------|-------------------|---------|-----------------|-----------|------------------|--------------------|---------------|
| taskId | CreateTaskResponse | operation-critical | output | required | none | uuid | no | yes | yes | `src/app/contracts.py::CreateTaskResponse.taskId` |

## Test Projection

### Test Projection Slice

| IF Scope | Operation ID | Test Scope | Primary TM IDs | TM ID(s) | TC ID(s) | Main Pass Anchor | Branch/Failure Anchor(s) | Command / Assertion Signal |
|----------|--------------|------------|----------------|----------|----------|------------------|--------------------------|----------------------------|
| IF-001 | createTask | Integration | [TM-001] | [TM-001] | [TC-001, TC-002] | task create success | task create failure | pytest -k createTask |

### Cross-Interface Smoke Candidate (Required)

| Smoke Candidate ID | IF Scope | Operation ID | Candidate Role | Depends On Candidate ID(s) | Trigger | Main Pass Anchor | Branch/Failure Anchor(s) | Command / Assertion Signal |
|--------------------|----------|--------------|----------------|----------------------------|---------|------------------|--------------------------|----------------------------|
| SMK-001 | IF-001 | createTask | entry | N/A | create task | task create success | task create failure | pytest -k createTask |

## Closure Check

| Check Item | Required Evidence | Status |
|------------|-------------------|--------|
| Interface-definition closure | request/response surface + full field dictionary + shared semantic reuse are all present | ok |
| UML closure | class diagram and two-party package relations both present and consistent with sequence | ok |
| Sequence closure | success/failure paths include mandatory second-party, third-party, and middleware calls | ok |
| Test closure | `TM/TC`, pass/failure anchors, and command/assertion signal are present | ok |

## Upstream References

- repo anchors: [src/app/tasks_controller.py::TasksController.create_task]

## Boundary Notes

- Placeholder request DTO should block readiness.
""",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ready_unit_inventory"] == []
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "contract_placeholder_names_present" in error_codes


def test_task_preflight_helper_blocks_duplicate_required_contract_sections(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(
        feature_dir,
        contract_text="""# Contract
**Boundary Anchor (Required)**: HTTP POST /tasks
**Implementation Entry Anchor (Required)**: src/app/tasks_controller.py::TasksController.create_task

## Binding Context
| Field | Value |
|-------|-------|
| `UIF Path Ref(s)` | UIF-Path-001 |
| `Primary TM IDs` | [TM-001] |
| `TM IDs` | [TM-001] |
| `TC IDs` | TC-001, TC-002 |

## Full Field Dictionary (Operation-scoped)
| Field | Owner Class | Dictionary Tier | Direction | Required/Optional | Default | Validation/Enum | Persisted | Contract-visible | Used in createTask | Source Anchor |
|-------|-------------|-----------------|-----------|-------------------|---------|-----------------|-----------|------------------|--------------------|---------------|
| taskId | CreateTaskResponse | operation-critical | output | required | none | uuid | no | yes | yes | `src/app/contracts.py::CreateTaskResponse.taskId` |

## UML Class Design
### Resolved Type Inventory
| Role | Concrete Name | Resolution | Source / Evidence | Notes |
|------|---------------|------------|-------------------|-------|
| boundary-entry | HTTP POST /tasks | existing | binding packet | boundary |
| implementation-entry | src/app/tasks_controller.py::TasksController.create_task | existing | binding packet | entry |

## Sequence Design
### Behavior Paths
| Path | Trigger | Key Steps | Outcome | Contract-Visible Failure | Sequence Ref | TM/TC Anchor |
|------|---------|-----------|---------|--------------------------|--------------|--------------|
| Main | create task | call controller | success | N/A | S1 | TM-001 / TC-001, TC-002 |

## Test Projection
### Test Projection Slice
| IF Scope | Operation ID | Test Scope | Primary TM IDs | TM ID(s) | TC ID(s) | Main Pass Anchor | Branch/Failure Anchor(s) | Command / Assertion Signal |
|----------|--------------|------------|----------------|----------|----------|------------------|--------------------------|----------------------------|
| IF-001 | createTask | Integration | [TM-001] | [TM-001] | [TC-001, TC-002] | success | fail | pytest -k createTask |

## Closure Check
| Check Item | Required Evidence | Status |
|------------|-------------------|--------|
| Interface-definition closure | request/response surface + full field dictionary + shared semantic reuse are all present | ok |
| UML closure | class diagram and two-party package relations both present and consistent with sequence | ok |
| Sequence closure | success/failure paths include mandatory second-party, third-party, and middleware calls | ok |
| Test closure | `TM/TC`, pass/failure anchors, and command/assertion signal are present | ok |

## Sequence Design
### Behavior Paths
| Path | Trigger | Key Steps | Outcome | Contract-Visible Failure | Sequence Ref | TM/TC Anchor |
|------|---------|-----------|---------|--------------------------|--------------|--------------|
| Duplicate Section | duplicate heading | duplicated sequence section | drift | N/A | S2 | TM-001 / TC-001 |
""",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "contract_duplicate_required_sections" in error_codes


def test_task_preflight_helper_blocks_binding_context_coverage_drift(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(
        feature_dir,
        contract_text="""# Contract
**Boundary Anchor (Required)**: HTTP POST /tasks
**Implementation Entry Anchor (Required)**: src/app/tasks_controller.py::TasksController.create_task

## Binding Context
| Field | Value |
|-------|-------|
| `UIF Path Ref(s)` | UIF-Path-001, UIF-Path-002 |
| `Primary TM IDs` | [TM-001] |
| `TM IDs` | [TM-001] |
| `TC IDs` | TC-001, TC-002 |

## Full Field Dictionary (Operation-scoped)
| Field | Owner Class | Dictionary Tier | Direction | Required/Optional | Default | Validation/Enum | Persisted | Contract-visible | Used in createTask | Source Anchor |
|-------|-------------|-----------------|-----------|-------------------|---------|-----------------|-----------|------------------|--------------------|---------------|
| taskId | CreateTaskResponse | operation-critical | output | required | none | uuid | no | yes | yes | `src/app/contracts.py::CreateTaskResponse.taskId` |

## UML Class Design
### Resolved Type Inventory
| Role | Concrete Name | Resolution | Source / Evidence | Notes |
|------|---------------|------------|-------------------|-------|
| boundary-entry | HTTP POST /tasks | existing | binding packet | boundary |
| implementation-entry | src/app/tasks_controller.py::TasksController.create_task | existing | binding packet | entry |

## Sequence Design
### Behavior Paths
| Path | Trigger | Key Steps | Outcome | Contract-Visible Failure | Sequence Ref | TM/TC Anchor |
|------|---------|-----------|---------|--------------------------|--------------|--------------|
| Main | create task | call controller | success | N/A | S1 | TM-001 / TC-001 |

## Test Projection
### Test Projection Slice
| IF Scope | Operation ID | Test Scope | Primary TM IDs | TM ID(s) | TC ID(s) | Main Pass Anchor | Branch/Failure Anchor(s) | Command / Assertion Signal |
|----------|--------------|------------|----------------|----------|----------|------------------|--------------------------|----------------------------|
| IF-001 | createTask | Integration | [TM-001] | [TM-001] | [TC-001] | success | fail | pytest -k createTask |

## Closure Check
| Check Item | Required Evidence | Status |
|------------|-------------------|--------|
| Interface-definition closure | request/response surface + full field dictionary + shared semantic reuse are all present | ok |
| UML closure | class diagram and two-party package relations both present and consistent with sequence | ok |
| Sequence closure | success/failure paths include mandatory second-party, third-party, and middleware calls | ok |
| Test closure | `TM/TC`, pass/failure anchors, and command/assertion signal are present | ok |
""",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "contract_binding_context_coverage_drift" in error_codes


def test_task_preflight_helper_allows_reference_case_and_separator_variants(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    contract_path = feature_dir / "contracts" / "create-task.md"
    contract_text = contract_path.read_text(encoding="utf-8")
    contract_path.write_text(
        contract_text.replace(
            "| Main | [UIF-Path-001] create task | controller -> service | task created | N/A | S1 | TM-001 / TC-001 |",
            "| Main | [uif-path-001] create task | controller -> service | task created | N/A | S1 | tm-001 / tc-001 |",
        ).replace(
            "| Failure | [UIF-Path-001] create task invalid | controller -> service -> error | N/A | validation error | S2 | TM-001 / TC-002 |",
            "| Failure | [uif-path-001] create task invalid | controller -> service -> error | N/A | validation error | S2 | tm-001 / tc-002 |",
        ).replace(
            "| IF-001 | createTask | Integration | [TM-001] | [TM-001] | [TC-001, TC-002] | task create success | task create failure | pytest -k createTask |",
            "| IF-001 | createTask | Integration | [tm-001] | [tm-001] | [tc-001, tc-002] | task create success | task create failure | pytest -k createTask |",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert len(payload["ready_unit_inventory"]) == 1
    assert payload["execution_readiness"]["ready_for_task_generation"] is True
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "contract_binding_context_coverage_drift" not in error_codes
    assert "contract_units_not_execution_ready" not in error_codes


def test_task_preflight_helper_allows_anchor_spacing_variants(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    contract_path = feature_dir / "contracts" / "create-task.md"
    contract_text = contract_path.read_text(encoding="utf-8")
    contract_path.write_text(
        contract_text.replace(
            "**Implementation Entry Anchor (Required)**: src/app/tasks_controller.py::TasksController.create_task",
            "**Implementation Entry Anchor (Required)**: src/app/tasks_controller.py :: TasksController . create_task",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert len(payload["ready_unit_inventory"]) == 1
    assert payload["execution_readiness"]["ready_for_task_generation"] is True
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "contract_anchor_inventory_mismatch" not in error_codes
    assert "contract_units_not_execution_ready" not in error_codes


def test_task_preflight_helper_blocks_anchor_inventory_mismatch(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    contract_path = feature_dir / "contracts" / "create-task.md"
    contract_path.write_text(
        contract_path.read_text(encoding="utf-8").replace(
            "**Boundary Anchor (Required)**: HTTP POST /tasks",
            "**Boundary Anchor (Required)**: TasksBoundary.handle",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "contract_anchor_inventory_mismatch" in error_codes


def test_task_preflight_helper_flags_missing_binding_projection_tuple_fields(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)

    plan_path = feature_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(
        plan_text.replace(
            "| BindingRowID-001 | test-matrix.md#Binding Packets:BindingRowID-001 |",
            "| BindingRowID-001 |  |",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "binding_projection_missing_required_fields" in error_codes


def test_task_preflight_helper_blocks_missing_binding_contract_packet(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir, include_binding_packet=False)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "test_matrix_required_sections_missing" in error_codes
    assert "contract_units_not_execution_ready" in error_codes
    warning_codes = [entry["code"] for entry in payload["execution_readiness"]["warnings"]]
    assert "missing_binding_contract_packet" in warning_codes


def test_task_preflight_helper_blocks_binding_projection_packet_drift(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)

    plan_path = feature_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(
        plan_text.replace(
            "| BindingRowID-001 | test-matrix.md#Binding Packets:BindingRowID-001 |",
            "| BindingRowID-001 | test-matrix.md#Binding Packets:BindingRowID-999 |",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "binding_packet_source_unresolved" in error_codes


def test_task_preflight_helper_blocks_duplicate_binding_projection_binding_row_ids(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)

    plan_path = feature_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(
        plan_text.replace(
            "| BindingRowID-001 | test-matrix.md#Binding Packets:BindingRowID-001 |\n",
            "| BindingRowID-001 | test-matrix.md#Binding Packets:BindingRowID-001 |\n"
            "| BindingRowID-001 | test-matrix.md#Binding Packets:BindingRowID-001 |\n",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "binding_projection_duplicate_binding_row_id" in error_codes


def test_task_preflight_helper_blocks_duplicate_binding_projection_packet_sources(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)

    plan_path = feature_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(
        plan_text.replace(
            "## Artifact Status\n",
            "## Artifact Status\n",
        ).replace(
            "| BindingRowID-001 | test-matrix.md#Binding Packets:BindingRowID-001 |\n\n## Artifact Status",
            "| BindingRowID-001 | test-matrix.md#Binding Packets:BindingRowID-001 |\n"
            "| BindingRowID-002 | test-matrix.md#Binding Packets:BindingRowID-001 |\n\n## Artifact Status",
        ).replace(
            "| BindingRowID-001 | contract | `contracts/create-task.md` | done | [none] |",
            "| BindingRowID-001 | contract | `contracts/create-task.md` | done | [none] |\n"
            "| BindingRowID-002 | contract | `contracts/create-task.md` | done | [none] |",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "binding_projection_duplicate_packet_source" in error_codes


def test_task_preflight_helper_blocks_duplicate_binding_packet_rows(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)

    test_matrix_path = feature_dir / "test-matrix.md"
    test_matrix_text = test_matrix_path.read_text(encoding="utf-8")
    test_matrix_path.write_text(
        test_matrix_text.replace(
            "| BindingRowID-001 | IF-001 | Create task | [UIF-001.trigger] | Input semantics only | Task created | create | permission-gated | task-entry-family | [UIF-Path-001] | [UDD-001] | [TM-001] | [TM-001] | [TC-001, TC-002] | Integration | [UC-001, FR-001] | [S1] | [SC-001] | [EC-001] |\n",
            "| BindingRowID-001 | IF-001 | Create task | [UIF-001.trigger] | Input semantics only | Task created | create | permission-gated | task-entry-family | [UIF-Path-001] | [UDD-001] | [TM-001] | [TM-001] | [TC-001, TC-002] | Integration | [UC-001, FR-001] | [S1] | [SC-001] | [EC-001] |\n"
            "| BindingRowID-001 | IF-001 | Create task | [UIF-001.trigger] | Input semantics only | Task created | create | permission-gated | task-entry-family | [UIF-Path-001] | [UDD-001] | [TM-001] | [TM-001] | [TC-001, TC-002] | Integration | [UC-001, FR-001] | [S1] | [SC-001] | [EC-001] |\n",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "binding_packets_duplicate_binding_row_id" in error_codes


def test_task_preflight_helper_blocks_missing_anchor_strategy_evidence_for_new_anchors(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(
        feature_dir,
        boundary_anchor_status="new",
        implementation_entry_anchor_status="new",
        boundary_anchor_strategy_evidence="existing rejected only",
        implementation_entry_anchor_strategy_evidence="",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "new_anchor_strategy_evidence_missing" in error_codes


def test_task_preflight_helper_blocks_new_anchor_repo_path_overclaim(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(
        feature_dir,
        boundary_anchor_status="new",
        implementation_entry_anchor_status="new",
        boundary_anchor_strategy_evidence="existing rejected: no consumer-visible route fit; extended rejected: semantic mismatch",
        implementation_entry_anchor_strategy_evidence="existing rejected: no entry fits operation; extended rejected: signature mismatch",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["execution_readiness"]["ready_for_task_generation"] is False
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "new_anchor_repo_path_overclaim" in error_codes


def test_task_preflight_helper_allows_new_anchor_design_target_name_without_repo_path(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(
        feature_dir,
        boundary_anchor_status="new",
        implementation_entry_anchor="TaskEntry.execute",
        implementation_entry_anchor_status="new",
        boundary_anchor_strategy_evidence="existing rejected: no consumer-visible route fit; extended rejected: semantic mismatch",
        implementation_entry_anchor_strategy_evidence="existing rejected: no entry fits operation; extended rejected: signature mismatch",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["execution_readiness"]["ready_for_task_generation"] is True
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "new_anchor_repo_path_overclaim" not in error_codes


def test_task_preflight_helper_warns_when_new_anchor_symbol_not_observable_in_repo_file(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(
        feature_dir,
        implementation_entry_anchor="src/app/task_entry.py::TaskEntry.execute",
        implementation_entry_anchor_status="new",
        implementation_entry_anchor_strategy_evidence="existing rejected: no entry fits operation; extended rejected: signature mismatch",
    )

    repo_symbol_path = feature_dir.parent.parent / "src" / "app" / "task_entry.py"
    repo_symbol_path.parent.mkdir(parents=True, exist_ok=True)
    repo_symbol_path.write_text(
        """class TaskRunner:\n    def run(self):\n        return 'ok'\n""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["execution_readiness"]["ready_for_task_generation"] is True
    warning_codes = [entry["code"] for entry in payload["execution_readiness"]["warnings"]]
    assert "new_anchor_symbol_unverified" in warning_codes
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "new_anchor_repo_path_overclaim" not in error_codes


def test_task_preflight_helper_accepts_new_anchor_symbol_when_observable_in_repo_file(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(
        feature_dir,
        implementation_entry_anchor="src/app/task_entry.py::TaskEntry.execute",
        implementation_entry_anchor_status="new",
        implementation_entry_anchor_strategy_evidence="existing rejected: no entry fits operation; extended rejected: signature mismatch",
    )

    repo_symbol_path = feature_dir.parent.parent / "src" / "app" / "task_entry.py"
    repo_symbol_path.parent.mkdir(parents=True, exist_ok=True)
    repo_symbol_path.write_text(
        """class TaskEntry:\n    def execute(self):\n        return 'ok'\n""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["execution_readiness"]["ready_for_task_generation"] is True
    warning_codes = [entry["code"] for entry in payload["execution_readiness"]["warnings"]]
    assert "new_anchor_symbol_unverified" not in warning_codes


def test_task_preflight_helper_ignores_template_placeholder_binding_rows(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    (feature_dir / "plan.md").write_text(
        """# Planning Control Plane: Demo

## Shared Context Snapshot

- Feature: Demo

## Stage Queue

| Stage ID | Command | Required Inputs | Output Path | Status | Blocker |
|----------|---------|-----------------|-------------|--------|---------|
| research | `/sdd.plan.research` | `plan.md` | `research.md` | done | [none] |
| test-matrix | `/sdd.plan.test-matrix` | `plan.md` | `test-matrix.md` | done | [none] |
| data-model | `/sdd.plan.data-model` | `plan.md` | `data-model.md` | done | [none] |

## Binding Projection Index

| BindingRowID | Packet Source |
|--------------|---------------|
| [BindingRowID-001] | [test-matrix.md#Binding Packets:BindingRowID-001] |

## Artifact Status

| BindingRowID | Unit Type | Target Path | Status | Blocker |
|--------------|-----------|-------------|--------|---------|
| [BindingRowID-001] | [contract] | [contracts/create-task.md] | [pending] | [none] |
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["binding_row_count"] == 0
    assert payload["artifact_status"] == []
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "empty_binding_projection_index" in error_codes
    assert "missing_contract_artifact_rows" in error_codes


def test_task_preflight_helper_parses_escaped_pipe_cells_in_artifact_status(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)

    plan_path = feature_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(
        plan_text.replace(
            "| BindingRowID-001 | contract | `contracts/create-task.md` | done | [none] |",
            r"| BindingRowID-001 | contract | `contracts/create-task.md` | done | test-matrix:abc\|binding:BindingRowID-001 |",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "task_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
            "--test-matrix",
            str(feature_dir / "test-matrix.md"),
            "--contracts-dir",
            str(feature_dir / "contracts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["artifact_status_summary"]["contract"]["done"] == 1
    assert payload["execution_readiness"]["ready_for_task_generation"] is True


def test_data_model_preflight_helper_parses_escaped_pipe_cells_in_stage_queue(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_data_model_feature(feature_dir)

    plan_path = feature_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(
        plan_text.replace(
            "| research | `/sdd.plan.research` | `plan.md`, `spec.md` | `research.md` | done | [none] |",
            r"| research | `/sdd.plan.research` | `plan.md`, `spec.md` | `research.md` | done | spec:abc\|research:def |",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "data_model_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--research",
            str(feature_dir / "research.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["research_stage"]["status"] == "done"
    assert payload["selected_stage"]["stage_id"] == "data-model"
    assert payload["generation_readiness"]["ready_for_generation"] is True


def test_bash_check_prerequisites_can_embed_tasks_bootstrap(tmp_path):
    repo_dir = tmp_path / "repo"
    scripts_bash = repo_dir / "scripts" / "bash"
    scripts_bash.mkdir(parents=True)

    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "common.sh", scripts_bash / "common.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "check-prerequisites.sh", scripts_bash / "check-prerequisites.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "task_preflight.py", repo_dir / "scripts" / "task_preflight.py")
    (scripts_bash / "check-prerequisites.sh").chmod(0o755)

    feature_dir = repo_dir / "specs" / "20250708-demo"
    _write_minimal_feature(feature_dir)

    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(["git", "checkout", "-b", "feature-20250708-demo"], cwd=repo_dir, capture_output=True, check=True)

    env = _env_with_specify_shim(repo_dir)
    env["SPECIFY_FEATURE"] = "feature-20250708-demo"

    result = subprocess.run(
        ["bash", "scripts/bash/check-prerequisites.sh", "--json", "--task-preflight"],
        cwd=repo_dir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    assert payload["FEATURE_DIR"].replace("\\", "/").endswith("/repo/specs/20250708-demo")
    assert "TASKS_BOOTSTRAP" in payload
    assert payload["TASKS_BOOTSTRAP"]["binding_row_count"] == 1
    assert len(payload["TASKS_BOOTSTRAP"]["ready_unit_inventory"]) == 1
    assert payload["TASKS_BOOTSTRAP"]["execution_readiness"]["ready_for_task_generation"] is True
    protocol = payload["TASKS_BOOTSTRAP"]["repository_first_gate_protocol"]
    assert protocol["schema_version"] == "1.0"
    assert protocol["gate_name"] == "task_bootstrap"
    assert protocol["baseline_checks"]["missing"] == []
    assert protocol["baseline_checks"]["stale"] == []
    assert protocol["baseline_checks"]["non_traceable"] == []
    freshness = protocol["baseline_freshness"]
    assert freshness["generated_at_utc"]["status"] == "available"
    assert isinstance(freshness["generated_at_utc"]["value"], str)
    assert "source_manifest_fingerprints" not in freshness


def test_bash_check_prerequisites_supports_feature_prefixed_branch_default(tmp_path):
    repo_dir = tmp_path / "repo"
    scripts_bash = repo_dir / "scripts" / "bash"
    scripts_bash.mkdir(parents=True)

    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "common.sh", scripts_bash / "common.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "check-prerequisites.sh", scripts_bash / "check-prerequisites.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "task_preflight.py", repo_dir / "scripts" / "task_preflight.py")
    (scripts_bash / "check-prerequisites.sh").chmod(0o755)

    feature_dir = repo_dir / "specs" / "20250708-parent-hanxue-channel"
    _write_minimal_feature(feature_dir)

    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(["git", "checkout", "-b", "feature-20250708-parent-hanxue-channel"], cwd=repo_dir, capture_output=True, check=True)

    env = _env_with_specify_shim(repo_dir)
    env["SPECIFY_FEATURE"] = "feature-20250708-parent-hanxue-channel"

    result = subprocess.run(
        ["bash", "scripts/bash/check-prerequisites.sh", "--json", "--task-preflight"],
        cwd=repo_dir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["FEATURE_DIR"].replace("\\", "/").endswith("/repo/specs/20250708-parent-hanxue-channel")
    assert payload["TASKS_BOOTSTRAP"]["execution_readiness"]["ready_for_task_generation"] is True


def test_bash_check_prerequisites_task_preflight_uses_branch_inferred_plan_file(tmp_path):
    repo_dir = tmp_path / "repo"
    scripts_bash = repo_dir / "scripts" / "bash"
    scripts_bash.mkdir(parents=True)

    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "common.sh", scripts_bash / "common.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "check-prerequisites.sh", scripts_bash / "check-prerequisites.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "task_preflight.py", repo_dir / "scripts" / "task_preflight.py")
    (scripts_bash / "check-prerequisites.sh").chmod(0o755)

    feature_dir = repo_dir / "specs" / "20250708-demo"
    _write_minimal_feature(feature_dir)
    env = _env_with_specify_shim(repo_dir)
    env["SPECIFY_FEATURE"] = "feature-20250708-demo"

    result = subprocess.run(
        ["bash", "scripts/bash/check-prerequisites.sh", "--json", "--task-preflight"],
        cwd=repo_dir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["FEATURE_DIR"].replace("\\", "/").endswith("/repo/specs/20250708-demo")
    assert payload["TASKS_BOOTSTRAP"]["schema_version"] == "1.4"
    assert payload["TASKS_BOOTSTRAP"]["execution_readiness"]["ready_for_task_generation"] is True


def test_implement_preflight_helper_reports_pass_when_latest_analyze_gate_is_pass(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    _write_tasks_and_analyze_history(feature_dir, gate_decision="PASS")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "implement_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--spec",
            str(feature_dir / "spec.md"),
            "--plan",
            str(feature_dir / "plan.md"),
            "--tasks",
            str(feature_dir / "tasks.md"),
            "--analyze-history",
            str(feature_dir / "audits" / "analyze-history.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1.0"
    assert payload["analyze_readiness"]["ready_for_implementation"] is True
    assert payload["analyze_readiness"]["error_count"] == 0
    assert payload["latest_run"]["gate_decision"] == "PASS"


def test_implement_preflight_helper_flags_non_pass_gate(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    _write_tasks_and_analyze_history(feature_dir, gate_decision="FAIL")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "implement_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--spec",
            str(feature_dir / "spec.md"),
            "--plan",
            str(feature_dir / "plan.md"),
            "--tasks",
            str(feature_dir / "tasks.md"),
            "--analyze-history",
            str(feature_dir / "audits" / "analyze-history.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["analyze_readiness"]["ready_for_implementation"] is False
    error_codes = [entry["code"] for entry in payload["analyze_readiness"]["errors"]]
    assert "gate_decision_not_pass" in error_codes




def test_bash_check_prerequisites_can_embed_implement_bootstrap(tmp_path):
    repo_dir = tmp_path / "repo"
    scripts_bash = repo_dir / "scripts" / "bash"
    scripts_bash.mkdir(parents=True)

    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "common.sh", scripts_bash / "common.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "check-prerequisites.sh", scripts_bash / "check-prerequisites.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "implement_preflight.py", repo_dir / "scripts" / "implement_preflight.py")
    (scripts_bash / "check-prerequisites.sh").chmod(0o755)

    feature_dir = repo_dir / "specs" / "20250708-demo"
    _write_minimal_feature(feature_dir)
    _write_tasks_and_analyze_history(feature_dir, gate_decision="PASS")

    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(["git", "checkout", "-b", "feature-20250708-demo"], cwd=repo_dir, capture_output=True, check=True)

    env = _env_with_specify_shim(repo_dir)
    env["SPECIFY_FEATURE"] = "feature-20250708-demo"

    result = subprocess.run(
        [
            "bash",
            "scripts/bash/check-prerequisites.sh",
            "--json",
            "--require-tasks",
            "--include-tasks",
            "--implement-preflight",
        ],
        cwd=repo_dir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["FEATURE_DIR"].replace("\\", "/").endswith("/repo/specs/20250708-demo")
    assert "IMPLEMENT_BOOTSTRAP" in payload
    assert payload["IMPLEMENT_BOOTSTRAP"]["schema_version"] == "1.0"
    assert payload["IMPLEMENT_BOOTSTRAP"]["analyze_readiness"]["ready_for_implementation"] is True
    protocol = payload["IMPLEMENT_BOOTSTRAP"]["repository_first_gate_protocol"]
    assert protocol["schema_version"] == "1.0"
    assert protocol["gate_name"] == "implement_bootstrap"
    assert protocol["baseline_checks"]["missing"] == []
    assert protocol["baseline_checks"]["stale"] == []
    assert protocol["baseline_checks"]["non_traceable"] == []
    freshness = protocol["baseline_freshness"]
    assert freshness["generated_at_utc"]["status"] == "available"
    assert isinstance(freshness["generated_at_utc"]["value"], str)
    assert "source_manifest_fingerprints" not in freshness
    assert payload["IMPLEMENT_BOOTSTRAP"]["latest_run"]["gate_decision"] == "PASS"
    assert isinstance(payload["IMPLEMENT_BOOTSTRAP"]["latest_run"]["run_at_utc"], str)
    assert "TASKS_MANIFEST_BOOTSTRAP" in payload
    assert payload["TASKS_MANIFEST_BOOTSTRAP"]["schema_version"] == "1.0"
    assert payload["TASKS_MANIFEST_BOOTSTRAP"]["validation"]["valid"] is True


def test_data_model_preflight_helper_reports_ready_when_research_done_and_data_model_pending(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_data_model_feature(feature_dir)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "data_model_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--research",
            str(feature_dir / "research.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1.4"
    assert payload["state_machine_policy"]["full_fsm_rule"] == "N > 3 or T >= 2N"
    assert payload["state_machine_policy"]["required_model_kinds"] == ["lightweight", "fsm"]
    assert payload["state_machine_policy"]["required_sections_by_model"]["lightweight"] == [
        "lifecycle_summary",
        "invariant_catalog",
        "state_transition_table",
    ]
    assert payload["state_machine_policy"]["required_sections_by_model"]["fsm"] == [
        "lifecycle_summary",
        "invariant_catalog",
        "state_transition_table",
        "transition_pseudocode",
        "state_diagram",
    ]
    assert payload["state_machine_policy"]["required_components_by_model"]["lightweight"] == [
        "allowed_transitions",
        "forbidden_transitions",
        "key_invariants",
    ]
    assert payload["shared_semantic_boundary_policy"]["forbidden_contract_suffixes"] == [
        "DTO",
        "Request",
        "Response",
        "Command",
        "Result",
    ]
    assert payload["shared_semantic_boundary_policy"]["forbidden_interface_role_suffixes"] == [
        "Controller",
        "Service",
        "Facade",
    ]
    assert payload["shared_semantic_boundary_policy"]["new_anchor_requires_strategy_evidence"] is True
    assert payload["shared_semantic_boundary_policy"]["new_anchor_prefers_todo_repo_anchor_until_symbol_exists"] is True
    assert payload["shared_semantic_boundary_policy"]["contract_must_reuse_shared_refs"] is True
    assert payload["shared_semantic_boundary_policy"]["contract_must_not_redefine_shared_semantics"] == [
        "owner_source_alignment",
        "lifecycle_vocabulary",
        "invariant_vocabulary",
        "shared_owner_decisions",
    ]
    assert payload["state_machine_policy"]["full_fsm_required_components"] == [
        "transition_table",
        "transition_pseudocode",
        "state_diagram",
    ]
    assert payload["state_machine_policy"]["lightweight_model_required_components"] == [
        "allowed_transitions",
        "forbidden_transitions",
        "key_invariants",
    ]
    assert payload["required_sections"]["summary"] is True
    assert payload["required_sections"]["shared_context_snapshot"] is True
    assert payload["required_sections"]["stage_queue"] is True
    assert payload["required_sections"]["binding_projection_index"] is True
    assert payload["required_sections"]["artifact_status"] is True
    assert payload["required_sections"]["handoff_protocol"] is True
    assert payload["research_stage"]["status"] == "done"
    assert payload["test_matrix_stage"]["status"] == "done"
    assert payload["selected_stage"]["stage_id"] == "data-model"
    assert payload["selected_stage"]["status"] == "pending"
    assert payload["test_matrix_path"].endswith("test-matrix.md")
    assert payload["generation_readiness"]["ready_for_generation"] is True
    assert payload["generation_readiness"]["error_count"] == 0
    assert payload["repo_anchor_policy"]["decision_order"] == ["existing", "extended", "new"]


def test_data_model_preflight_helper_warns_research_not_done(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_data_model_feature(feature_dir, research_status="pending")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "data_model_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--research",
            str(feature_dir / "research.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["generation_readiness"]["ready_for_generation"] is True
    warning_codes = [entry["code"] for entry in payload["generation_readiness"]["warnings"]]
    assert "research_stage_not_done" in warning_codes


def test_data_model_preflight_helper_flags_test_matrix_not_done(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_data_model_feature(feature_dir, test_matrix_status="pending")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "data_model_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--research",
            str(feature_dir / "research.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["generation_readiness"]["ready_for_generation"] is True
    warning_codes = [entry["code"] for entry in payload["generation_readiness"]["warnings"]]
    assert "test_matrix_stage_not_done" in warning_codes


def test_data_model_preflight_helper_flags_missing_test_matrix_artifact(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_data_model_feature(feature_dir, include_test_matrix=False)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "data_model_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--research",
            str(feature_dir / "research.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["generation_readiness"]["ready_for_generation"] is False
    error_codes = [entry["code"] for entry in payload["generation_readiness"]["errors"]]
    assert "test_matrix_missing" in error_codes


def test_data_model_preflight_helper_flags_missing_required_test_matrix_sections(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_data_model_feature(feature_dir)

    test_matrix_path = feature_dir / "test-matrix.md"
    test_matrix_path.write_text(
        test_matrix_path.read_text(encoding="utf-8").replace("## UIF Path Coverage Ledger\n", ""),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "data_model_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--research",
            str(feature_dir / "research.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["generation_readiness"]["ready_for_generation"] is False
    error_codes = [entry["code"] for entry in payload["generation_readiness"]["errors"]]
    assert "test_matrix_required_sections_missing" in error_codes


def test_data_model_preflight_helper_flags_duplicate_binding_projection_binding_row_ids(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_data_model_feature(feature_dir)

    plan_path = feature_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(
        plan_text.replace(
            "|--------------|---------------|\n\n## Artifact Status",
            "|--------------|---------------|\n"
            "| BR-001 | test-matrix.md#Binding Packets:BR-001 |\n"
            "| BR-001 | test-matrix.md#Binding Packets:BR-001 |\n\n## Artifact Status",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "data_model_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--research",
            str(feature_dir / "research.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    error_codes = [entry["code"] for entry in payload["generation_readiness"]["errors"]]
    assert "binding_projection_duplicate_binding_row_id" in error_codes


def test_data_model_preflight_helper_flags_duplicate_binding_packet_rows(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_data_model_feature(feature_dir)

    plan_path = feature_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(
        plan_text.replace(
            "|--------------|---------------|\n\n## Artifact Status",
            "|--------------|---------------|\n| BR-001 | test-matrix.md#Binding Packets:BR-001 |\n\n## Artifact Status",
        ),
        encoding="utf-8",
    )

    test_matrix_path = feature_dir / "test-matrix.md"
    test_matrix_text = test_matrix_path.read_text(encoding="utf-8")
    test_matrix_path.write_text(
        test_matrix_text.replace(
            "| BR-001 | IF-001 | Demo intent | [UIF-001.trigger] | Input semantics only | Demo visible | none | N/A | demo-entry-family | [UIF-Path-001] | [UDD-001] | [TM-001] | [TM-001] | [TC-001] | Integration | [UC-001, FR-001] | [S1] | [SC-001] | [EC-001] |\n",
            "| BR-001 | IF-001 | Demo intent | [UIF-001.trigger] | Input semantics only | Demo visible | none | N/A | demo-entry-family | [UIF-Path-001] | [UDD-001] | [TM-001] | [TM-001] | [TC-001] | Integration | [UC-001, FR-001] | [S1] | [SC-001] | [EC-001] |\n"
            "| BR-001 | IF-001 | Demo intent | [UIF-001.trigger] | Input semantics only | Demo visible | none | N/A | demo-entry-family | [UIF-Path-001] | [UDD-001] | [TM-001] | [TM-001] | [TC-001] | Integration | [UC-001, FR-001] | [S1] | [SC-001] | [EC-001] |\n",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "data_model_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--research",
            str(feature_dir / "research.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    error_codes = [entry["code"] for entry in payload["generation_readiness"]["errors"]]
    assert "binding_packets_duplicate_binding_row_id" in error_codes


def test_data_model_preflight_helper_flags_missing_pending_data_model_row(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_data_model_feature(feature_dir, data_model_status="done", include_data_model=True)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "data_model_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--research",
            str(feature_dir / "research.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["generation_readiness"]["ready_for_generation"] is True
    warning_codes = [entry["code"] for entry in payload["generation_readiness"]["warnings"]]
    assert "data_model_stage_not_pending" in warning_codes


def test_data_model_preflight_helper_suggests_test_matrix_recovery_route(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_data_model_feature(feature_dir)

    test_matrix_path = feature_dir / "test-matrix.md"
    test_matrix_path.write_text(
        test_matrix_path.read_text(encoding="utf-8").replace("## UIF Path Coverage Ledger\n", ""),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "data_model_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--research",
            str(feature_dir / "research.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["generation_readiness"]["ready_for_generation"] is False
    assert payload["recovery_handoff"]["next_command"] == "/sdd.plan.test-matrix"
    assert payload["recovery_handoff"]["ready_blocked"] == "Blocked"


def test_data_model_preflight_helper_suggests_plan_recovery_route_for_stage_queue_blocker(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_data_model_feature(feature_dir, data_model_status="done", include_data_model=True)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "data_model_preflight.py"),
            "--feature-dir",
            str(feature_dir),
            "--plan",
            str(feature_dir / "plan.md"),
            "--spec",
            str(feature_dir / "spec.md"),
            "--research",
            str(feature_dir / "research.md"),
            "--data-model",
            str(feature_dir / "data-model.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["generation_readiness"]["ready_for_generation"] is True
    assert payload["recovery_handoff"]["next_command"] == "/sdd.plan.contract"
    assert payload["recovery_handoff"]["ready_blocked"] == "Ready"


def test_bash_check_prerequisites_can_embed_data_model_bootstrap(tmp_path):
    repo_dir = tmp_path / "repo"
    scripts_bash = repo_dir / "scripts" / "bash"
    scripts_bash.mkdir(parents=True)

    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "common.sh", scripts_bash / "common.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "check-prerequisites.sh", scripts_bash / "check-prerequisites.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "data_model_preflight.py", repo_dir / "scripts" / "data_model_preflight.py")
    (scripts_bash / "check-prerequisites.sh").chmod(0o755)

    feature_dir = repo_dir / "specs" / "20250708-demo"
    _write_data_model_feature(feature_dir)

    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(["git", "checkout", "-b", "feature-20250708-demo"], cwd=repo_dir, capture_output=True, check=True)

    env = _env_with_specify_shim(repo_dir)
    env["SPECIFY_FEATURE"] = "feature-20250708-demo"

    result = subprocess.run(
        ["bash", "scripts/bash/check-prerequisites.sh", "--json", "--data-model-preflight"],
        cwd=repo_dir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["FEATURE_DIR"].replace("\\", "/").endswith("/repo/specs/20250708-demo")
    assert "DATA_MODEL_BOOTSTRAP" in payload
    assert payload["DATA_MODEL_BOOTSTRAP"]["schema_version"] == "1.4"
    assert payload["DATA_MODEL_BOOTSTRAP"]["shared_semantic_boundary_policy"]["forbidden_contract_suffixes"] == [
        "DTO",
        "Request",
        "Response",
        "Command",
        "Result",
    ]
    assert payload["DATA_MODEL_BOOTSTRAP"]["shared_semantic_boundary_policy"]["new_anchor_requires_strategy_evidence"] is True
    assert payload["DATA_MODEL_BOOTSTRAP"]["shared_semantic_boundary_policy"]["contract_must_reuse_shared_refs"] is True
    assert payload["DATA_MODEL_BOOTSTRAP"]["state_machine_policy"]["required_model_kinds"] == ["lightweight", "fsm"]
    assert payload["DATA_MODEL_BOOTSTRAP"]["generation_readiness"]["ready_for_generation"] is True


def test_tasks_command_prefers_task_preflight_bootstrap():
    tasks_command = (REPO_ROOT / "templates" / "commands" / "tasks.md").read_text(encoding="utf-8")
    mapping_path = REPO_ROOT / "docs" / "command-template-mapping.md"
    mapping_doc = mapping_path.read_text(encoding="utf-8") if mapping_path.exists() else None
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    powershell_script = (REPO_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1").read_text(encoding="utf-8")
    bash_script = (REPO_ROOT / "scripts" / "bash" / "check-prerequisites.sh").read_text(encoding="utf-8")

    assert "scripts/bash/check-prerequisites.sh --json --task-preflight" in tasks_command
    assert "scripts/powershell/check-prerequisites.ps1 -Json -TaskPreflight" in tasks_command
    assert "`/sdd.tasks`" in tasks_command
    assert "Treat `TASKS_BOOTSTRAP.execution_readiness` as the primary hard gate." in tasks_command
    assert "do not recompute full hard gates by re-deriving complete `plan.md` tables" in tasks_command
    assert "Run `{SCRIPT}` once from repo root." in tasks_command
    assert "Parse `FEATURE_DIR`, `AVAILABLE_DOCS`, `LOCAL_EXECUTION_PROTOCOL`, and `TASKS_BOOTSTRAP`" in tasks_command
    assert "`TASKS_BOOTSTRAP.execution_readiness.errors` contains blockers" in tasks_command
    assert "LOCAL_EXECUTION_PROTOCOL.repo_search.list_files_cmd" in tasks_command
    assert "LOCAL_EXECUTION_PROTOCOL.repo_search.available = false" in tasks_command
    assert "same run-local execution graph used to render `tasks.md` drives the manifest generation." in tasks_command
    assert "Top-level keys: `schema_version`, `generated_at`, `generated_from`, `tasks`, `presentation`" in tasks_command
    assert "`generated_from` minimal provenance: `plan_path` only" in tasks_command
    assert "`presentation.board_style` MUST be `enhanced`; `presentation.source_lineage` MUST include `plan_path`." in tasks_command

    if mapping_doc is not None:
        assert "prerequisite script may emit `TASKS_BOOTSTRAP` as a derived preflight packet" in mapping_doc
        assert "if `TASKS_BOOTSTRAP` is missing, invalid, or contradictory" not in mapping_doc
    assert "emits a compact runtime `TASKS_BOOTSTRAP` packet from `plan.md`" in readme
    assert "LOCAL_EXECUTION_PROTOCOL" in readme

    assert "LOCAL_EXECUTION_PROTOCOL" in bash_script
    assert "internal-task-bootstrap" in bash_script
    assert '"runtime_tools":' in bash_script
    assert "-TaskPreflight" in powershell_script
    assert "LOCAL_EXECUTION_PROTOCOL" in powershell_script
    assert "internal-task-bootstrap" in powershell_script
    assert "runtime_tools = $runtimeTools" in powershell_script
    assert "TASKS_BOOTSTRAP" in powershell_script
    assert "Get-RequiredBootstrapPayload" in powershell_script


def test_implement_command_prefers_implement_preflight_bootstrap():
    implement_command = (REPO_ROOT / "templates" / "commands" / "implement.md").read_text(encoding="utf-8")
    powershell_script = (REPO_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1").read_text(encoding="utf-8")
    bash_script = (REPO_ROOT / "scripts" / "bash" / "check-prerequisites.sh").read_text(encoding="utf-8")

    assert "scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks --implement-preflight" in implement_command
    assert "scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks -ImplementPreflight" in implement_command
    assert "Treat `IMPLEMENT_BOOTSTRAP.analyze_readiness` as the primary analyze hard gate." in implement_command
    assert "stop immediately and report the runtime bootstrap blocker" in implement_command
    assert "`IMPLEMENT_BOOTSTRAP.analyze_readiness.errors` contains blockers" in implement_command
    assert "parse `FEATURE_DIR`, `AVAILABLE_DOCS`, `LOCAL_EXECUTION_PROTOCOL`, `IMPLEMENT_BOOTSTRAP`, and `TASKS_MANIFEST_BOOTSTRAP`" in implement_command
    assert "LOCAL_EXECUTION_PROTOCOL.repo_search.list_files_cmd" in implement_command
    assert "no local CLI trial-and-error outside `LOCAL_EXECUTION_PROTOCOL`" in implement_command

    assert "--implement-preflight" in bash_script
    assert "LOCAL_EXECUTION_PROTOCOL" in bash_script
    assert "internal-implement-bootstrap" in bash_script
    assert "internal-tasks-manifest-bootstrap" in bash_script
    assert "IMPLEMENT_BOOTSTRAP" in bash_script
    assert "TASKS_MANIFEST_BOOTSTRAP" in bash_script
    assert "-ImplementPreflight" in powershell_script
    assert "LOCAL_EXECUTION_PROTOCOL" in powershell_script
    assert "internal-implement-bootstrap" in powershell_script
    assert "internal-tasks-manifest-bootstrap" in powershell_script
    assert "IMPLEMENT_BOOTSTRAP" in powershell_script
    assert "TASKS_MANIFEST_BOOTSTRAP" in powershell_script
    assert "Get-RequiredBootstrapPayload" in powershell_script


def test_data_model_command_prefers_data_model_preflight_bootstrap():
    data_model_command = (REPO_ROOT / "templates" / "commands" / "plan.data-model.md").read_text(encoding="utf-8")
    powershell_script = (REPO_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1").read_text(encoding="utf-8")
    bash_script = (REPO_ROOT / "scripts" / "bash" / "check-prerequisites.sh").read_text(encoding="utf-8")

    assert "scripts/bash/check-prerequisites.sh --json --data-model-preflight" in data_model_command
    assert "scripts/powershell/check-prerequisites.ps1 -Json -DataModelPreflight" in data_model_command
    assert "Treat `DATA_MODEL_BOOTSTRAP.generation_readiness` as the primary queue/readiness gate" in data_model_command
    assert "Consume `DATA_MODEL_BOOTSTRAP.selected_stage` as the authoritative queue context for this run." in data_model_command
    assert "runtime selection order is authoritative: first `pending` `data-model` row, then fallback `data-model` row, then synthetic row if absent." in data_model_command
    assert "Do not recompute stage-row hard gates locally; bootstrap `generation_readiness` + `recovery_handoff` are the authority." in data_model_command
    assert "resolved `plan.md` / `spec.md` / `test-matrix.md` / `data-model.md` paths" in data_model_command
    assert "`DATA_MODEL_BOOTSTRAP.state_machine_policy`" in data_model_command
    assert "required_model_kinds" in data_model_command
    assert "required_sections_by_model" in data_model_command
    assert "required_components_by_model" in data_model_command
    assert "If `N > 3` or `T >= 2N`, emit `Required Model = fsm` and include transition table, transition pseudocode, invariant catalog rows, and state diagram." in data_model_command
    assert "If `DATA_MODEL_BOOTSTRAP` is missing, malformed, contradictory, or unavailable" in data_model_command

    assert "--data-model-preflight" in bash_script
    assert "internal-data-model-bootstrap" in bash_script
    assert "DATA_MODEL_BOOTSTRAP" in bash_script
    assert "-DataModelPreflight" in powershell_script
    assert "internal-data-model-bootstrap" in powershell_script
    assert "DATA_MODEL_BOOTSTRAP" in powershell_script
    assert "Get-RequiredBootstrapPayload" in powershell_script

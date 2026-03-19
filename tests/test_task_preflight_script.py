import json
import os
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_minimal_feature(feature_dir: Path, contract_text: str | None = None, contract_status: str = "done") -> None:
    (feature_dir / "contracts").mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (feature_dir / "data-model.md").write_text("# Data Model\n", encoding="utf-8")
    (feature_dir / "test-matrix.md").write_text("# Test Matrix\n", encoding="utf-8")
    if contract_text is None:
        contract_text = """# Contract

## Full Field Dictionary (Operation-scoped)

| Field | Owner Class | Direction | Required/Optional | Default | Validation/Enum | Persisted | Contract-visible | Used in createTask | Source Anchor |
|-------|-------------|-----------|-------------------|---------|-----------------|-----------|------------------|--------------------|---------------|
| taskId | CreateTaskResponse | output | required | none | uuid | no | yes | yes | `src/app/contracts.py::CreateTaskResponse.taskId` |
"""
    (feature_dir / "contracts" / "create-task.md").write_text(contract_text, encoding="utf-8")

    (feature_dir / "plan.md").write_text(
        f"""# Planning Control Plane: Demo

## Shared Context Snapshot

- Feature: Demo

## Stage Queue

| Stage ID | Command | Required Inputs | Output Path | Status | Source Fingerprint | Output Fingerprint | Blocker |
|----------|---------|-----------------|-------------|--------|--------------------|--------------------|---------|
| research | `/sdd.plan.research` | `plan.md` | `research.md` | done | a | b | [none] |
| data-model | `/sdd.plan.data-model` | `plan.md` | `data-model.md` | done | a | b | [none] |
| test-matrix | `/sdd.plan.test-matrix` | `plan.md` | `test-matrix.md` | done | a | b | [none] |

## Binding Projection Index

| BindingRowID | UC ID | UIF ID | FR ID | IF ID / IF Scope | TM ID | TC IDs | Operation ID | Boundary Anchor |
|--------------|-------|--------|-------|------------------|-------|--------|--------------|-----------------|
| BindingRowID-001 | UC-001 | UIF-001 | FR-001 | IF-001 | TM-001 | TC-001, TC-002 | createTask | HTTP POST /tasks |

## Artifact Status

| BindingRowID | Unit Type | Target Path | Status | Source Fingerprint | Output Fingerprint | Blocker |
|--------------|-----------|-------------|--------|--------------------|--------------------|---------|
| BindingRowID-001 | contract | `contracts/create-task.md` | {contract_status} | a | b | [none] |
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
    data_model_status: str = "pending",
    include_spec: bool = True,
    include_research: bool = True,
    include_data_model: bool = False,
) -> None:
    feature_dir.mkdir(parents=True, exist_ok=True)
    if include_spec:
        (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    if include_research:
        (feature_dir / "research.md").write_text("# Research\n", encoding="utf-8")
    if include_data_model:
        (feature_dir / "data-model.md").write_text("# Data Model\n", encoding="utf-8")

    (feature_dir / "plan.md").write_text(
        f"""# Planning Control Plane: Demo

## Shared Context Snapshot

- Feature: Demo

## Stage Queue

| Stage ID | Command | Required Inputs | Output Path | Status | Source Fingerprint | Output Fingerprint | Blocker |
|----------|---------|-----------------|-------------|--------|--------------------|--------------------|---------|
| research | `/sdd.plan.research` | `plan.md`, `spec.md` | `research.md` | {research_status} | a | b | [none] |
| data-model | `/sdd.plan.data-model` | `plan.md`, `spec.md`, `research.md` | `data-model.md` | {data_model_status} | a | b | [none] |
| test-matrix | `/sdd.plan.test-matrix` | `plan.md`, `spec.md`, `research.md`, `data-model.md` | `test-matrix.md` | pending | a | b | [none] |
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

    assert payload["schema_version"] == "1.1"
    assert payload["required_sections"]["stage_queue"] is True
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
    assert unit["contract"]["target_path"] == "contracts/create-task.md"
    assert unit["contract"]["exists"] is True
    assert unit["contract"]["full_field_dictionary_present"] is True
    assert unit["contract"]["has_unresolved_field_gaps"] is False
    assert unit["contract"]["controller_first_violation"] is False
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
            "| BindingRowID-001 | contract | `contracts/create-task.md` | done | a | b | [none] |",
            "| BindingRowID-001 | contract |  | done | a | b | [none] |",
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
    plan_path.write_text(plan_text.replace("| test-matrix | `/sdd.plan.test-matrix` | `plan.md` | `test-matrix.md` | done | a | b | [none] |", "| test-matrix | `/sdd.plan.test-matrix` | `plan.md` | `test-matrix.md` | pending | a | b | [none] |"), encoding="utf-8")

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


def test_task_preflight_helper_flags_missing_full_field_dictionary(tmp_path):
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
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "full_field_dictionary_missing" in error_codes


def test_task_preflight_helper_flags_unresolved_contract_field_gaps(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(
        feature_dir,
        contract_text="""# Contract

## Full Field Dictionary (Operation-scoped)

| Field | Owner Class | Direction | Required/Optional | Default | Validation/Enum | Persisted | Contract-visible | Used in createTask | Source Anchor |
|-------|-------------|-----------|-------------------|---------|-----------------|-----------|------------------|--------------------|---------------|
| taskId | CreateTaskResponse | output | required | gap | gap | gap | yes | yes | TODO(REPO_ANCHOR) |
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
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "contract_field_gap_unresolved" in error_codes


def test_task_preflight_helper_flags_http_controller_first_violation(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(
        feature_dir,
        contract_text="""# Contract

## Full Field Dictionary (Operation-scoped)

| Field | Owner Class | Direction | Required/Optional | Default | Validation/Enum | Persisted | Contract-visible | Used in createTask | Source Anchor |
|-------|-------------|-----------|-------------------|---------|-----------------|-----------|------------------|--------------------|---------------|
| taskId | CreateTaskResponse | output | required | none | uuid | no | yes | yes | `src/app/contracts.py::CreateTaskResponse.taskId` |
**Implementation Entry Anchor (Required)**: src/app/task_service.py::TaskService.create_task
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
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "controller_first_violation" in error_codes


def test_task_preflight_helper_ignores_template_placeholder_binding_rows(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    (feature_dir / "plan.md").write_text(
        """# Planning Control Plane: Demo

## Shared Context Snapshot

- Feature: Demo

## Stage Queue

| Stage ID | Command | Required Inputs | Output Path | Status | Source Fingerprint | Output Fingerprint | Blocker |
|----------|---------|-----------------|-------------|--------|--------------------|--------------------|---------|
| research | `/sdd.plan.research` | `plan.md` | `research.md` | done | a | b | [none] |
| data-model | `/sdd.plan.data-model` | `plan.md` | `data-model.md` | done | a | b | [none] |
| test-matrix | `/sdd.plan.test-matrix` | `plan.md` | `test-matrix.md` | done | a | b | [none] |

## Binding Projection Index

| BindingRowID | UC ID | UIF ID | FR ID | IF ID / IF Scope | TM ID | TC IDs | Operation ID | Boundary Anchor |
|--------------|-------|--------|-------|------------------|-------|--------|--------------|-----------------|
| [BindingRowID-001] | [UC-001] | [UIF-001] | [FR-001] | [IF-001] | [TM-001] | [TC-001, TC-002] | [createTask] | [HTTP POST /tasks] |

## Artifact Status

| BindingRowID | Unit Type | Target Path | Status | Source Fingerprint | Output Fingerprint | Blocker |
|--------------|-----------|-------------|--------|--------------------|--------------------|---------|
| [BindingRowID-001] | [contract] | [contracts/create-task.md] | [pending] | [a] | [b] | [none] |
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
            "| BindingRowID-001 | contract | `contracts/create-task.md` | done | a | b | [none] |",
            "| BindingRowID-001 | contract | `contracts/create-task.md` | done | test-matrix:abc\\|binding:BindingRowID-001 | b | [none] |",
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
            "| research | `/sdd.plan.research` | `plan.md`, `spec.md` | `research.md` | done | a | b | [none] |",
            "| research | `/sdd.plan.research` | `plan.md`, `spec.md` | `research.md` | done | spec:abc\\|research:def | b | [none] |",
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

    feature_dir = repo_dir / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)

    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(["git", "checkout", "-b", "001-demo"], cwd=repo_dir, capture_output=True, check=True)

    env = os.environ.copy()
    env["SPECIFY_FEATURE"] = "001-demo"

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

    assert payload["FEATURE_DIR"].replace("\\", "/").endswith("/repo/specs/001-demo")
    assert "TASKS_BOOTSTRAP" in payload
    assert payload["TASKS_BOOTSTRAP"]["binding_row_count"] == 1
    assert len(payload["TASKS_BOOTSTRAP"]["ready_unit_inventory"]) == 1
    assert payload["TASKS_BOOTSTRAP"]["execution_readiness"]["ready_for_task_generation"] is True


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

    env = os.environ.copy()
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

    feature_dir = repo_dir / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    env = os.environ.copy()
    env["SPECIFY_FEATURE"] = "001-demo"

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
    assert payload["FEATURE_DIR"].replace("\\", "/").endswith("/repo/specs/001-demo")
    assert payload["TASKS_BOOTSTRAP"]["schema_version"] == "1.1"
    assert payload["TASKS_BOOTSTRAP"]["execution_readiness"]["ready_for_task_generation"] is True


def test_implement_preflight_helper_reports_pass_when_latest_analyze_pass_matches_fingerprints(tmp_path):
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


def test_implement_preflight_helper_flags_fingerprint_mismatch(tmp_path):
    feature_dir = tmp_path / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    _write_tasks_and_analyze_history(feature_dir, gate_decision="PASS", mismatched_hashes=True)

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
    assert "analyze_fingerprint_mismatch" in error_codes


def test_bash_check_prerequisites_can_embed_implement_bootstrap(tmp_path):
    repo_dir = tmp_path / "repo"
    scripts_bash = repo_dir / "scripts" / "bash"
    scripts_bash.mkdir(parents=True)

    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "common.sh", scripts_bash / "common.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "check-prerequisites.sh", scripts_bash / "check-prerequisites.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "implement_preflight.py", repo_dir / "scripts" / "implement_preflight.py")
    (scripts_bash / "check-prerequisites.sh").chmod(0o755)

    feature_dir = repo_dir / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    _write_tasks_and_analyze_history(feature_dir, gate_decision="PASS")

    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(["git", "checkout", "-b", "001-demo"], cwd=repo_dir, capture_output=True, check=True)

    env = os.environ.copy()
    env["SPECIFY_FEATURE"] = "001-demo"

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
    assert payload["FEATURE_DIR"].replace("\\", "/").endswith("/repo/specs/001-demo")
    assert "IMPLEMENT_BOOTSTRAP" in payload
    assert payload["IMPLEMENT_BOOTSTRAP"]["schema_version"] == "1.0"
    assert payload["IMPLEMENT_BOOTSTRAP"]["analyze_readiness"]["ready_for_implementation"] is True


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
    assert payload["schema_version"] == "1.0"
    assert payload["required_sections"]["shared_context_snapshot"] is True
    assert payload["required_sections"]["stage_queue"] is True
    assert payload["research_stage"]["status"] == "done"
    assert payload["selected_stage"]["stage_id"] == "data-model"
    assert payload["selected_stage"]["status"] == "pending"
    assert payload["generation_readiness"]["ready_for_generation"] is True
    assert payload["generation_readiness"]["error_count"] == 0
    assert payload["repo_anchor_policy"]["decision_order"] == ["existing", "extended", "new"]


def test_data_model_preflight_helper_flags_research_not_done(tmp_path):
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
    assert payload["generation_readiness"]["ready_for_generation"] is False
    error_codes = [entry["code"] for entry in payload["generation_readiness"]["errors"]]
    assert "research_stage_not_done" in error_codes


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
    assert payload["generation_readiness"]["ready_for_generation"] is False
    error_codes = [entry["code"] for entry in payload["generation_readiness"]["errors"]]
    assert "data_model_stage_pending_missing" in error_codes


def test_bash_check_prerequisites_can_embed_data_model_bootstrap(tmp_path):
    repo_dir = tmp_path / "repo"
    scripts_bash = repo_dir / "scripts" / "bash"
    scripts_bash.mkdir(parents=True)

    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "common.sh", scripts_bash / "common.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "check-prerequisites.sh", scripts_bash / "check-prerequisites.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "data_model_preflight.py", repo_dir / "scripts" / "data_model_preflight.py")
    (scripts_bash / "check-prerequisites.sh").chmod(0o755)

    feature_dir = repo_dir / "specs" / "001-demo"
    _write_data_model_feature(feature_dir)

    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(["git", "checkout", "-b", "001-demo"], cwd=repo_dir, capture_output=True, check=True)

    env = os.environ.copy()
    env["SPECIFY_FEATURE"] = "001-demo"

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
    assert payload["FEATURE_DIR"].replace("\\", "/").endswith("/repo/specs/001-demo")
    assert "DATA_MODEL_BOOTSTRAP" in payload
    assert payload["DATA_MODEL_BOOTSTRAP"]["schema_version"] == "1.0"
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
    assert "Generate `tasks.manifest.json` from the same run-local execution graph used to render `tasks.md`." in tasks_command
    assert "Top-level keys: `schema_version`, `generated_at`, `generated_from`, `tasks`" in tasks_command
    assert "`generated_from` keys: `plan_path`, `plan_source_fingerprint`, `contract_source_fingerprints`" in tasks_command

    if mapping_doc is not None:
        assert "prerequisite script may emit `TASKS_BOOTSTRAP` as a derived preflight packet" in mapping_doc
        assert "if `TASKS_BOOTSTRAP` is missing, invalid, or contradictory, fall back to the authoritative `plan.md` control plane" in mapping_doc
    assert "pre-extract a compact `TASKS_BOOTSTRAP` packet from `plan.md`" in readme
    assert "LOCAL_EXECUTION_PROTOCOL" in readme

    assert "LOCAL_EXECUTION_PROTOCOL" in bash_script
    assert "-TaskPreflight" in powershell_script
    assert "LOCAL_EXECUTION_PROTOCOL" in powershell_script
    assert "TASKS_BOOTSTRAP" in powershell_script
    assert '$payload.TASKS_BOOTSTRAP = $null' in powershell_script


def test_implement_command_prefers_implement_preflight_bootstrap():
    implement_command = (REPO_ROOT / "templates" / "commands" / "implement.md").read_text(encoding="utf-8")
    powershell_script = (REPO_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1").read_text(encoding="utf-8")
    bash_script = (REPO_ROOT / "scripts" / "bash" / "check-prerequisites.sh").read_text(encoding="utf-8")

    assert "scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks --implement-preflight" in implement_command
    assert "scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks -ImplementPreflight" in implement_command
    assert "Treat `IMPLEMENT_BOOTSTRAP.analyze_readiness` as the primary analyze hard gate." in implement_command
    assert "bounded fallback validation" in implement_command
    assert "`IMPLEMENT_BOOTSTRAP.analyze_readiness.errors` contains blockers" in implement_command
    assert "parse `feature_dir`, `available_docs`, `local_execution_protocol`, and `implement_bootstrap`" in implement_command.lower()
    assert "LOCAL_EXECUTION_PROTOCOL.repo_search.list_files_cmd" in implement_command
    assert "no local CLI trial-and-error outside `LOCAL_EXECUTION_PROTOCOL`" in implement_command

    assert "--implement-preflight" in bash_script
    assert "LOCAL_EXECUTION_PROTOCOL" in bash_script
    assert "IMPLEMENT_BOOTSTRAP" in bash_script
    assert "-ImplementPreflight" in powershell_script
    assert "LOCAL_EXECUTION_PROTOCOL" in powershell_script
    assert "IMPLEMENT_BOOTSTRAP" in powershell_script
    assert '$payload.IMPLEMENT_BOOTSTRAP = $null' in powershell_script


def test_data_model_command_prefers_data_model_preflight_bootstrap():
    data_model_command = (REPO_ROOT / "templates" / "commands" / "plan.data-model.md").read_text(encoding="utf-8")
    powershell_script = (REPO_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1").read_text(encoding="utf-8")
    bash_script = (REPO_ROOT / "scripts" / "bash" / "check-prerequisites.sh").read_text(encoding="utf-8")

    assert "scripts/bash/check-prerequisites.sh --json --data-model-preflight" in data_model_command
    assert "scripts/powershell/check-prerequisites.ps1 -Json -DataModelPreflight" in data_model_command
    assert "Treat `DATA_MODEL_BOOTSTRAP.generation_readiness` as the primary hard gate." in data_model_command
    assert "reuse the selected stage row and resolved `plan.md` / `spec.md` / `research.md` / `data-model.md` paths from `DATA_MODEL_BOOTSTRAP`" in data_model_command
    assert "`DATA_MODEL_BOOTSTRAP.generation_readiness.errors` contains blockers" in data_model_command

    assert "--data-model-preflight" in bash_script
    assert "DATA_MODEL_BOOTSTRAP" in bash_script
    assert "-DataModelPreflight" in powershell_script
    assert "DATA_MODEL_BOOTSTRAP" in powershell_script
    assert '$payload.DATA_MODEL_BOOTSTRAP = $null' in powershell_script

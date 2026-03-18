import json
import os
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

#### Sequence Variant B (Boundary == Entry)
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
    error_codes = [entry["code"] for entry in payload["execution_readiness"]["errors"]]
    assert "controller_first_violation" in error_codes


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


def test_bash_check_prerequisites_task_preflight_supports_explicit_plan_file(tmp_path):
    repo_dir = tmp_path / "repo"
    scripts_bash = repo_dir / "scripts" / "bash"
    scripts_bash.mkdir(parents=True)

    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "common.sh", scripts_bash / "common.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "bash" / "check-prerequisites.sh", scripts_bash / "check-prerequisites.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "task_preflight.py", repo_dir / "scripts" / "task_preflight.py")
    (scripts_bash / "check-prerequisites.sh").chmod(0o755)

    feature_dir = repo_dir / "specs" / "001-demo"
    _write_minimal_feature(feature_dir)
    plan_path = feature_dir / "plan.md"

    result = subprocess.run(
        ["bash", "scripts/bash/check-prerequisites.sh", "--json", "--task-preflight", "--plan-file", plan_path.relative_to(repo_dir).as_posix()],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["FEATURE_DIR"].replace("\\", "/").endswith("/repo/specs/001-demo")
    assert payload["TASKS_BOOTSTRAP"]["schema_version"] == "1.1"
    assert payload["TASKS_BOOTSTRAP"]["execution_readiness"]["ready_for_task_generation"] is True


def test_tasks_command_prefers_task_preflight_bootstrap():
    tasks_command = (REPO_ROOT / "templates" / "commands" / "tasks.md").read_text(encoding="utf-8")
    mapping_path = REPO_ROOT / "docs" / "command-template-mapping.md"
    mapping_doc = mapping_path.read_text(encoding="utf-8") if mapping_path.exists() else None
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    powershell_script = (REPO_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1").read_text(encoding="utf-8")

    assert "scripts/bash/check-prerequisites.sh --json --task-preflight" in tasks_command
    assert "scripts/powershell/check-prerequisites.ps1 -Json -TaskPreflight" in tasks_command
    assert "`/sdd.tasks <path/to/plan.md> [context...]`" in tasks_command
    assert "If `PLAN_FILE` is present, pass `--plan-file <PLAN_FILE>`; otherwise rely on script branch-derived default." in tasks_command
    assert "Parse `FEATURE_DIR`, `AVAILABLE_DOCS`, and `TASKS_BOOTSTRAP`" in tasks_command
    assert "Prefer `TASKS_BOOTSTRAP.unit_inventory` and `TASKS_BOOTSTRAP.ready_unit_inventory`" in tasks_command
    assert "Manifest top-level MUST include: `schema_version`, `generated_at`, `generated_from`, `tasks`." in tasks_command
    assert "`generated_from` MUST include at least: `plan_path`, `plan_source_fingerprint`, `contract_source_fingerprints`." in tasks_command

    if mapping_doc is not None:
        assert "prerequisite script may emit `TASKS_BOOTSTRAP` as a derived preflight packet" in mapping_doc
        assert "if `TASKS_BOOTSTRAP` is missing, invalid, or contradictory, fall back to the authoritative `plan.md` control plane" in mapping_doc
    assert "pre-extract a compact `TASKS_BOOTSTRAP` packet from `plan.md`" in readme

    assert "-TaskPreflight" in powershell_script
    assert "TASKS_BOOTSTRAP" in powershell_script
    assert '$payload.TASKS_BOOTSTRAP = $null' in powershell_script

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_minimal_feature(feature_dir: Path) -> None:
    (feature_dir / "contracts").mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (feature_dir / "data-model.md").write_text("# Data Model\n", encoding="utf-8")
    (feature_dir / "test-matrix.md").write_text("# Test Matrix\n", encoding="utf-8")
    (feature_dir / "contracts" / "create-task.md").write_text("# Contract\n", encoding="utf-8")

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
| BindingRowID-001 | UC-001 | UIF-001 | FR-001 | IF-001 | TM-001 | TC-001, TC-002 | createTask | POST /tasks |

## Artifact Status

| BindingRowID | Unit Type | Target Path | Status | Source Fingerprint | Output Fingerprint | Blocker |
|--------------|-----------|-------------|--------|--------------------|--------------------|---------|
| BindingRowID-001 | contract | `contracts/create-task.md` | done | a | b | [none] |
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

    assert payload["required_sections"]["stage_queue"] is True
    assert payload["incomplete_stage_ids"] == []
    assert payload["binding_row_count"] == 1
    assert payload["artifact_status_summary"]["contract"]["done"] == 1
    assert len(payload["unit_inventory"]) == 1
    assert len(payload["ready_unit_inventory"]) == 1
    unit = payload["ready_unit_inventory"][0]
    assert unit["binding_row_id"] == "BindingRowID-001"
    assert unit["operation_id"] == "createTask"
    assert unit["if_scope"] == "IF-001"
    assert unit["contract"]["target_path"] == "contracts/create-task.md"
    assert unit["contract"]["exists"] is True
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


def test_tasks_command_prefers_task_preflight_bootstrap():
    tasks_command = (REPO_ROOT / "templates" / "commands" / "tasks.md").read_text(encoding="utf-8")
    mapping_doc = (REPO_ROOT / "docs" / "command-template-mapping.md").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    powershell_script = (REPO_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1").read_text(encoding="utf-8")

    assert "scripts/bash/check-prerequisites.sh --json --task-preflight" in tasks_command
    assert "scripts/powershell/check-prerequisites.ps1 -Json -TaskPreflight" in tasks_command
    assert "parse `FEATURE_DIR`, `AVAILABLE_DOCS`, and `TASKS_BOOTSTRAP`" in tasks_command
    assert "Prefer `TASKS_BOOTSTRAP.unit_inventory` and `TASKS_BOOTSTRAP.ready_unit_inventory`" in tasks_command

    assert "prerequisite script may emit `TASKS_BOOTSTRAP` as a derived preflight packet" in mapping_doc
    assert "if `TASKS_BOOTSTRAP` is missing, invalid, or contradictory, fall back to the authoritative `plan.md` control plane" in mapping_doc
    assert "pre-extract a compact `TASKS_BOOTSTRAP` packet from `plan.md`" in readme

    assert "-TaskPreflight" in powershell_script
    assert "TASKS_BOOTSTRAP" in powershell_script
    assert '$payload.TASKS_BOOTSTRAP = $null' in powershell_script

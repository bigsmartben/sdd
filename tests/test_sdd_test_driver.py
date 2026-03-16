import importlib.util
import subprocess
import sys
from pathlib import Path


def _load_driver_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "sdd_test_driver.py"
    spec = importlib.util.spec_from_file_location("sdd_test_driver", module_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _build_minimal_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo_dir = tmp_path / "repo"
    scripts_bash = repo_dir / "scripts" / "bash"
    rules_dir = repo_dir / "rules"

    scripts_bash.mkdir(parents=True)
    rules_dir.mkdir(parents=True)

    for file_name in (
        "create-new-feature.sh",
        "setup-plan.sh",
        "check-prerequisites.sh",
        "run-planning-lint.sh",
    ):
        (scripts_bash / file_name).write_text("#!/usr/bin/env bash\n")

    (rules_dir / "planning-lint-rules.tsv").write_text("id\tenabled\n")
    return repo_dir, rules_dir / "planning-lint-rules.tsv"


def test_nonexistent_directory_returns_invalid_input(tmp_path):
    driver = _load_driver_module()
    missing_dir = tmp_path / "not-exists"

    exit_code = driver.main(["--directory", str(missing_dir)])

    assert exit_code == driver.EXIT_INVALID_INPUT


def test_subcommand_failure_returns_nonzero(tmp_path, monkeypatch):
    driver = _load_driver_module()
    repo_dir, _ = _build_minimal_repo(tmp_path)

    config = driver.PlatformConfig(
        shell_prefix=["bash"],
        create_feature_script=repo_dir / "scripts" / "bash" / "create-new-feature.sh",
        setup_plan_script=repo_dir / "scripts" / "bash" / "setup-plan.sh",
        check_prerequisites_script=repo_dir / "scripts" / "bash" / "check-prerequisites.sh",
        run_planning_lint_script=repo_dir / "scripts" / "bash" / "run-planning-lint.sh",
        is_powershell=False,
    )

    monkeypatch.setattr(driver, "resolve_platform_config", lambda _target: config)

    def fake_run_command(_command, _cwd):
        return subprocess.CompletedProcess(
            args=["bash"],
            returncode=1,
            stdout="create feature failed",
            stderr="mock failure",
        )

    monkeypatch.setattr(driver, "run_command", fake_run_command)

    exit_code = driver.main(["--directory", str(repo_dir)])

    assert exit_code == driver.EXIT_SUBCOMMAND_FAILED


def test_full_flow_success_returns_zero(tmp_path, monkeypatch):
    driver = _load_driver_module()
    repo_dir, rules_file = _build_minimal_repo(tmp_path)

    config = driver.PlatformConfig(
        shell_prefix=["bash"],
        create_feature_script=repo_dir / "scripts" / "bash" / "create-new-feature.sh",
        setup_plan_script=repo_dir / "scripts" / "bash" / "setup-plan.sh",
        check_prerequisites_script=repo_dir / "scripts" / "bash" / "check-prerequisites.sh",
        run_planning_lint_script=repo_dir / "scripts" / "bash" / "run-planning-lint.sh",
        is_powershell=False,
    )

    monkeypatch.setattr(driver, "resolve_platform_config", lambda _target: config)

    feature_dir = repo_dir / "specs" / "999-sdd-auto"
    spec_file = feature_dir / "spec.md"

    calls = []

    def fake_run_command(command, cwd):
        calls.append((list(command), cwd))
        index = len(calls)

        if index == 1:
            stdout = f'{{"SPEC_FILE":"{spec_file.as_posix()}"}}'
            return subprocess.CompletedProcess(args=list(command), returncode=0, stdout=stdout, stderr="")
        if index in (2, 3):
            return subprocess.CompletedProcess(args=list(command), returncode=0, stdout="{}", stderr="")
        if index == 4:
            stdout = '{"findings_total":0}'
            return subprocess.CompletedProcess(args=list(command), returncode=0, stdout=stdout, stderr="")

        raise AssertionError("Unexpected extra command call")

    monkeypatch.setattr(driver, "run_command", fake_run_command)

    exit_code = driver.main(["--directory", str(repo_dir)])

    assert exit_code == driver.EXIT_SUCCESS
    assert len(calls) == 4
    setup_command = calls[1][0]
    assert "--spec-file" in setup_command
    assert str(spec_file.resolve()) in setup_command
    check_command = calls[2][0]
    assert "--plan-file" in check_command
    assert str((feature_dir / "plan.md").resolve()) in check_command
    lint_command = calls[3][0]
    assert "--feature-dir" in lint_command
    assert str(feature_dir) in lint_command
    assert "--rules" in lint_command
    assert str(rules_file.resolve()) in lint_command

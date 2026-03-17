import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _require_bash() -> str:
    bash = shutil.which("bash")
    if not bash:
        pytest.skip("bash is required for shell script runtime tests")
    return bash


def _copy_shell_runtime(repo_dir: Path, script_names: list[str]) -> None:
    scripts_dir = repo_dir / "scripts" / "bash"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    for script_name in ["common.sh", *script_names]:
        source = REPO_ROOT / "scripts" / "bash" / script_name
        target = scripts_dir / script_name
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def _init_git_repo(repo_dir: Path, branch: str) -> None:
    subprocess.run(["git", "init", "-b", branch], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    (repo_dir / ".gitkeep").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", ".gitkeep"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, capture_output=True, text=True)


def test_setup_plan_preserves_existing_plan_on_rerun(tmp_path):
    bash = _require_bash()
    repo_dir = tmp_path / "repo"
    _copy_shell_runtime(repo_dir, ["setup-plan.sh"])
    _init_git_repo(repo_dir, "001-demo-feature")

    feature_dir = repo_dir / "specs" / "001-demo-feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Demo spec\n", encoding="utf-8")

    template_dir = repo_dir / ".specify" / "templates"
    template_dir.mkdir(parents=True)
    (template_dir / "plan-template.md").write_text("# Seed plan\n", encoding="utf-8")

    script = repo_dir / "scripts" / "bash" / "setup-plan.sh"

    first = subprocess.run(
        [bash, str(script), "--json"],
        cwd=repo_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert first.returncode == 0, first.stderr

    plan_path = feature_dir / "plan.md"
    assert plan_path.read_text(encoding="utf-8") == "# Seed plan\n"

    preserved_content = "# Existing generated plan\n"
    plan_path.write_text(preserved_content, encoding="utf-8")

    second = subprocess.run(
        [bash, str(script), "--json"],
        cwd=repo_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert second.returncode == 0, second.stderr
    assert "Using existing plan" in second.stdout
    assert plan_path.read_text(encoding="utf-8") == preserved_content


def test_check_prerequisites_paths_only_skips_feature_branch_validation(tmp_path):
    bash = _require_bash()
    repo_dir = tmp_path / "repo"
    _copy_shell_runtime(repo_dir, ["check-prerequisites.sh"])
    _init_git_repo(repo_dir, "main")

    script = repo_dir / "scripts" / "bash" / "check-prerequisites.sh"

    paths_only = subprocess.run(
        [bash, str(script), "--json", "--paths-only"],
        cwd=repo_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert paths_only.returncode == 0, paths_only.stderr

    payload = json.loads(paths_only.stdout)
    assert payload["BRANCH"] == "main"
    assert payload["FEATURE_DIR"].endswith("/specs/main")

    validated = subprocess.run(
        [bash, str(script), "--json"],
        cwd=repo_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert validated.returncode != 0
    assert "Not on a feature branch" in validated.stderr

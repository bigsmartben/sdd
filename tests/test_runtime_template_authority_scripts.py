import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def copy_bash_script(repo_dir: Path, name: str) -> Path:
    scripts_dir = repo_dir / "scripts" / "bash"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    src = REPO_ROOT / "scripts" / "bash" / name
    dst = scripts_dir / name
    shutil.copy2(src, dst)
    dst.chmod(0o755)
    return dst


def run_bash(script: Path, cwd: Path, args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def test_create_new_feature_bash_blocks_when_runtime_spec_template_missing(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify").mkdir(parents=True)
    script = copy_bash_script(repo_dir, "create-new-feature.sh")

    result = run_bash(
        script,
        repo_dir,
        ["--json", "--short-name", "demo", "Build demo feature"],
    )

    assert result.returncode != 0
    assert "Required runtime template not found or not readable" in result.stderr
    assert not any((repo_dir / "specs").glob("*/spec.md"))


def test_setup_plan_bash_blocks_when_runtime_plan_template_missing(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify").mkdir(parents=True)
    feature_dir = repo_dir / "specs" / "001-demo"
    feature_dir.mkdir(parents=True)
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "setup-plan.sh")

    env = os.environ.copy()
    env["SPECIFY_FEATURE"] = "001-demo"

    result = run_bash(script, repo_dir, ["--json"], env=env)

    assert result.returncode != 0
    assert "Required runtime template not found or not readable" in result.stderr
    assert not (feature_dir / "plan.md").exists()


def test_powershell_generation_scripts_remove_template_fallbacks():
    create_feature = read("scripts/powershell/create-new-feature.ps1")
    setup_plan = read("scripts/powershell/setup-plan.ps1")

    assert "Required runtime template not found or not readable at $template" in create_feature
    assert "New-Item -ItemType File -Path $specFile" not in create_feature
    assert "Copy-Item $template $specFile -Force" in create_feature

    assert "Required runtime template not found or not readable at $template" in setup_plan
    assert "Write-Warning \"Plan template not found at $template\"" not in setup_plan
    assert "New-Item -ItemType File -Path $paths.IMPL_PLAN" not in setup_plan
    assert "Copy-Item $template $paths.IMPL_PLAN -Force" in setup_plan


def test_update_agent_context_scripts_require_runtime_agent_template():
    bash = read("scripts/bash/update-agent-context.sh")
    pwsh = read("scripts/powershell/update-agent-context.ps1")

    assert "log_error \"Template file not found at $TEMPLATE_FILE\"" in bash
    assert "Run specify init to scaffold .specify/templates, or add agent-file-template.md there." in bash
    assert "Creating new agent files will fail" not in bash

    assert "Write-Err \"Template file not found at $TEMPLATE_FILE\"" in pwsh
    assert "Run specify init to scaffold .specify/templates, or add agent-file-template.md there." in pwsh

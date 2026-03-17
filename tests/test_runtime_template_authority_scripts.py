import json
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
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "setup-plan.sh")

    result = run_bash(script, repo_dir, ["--json", "--spec-file", "specs/001-demo/spec.md"])

    assert result.returncode != 0
    assert "Required runtime template not found or not readable" in result.stderr
    assert not (feature_dir / "plan.md").exists()


def test_setup_plan_bash_requires_explicit_spec_file_under_specs(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan\n", encoding="utf-8")
    feature_dir = repo_dir / "specs" / "001-demo"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "setup-plan.sh")

    missing_arg = run_bash(script, repo_dir, ["--json"])
    assert missing_arg.returncode != 0
    assert "--spec-file is required" in missing_arg.stderr

    wrong_name = run_bash(script, repo_dir, ["--json", "--spec-file", "specs/001-demo/not-spec.md"])
    assert wrong_name.returncode != 0
    assert "must point to a file named spec.md" in wrong_name.stderr

    outside_specs = repo_dir / "spec.md"
    outside_specs.write_text("# Outside\n", encoding="utf-8")
    outside = run_bash(script, repo_dir, ["--json", "--spec-file", str(outside_specs)])
    assert outside.returncode != 0
    assert "must be located under" in outside.stderr


def test_setup_plan_bash_uses_explicit_spec_file_and_copies_template(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan Template\n", encoding="utf-8")
    feature_dir = repo_dir / "specs" / "001-demo"
    feature_dir.mkdir(parents=True)
    spec_path = feature_dir / "spec.md"
    spec_path.write_text("# Spec\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "setup-plan.sh")

    result = run_bash(script, repo_dir, ["--json", "--spec-file", "specs/001-demo/spec.md"])

    assert result.returncode == 0
    assert (feature_dir / "plan.md").read_text(encoding="utf-8") == "# Plan Template\n"
    payload = json.loads(result.stdout)
    assert payload["FEATURE_SPEC"] == spec_path.as_posix()
    assert payload["IMPL_PLAN"] == (feature_dir / "plan.md").as_posix()
    assert "Copied plan template" not in result.stdout


def test_check_prerequisites_bash_uses_explicit_plan_file(tmp_path):
    repo_dir = tmp_path / "repo"
    feature_dir = repo_dir / "specs" / "001-demo"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (feature_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "check-prerequisites.sh")

    result = run_bash(script, repo_dir, ["--json", "--plan-file", "specs/001-demo/plan.md"])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["FEATURE_DIR"] == feature_dir.as_posix()
    assert payload["AVAILABLE_DOCS"] == []


def test_setup_plan_bash_handles_explicit_spec_file_with_quotes_in_path(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan Template\n", encoding="utf-8")
    feature_dir = repo_dir / "specs" / "001-demo'\"quoted"
    feature_dir.mkdir(parents=True)
    spec_path = feature_dir / "spec.md"
    spec_path.write_text("# Spec\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "setup-plan.sh")

    result = run_bash(script, repo_dir, ["--json", "--spec-file", spec_path.relative_to(repo_dir).as_posix()])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["FEATURE_SPEC"] == spec_path.as_posix()
    assert payload["IMPL_PLAN"] == (feature_dir / "plan.md").as_posix()


def test_check_prerequisites_bash_handles_explicit_plan_file_with_quotes_in_path(tmp_path):
    repo_dir = tmp_path / "repo"
    feature_dir = repo_dir / "specs" / "001-demo'\"quoted"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    plan_path = feature_dir / "plan.md"
    plan_path.write_text("# Plan\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "check-prerequisites.sh")

    result = run_bash(script, repo_dir, ["--json", "--plan-file", plan_path.relative_to(repo_dir).as_posix()])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["FEATURE_DIR"] == feature_dir.as_posix()
    assert payload["AVAILABLE_DOCS"] == []


def test_powershell_generation_scripts_remove_template_fallbacks():
    create_feature = read("scripts/powershell/create-new-feature.ps1")
    setup_plan = read("scripts/powershell/setup-plan.ps1")
    check_prerequisites = read("scripts/powershell/check-prerequisites.ps1")
    common = read("scripts/powershell/common.ps1")

    assert "Required runtime template not found or not readable at $template" in create_feature
    assert "New-Item -ItemType File -Path $specFile" not in create_feature
    assert "Copy-Item $template $specFile -Force" in create_feature

    assert "Required runtime template not found or not readable at $template" in setup_plan
    assert "[string]$SpecFile" in setup_plan
    assert "Get-FeaturePathsFromSpecFile" in setup_plan
    assert "Write-Warning \"Plan template not found at $template\"" not in setup_plan
    assert "New-Item -ItemType File -Path $paths.IMPL_PLAN" not in setup_plan
    assert "Copy-Item $template $paths.IMPL_PLAN -Force" in setup_plan

    assert "[string]$PlanFile" in check_prerequisites
    assert "Get-FeaturePathsFromPlanFile" in check_prerequisites

    assert '${ExpectedFileName}: $resolvedPath' in common
    assert '$ExpectedFileName: $resolvedPath' not in common


def test_update_agent_context_scripts_require_runtime_agent_template():
    bash = read("scripts/bash/update-agent-context.sh")
    pwsh = read("scripts/powershell/update-agent-context.ps1")

    assert "log_error \"Template file not found at $TEMPLATE_FILE\"" in bash
    assert "Run specify init to scaffold .specify/templates, or add agent-file-template.md there." in bash
    assert "Creating new agent files will fail" not in bash

    assert "Write-Err \"Template file not found at $TEMPLATE_FILE\"" in pwsh
    assert "Run specify init to scaffold .specify/templates, or add agent-file-template.md there." in pwsh

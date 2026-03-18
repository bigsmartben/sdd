import json
import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def normalize_path(value: str | Path) -> str:
    raw = value.as_posix() if isinstance(value, Path) else str(value).replace("\\", "/")
    if raw.lower().startswith("/mnt/") and len(raw) > 7 and raw[5].isalpha() and raw[6] == "/":
        raw = f"{raw[5].upper()}:{raw[6:]}"
    return raw.rstrip("/")


def copy_bash_script(repo_dir: Path, name: str) -> Path:
    scripts_dir = repo_dir / "scripts" / "bash"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    src = REPO_ROOT / "scripts" / "bash" / name
    dst = scripts_dir / name
    shutil.copy2(src, dst)
    dst.chmod(0o755)
    return dst


def run_bash(script: Path, cwd: Path, args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        script_path = script.relative_to(cwd).as_posix()
    except ValueError:
        script_path = script.as_posix()
    return subprocess.run(
        ["bash", script_path, *args],
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


def test_setup_plan_bash_supports_branch_derived_default_spec_file(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan\n", encoding="utf-8")
    feature_dir = repo_dir / "specs" / "001-demo"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "setup-plan.sh")

    missing_arg = run_bash(script, repo_dir, ["--json"])
    assert missing_arg.returncode == 0
    payload = json.loads(missing_arg.stdout)
    assert normalize_path(payload["FEATURE_SPEC"]) == normalize_path(feature_dir / "spec.md")
    assert normalize_path(payload["IMPL_PLAN"]) == normalize_path(feature_dir / "plan.md")

    wrong_name = run_bash(script, repo_dir, ["--json", "--spec-file", "specs/001-demo/not-spec.md"])
    assert wrong_name.returncode != 0
    assert "must point to a file named spec.md" in wrong_name.stderr

    outside_specs = repo_dir / "spec.md"
    outside_specs.write_text("# Outside\n", encoding="utf-8")
    outside = run_bash(script, repo_dir, ["--json", "--spec-file", outside_specs.relative_to(repo_dir).as_posix()])
    assert outside.returncode != 0
    assert "must be located under" in outside.stderr


def test_setup_plan_bash_branch_default_supports_feature_prefixed_branch(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan\n", encoding="utf-8")
    feature_dir = repo_dir / "specs" / "20250708-parent-hanxue-channel"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "setup-plan.sh")

    env = os.environ.copy()
    env["SPECIFY_FEATURE"] = "feature-20250708-parent-hanxue-channel"
    result = run_bash(script, repo_dir, ["--json"], env=env)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert normalize_path(payload["FEATURE_SPEC"]) == normalize_path(feature_dir / "spec.md")
    assert normalize_path(payload["IMPL_PLAN"]) == normalize_path(feature_dir / "plan.md")


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
    assert normalize_path(payload["FEATURE_SPEC"]) == normalize_path(spec_path)
    assert normalize_path(payload["IMPL_PLAN"]) == normalize_path(feature_dir / "plan.md")
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
    assert normalize_path(payload["FEATURE_DIR"]) == normalize_path(feature_dir)
    assert payload["AVAILABLE_DOCS"] == []


def test_setup_plan_bash_handles_explicit_spec_file_with_spaces_in_path(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan Template\n", encoding="utf-8")
    feature_dir = repo_dir / "specs" / "001-demo with spaces"
    feature_dir.mkdir(parents=True)
    spec_path = feature_dir / "spec.md"
    spec_path.write_text("# Spec\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "setup-plan.sh")

    result = run_bash(script, repo_dir, ["--json", "--spec-file", spec_path.relative_to(repo_dir).as_posix()])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert normalize_path(payload["FEATURE_SPEC"]) == normalize_path(spec_path)
    assert normalize_path(payload["IMPL_PLAN"]) == normalize_path(feature_dir / "plan.md")


def test_create_new_feature_bash_uses_current_branch_and_does_not_switch(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "spec-template.md").write_text("# Spec Template\n", encoding="utf-8")
    script = copy_bash_script(repo_dir, "create-new-feature.sh")

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True, capture_output=True, text=True)
    (repo_dir / "README.md").write_text("init\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "checkout", "-b", "123-demo-feature"], cwd=repo_dir, check=True, capture_output=True, text=True)

    before = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    result = run_bash(
        script,
        repo_dir,
        ["--json", "--short-name", "ignored", "Build demo feature"],
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["BRANCH_NAME"] == "123-demo-feature"

    spec_path = repo_dir / "specs" / "123-demo-feature" / "spec.md"
    assert spec_path.exists()
    assert spec_path.read_text(encoding="utf-8") == "# Spec Template\n"

    after = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert after == before


def test_create_new_feature_bash_normalizes_feature_prefixed_branch_to_spec_key(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "spec-template.md").write_text("# Spec Template\n", encoding="utf-8")
    script = copy_bash_script(repo_dir, "create-new-feature.sh")

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True, capture_output=True, text=True)
    (repo_dir / "README.md").write_text("init\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "checkout", "-b", "feature-20250708-parent-hanxue-channel"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )

    result = run_bash(
        script,
        repo_dir,
        ["--json", "--short-name", "ignored", "Build demo feature"],
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["BRANCH_NAME"] == "feature-20250708-parent-hanxue-channel"

    spec_path = repo_dir / "specs" / "20250708-parent-hanxue-channel" / "spec.md"
    assert spec_path.exists()
    assert spec_path.read_text(encoding="utf-8") == "# Spec Template\n"
    assert not (repo_dir / "specs" / "feature-20250708-parent-hanxue-channel").exists()


def test_check_prerequisites_bash_handles_explicit_plan_file_with_spaces_in_path(tmp_path):
    repo_dir = tmp_path / "repo"
    feature_dir = repo_dir / "specs" / "001-demo with spaces"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    plan_path = feature_dir / "plan.md"
    plan_path.write_text("# Plan\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "check-prerequisites.sh")

    result = run_bash(script, repo_dir, ["--json", "--plan-file", plan_path.relative_to(repo_dir).as_posix()])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert normalize_path(payload["FEATURE_DIR"]) == normalize_path(feature_dir)
    assert payload["AVAILABLE_DOCS"] == []


def test_powershell_generation_scripts_remove_template_fallbacks():
    create_feature = read("scripts/powershell/create-new-feature.ps1")
    setup_plan = read("scripts/powershell/setup-plan.ps1")
    check_prerequisites = read("scripts/powershell/check-prerequisites.ps1")
    common = read("scripts/powershell/common.ps1")

    assert "Required runtime template not found or not readable at $template" in create_feature
    assert "New-Item -ItemType File -Path $specFile" not in create_feature
    assert "Copy-Item $template $specFile -Force" in create_feature
    assert "git checkout -q -b $branchName" not in create_feature
    assert 'FEATURE_KEY="$BRANCH_NAME"' in read("scripts/bash/create-new-feature.sh")
    assert 'FEATURE_DIR="$SPECS_DIR/$FEATURE_KEY"' in read("scripts/bash/create-new-feature.sh")
    assert "$featureKey = $branchName" in create_feature
    assert "Join-Path $specsDir $featureKey" in create_feature

    assert "Required runtime template not found or not readable at $template" in setup_plan
    assert "[string]$SpecFile" in setup_plan
    assert "Get-FeaturePathsFromSpecFile" in setup_plan
    assert "Select-Object -Last 1" in setup_plan
    assert "Write-Warning \"Plan template not found at $template\"" not in setup_plan
    assert "New-Item -ItemType File -Path $paths.IMPL_PLAN" not in setup_plan
    assert "Copy-Item $template $paths.IMPL_PLAN -Force" in setup_plan

    assert "[string]$PlanFile" in check_prerequisites
    assert "Get-FeaturePathsFromPlanFile" in check_prerequisites

    assert '${ExpectedFileName}: $resolvedPath' in common
    assert '$ExpectedFileName: $resolvedPath' not in common
    assert '[Console]::Error.WriteLine("ERROR: Not on a feature branch. Current branch: $Branch")' in common
    assert 'Write-Output "ERROR: Not on a feature branch. Current branch: $Branch"' not in common


def test_update_agent_context_scripts_require_runtime_agent_template():
    bash = read("scripts/bash/update-agent-context.sh")
    pwsh = read("scripts/powershell/update-agent-context.ps1")
    create_bash = read("scripts/bash/create-new-feature.sh")

    assert "log_error \"Template file not found at $TEMPLATE_FILE\"" in bash
    assert "Run specify init to scaffold .specify/templates, or add agent-file-template.md there." in bash
    assert "Creating new agent files will fail" not in bash
    assert "git checkout -b \"$BRANCH_NAME\"" not in create_bash

    assert "Write-Err \"Template file not found at $TEMPLATE_FILE\"" in pwsh
    assert "Run specify init to scaffold .specify/templates, or add agent-file-template.md there." in pwsh

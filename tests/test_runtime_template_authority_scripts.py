import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pytest


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


def copy_powershell_script(repo_dir: Path, name: str) -> Path:
    scripts_dir = repo_dir / "scripts" / "powershell"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    src = REPO_ROOT / "scripts" / "powershell" / name
    dst = scripts_dir / name
    shutil.copy2(src, dst)
    return dst


def run_powershell(script: Path, cwd: Path, args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    ps_exe = shutil.which("pwsh") or shutil.which("powershell")
    if ps_exe is None:
        pytest.skip("PowerShell is not available in this environment")

    try:
        script_path = script.relative_to(cwd).as_posix()
    except ValueError:
        script_path = script.as_posix()

    return subprocess.run(
        [ps_exe, "-NoProfile", "-File", script_path, *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def parse_last_json_line(stdout: str) -> dict:
    line = next((ln for ln in reversed(stdout.splitlines()) if ln.strip()), "")
    return json.loads(line)


def assert_local_execution_protocol(payload: dict) -> None:
    protocol = payload["LOCAL_EXECUTION_PROTOCOL"]
    assert protocol["schema_version"] == "1.0"
    assert protocol["rules"]
    assert set(protocol["repo_search"]) >= {"available", "tool", "list_files_cmd", "search_text_cmd"}
    assert set(protocol["repo_inspection"]) >= {"available", "status_cmd", "diff_cmd", "history_cmd"}
    assert set(protocol["python"]) >= {"available", "tool", "runner_cmd"}
    assert "runtime_tools" in protocol
    if protocol["repo_search"]["available"]:
        assert protocol["repo_search"]["tool"] in {"rg", "git"}
        assert protocol["repo_search"]["list_files_cmd"]
        assert protocol["repo_search"]["search_text_cmd"]
    if protocol["repo_inspection"]["available"]:
        assert protocol["repo_inspection"]["status_cmd"].startswith("git ")
        assert protocol["repo_inspection"]["diff_cmd"].startswith("git ")
        assert protocol["repo_inspection"]["history_cmd"].startswith("git ")
    if protocol["python"]["available"]:
        assert protocol["python"]["tool"] == "specify-cli"
        assert protocol["python"]["runner_cmd"]
        assert protocol["python"]["runner_cmd"] == "specify <internal-helper-command>"
        assert protocol["runtime_tools"]["schema_version"] == "1.0"
        assert [tool["tool"] for tool in protocol["runtime_tools"]["core_runtime_tools"]] == [
            "specify-cli",
            "git",
            "rg",
        ]
        assert "node" in protocol["runtime_tools"]["excluded_runtime_families"]


def write_runtime_plan_baselines(repo_dir: Path) -> None:
    memory_dir = repo_dir / ".specify" / "memory" / "repository-first"
    memory_dir.mkdir(parents=True, exist_ok=True)
    (repo_dir / ".specify" / "memory" / "constitution.md").write_text("# Constitution\n", encoding="utf-8")
    (memory_dir / "technical-dependency-matrix.md").write_text("# Dependency Matrix\n", encoding="utf-8")
    (memory_dir / "module-invocation-spec.md").write_text("# Module Invocation\n", encoding="utf-8")


def today_key() -> str:
    return datetime.now().strftime("%Y%m%d")


def test_create_new_feature_powershell_accepts_positional_feature_description(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "spec-template.md").write_text("# Spec Template\n", encoding="utf-8")
    copy_powershell_script(repo_dir, "common.ps1")
    script = copy_powershell_script(repo_dir, "create-new-feature.ps1")

    result = run_powershell(
        script,
        repo_dir,
        ["-Json", "-ShortName", "demo", "Build demo feature"],
    )

    assert result.returncode == 0
    payload = parse_last_json_line(result.stdout)
    assert payload["BRANCH_NAME"].endswith("-demo")
    spec_path = Path(payload["SPEC_FILE"])
    assert spec_path.exists()
    assert spec_path.read_text(encoding="utf-8") == "# Spec Template\n"


def test_create_new_feature_powershell_rejects_number_flag(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "spec-template.md").write_text("# Spec Template\n", encoding="utf-8")
    copy_powershell_script(repo_dir, "common.ps1")
    script = copy_powershell_script(repo_dir, "create-new-feature.ps1")

    result = run_powershell(
        script,
        repo_dir,
        ["-Json", "-ShortName", "demo", "-Number", "123", "Build demo feature"],
    )

    assert result.returncode != 0
    assert "-Number/--number is not supported" in result.stderr


def test_create_new_feature_powershell_uses_current_date_instead_of_incrementing_spec_dir_dates(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "spec-template.md").write_text("# Spec Template\n", encoding="utf-8")
    (repo_dir / "specs" / "20260328-existing-feature").mkdir(parents=True)
    copy_powershell_script(repo_dir, "common.ps1")
    script = copy_powershell_script(repo_dir, "create-new-feature.ps1")

    result = run_powershell(
        script,
        repo_dir,
        ["-Json", "-ShortName", "parent-hanxu", "Build parent hanxu flow"],
    )

    assert result.returncode == 0
    payload = parse_last_json_line(result.stdout)
    expected_key = f"{today_key()}-parent-hanxu"
    assert payload["BRANCH_NAME"] == f"feature-{expected_key}"
    assert normalize_path(payload["SPEC_FILE"]) == normalize_path(repo_dir / "specs" / expected_key / "spec.md")


def test_setup_plan_powershell_json_output_is_pure_json(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan Template\n", encoding="utf-8")
    write_runtime_plan_baselines(repo_dir)
    feature_dir = repo_dir / "specs" / "001-demo"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    copy_powershell_script(repo_dir, "common.ps1")
    script = copy_powershell_script(repo_dir, "setup-plan.ps1")

    result = run_powershell(script, repo_dir, ["-Json"])

    assert result.returncode == 0
    assert "Copied plan template" not in result.stdout
    payload = parse_last_json_line(result.stdout)
    assert normalize_path(payload["FEATURE_SPEC"]) == normalize_path(feature_dir / "spec.md")
    assert normalize_path(payload["IMPL_PLAN"]) == normalize_path(feature_dir / "plan.md")
    assert (feature_dir / "plan.md").read_text(encoding="utf-8") == "# Plan Template\n"


def test_setup_plan_powershell_rejects_positional_spec_file(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan Template\n", encoding="utf-8")
    feature_dir = repo_dir / "specs" / "001-demo"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    copy_powershell_script(repo_dir, "common.ps1")
    script = copy_powershell_script(repo_dir, "setup-plan.ps1")

    result = run_powershell(script, repo_dir, ["-Json", "specs/001-demo/spec.md"])

    assert result.returncode != 0
    combined_output = f"{result.stdout}\n{result.stderr}"
    assert "A positional parameter cannot be found" in combined_output


def test_setup_plan_powershell_blocks_when_repository_first_baselines_missing(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan Template\n", encoding="utf-8")
    feature_dir = repo_dir / "specs" / "001-demo"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    copy_powershell_script(repo_dir, "common.ps1")
    script = copy_powershell_script(repo_dir, "setup-plan.ps1")

    result = run_powershell(script, repo_dir, ["-Json"])

    assert result.returncode != 0
    combined_output = f"{result.stdout}\n{result.stderr}"
    assert "Run /sdd.constitution first." in combined_output
    assert not (feature_dir / "plan.md").exists()


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

    result = run_bash(script, repo_dir, ["--json"])

    assert result.returncode != 0
    assert "Required runtime template not found or not readable" in result.stderr
    assert not (feature_dir / "plan.md").exists()


def test_setup_plan_bash_blocks_when_repository_first_baselines_missing(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan\n", encoding="utf-8")
    feature_dir = repo_dir / "specs" / "001-demo"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "setup-plan.sh")

    result = run_bash(script, repo_dir, ["--json"])

    assert result.returncode != 0
    assert "Run /sdd.constitution first." in result.stderr
    assert not (feature_dir / "plan.md").exists()


def test_setup_plan_bash_supports_branch_derived_default_spec_file(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan\n", encoding="utf-8")
    write_runtime_plan_baselines(repo_dir)
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

    legacy_flag = run_bash(script, repo_dir, ["--json", "--spec-file", "specs/001-demo/spec.md"])
    assert legacy_flag.returncode != 0
    assert "Unknown option '--spec-file'" in legacy_flag.stderr


def test_setup_plan_bash_branch_default_supports_feature_prefixed_branch(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan\n", encoding="utf-8")
    write_runtime_plan_baselines(repo_dir)
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


def test_setup_plan_bash_copies_template_with_branch_inference(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan Template\n", encoding="utf-8")
    write_runtime_plan_baselines(repo_dir)
    feature_dir = repo_dir / "specs" / "001-demo"
    feature_dir.mkdir(parents=True)
    spec_path = feature_dir / "spec.md"
    spec_path.write_text("# Spec\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "setup-plan.sh")

    result = run_bash(script, repo_dir, ["--json"])

    assert result.returncode == 0
    assert (feature_dir / "plan.md").read_text(encoding="utf-8") == "# Plan Template\n"
    payload = json.loads(result.stdout)
    assert normalize_path(payload["FEATURE_SPEC"]) == normalize_path(spec_path)
    assert normalize_path(payload["IMPL_PLAN"]) == normalize_path(feature_dir / "plan.md")
    assert "Copied plan template" not in result.stdout


def test_check_prerequisites_bash_uses_branch_inferred_plan_file(tmp_path):
    repo_dir = tmp_path / "repo"
    feature_dir = repo_dir / "specs" / "001-demo"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (feature_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "check-prerequisites.sh")

    result = run_bash(script, repo_dir, ["--json"])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert normalize_path(payload["FEATURE_DIR"]) == normalize_path(feature_dir)
    assert payload["AVAILABLE_DOCS"] == []
    assert_local_execution_protocol(payload)

    legacy_flag = run_bash(script, repo_dir, ["--json", "--plan-file", "specs/001-demo/plan.md"])
    assert legacy_flag.returncode != 0
    assert "Unknown option '--plan-file'" in legacy_flag.stderr


def test_check_prerequisites_powershell_rejects_positional_plan_file(tmp_path):
    repo_dir = tmp_path / "repo"
    feature_dir = repo_dir / "specs" / "001-demo"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (feature_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
    copy_powershell_script(repo_dir, "common.ps1")
    script = copy_powershell_script(repo_dir, "check-prerequisites.ps1")

    result = run_powershell(script, repo_dir, ["-Json", "specs/001-demo/plan.md"])

    assert result.returncode != 0
    combined_output = f"{result.stdout}\n{result.stderr}"
    assert "A positional parameter cannot be found" in combined_output


def test_check_prerequisites_powershell_emits_local_execution_protocol(tmp_path):
    repo_dir = tmp_path / "repo"
    feature_dir = repo_dir / "specs" / "001-demo"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (feature_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
    copy_powershell_script(repo_dir, "common.ps1")
    script = copy_powershell_script(repo_dir, "check-prerequisites.ps1")

    result = run_powershell(script, repo_dir, ["-Json"])

    assert result.returncode == 0
    payload = parse_last_json_line(result.stdout)
    assert normalize_path(payload["FEATURE_DIR"]) == normalize_path(feature_dir)
    assert payload["AVAILABLE_DOCS"] == []
    assert_local_execution_protocol(payload)


def test_setup_plan_bash_handles_branch_inferred_spec_file_with_spaces_in_path(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "plan-template.md").write_text("# Plan Template\n", encoding="utf-8")
    write_runtime_plan_baselines(repo_dir)
    feature_dir = repo_dir / "specs" / "001-demo with spaces"
    feature_dir.mkdir(parents=True)
    spec_path = feature_dir / "spec.md"
    spec_path.write_text("# Spec\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "setup-plan.sh")

    env = os.environ.copy()
    env["SPECIFY_FEATURE"] = "001-demo with spaces"
    result = run_bash(script, repo_dir, ["--json"], env=env)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert normalize_path(payload["FEATURE_SPEC"]) == normalize_path(spec_path)
    assert normalize_path(payload["IMPL_PLAN"]) == normalize_path(feature_dir / "plan.md")


def test_create_new_feature_bash_keeps_current_feature_branch(tmp_path):
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
    current_branch_name = "feature-20250708-demo-feature"
    subprocess.run(["git", "checkout", "-b", current_branch_name], cwd=repo_dir, check=True, capture_output=True, text=True)

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
    assert payload["BRANCH_NAME"] == current_branch_name

    spec_path = repo_dir / "specs" / "20250708-demo-feature" / "spec.md"
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


def test_create_new_feature_bash_switches_to_generated_branch_by_default(tmp_path):
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

    result = run_bash(
        script,
        repo_dir,
        ["--json", "--short-name", "demo-feature", "Build demo feature"],
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    expected_branch = payload["BRANCH_NAME"]
    active_branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert active_branch == expected_branch


def test_create_new_feature_bash_does_not_write_spec_when_branch_switch_fails(tmp_path):
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
    default_branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    conflict_branch_name = f"feature-{today_key()}-demo-feature"
    conflict_feature_key = f"{today_key()}-demo-feature"
    subprocess.run(["git", "checkout", "-b", conflict_branch_name], cwd=repo_dir, check=True, capture_output=True, text=True)
    target_spec = repo_dir / "specs" / conflict_feature_key / "spec.md"
    target_spec.parent.mkdir(parents=True, exist_ok=True)
    target_spec.write_text("# Existing branch spec\n", encoding="utf-8")
    subprocess.run(["git", "add", str(target_spec)], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "add branch spec"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "checkout", default_branch], cwd=repo_dir, check=True, capture_output=True, text=True)

    target_spec.parent.mkdir(parents=True, exist_ok=True)
    target_spec.write_text("# local conflict file\n", encoding="utf-8")

    result = run_bash(
        script,
        repo_dir,
        ["--json", "--short-name", "demo-feature", "Build demo feature"],
    )

    assert result.returncode != 0
    assert f"Failed to switch to git branch '{conflict_branch_name}'" in result.stderr
    assert target_spec.read_text(encoding="utf-8") == "# local conflict file\n"


def test_create_new_feature_bash_tracks_remote_only_branch(tmp_path):
    remote_dir = tmp_path / "remote.git"
    seed_dir = tmp_path / "seed"
    repo_dir = tmp_path / "repo"

    subprocess.run(["git", "init", "--bare", str(remote_dir)], check=True, capture_output=True, text=True)
    seed_dir.mkdir()
    subprocess.run(["git", "init"], cwd=seed_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=seed_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=seed_dir, check=True, capture_output=True, text=True)
    (seed_dir / "README.md").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=seed_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=seed_dir, check=True, capture_output=True, text=True)
    default_branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=seed_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    subprocess.run(["git", "remote", "add", "origin", str(remote_dir)], cwd=seed_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "push", "-u", "origin", default_branch], cwd=seed_dir, check=True, capture_output=True, text=True)
    remote_branch_name = f"feature-{today_key()}-demo-feature"
    remote_feature_key = f"{today_key()}-demo-feature"
    subprocess.run(["git", "checkout", "-b", remote_branch_name], cwd=seed_dir, check=True, capture_output=True, text=True)
    branch_spec = seed_dir / "specs" / remote_feature_key / "spec.md"
    branch_spec.parent.mkdir(parents=True, exist_ok=True)
    branch_spec.write_text("# Remote branch spec\n", encoding="utf-8")
    subprocess.run(["git", "add", str(branch_spec)], cwd=seed_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "branch spec"], cwd=seed_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "push", "-u", "origin", remote_branch_name], cwd=seed_dir, check=True, capture_output=True, text=True)

    subprocess.run(["git", "clone", str(remote_dir), str(repo_dir)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True, capture_output=True, text=True)
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "spec-template.md").write_text("# Spec Template\n", encoding="utf-8")
    script = copy_bash_script(repo_dir, "create-new-feature.sh")

    branch_exists_local = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{remote_branch_name}"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    assert branch_exists_local.returncode != 0

    result = run_bash(
        script,
        repo_dir,
        ["--json", "--short-name", "demo-feature", "Build demo feature"],
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["BRANCH_NAME"] == remote_branch_name
    active_branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert active_branch == remote_branch_name
    upstream = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert upstream == f"origin/{remote_branch_name}"


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


def test_create_new_feature_bash_uses_current_date_instead_of_incrementing_spec_dir_dates(tmp_path):
    repo_dir = tmp_path / "repo"
    (repo_dir / ".specify" / "templates").mkdir(parents=True)
    (repo_dir / ".specify" / "templates" / "spec-template.md").write_text("# Spec Template\n", encoding="utf-8")
    (repo_dir / "specs" / "20260328-existing-feature").mkdir(parents=True)
    script = copy_bash_script(repo_dir, "create-new-feature.sh")

    result = run_bash(
        script,
        repo_dir,
        ["--json", "--short-name", "parent-hanxu", "Build parent hanxu flow"],
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    expected_key = f"{today_key()}-parent-hanxu"
    assert payload["BRANCH_NAME"] == f"feature-{expected_key}"
    assert normalize_path(payload["SPEC_FILE"]) == normalize_path(repo_dir / "specs" / expected_key / "spec.md")


def test_check_prerequisites_bash_handles_branch_inferred_plan_file_with_spaces_in_path(tmp_path):
    repo_dir = tmp_path / "repo"
    feature_dir = repo_dir / "specs" / "001-demo with spaces"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    plan_path = feature_dir / "plan.md"
    plan_path.write_text("# Plan\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "check-prerequisites.sh")

    env = os.environ.copy()
    env["SPECIFY_FEATURE"] = "001-demo with spaces"
    result = run_bash(script, repo_dir, ["--json"], env=env)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert normalize_path(payload["FEATURE_DIR"]) == normalize_path(feature_dir)
    assert payload["AVAILABLE_DOCS"] == []


def test_check_prerequisites_bash_resolves_legacy_three_digit_branch_by_numeric_prefix(tmp_path):
    repo_dir = tmp_path / "repo"
    feature_dir = repo_dir / "specs" / "001-existing-slug"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (feature_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "check-prerequisites.sh")

    env = os.environ.copy()
    env["SPECIFY_FEATURE"] = "001-other-slug"
    result = run_bash(script, repo_dir, ["--json"], env=env)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert normalize_path(payload["FEATURE_DIR"]) == normalize_path(feature_dir)


def test_check_prerequisites_powershell_resolves_legacy_three_digit_branch_by_numeric_prefix(tmp_path):
    repo_dir = tmp_path / "repo"
    feature_dir = repo_dir / "specs" / "001-existing-slug"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (feature_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
    copy_powershell_script(repo_dir, "common.ps1")
    script = copy_powershell_script(repo_dir, "check-prerequisites.ps1")

    env = os.environ.copy()
    env["SPECIFY_FEATURE"] = "001-other-slug"
    result = run_powershell(script, repo_dir, ["-Json"], env=env)

    assert result.returncode == 0
    payload = parse_last_json_line(result.stdout)
    assert normalize_path(payload["FEATURE_DIR"]) == normalize_path(feature_dir)


def test_check_prerequisites_bash_rejects_legacy_numeric_branch_prefix(tmp_path):
    repo_dir = tmp_path / "repo"
    feature_dir = repo_dir / "specs" / "12-demo"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (feature_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
    copy_bash_script(repo_dir, "common.sh")
    script = copy_bash_script(repo_dir, "check-prerequisites.sh")

    env = os.environ.copy()
    env["SPECIFY_FEATURE"] = "12-demo"
    result = run_bash(script, repo_dir, ["--json"], env=env)

    assert result.returncode != 0
    assert "Not on a feature branch" in result.stderr


def test_check_prerequisites_powershell_rejects_legacy_numeric_branch_prefix(tmp_path):
    repo_dir = tmp_path / "repo"
    feature_dir = repo_dir / "specs" / "12-demo"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (feature_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
    copy_powershell_script(repo_dir, "common.ps1")
    script = copy_powershell_script(repo_dir, "check-prerequisites.ps1")

    env = os.environ.copy()
    env["SPECIFY_FEATURE"] = "12-demo"
    result = run_powershell(script, repo_dir, ["-Json"], env=env)

    assert result.returncode != 0
    assert "Not on a feature branch" in result.stderr


def test_powershell_generation_scripts_remove_template_fallbacks():
    create_feature = read("scripts/powershell/create-new-feature.ps1")
    setup_plan = read("scripts/powershell/setup-plan.ps1")
    check_prerequisites = read("scripts/powershell/check-prerequisites.ps1")
    common = read("scripts/powershell/common.ps1")

    assert "Required runtime template not found or not readable at $template" in create_feature
    assert "[CmdletBinding(PositionalBinding = $false)]" in create_feature
    assert "New-Item -ItemType File -Path $specFile" not in create_feature
    assert "Copy-Item $template $specFile -Force" in create_feature
    assert "git checkout -b $branchName" in create_feature
    assert "git checkout --track $remoteRef" in create_feature
    assert create_feature.index("if ($hasGit)") < create_feature.index("Copy-Item $template $specFile -Force")
    create_bash = read("scripts/bash/create-new-feature.sh")
    assert create_bash.index("if [ \"$HAS_GIT\" = true ]; then") < create_bash.index("cp \"$TEMPLATE\" \"$SPEC_FILE\"")
    assert 'FEATURE_KEY="$BRANCH_NAME"' in read("scripts/bash/create-new-feature.sh")
    assert 'FEATURE_DIR="$SPECS_DIR/$FEATURE_KEY"' in read("scripts/bash/create-new-feature.sh")
    assert "$featureKey = $branchName" in create_feature
    assert "Join-Path $specsDir $featureKey" in create_feature

    assert "Required runtime template not found or not readable at $template" in setup_plan
    assert "[CmdletBinding(PositionalBinding = $false)]" in setup_plan
    assert "[string]$SpecFile" not in setup_plan
    assert "Get-FeaturePathsFromSpecFile" not in setup_plan
    assert "Select-Object -Last 1" in setup_plan
    assert "Write-Warning \"Plan template not found at $template\"" not in setup_plan
    assert "New-Item -ItemType File -Path $paths.IMPL_PLAN" not in setup_plan
    assert "Copy-Item $template $paths.IMPL_PLAN -Force" in setup_plan
    assert "Run /sdd.constitution first." in setup_plan
    assert "if (-not $Json)" in setup_plan

    assert "[string]$PlanFile" not in check_prerequisites
    assert "[CmdletBinding(PositionalBinding = $false)]" in check_prerequisites
    assert "Get-FeaturePathsFromPlanFile" not in check_prerequisites

    assert "Resolve-FeatureFilePath" not in common
    assert "Get-FeaturePathsFromSpecFile" not in common
    assert "Get-FeaturePathsFromPlanFile" not in common
    assert '[Console]::Error.WriteLine("ERROR: Not on a feature branch. Current branch: $Branch")' in common
    assert 'Write-Output "ERROR: Not on a feature branch. Current branch: $Branch"' not in common


def test_update_agent_context_scripts_require_runtime_agent_template():
    bash = read("scripts/bash/update-agent-context.sh")
    pwsh = read("scripts/powershell/update-agent-context.ps1")
    create_bash = read("scripts/bash/create-new-feature.sh")

    assert "log_error \"Template file not found at $TEMPLATE_FILE\"" in bash
    assert "Run specify init to scaffold .specify/templates, or add agent-file-template.md there." in bash
    assert "Creating new agent files will fail" not in bash
    assert "git checkout -b \"$BRANCH_NAME\"" in create_bash

    assert "Write-Err \"Template file not found at $TEMPLATE_FILE\"" in pwsh
    assert "Run specify init to scaffold .specify/templates, or add agent-file-template.md there." in pwsh


def test_agent_template_includes_stable_local_execution_guidance():
    template = read("templates/agent-file-template.md")

    assert "## Stable Local Execution" in template
    assert "LOCAL_EXECUTION_PROTOCOL" in template
    assert "specify internal-task-bootstrap" in template
    assert "constitution-defined local execution policy" in template

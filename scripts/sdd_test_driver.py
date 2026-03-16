#!/usr/bin/env python3
"""Cross-platform SDD automation test driver.

This script runs a minimal, stable SDD flow in a target repository directory and
returns an explicit process exit code.

Usage:
    python scripts/sdd_test_driver.py --directory <target-repo-dir>

Workflow (fail-fast):
1. create-new-feature
2. setup-plan
3. check-prerequisites
4. run-planning-lint (requires findings_total == 0)

Exit codes:
- 0: Success
- 2: Invalid input (e.g., target directory missing)
- 3: Environment/setup error (e.g., missing scripts, missing shell)
- 10: Subcommand execution failed
- 11: Invalid/missing expected JSON output
- 12: Planning lint reported findings
"""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

EXIT_SUCCESS = 0
EXIT_INVALID_INPUT = 2
EXIT_SETUP_ERROR = 3
EXIT_SUBCOMMAND_FAILED = 10
EXIT_INVALID_OUTPUT = 11
EXIT_LINT_FAILED = 12


@dataclass(frozen=True)
class PlatformConfig:
    shell_prefix: list[str]
    create_feature_script: Path
    setup_plan_script: Path
    check_prerequisites_script: Path
    run_planning_lint_script: Path
    is_powershell: bool


def log(message: str) -> None:
    print(f"[SDD-DRIVER] {message}")


def log_error(message: str) -> None:
    print(f"[SDD-DRIVER][ERROR] {message}", file=sys.stderr)


class FlowExecutionError(RuntimeError):
    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run minimal SDD automation flow in a target directory")
    parser.add_argument(
        "--directory",
        required=True,
        help="Target repository directory where SDD flow will run",
    )
    parser.add_argument(
        "--feature-description",
        default="Automated SDD flow validation",
        help="Feature description passed to create-new-feature",
    )
    return parser.parse_args(argv)


def resolve_platform_config(target_dir: Path) -> PlatformConfig:
    scripts_dir = target_dir / "scripts"

    if sys.platform.startswith("win"):
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if not powershell:
            raise FlowExecutionError("PowerShell not found (pwsh/powershell)", EXIT_SETUP_ERROR)

        shell_prefix = [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]
        return PlatformConfig(
            shell_prefix=shell_prefix,
            create_feature_script=scripts_dir / "powershell" / "create-new-feature.ps1",
            setup_plan_script=scripts_dir / "powershell" / "setup-plan.ps1",
            check_prerequisites_script=scripts_dir / "powershell" / "check-prerequisites.ps1",
            run_planning_lint_script=scripts_dir / "powershell" / "run-planning-lint.ps1",
            is_powershell=True,
        )

    if not shutil.which("bash"):
        raise FlowExecutionError("bash not found on current system", EXIT_SETUP_ERROR)

    return PlatformConfig(
        shell_prefix=["bash"],
        create_feature_script=scripts_dir / "bash" / "create-new-feature.sh",
        setup_plan_script=scripts_dir / "bash" / "setup-plan.sh",
        check_prerequisites_script=scripts_dir / "bash" / "check-prerequisites.sh",
        run_planning_lint_script=scripts_dir / "bash" / "run-planning-lint.sh",
        is_powershell=False,
    )


def find_missing_paths(paths: Sequence[Path]) -> list[Path]:
    return [path for path in paths if not path.exists()]


def run_command(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def extract_json_payload(stdout: str) -> dict[str, Any]:
    candidates = [stdout.strip()]
    candidates.extend(line.strip() for line in reversed(stdout.splitlines()) if line.strip())

    for candidate in candidates:
        if not candidate:
            continue
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        if isinstance(payload, dict):
            return payload

    raise FlowExecutionError("Expected JSON object in command output but none was found", EXIT_INVALID_OUTPUT)


def execute_step(step_name: str, command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    rendered = " ".join(shlex.quote(part) for part in command)
    log(f"STEP {step_name}: {rendered}")

    result = run_command(command, cwd)
    if result.returncode != 0:
        if result.stdout.strip():
            log_error(f"{step_name} stdout:\n{result.stdout.strip()}")
        if result.stderr.strip():
            log_error(f"{step_name} stderr:\n{result.stderr.strip()}")
        raise FlowExecutionError(f"{step_name} failed with exit code {result.returncode}", EXIT_SUBCOMMAND_FAILED)

    log(f"STEP {step_name}: success")
    return result


def run_sdd_flow(target_dir: Path, feature_description: str) -> int:
    if not target_dir.exists() or not target_dir.is_dir():
        log_error(f"Target directory does not exist: {target_dir}")
        return EXIT_INVALID_INPUT

    try:
        config = resolve_platform_config(target_dir)
    except FlowExecutionError as exc:
        log_error(str(exc))
        return exc.exit_code

    rules_path = target_dir / "rules" / "planning-lint-rules.tsv"
    required_paths = [
        config.create_feature_script,
        config.setup_plan_script,
        config.check_prerequisites_script,
        config.run_planning_lint_script,
        rules_path,
    ]
    missing_paths = find_missing_paths(required_paths)
    if missing_paths:
        joined = "\n".join(f"- {path}" for path in missing_paths)
        log_error(f"Required files are missing:\n{joined}")
        return EXIT_SETUP_ERROR

    short_name = f"sdd-auto-{int(time.time())}"

    if config.is_powershell:
        create_args = ["-Json", "-ShortName", short_name, feature_description]
        setup_args = ["-Json", "-SpecFile", ""]
        check_args = ["-Json", "-PlanFile", ""]
        lint_args = ["-FeatureDir", "", "-Rules", "", "-Json"]
    else:
        create_args = ["--json", "--short-name", short_name, feature_description]
        setup_args = ["--json", "--spec-file", ""]
        check_args = ["--json", "--plan-file", ""]
        lint_args = ["--feature-dir", "", "--rules", "", "--json"]

    try:
        create_cmd = config.shell_prefix + [str(config.create_feature_script), *create_args]
        create_result = execute_step("1/4 create-new-feature", create_cmd, target_dir)
        create_payload = extract_json_payload(create_result.stdout)

        spec_file = create_payload.get("SPEC_FILE")
        if not isinstance(spec_file, str) or not spec_file.strip():
            raise FlowExecutionError("create-new-feature output missing SPEC_FILE", EXIT_INVALID_OUTPUT)

        spec_path = Path(spec_file).resolve()
        feature_dir = spec_path.parent
        plan_path = feature_dir / "plan.md"

        setup_args[2] = str(spec_path)
        check_args[2] = str(plan_path)

        setup_cmd = config.shell_prefix + [str(config.setup_plan_script), *setup_args]
        execute_step("2/4 setup-plan", setup_cmd, target_dir)

        check_cmd = config.shell_prefix + [str(config.check_prerequisites_script), *check_args]
        execute_step("3/4 check-prerequisites", check_cmd, target_dir)

        lint_args[1] = str(feature_dir)
        lint_args[3] = str(rules_path.resolve())
        lint_cmd = config.shell_prefix + [str(config.run_planning_lint_script), *lint_args]
        lint_result = execute_step("4/4 run-planning-lint", lint_cmd, target_dir)
        lint_payload = extract_json_payload(lint_result.stdout)

        findings_total = lint_payload.get("findings_total")
        if not isinstance(findings_total, int):
            raise FlowExecutionError("run-planning-lint output missing integer findings_total", EXIT_INVALID_OUTPUT)

        if findings_total > 0:
            log_error(f"Planning lint reported findings_total={findings_total}")
            return EXIT_LINT_FAILED

        log("Workflow completed successfully with zero lint findings")
        return EXIT_SUCCESS

    except FlowExecutionError as exc:
        log_error(str(exc))
        return exc.exit_code


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    target_dir = Path(args.directory).resolve()
    return run_sdd_flow(target_dir=target_dir, feature_description=args.feature_description)


if __name__ == "__main__":
    raise SystemExit(main())

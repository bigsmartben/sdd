#!/usr/bin/env python3
"""Validate implementation completion anchors by executing command anchors.

This helper is intended for `/sdd.implement` post-task checks:
- Enforce strict/adaptive waiver policy.
- Prefer `tasks.manifest.json`; adaptive mode may fall back to `tasks.md`.
- Execute command anchors for selected tasks.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run completion-anchor command gate for implement tasks.")
    parser.add_argument("--feature-dir", required=True, help="Feature directory path.")
    parser.add_argument("--tasks", required=True, help="Path to tasks.md.")
    parser.add_argument("--tasks-manifest", required=True, help="Path to tasks.manifest.json.")
    parser.add_argument("--mode", choices=("strict", "adaptive"), default="strict")
    parser.add_argument("--waive-analyze-gate", action="store_true")
    parser.add_argument("--waiver-reason", default="", help="Required when waive-analyze-gate is used.")
    parser.add_argument("--task-id", action="append", default=[], help="Task ID to validate. Can repeat.")
    parser.add_argument("--workdir", default="", help="Working directory for anchor command execution.")
    parser.add_argument(
        "--strict-non-executable",
        action="store_true",
        help="Treat missing executable completion anchors as hard failures.",
    )
    return parser.parse_args(argv)


def _load_manifest(tasks_manifest_path: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    if not tasks_manifest_path.is_file():
        errors.append(
            {
                "code": "tasks_manifest_missing",
                "message": "tasks.manifest.json is missing.",
                "details": {"path": str(tasks_manifest_path)},
            }
        )
        return None, errors
    try:
        data = json.loads(tasks_manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(
            {
                "code": "tasks_manifest_invalid_json",
                "message": "tasks.manifest.json is invalid JSON.",
                "details": {"line": exc.lineno, "column": exc.colno, "path": str(tasks_manifest_path)},
            }
        )
        return None, errors

    if not isinstance(data, dict):
        errors.append(
            {
                "code": "tasks_manifest_invalid_root",
                "message": "tasks.manifest.json root must be an object.",
                "details": {"path": str(tasks_manifest_path)},
            }
        )
        return None, errors

    for key in ("schema_version", "generated_at", "generated_from", "tasks"):
        if key not in data:
            errors.append(
                {
                    "code": "tasks_manifest_missing_top_level_keys",
                    "message": "tasks.manifest.json is missing required top-level keys.",
                    "details": {"missing_key": key},
                }
            )
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        errors.append(
            {
                "code": "tasks_manifest_tasks_invalid",
                "message": "tasks.manifest.json `tasks` must be an array.",
                "details": {},
            }
        )
        return data, errors

    invalid_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(tasks):
        if not isinstance(row, dict):
            invalid_rows.append({"index": idx, "reason": "row_not_object"})
            continue
        for key in ("task_id", "completion_anchors"):
            if key not in row:
                invalid_rows.append({"index": idx, "reason": f"missing_{key}"})
    if invalid_rows:
        errors.append(
            {
                "code": "tasks_manifest_task_rows_invalid",
                "message": "One or more manifest task rows are invalid for anchor execution.",
                "details": {"rows": invalid_rows},
            }
        )
    return data, errors


def _parse_tasks_md(tasks_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    if not tasks_path.is_file():
        errors.append(
            {"code": "tasks_md_missing", "message": "tasks.md is missing.", "details": {"path": str(tasks_path)}}
        )
        return [], errors
    content = tasks_path.read_text(encoding="utf-8")
    # Extract lines like:
    # - [ ] T001 ... (Completion Anchor: [cmd:pytest -q])
    line_pattern = re.compile(
        r"^- \[[ xX]\] (?P<task_id>T\d+).*\(Completion Anchor:\s*(?P<anchor>.+?)\)\s*$",
        flags=re.MULTILINE,
    )
    tasks: list[dict[str, Any]] = []
    for match in line_pattern.finditer(content):
        anchor_text = match.group("anchor").strip()
        anchors = [anchor_text]
        tasks.append(
            {
                "task_id": match.group("task_id"),
                "status": "unknown",
                "completion_anchors": anchors,
            }
        )
    return tasks, errors


def _select_tasks(
    *,
    tasks: list[dict[str, Any]],
    selected_ids: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    if not selected_ids:
        return tasks, errors
    selected_set = {task_id.strip() for task_id in selected_ids if task_id.strip()}
    selected_tasks = [task for task in tasks if str(task.get("task_id", "")).strip() in selected_set]
    found_ids = {str(task.get("task_id", "")).strip() for task in selected_tasks}
    missing = sorted(selected_set - found_ids)
    if missing:
        errors.append(
            {
                "code": "selected_task_not_found",
                "message": "One or more selected task IDs are not present in the runtime source.",
                "details": {"task_ids": missing},
            }
        )
    return selected_tasks, errors


def _extract_command_anchors(raw_anchors: Any) -> list[str]:
    anchors = raw_anchors if isinstance(raw_anchors, list) else [raw_anchors]
    commands: list[str] = []
    for anchor in anchors:
        value = str(anchor or "").strip()
        if value.lower().startswith("cmd:"):
            command = value[4:].strip()
            if command:
                commands.append(command)
    return commands


def _run_command(command: str, *, cwd: Path) -> dict[str, Any]:
    started = time.time()
    try:
        result = subprocess.run(command, shell=True, cwd=str(cwd), capture_output=True, text=True, check=False, timeout=300)
        status = "pass" if result.returncode == 0 else "fail"
        return {
            "command": command,
            "result": status,
            "exit_code": result.returncode,
            "duration_ms": int((time.time() - started) * 1000),
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "result": "timeout",
            "exit_code": 124,
            "duration_ms": int((time.time() - started) * 1000),
            "stdout": str((exc.stdout or "")[-4000:]),
            "stderr": str((exc.stderr or "")[-4000:]),
        }


def _is_completed_task(task: dict[str, Any]) -> bool:
    status = str(task.get("status", "")).strip().lower()
    return status in {"done", "completed", "complete", "success", "passed"}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    feature_dir = Path(args.feature_dir).resolve()
    tasks_path = Path(args.tasks).resolve()
    tasks_manifest_path = Path(args.tasks_manifest).resolve()
    workdir = Path(args.workdir).resolve() if args.workdir else feature_dir

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if args.mode == "strict" and args.waive_analyze_gate:
        errors.append(
            {
                "code": "strict_mode_disallows_waiver",
                "message": "strict mode does not allow waive-analyze-gate.",
                "details": {},
            }
        )
    if args.waive_analyze_gate and not args.waiver_reason.strip():
        errors.append(
            {
                "code": "waiver_reason_missing",
                "message": "waive-analyze-gate requires a non-empty waiver reason.",
                "details": {},
            }
        )

    manifest_data, manifest_errors = _load_manifest(tasks_manifest_path)
    if manifest_errors:
        if args.mode == "strict":
            errors.extend(manifest_errors)
            tasks_source = "tasks.manifest.json"
            tasks_for_eval: list[dict[str, Any]] = []
        else:
            warnings.extend(manifest_errors)
            tasks_source = "tasks.md"
            tasks_for_eval, tasks_md_errors = _parse_tasks_md(tasks_path)
            if tasks_md_errors:
                errors.extend(tasks_md_errors)
    else:
        tasks_source = "tasks.manifest.json"
        tasks_for_eval = list(manifest_data.get("tasks", [])) if manifest_data is not None else []

    default_tasks = [task for task in tasks_for_eval if _is_completed_task(task)]
    selected_tasks, selection_errors = _select_tasks(
        tasks=default_tasks if not args.task_id else tasks_for_eval,
        selected_ids=args.task_id,
    )
    if selection_errors:
        errors.extend(selection_errors)

    evaluation: list[dict[str, Any]] = []
    executed_command_count = 0
    failed_command_count = 0
    skipped_non_executable_count = 0
    for task in selected_tasks:
        task_id = str(task.get("task_id", "")).strip()
        commands = _extract_command_anchors(task.get("completion_anchors", []))
        task_result: dict[str, Any] = {
            "task_id": task_id,
            "source_status": str(task.get("status", "")).strip(),
            "command_anchors": commands,
            "anchors": [],
            "passed": False,
        }
        if not commands:
            task_result["error"] = "missing_executable_completion_anchor"
            evaluation.append(task_result)
            skipped_non_executable_count += 1
            issue = {
                "code": "missing_executable_completion_anchor",
                "message": "Task does not declare executable completion anchors (`cmd:` prefix).",
                "details": {"task_id": task_id},
            }
            if args.strict_non_executable or args.mode == "strict":
                errors.append(issue)
            else:
                warnings.append(issue)
            continue
        cmd_results = [_run_command(command, cwd=workdir) for command in commands]
        executed_command_count += len(cmd_results)
        failed_command_count += sum(1 for result in cmd_results if result["result"] in {"fail", "timeout"})
        task_result["anchors"] = cmd_results
        task_result["passed"] = all(result["result"] == "pass" for result in cmd_results)
        evaluation.append(task_result)
        if not task_result["passed"]:
            errors.append(
                {
                    "code": "completion_anchor_command_failed",
                    "message": "One or more completion anchor commands failed.",
                    "details": {"task_id": task_id},
                }
            )

    ready = len(errors) == 0
    payload = {
        "schema_version": SCHEMA_VERSION,
        "feature_dir": str(feature_dir),
        "tasks_path": str(tasks_path),
        "tasks_manifest_path": str(tasks_manifest_path),
        "mode": args.mode,
        "waive_analyze_gate": bool(args.waive_analyze_gate),
        "waiver_reason": args.waiver_reason.strip(),
        "tasks_source": tasks_source,
        "selected_task_ids": args.task_id,
        "strict_non_executable": bool(args.strict_non_executable),
        "ready_for_task_completion_update": ready,
        "ready_for_completion": ready,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "validated_task_count": len(selected_tasks),
        "executed_anchor_count": executed_command_count,
        "failed_anchor_count": failed_command_count,
        "executed_command_count": executed_command_count,
        "failed_command_count": failed_command_count,
        "skipped_non_executable_count": skipped_non_executable_count,
        "task_results": evaluation,
        "evaluated_tasks": evaluation,
    }
    json.dump(payload, sys.stdout, ensure_ascii=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())

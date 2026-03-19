"""Packaged tasks.manifest bootstrap extractor."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from specify_cli.runtime_common import compute_sha256


TASKS_MANIFEST_BOOTSTRAP_SCHEMA_VERSION = "1.0"
REQUIRED_TOP_LEVEL_KEYS = ("schema_version", "generated_at", "generated_from", "tasks")
REQUIRED_GENERATED_FROM_KEYS = ("plan_path", "plan_source_fingerprint", "contract_source_fingerprints")
REQUIRED_TASK_KEYS = (
    "task_id",
    "dependencies",
    "if_scope",
    "refs",
    "target_paths",
    "completion_anchors",
    "conflict_hints",
    "topo_layer",
    "status",
)


def _resolve_path(value: str, *, feature_dir: Path) -> Path | None:
    normalized = (value or "").strip()
    if not normalized:
        return None
    candidate = Path(normalized)
    if not candidate.is_absolute():
        candidate = feature_dir / candidate
    return candidate.resolve()


def build_tasks_manifest_validation(
    *,
    feature_dir: Path,
    plan_path: Path,
    tasks_path: Path,
    tasks_manifest_path: Path,
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    manifest_data: dict[str, Any] | None = None
    if not tasks_manifest_path.is_file():
        errors.append(
            {
                "code": "tasks_manifest_missing",
                "message": "tasks.manifest.json is missing; runtime should fall back to tasks.md parsing.",
                "details": {"path": str(tasks_manifest_path)},
            }
        )
    else:
        try:
            decoded = json.loads(tasks_manifest_path.read_text(encoding="utf-8"))
            if not isinstance(decoded, dict):
                errors.append(
                    {
                        "code": "tasks_manifest_invalid_root_type",
                        "message": "tasks.manifest.json root must be a JSON object.",
                        "details": {"path": str(tasks_manifest_path)},
                    }
                )
            else:
                manifest_data = decoded
        except json.JSONDecodeError as exc:
            errors.append(
                {
                    "code": "tasks_manifest_invalid_json",
                    "message": "tasks.manifest.json is not valid JSON.",
                    "details": {
                        "path": str(tasks_manifest_path),
                        "line": exc.lineno,
                        "column": exc.colno,
                    },
                }
            )

    task_count = 0
    if manifest_data is not None:
        missing_top_level = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in manifest_data]
        if missing_top_level:
            errors.append(
                {
                    "code": "tasks_manifest_missing_top_level_keys",
                    "message": "tasks.manifest.json is missing required top-level keys.",
                    "details": {"keys": missing_top_level},
                }
            )

        generated_from = manifest_data.get("generated_from")
        if not isinstance(generated_from, dict):
            errors.append(
                {
                    "code": "tasks_manifest_generated_from_invalid",
                    "message": "tasks.manifest.json `generated_from` must be a JSON object.",
                    "details": {},
                }
            )
        else:
            missing_generated_from = [key for key in REQUIRED_GENERATED_FROM_KEYS if key not in generated_from]
            if missing_generated_from:
                errors.append(
                    {
                        "code": "tasks_manifest_generated_from_missing_keys",
                        "message": "tasks.manifest.json `generated_from` is missing required keys.",
                        "details": {"keys": missing_generated_from},
                    }
                )
            generated_plan_path = generated_from.get("plan_path", "")
            resolved_generated_plan = _resolve_path(str(generated_plan_path), feature_dir=feature_dir)
            if resolved_generated_plan is not None and resolved_generated_plan != plan_path.resolve():
                warnings.append(
                    {
                        "code": "tasks_manifest_plan_path_mismatch",
                        "message": "tasks.manifest.json `generated_from.plan_path` does not match current plan.md path.",
                        "details": {
                            "manifest_plan_path": str(resolved_generated_plan),
                            "current_plan_path": str(plan_path.resolve()),
                        },
                    }
                )

        tasks = manifest_data.get("tasks")
        if not isinstance(tasks, list):
            errors.append(
                {
                    "code": "tasks_manifest_tasks_invalid",
                    "message": "tasks.manifest.json `tasks` must be an array.",
                    "details": {},
                }
            )
        else:
            task_count = len(tasks)
            invalid_task_rows: list[dict[str, Any]] = []
            duplicate_ids: list[str] = []
            seen_task_ids: set[str] = set()
            for index, task in enumerate(tasks):
                if not isinstance(task, dict):
                    invalid_task_rows.append({"index": index, "missing_keys": list(REQUIRED_TASK_KEYS)})
                    continue
                task_id = str(task.get("task_id", "")).strip()
                if task_id:
                    if task_id in seen_task_ids:
                        duplicate_ids.append(task_id)
                    seen_task_ids.add(task_id)
                missing_task_keys = [key for key in REQUIRED_TASK_KEYS if key not in task]
                if missing_task_keys:
                    invalid_task_rows.append({"index": index, "missing_keys": missing_task_keys})
            if invalid_task_rows:
                errors.append(
                    {
                        "code": "tasks_manifest_task_rows_missing_keys",
                        "message": "One or more task rows are missing required keys.",
                        "details": {"rows": invalid_task_rows},
                    }
                )
            if duplicate_ids:
                warnings.append(
                    {
                        "code": "tasks_manifest_duplicate_task_ids",
                        "message": "tasks.manifest.json contains duplicated task_id values.",
                        "details": {"task_ids": sorted(set(duplicate_ids))},
                    }
                )

    if not tasks_path.is_file():
        errors.append(
            {
                "code": "tasks_md_missing",
                "message": "tasks.md is missing; fallback parsing is unavailable.",
                "details": {"path": str(tasks_path)},
            }
        )

    valid = len(errors) == 0
    return {
        "valid": valid,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "task_count": task_count,
        "runtime_source_preference": "tasks.manifest.json" if valid else "tasks.md",
    }


def build_tasks_manifest_bootstrap_payload(
    *,
    feature_dir: Path,
    plan_path: Path,
    tasks_path: Path,
    tasks_manifest_path: Path,
) -> dict[str, Any]:
    return {
        "schema_version": TASKS_MANIFEST_BOOTSTRAP_SCHEMA_VERSION,
        "feature_dir": str(feature_dir),
        "plan_path": str(plan_path),
        "tasks_path": str(tasks_path),
        "tasks_manifest_path": str(tasks_manifest_path),
        "current_fingerprints": {
            "plan_sha256": compute_sha256(plan_path),
            "tasks_sha256": compute_sha256(tasks_path),
            "tasks_manifest_sha256": compute_sha256(tasks_manifest_path),
        },
        "validation": build_tasks_manifest_validation(
            feature_dir=feature_dir,
            plan_path=plan_path,
            tasks_path=tasks_path,
            tasks_manifest_path=tasks_manifest_path,
        ),
    }

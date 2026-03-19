"""Packaged implement bootstrap extractor."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from specify_cli.runtime_common import compute_sha256
from specify_cli.runtime_gate_protocol import build_repository_first_gate_protocol


IMPLEMENT_BOOTSTRAP_SCHEMA_VERSION = "1.0"
RUN_BEGIN = "<!-- SDD_ANALYZE_RUN_BEGIN -->"
RUN_END = "<!-- SDD_ANALYZE_RUN_END -->"
IMPLEMENT_BASELINE_CODE_TO_CATEGORY = {
    "missing_required_artifacts": "missing",
    "analyze_history_missing": "missing",
    "analyze_run_block_missing": "missing",
    "analyze_fingerprints_missing": "missing",
    "gate_decision_missing": "non_traceable",
    "gate_decision_not_pass": "stale",
    "analyze_fingerprint_mismatch": "stale",
}


def extract_latest_run_block(content: str) -> str | None:
    matches = re.findall(rf"{re.escape(RUN_BEGIN)}(.*?){re.escape(RUN_END)}", content, flags=re.DOTALL)
    if not matches:
        return None
    return matches[-1].strip()


def extract_marker(block: str, marker: str) -> str:
    pattern = rf"^\s*{re.escape(marker)}\s*(.+?)\s*$"
    match = re.search(pattern, block, flags=re.MULTILINE)
    if not match:
        return ""
    return match.group(1).strip()


def normalize_gate_decision(raw: str) -> str:
    if not raw:
        return ""
    return raw.split()[0].strip().upper()


def build_analyze_readiness(
    *,
    required_paths: dict[str, Path],
    current_fingerprints: dict[str, str],
    analyze_history_path: Path,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    latest_run: dict[str, Any] | None = None

    missing_required = sorted([name for name, path in required_paths.items() if not path.is_file()])
    if missing_required:
        errors.append(
            {
                "code": "missing_required_artifacts",
                "message": "One or more required artifacts for implementation are missing.",
                "details": {"artifacts": missing_required},
            }
        )

    if not analyze_history_path.is_file():
        errors.append(
            {
                "code": "analyze_history_missing",
                "message": "Analyze history file is missing.",
                "details": {"path": str(analyze_history_path)},
            }
        )
        return {
            "ready_for_implementation": False,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
        }, latest_run

    content = analyze_history_path.read_text(encoding="utf-8")
    latest_block = extract_latest_run_block(content)
    if latest_block is None:
        errors.append(
            {
                "code": "analyze_run_block_missing",
                "message": "No analyze run block was found in analyze-history.md.",
                "details": {"path": str(analyze_history_path)},
            }
        )
        return {
            "ready_for_implementation": False,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
        }, latest_run

    run_at = extract_marker(latest_block, "Run At (UTC):")
    spec_sha = extract_marker(latest_block, "Spec SHA256:")
    plan_sha = extract_marker(latest_block, "Plan SHA256:")
    tasks_sha = extract_marker(latest_block, "Tasks SHA256:")
    gate_decision = normalize_gate_decision(extract_marker(latest_block, "Gate Decision:"))

    latest_run = {
        "run_at_utc": run_at,
        "gate_decision": gate_decision,
        "fingerprints": {
            "spec_sha256": spec_sha,
            "plan_sha256": plan_sha,
            "tasks_sha256": tasks_sha,
        },
    }

    if not gate_decision:
        errors.append({"code": "gate_decision_missing", "message": "Latest analyze run is missing Gate Decision.", "details": {}})
    elif gate_decision != "PASS":
        errors.append(
            {
                "code": "gate_decision_not_pass",
                "message": "Latest analyze gate decision is not PASS.",
                "details": {"gate_decision": gate_decision},
            }
        )

    missing_fingerprint_labels = sorted(
        [
            label
            for label, value in {
                "spec_sha256": spec_sha,
                "plan_sha256": plan_sha,
                "tasks_sha256": tasks_sha,
            }.items()
            if not value
        ]
    )
    if missing_fingerprint_labels:
        errors.append(
            {
                "code": "analyze_fingerprints_missing",
                "message": "Latest analyze run is missing required fingerprints.",
                "details": {"fingerprints": missing_fingerprint_labels},
            }
        )
    else:
        mismatches: list[dict[str, str]] = []
        for artifact_name, key in (("spec.md", "spec_sha256"), ("plan.md", "plan_sha256"), ("tasks.md", "tasks_sha256")):
            current = current_fingerprints[key]
            analyze = latest_run["fingerprints"][key]
            if analyze != current:
                mismatches.append({"artifact": artifact_name, "analyze": analyze, "current": current})
        if mismatches:
            errors.append(
                {
                    "code": "analyze_fingerprint_mismatch",
                    "message": "Latest analyze fingerprints do not match current artifact fingerprints.",
                    "details": {"mismatches": mismatches},
                }
            )

    return {
        "ready_for_implementation": len(errors) == 0,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }, latest_run


def build_implement_bootstrap_payload(
    *,
    feature_dir: Path,
    spec_path: Path,
    plan_path: Path,
    tasks_path: Path,
    analyze_history_path: Path,
) -> dict[str, Any]:
    required_paths = {
        "spec.md": spec_path,
        "plan.md": plan_path,
        "tasks.md": tasks_path,
    }
    current_fingerprints = {
        "spec_sha256": compute_sha256(spec_path),
        "plan_sha256": compute_sha256(plan_path),
        "tasks_sha256": compute_sha256(tasks_path),
    }
    analyze_readiness, latest_run = build_analyze_readiness(
        required_paths=required_paths,
        current_fingerprints=current_fingerprints,
        analyze_history_path=analyze_history_path,
    )
    source_manifest_fingerprints = None
    if latest_run and isinstance(latest_run.get("fingerprints"), dict):
        source_manifest_fingerprints = {
            "spec_sha256": str(latest_run["fingerprints"].get("spec_sha256", "")),
            "plan_sha256": str(latest_run["fingerprints"].get("plan_sha256", "")),
            "tasks_sha256": str(latest_run["fingerprints"].get("tasks_sha256", "")),
        }
    repository_first_gate_protocol = build_repository_first_gate_protocol(
        gate_name="implement_bootstrap",
        readiness=analyze_readiness,
        ready_field="ready_for_implementation",
        code_to_category=IMPLEMENT_BASELINE_CODE_TO_CATEGORY,
        source_manifest_fingerprints=source_manifest_fingerprints,
    )

    return {
        "schema_version": IMPLEMENT_BOOTSTRAP_SCHEMA_VERSION,
        "feature_dir": str(feature_dir),
        "spec_path": str(spec_path),
        "plan_path": str(plan_path),
        "tasks_path": str(tasks_path),
        "analyze_history_path": str(analyze_history_path),
        "current_fingerprints": current_fingerprints,
        "latest_run": latest_run,
        "analyze_readiness": analyze_readiness,
        "repository_first_gate_protocol": repository_first_gate_protocol,
    }

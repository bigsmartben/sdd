#!/usr/bin/env python3
"""Extract a compact implementation-readiness bootstrap packet.

This script precomputes analyze-gate readiness for `/sdd.implement` by
reading the latest run block in `audits/analyze-history.md` and comparing
recorded fingerprints against current `spec.md`, `plan.md`, and `tasks.md`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


BOOTSTRAP_SCHEMA_VERSION = "1.0"
RUN_BEGIN = "<!-- SDD_ANALYZE_RUN_BEGIN -->"
RUN_END = "<!-- SDD_ANALYZE_RUN_END -->"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract compact implement bootstrap packet")
    parser.add_argument("--feature-dir", required=True, help="Absolute or repo-relative feature directory")
    parser.add_argument("--spec", required=True, help="Path to spec.md")
    parser.add_argument("--plan", required=True, help="Path to plan.md")
    parser.add_argument("--tasks", required=True, help="Path to tasks.md")
    parser.add_argument("--analyze-history", required=True, help="Path to audits/analyze-history.md")
    return parser.parse_args(argv)


def compute_sha256(path: Path) -> str:
    if not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_latest_run_block(content: str) -> str | None:
    matches = re.findall(
        rf"{re.escape(RUN_BEGIN)}(.*?){re.escape(RUN_END)}",
        content,
        flags=re.DOTALL,
    )
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
    token = raw.split()[0].strip().upper()
    return token


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
        return (
            {
                "ready_for_implementation": False,
                "error_count": len(errors),
                "warning_count": len(warnings),
                "errors": errors,
                "warnings": warnings,
            },
            latest_run,
        )

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
        return (
            {
                "ready_for_implementation": False,
                "error_count": len(errors),
                "warning_count": len(warnings),
                "errors": errors,
                "warnings": warnings,
            },
            latest_run,
        )

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
        errors.append(
            {
                "code": "gate_decision_missing",
                "message": "Latest analyze run is missing Gate Decision.",
                "details": {},
            }
        )
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
        if spec_sha != current_fingerprints["spec_sha256"]:
            mismatches.append({"artifact": "spec.md", "analyze": spec_sha, "current": current_fingerprints["spec_sha256"]})
        if plan_sha != current_fingerprints["plan_sha256"]:
            mismatches.append({"artifact": "plan.md", "analyze": plan_sha, "current": current_fingerprints["plan_sha256"]})
        if tasks_sha != current_fingerprints["tasks_sha256"]:
            mismatches.append({"artifact": "tasks.md", "analyze": tasks_sha, "current": current_fingerprints["tasks_sha256"]})
        if mismatches:
            errors.append(
                {
                    "code": "analyze_fingerprint_mismatch",
                    "message": "Latest analyze fingerprints do not match current artifact fingerprints.",
                    "details": {"mismatches": mismatches},
                }
            )

    readiness = {
        "ready_for_implementation": len(errors) == 0,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }
    return readiness, latest_run


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    feature_dir = Path(args.feature_dir).resolve()
    spec_path = Path(args.spec).resolve()
    plan_path = Path(args.plan).resolve()
    tasks_path = Path(args.tasks).resolve()
    analyze_history_path = Path(args.analyze_history).resolve()

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

    payload = {
        "schema_version": BOOTSTRAP_SCHEMA_VERSION,
        "feature_dir": str(feature_dir),
        "spec_path": str(spec_path),
        "plan_path": str(plan_path),
        "tasks_path": str(tasks_path),
        "analyze_history_path": str(analyze_history_path),
        "current_fingerprints": current_fingerprints,
        "latest_run": latest_run,
        "analyze_readiness": analyze_readiness,
    }

    json.dump(payload, sys.stdout, ensure_ascii=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

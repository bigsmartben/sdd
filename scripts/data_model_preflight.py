#!/usr/bin/env python3
"""Extract a compact data-model generation bootstrap packet.

This script precomputes queue selection and readiness for `/sdd.plan.data-model`
so the model can consume a narrow gate packet instead of rediscovering stage
state from `plan.md` during the same run.
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
SECTION_HEADINGS = (
    "Shared Context Snapshot",
    "Stage Queue",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract compact data-model bootstrap packet")
    parser.add_argument("--feature-dir", required=True, help="Absolute or repo-relative feature directory")
    parser.add_argument("--plan", required=True, help="Path to plan.md")
    parser.add_argument("--spec", required=True, help="Path to spec.md")
    parser.add_argument("--research", required=True, help="Path to research.md")
    parser.add_argument("--data-model", required=True, help="Path to data-model.md")
    return parser.parse_args(argv)


def compute_sha256(path: Path) -> str:
    if not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def parse_markdown_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return []

    content = stripped.strip("|")
    cells: list[str] = []
    current: list[str] = []
    escaping = False

    for ch in content:
        if escaping:
            if ch in {"|", "\\"}:
                current.append(ch)
            else:
                current.append("\\")
                current.append(ch)
            escaping = False
            continue
        if ch == "\\":
            escaping = True
            continue
        if ch == "|":
            cells.append("".join(current))
            current = []
            continue
        current.append(ch)

    if escaping:
        current.append("\\")
    cells.append("".join(current))
    return cells


def resolve_target_path(feature_dir: Path, raw_path: str) -> str:
    normalized = clean_cell(raw_path)
    if not normalized:
        return ""
    candidate = Path(normalized)
    if candidate.is_absolute():
        return str(candidate)
    return str((feature_dir / candidate).resolve())


def extract_section(document: str, heading: str) -> str | None:
    pattern = rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, document, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()


def parse_markdown_table(section: str | None) -> list[dict[str, str]]:
    if not section:
        return []

    lines = section.splitlines()
    table_lines: list[str] = []
    collecting = False

    for line in lines:
        if line.lstrip().startswith("|"):
            table_lines.append(line.rstrip())
            collecting = True
            continue
        if collecting:
            break

    if len(table_lines) < 2:
        return []

    headers = [clean_cell(cell) for cell in parse_markdown_cells(table_lines[0])]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [clean_cell(cell) for cell in parse_markdown_cells(line)]
        if len(cells) != len(headers):
            continue
        row = {header: cell for header, cell in zip(headers, cells)}
        if any(value for value in row.values()):
            rows.append(row)
    return rows


def build_stage_row(feature_dir: Path, row: dict[str, str] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "stage_id": clean_cell(row.get("Stage ID", "")),
        "command": clean_cell(row.get("Command", "")),
        "required_inputs": clean_cell(row.get("Required Inputs", "")),
        "output_path": clean_cell(row.get("Output Path", "")),
        "output_path_abs": resolve_target_path(feature_dir, row.get("Output Path", "")),
        "status": clean_cell(row.get("Status", "")),
        "source_fingerprint": clean_cell(row.get("Source Fingerprint", "")),
        "output_fingerprint": clean_cell(row.get("Output Fingerprint", "")),
        "blocker": clean_cell(row.get("Blocker", "")),
    }


def build_generation_readiness(
    *,
    missing_sections: list[str],
    spec_path: Path,
    research_path: Path,
    data_model_path: Path,
    research_stage: dict[str, Any] | None,
    selected_stage: dict[str, Any] | None,
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if missing_sections:
        errors.append(
            {
                "code": "missing_required_sections",
                "message": "plan.md is missing required control-plane sections for /sdd.plan.data-model.",
                "details": {"sections": missing_sections},
            }
        )

    if not spec_path.is_file():
        errors.append(
            {
                "code": "spec_missing",
                "message": "spec.md is missing for the selected feature.",
                "details": {"path": str(spec_path)},
            }
        )

    if not research_path.is_file():
        errors.append(
            {
                "code": "research_artifact_missing",
                "message": "research.md is missing for the selected feature.",
                "details": {"path": str(research_path)},
            }
        )

    if research_stage is None:
        errors.append(
            {
                "code": "research_stage_missing",
                "message": "Stage Queue does not contain a research row.",
                "details": {},
            }
        )
    elif research_stage["status"] != "done":
        errors.append(
            {
                "code": "research_stage_not_done",
                "message": "Research prerequisite is not done.",
                "details": {
                    "status": research_stage["status"],
                    "blocker": research_stage["blocker"],
                },
            }
        )

    if selected_stage is None:
        errors.append(
            {
                "code": "data_model_stage_pending_missing",
                "message": "No pending data-model row is available in Stage Queue.",
                "details": {},
            }
        )
    elif selected_stage["status"] != "pending":
        errors.append(
            {
                "code": "data_model_stage_not_pending",
                "message": "Selected data-model row is not pending.",
                "details": {"status": selected_stage["status"]},
            }
        )

    if selected_stage and selected_stage["output_path_abs"] and selected_stage["output_path_abs"] != str(data_model_path):
        errors.append(
            {
                "code": "data_model_output_path_mismatch",
                "message": "Selected data-model row output path does not match resolved data-model.md path.",
                "details": {
                    "stage_output_path": selected_stage["output_path_abs"],
                    "resolved_data_model_path": str(data_model_path),
                },
            }
        )

    return {
        "ready_for_generation": len(errors) == 0,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    feature_dir = Path(args.feature_dir).resolve()
    plan_path = Path(args.plan).resolve()
    spec_path = Path(args.spec).resolve()
    research_path = Path(args.research).resolve()
    data_model_path = Path(args.data_model).resolve()

    if not plan_path.is_file():
        print(f"ERROR: plan.md not found: {plan_path}", file=sys.stderr)
        return 1

    document = plan_path.read_text(encoding="utf-8")
    sections = {heading: extract_section(document, heading) for heading in SECTION_HEADINGS}
    required_sections = {
        "shared_context_snapshot": sections["Shared Context Snapshot"] is not None,
        "stage_queue": sections["Stage Queue"] is not None,
    }
    missing_sections = [name for name, present in required_sections.items() if not present]

    stage_rows = parse_markdown_table(sections["Stage Queue"])
    research_stage = build_stage_row(
        feature_dir,
        next((row for row in stage_rows if clean_cell(row.get("Stage ID", "")) == "research"), None),
    )
    selected_stage = build_stage_row(
        feature_dir,
        next(
            (
                row
                for row in stage_rows
                if clean_cell(row.get("Stage ID", "")) == "data-model"
                and clean_cell(row.get("Status", "")) == "pending"
            ),
            None,
        ),
    )

    current_fingerprints = {
        "plan_sha256": compute_sha256(plan_path),
        "spec_sha256": compute_sha256(spec_path),
        "research_sha256": compute_sha256(research_path),
        "data_model_sha256": compute_sha256(data_model_path),
    }

    generation_readiness = build_generation_readiness(
        missing_sections=missing_sections,
        spec_path=spec_path,
        research_path=research_path,
        data_model_path=data_model_path,
        research_stage=research_stage,
        selected_stage=selected_stage,
    )

    payload = {
        "schema_version": BOOTSTRAP_SCHEMA_VERSION,
        "feature_dir": str(feature_dir),
        "plan_path": str(plan_path),
        "spec_path": str(spec_path),
        "research_path": str(research_path),
        "data_model_path": str(data_model_path),
        "required_sections": required_sections,
        "current_fingerprints": current_fingerprints,
        "research_stage": research_stage,
        "selected_stage": selected_stage,
        "repo_anchor_policy": {
            "decision_order": ["existing", "extended", "new"],
            "repo_anchor_input_limit": 5,
            "inv_requires_repo_evidence": True,
            "inv_forbids_todo": True,
            "lifecycle_stable_states_forbid_todo": True,
        },
        "generation_readiness": generation_readiness,
    }

    json.dump(payload, sys.stdout, ensure_ascii=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

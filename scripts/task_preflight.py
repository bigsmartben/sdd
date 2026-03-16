#!/usr/bin/env python3
"""Extract a compact task-generation bootstrap packet from plan.md.

This script precomputes the minimum control-plane inventory needed by
`/sdd.tasks` so the model can consume a small JSON packet instead of
re-reading and re-joining `plan.md` tables during task generation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SECTION_HEADINGS = (
    "Shared Context Snapshot",
    "Stage Queue",
    "Binding Projection Index",
    "Artifact Status",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract compact tasks bootstrap packet from plan.md")
    parser.add_argument("--feature-dir", required=True, help="Absolute or repo-relative feature directory")
    parser.add_argument("--plan", required=True, help="Path to plan.md")
    parser.add_argument("--spec", required=True, help="Path to spec.md")
    parser.add_argument("--data-model", required=True, help="Path to data-model.md")
    parser.add_argument("--test-matrix", required=True, help="Path to test-matrix.md")
    parser.add_argument("--contracts-dir", required=True, help="Path to contracts directory")
    parser.add_argument("--interface-details-dir", required=True, help="Path to interface-details directory")
    return parser.parse_args(argv)


def clean_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def split_csv_cell(value: str) -> list[str]:
    text = clean_cell(value)
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


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

    headers = [clean_cell(cell) for cell in table_lines[0].strip().strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [clean_cell(cell) for cell in line.strip().strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        row = {header: cell for header, cell in zip(headers, cells)}
        if any(value for value in row.values()):
            rows.append(row)
    return rows


def resolve_target_path(feature_dir: Path, raw_path: str) -> str:
    normalized = clean_cell(raw_path)
    if not normalized:
        return ""
    candidate = Path(normalized)
    if candidate.is_absolute():
        return str(candidate)
    return str((feature_dir / candidate).resolve())


def summarize_status_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    summary: dict[str, Counter[str]] = {}
    for row in rows:
        unit_type = clean_cell(row.get("Unit Type", "unknown")) or "unknown"
        status = clean_cell(row.get("Status", "unknown")) or "unknown"
        summary.setdefault(unit_type, Counter())
        summary[unit_type][status] += 1
    return {unit_type: dict(counter) for unit_type, counter in summary.items()}


def build_unit_inventory(
    binding_rows: list[dict[str, str]],
    artifact_rows: list[dict[str, str]],
    feature_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    artifacts_by_binding: dict[str, dict[str, dict[str, str]]] = {}
    for row in artifact_rows:
        binding_row_id = clean_cell(row.get("BindingRowID", ""))
        unit_type = clean_cell(row.get("Unit Type", ""))
        if not binding_row_id or not unit_type:
            continue
        artifacts_by_binding.setdefault(binding_row_id, {})[unit_type] = row

    unit_inventory: list[dict[str, Any]] = []
    ready_unit_inventory: list[dict[str, Any]] = []

    for row in binding_rows:
        binding_row_id = clean_cell(row.get("BindingRowID", ""))
        contract_row = artifacts_by_binding.get(binding_row_id, {}).get("contract", {})
        interface_detail_row = artifacts_by_binding.get(binding_row_id, {}).get("interface-detail", {})
        contract_target_path_abs = resolve_target_path(feature_dir, contract_row.get("Target Path", ""))
        interface_detail_target_path_abs = resolve_target_path(feature_dir, interface_detail_row.get("Target Path", ""))
        contract_exists = bool(contract_target_path_abs) and Path(contract_target_path_abs).is_file()
        interface_detail_exists = bool(interface_detail_target_path_abs) and Path(interface_detail_target_path_abs).is_file()

        unit = {
            "binding_row_id": binding_row_id,
            "if_scope": clean_cell(row.get("IF ID / IF Scope", "")),
            "operation_id": clean_cell(row.get("Operation ID", "")),
            "tm_id": clean_cell(row.get("TM ID", "")),
            "tc_ids": split_csv_cell(row.get("TC IDs", "")),
            "boundary_anchor": clean_cell(row.get("Boundary Anchor", "")),
            "contract": {
                "status": clean_cell(contract_row.get("Status", "")),
                "target_path": clean_cell(contract_row.get("Target Path", "")),
                "target_path_abs": contract_target_path_abs,
                "exists": contract_exists,
            },
            "interface_detail": {
                "status": clean_cell(interface_detail_row.get("Status", "")),
                "target_path": clean_cell(interface_detail_row.get("Target Path", "")),
                "target_path_abs": interface_detail_target_path_abs,
                "exists": interface_detail_exists,
            },
        }
        unit_inventory.append(unit)

        if (
            unit["contract"]["status"] == "done"
            and unit["interface_detail"]["status"] == "done"
            and contract_exists
            and interface_detail_exists
        ):
            ready_unit_inventory.append(unit)

    return unit_inventory, ready_unit_inventory


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    feature_dir = Path(args.feature_dir).resolve()
    plan_path = Path(args.plan).resolve()
    spec_path = Path(args.spec).resolve()
    data_model_path = Path(args.data_model).resolve()
    test_matrix_path = Path(args.test_matrix).resolve()
    contracts_dir = Path(args.contracts_dir).resolve()
    interface_details_dir = Path(args.interface_details_dir).resolve()

    if not plan_path.is_file():
        print(f"ERROR: plan.md not found: {plan_path}", file=sys.stderr)
        return 1

    document = plan_path.read_text(encoding="utf-8")
    sections = {heading: extract_section(document, heading) for heading in SECTION_HEADINGS}
    required_sections = {
        "shared_context_snapshot": sections["Shared Context Snapshot"] is not None,
        "stage_queue": sections["Stage Queue"] is not None,
        "binding_projection_index": sections["Binding Projection Index"] is not None,
        "artifact_status": sections["Artifact Status"] is not None,
    }
    missing_sections = [name for name, present in required_sections.items() if not present]

    stage_rows = parse_markdown_table(sections["Stage Queue"])
    binding_rows = parse_markdown_table(sections["Binding Projection Index"])
    artifact_rows = parse_markdown_table(sections["Artifact Status"])

    stage_queue = [
        {
            "stage_id": clean_cell(row.get("Stage ID", "")),
            "status": clean_cell(row.get("Status", "")),
            "output_path": clean_cell(row.get("Output Path", "")),
            "output_path_abs": resolve_target_path(feature_dir, row.get("Output Path", "")),
        }
        for row in stage_rows
    ]

    incomplete_stage_ids = [row["stage_id"] for row in stage_queue if row["status"] != "done"]

    binding_projection_index = [
        {
            "binding_row_id": clean_cell(row.get("BindingRowID", "")),
            "if_scope": clean_cell(row.get("IF ID / IF Scope", "")),
            "operation_id": clean_cell(row.get("Operation ID", "")),
            "tm_id": clean_cell(row.get("TM ID", "")),
            "tc_ids": split_csv_cell(row.get("TC IDs", "")),
            "boundary_anchor": clean_cell(row.get("Boundary Anchor", "")),
        }
        for row in binding_rows
    ]

    artifact_status = [
        {
            "binding_row_id": clean_cell(row.get("BindingRowID", "")),
            "unit_type": clean_cell(row.get("Unit Type", "")),
            "target_path": clean_cell(row.get("Target Path", "")),
            "target_path_abs": resolve_target_path(feature_dir, row.get("Target Path", "")),
            "status": clean_cell(row.get("Status", "")),
        }
        for row in artifact_rows
    ]

    unit_inventory, ready_unit_inventory = build_unit_inventory(binding_rows, artifact_rows, feature_dir)

    payload = {
        "feature_dir": str(feature_dir),
        "plan_path": str(plan_path),
        "spec_path": str(spec_path),
        "data_model_path": str(data_model_path),
        "test_matrix_path": str(test_matrix_path),
        "contracts_dir": str(contracts_dir),
        "interface_details_dir": str(interface_details_dir),
        "required_sections": required_sections,
        "missing_sections": missing_sections,
        "stage_queue": stage_queue,
        "incomplete_stage_ids": incomplete_stage_ids,
        "binding_row_count": len(binding_projection_index),
        "binding_projection_index": binding_projection_index,
        "artifact_status": artifact_status,
        "artifact_status_summary": summarize_status_rows(artifact_rows),
        "unit_inventory": unit_inventory,
        "ready_unit_inventory": ready_unit_inventory,
    }

    json.dump(payload, sys.stdout, ensure_ascii=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

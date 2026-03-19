#!/usr/bin/env python3
"""Extract a compact task-generation bootstrap packet from plan.md."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SECTION_HEADINGS = (
    "Summary",
    "Shared Context Snapshot",
    "Stage Queue",
    "Binding Projection Index",
    "Artifact Status",
    "Handoff Protocol",
)

BOOTSTRAP_SCHEMA_VERSION = "1.4"
PLACEHOLDER_TOKEN_RE = re.compile(r"^\[[^\]]+\]$")
UNRESOLVED_CONTRACT_NAME_RE = re.compile(r"<([A-Z][A-Za-z0-9]+)>")
TASK_REQUIRED_STAGE_IDS = {"research", "test-matrix", "data-model"}


def is_placeholder_token(value: str) -> bool:
    return bool(PLACEHOLDER_TOKEN_RE.fullmatch(clean_cell(value)))


def inspect_contract_artifact(contract_path_abs: str) -> dict[str, Any]:
    inspection = {
        "full_field_dictionary_present": False,
        "field_dictionary_tier_present": False,
        "test_projection_section_present": False,
        "closure_check_section_present": False,
        "interface_definition_closure_check_present": False,
        "uml_closure_check_present": False,
        "sequence_closure_check_present": False,
        "test_closure_check_present": False,
        "has_unresolved_field_gaps": False,
        "placeholder_names_present": False,
        "placeholder_names": [],
    }
    if not contract_path_abs or not Path(contract_path_abs).is_file():
        return inspection

    content = Path(contract_path_abs).read_text(encoding="utf-8")
    inspection["full_field_dictionary_present"] = "## Full Field Dictionary (Operation-scoped)" in content
    inspection["field_dictionary_tier_present"] = re.search(
        r"(?i)^\|\s*Field\s*\|\s*Owner\s+Class\s*\|\s*Dictionary\s+Tier\s*\|",
        content,
        flags=re.MULTILINE,
    ) is not None
    inspection["test_projection_section_present"] = "## Test Projection" in content
    inspection["closure_check_section_present"] = "## Closure Check" in content
    inspection["interface_definition_closure_check_present"] = "| Interface-definition closure |" in content
    inspection["uml_closure_check_present"] = "| UML closure |" in content
    inspection["sequence_closure_check_present"] = "| Sequence closure |" in content
    inspection["test_closure_check_present"] = "| Test closure |" in content
    inspection["has_unresolved_field_gaps"] = "TODO(REPO_ANCHOR)" in content or re.search(
        r"(?i)\|\s*gap\s*\|",
        content,
    ) is not None
    placeholder_names = sorted(set(UNRESOLVED_CONTRACT_NAME_RE.findall(content)))
    inspection["placeholder_names_present"] = bool(placeholder_names)
    inspection["placeholder_names"] = placeholder_names
    return inspection


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract compact tasks bootstrap packet from plan.md")
    parser.add_argument("--feature-dir", required=True, help="Absolute or repo-relative feature directory")
    parser.add_argument("--plan", required=True, help="Path to plan.md")
    parser.add_argument("--spec", required=True, help="Path to spec.md")
    parser.add_argument("--data-model", required=True, help="Path to data-model.md")
    parser.add_argument("--test-matrix", required=True, help="Path to test-matrix.md")
    parser.add_argument("--contracts-dir", required=True, help="Path to contracts directory")
    return parser.parse_args(argv)


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


def split_csv_cell(value: str) -> list[str]:
    text = clean_cell(value)
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def split_ref_cell(value: str) -> list[str]:
    return split_csv_cell(value)


def extract_section(document: str, heading: str) -> str | None:
    pattern = rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, document, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()


def is_active_status(status: str) -> bool:
    return clean_cell(status).lower() != "done"


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
        if cells and is_placeholder_token(cells[0]):
            continue
        if any(value for value in row.values()):
            rows.append(row)
    return rows


def load_binding_contract_packets(test_matrix_path: Path) -> dict[str, dict[str, Any]]:
    if not test_matrix_path.is_file():
        return {}

    document = test_matrix_path.read_text(encoding="utf-8")
    packet_rows = parse_markdown_table(extract_section(document, "Binding Contract Packets"))
    packets: dict[str, dict[str, Any]] = {}
    for row in packet_rows:
        binding_row_id = clean_cell(row.get("BindingRowID", ""))
        if not binding_row_id:
            continue
        packets[binding_row_id] = {
            "binding_row_id": binding_row_id,
            "operation_id": clean_cell(row.get("Operation ID", "")),
            "if_scope": clean_cell(row.get("IF Scope", "")),
            "uif_path_refs": split_ref_cell(row.get("UIF Path Ref(s)", "")),
            "udd_refs": split_ref_cell(row.get("UDD Ref(s)", "")),
            "tm_id": clean_cell(row.get("TM ID", "")),
            "tc_ids": split_ref_cell(row.get("TC IDs", "")),
            "test_scope": clean_cell(row.get("Test Scope", "")),
            "spec_refs": split_ref_cell(row.get("Spec Ref(s)", "")),
            "scenario_refs": split_ref_cell(row.get("Scenario Ref(s)", "")),
            "success_refs": split_ref_cell(row.get("Success Ref(s)", "")),
            "edge_refs": split_ref_cell(row.get("Edge Ref(s)", "")),
        }
    return packets


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


def summarize_stage_queue(stage_queue: list[dict[str, str]]) -> dict[str, int]:
    status_counts: Counter[str] = Counter()
    for row in stage_queue:
        status_counts[clean_cell(row.get("status", "")) or "unknown"] += 1
    return dict(status_counts)


def normalize_stage_ids(stage_ids: list[str]) -> list[str]:
    normalized = [stage_id for stage_id in stage_ids if stage_id]
    return sorted(dict.fromkeys(normalized))


def build_execution_readiness(
    *,
    missing_sections: list[str],
    incomplete_stage_ids: list[str],
    binding_projection_index: list[dict[str, Any]],
    artifact_status: list[dict[str, Any]],
    unit_inventory: list[dict[str, Any]],
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if missing_sections:
        errors.append(
            {
                "code": "missing_required_sections",
                "message": "plan.md is missing required control-plane sections.",
                "details": {"sections": missing_sections},
            }
        )

    if incomplete_stage_ids:
        errors.append(
            {
                "code": "incomplete_stage_queue",
                "message": "Stage Queue contains non-done rows required before /sdd.tasks.",
                "details": {"stage_ids": incomplete_stage_ids},
            }
        )

    if not binding_projection_index:
        errors.append(
            {
                "code": "empty_binding_projection_index",
                "message": "Binding Projection Index has no consumable rows.",
                "details": {},
            }
        )

    binding_projection_missing_required_fields = sorted(
        [
            {"binding_row_id": unit["binding_row_id"], "fields": unit["missing_binding_projection_fields"]}
            for unit in unit_inventory
            if unit["missing_binding_projection_fields"]
        ],
        key=lambda item: item["binding_row_id"],
    )
    if binding_projection_missing_required_fields:
        errors.append(
            {
                "code": "binding_projection_missing_required_fields",
                "message": "Some binding rows are missing required binding-projection fields.",
                "details": {"rows": binding_projection_missing_required_fields},
            }
        )

    missing_binding_packet_rows = sorted(
        [unit["binding_row_id"] for unit in unit_inventory if not unit["binding_packet"]["present"]]
    )
    if missing_binding_packet_rows:
        warnings.append(
            {
                "code": "missing_binding_contract_packet",
                "message": "Some binding rows have no matching Binding Contract Packet in test-matrix.md.",
                "details": {"binding_row_ids": missing_binding_packet_rows},
            }
        )

    incomplete_binding_packet_rows = sorted(
        [
            {"binding_row_id": unit["binding_row_id"], "fields": unit["missing_binding_packet_fields"]}
            for unit in unit_inventory
            if unit["binding_packet"]["present"] and unit["missing_binding_packet_fields"]
        ],
        key=lambda item: item["binding_row_id"],
    )
    if incomplete_binding_packet_rows:
        warnings.append(
            {
                "code": "binding_contract_packet_missing_required_fields",
                "message": "Some binding packets are missing required minimal projection fields.",
                "details": {"rows": incomplete_binding_packet_rows},
            }
        )

    binding_projection_packet_drift_rows = sorted(
        [
            unit["binding_row_id"]
            for unit in unit_inventory
            if unit["binding_packet"]["present"] and unit["binding_packet"]["has_projection_drift"]
        ]
    )
    if binding_projection_packet_drift_rows:
        errors.append(
            {
                "code": "binding_projection_packet_drift",
                "message": "Some binding rows drift from their authoritative Binding Contract Packets.",
                "details": {"binding_row_ids": binding_projection_packet_drift_rows},
            }
        )

    contract_rows = [row for row in artifact_status if row.get("unit_type") == "contract"]
    if not contract_rows:
        errors.append(
            {
                "code": "missing_contract_artifact_rows",
                "message": "Artifact Status has no contract rows.",
                "details": {},
            }
        )

    missing_contract_rows = sorted(
        [
            unit["binding_row_id"]
            for unit in unit_inventory
            if not unit["contract"]["status"] and not unit["contract"]["target_path"]
        ]
    )
    if missing_contract_rows:
        errors.append(
            {
                "code": "missing_contract_for_binding_rows",
                "message": "Some binding rows have no contract artifact status row.",
                "details": {"binding_row_ids": missing_contract_rows},
            }
        )

    contract_target_path_missing_rows = sorted(
        [
            unit["binding_row_id"]
            for unit in unit_inventory
            if unit["contract"]["status"] and not unit["contract"]["target_path"]
        ]
    )
    if contract_target_path_missing_rows:
        errors.append(
            {
                "code": "contract_target_path_missing",
                "message": "Some contract rows have status but no target path.",
                "details": {"binding_row_ids": contract_target_path_missing_rows},
            }
        )

    non_done_contract_rows = sorted(
        [
            unit["binding_row_id"]
            for unit in unit_inventory
            if unit["contract"]["target_path"] and unit["contract"]["status"] != "done"
        ]
    )
    if non_done_contract_rows:
        errors.append(
            {
                "code": "contract_rows_not_done",
                "message": "Some contract rows are not done.",
                "details": {"binding_row_ids": non_done_contract_rows},
            }
        )

    done_contract_missing_files = sorted(
        [
            unit["binding_row_id"]
            for unit in unit_inventory
            if unit["contract"]["status"] == "done" and not unit["contract"]["exists"]
        ]
    )
    if done_contract_missing_files:
        errors.append(
            {
                "code": "done_contract_target_missing",
                "message": "Some done contract rows point to files that do not exist.",
                "details": {"binding_row_ids": done_contract_missing_files},
            }
        )

    placeholder_names_present_rows = sorted(
        [
            {"binding_row_id": unit["binding_row_id"], "placeholder_names": unit["contract"]["placeholder_names"]}
            for unit in unit_inventory
            if unit["contract"]["status"] == "done"
            and unit["contract"]["exists"]
            and unit["contract"]["placeholder_names_present"]
        ],
        key=lambda item: item["binding_row_id"],
    )
    if placeholder_names_present_rows:
        errors.append(
            {
                "code": "contract_placeholder_names_present",
                "message": "Some done contract rows still contain unresolved placeholder class/type names.",
                "details": {"rows": placeholder_names_present_rows},
            }
        )

    missing_field_dictionary_rows = sorted(
        [
            unit["binding_row_id"]
            for unit in unit_inventory
            if unit["contract"]["status"] == "done"
            and unit["contract"]["exists"]
            and not unit["contract"]["full_field_dictionary_present"]
        ]
    )
    if missing_field_dictionary_rows:
        errors.append(
            {
                "code": "full_field_dictionary_missing",
                "message": "Some done contract rows are missing `Full Field Dictionary (Operation-scoped)`.",
                "details": {"binding_row_ids": missing_field_dictionary_rows},
            }
        )

    missing_field_dictionary_tier_rows = sorted(
        [
            unit["binding_row_id"]
            for unit in unit_inventory
            if unit["contract"]["status"] == "done"
            and unit["contract"]["exists"]
            and not unit["contract"]["field_dictionary_tier_present"]
        ]
    )
    if missing_field_dictionary_tier_rows:
        warnings.append(
            {
                "code": "field_dictionary_tier_missing",
                "message": "Some done contract rows are missing `Dictionary Tier` in `Full Field Dictionary (Operation-scoped)`.",
                "details": {"binding_row_ids": missing_field_dictionary_tier_rows},
            }
        )

    missing_test_projection_section_rows = sorted(
        [
            unit["binding_row_id"]
            for unit in unit_inventory
            if unit["contract"]["status"] == "done"
            and unit["contract"]["exists"]
            and not unit["contract"]["test_projection_section_present"]
        ]
    )
    if missing_test_projection_section_rows:
        warnings.append(
            {
                "code": "test_projection_section_missing",
                "message": "Some done contract rows are missing `Test Projection`.",
                "details": {"binding_row_ids": missing_test_projection_section_rows},
            }
        )

    missing_closure_check_section_rows = sorted(
        [
            unit["binding_row_id"]
            for unit in unit_inventory
            if unit["contract"]["status"] == "done"
            and unit["contract"]["exists"]
            and not unit["contract"]["closure_check_section_present"]
        ]
    )
    if missing_closure_check_section_rows:
        warnings.append(
            {
                "code": "closure_check_section_missing",
                "message": "Some done contract rows are missing `Closure Check`.",
                "details": {"binding_row_ids": missing_closure_check_section_rows},
            }
        )

    missing_closure_check_rows = sorted(
        [
            {
                "binding_row_id": unit["binding_row_id"],
                "checks": [
                    check_name
                    for check_name, check_present in (
                        ("interface_definition_closure", unit["contract"]["interface_definition_closure_check_present"]),
                        ("uml_closure", unit["contract"]["uml_closure_check_present"]),
                        ("sequence_closure", unit["contract"]["sequence_closure_check_present"]),
                        ("test_closure", unit["contract"]["test_closure_check_present"]),
                    )
                    if not check_present
                ],
            }
            for unit in unit_inventory
            if unit["contract"]["status"] == "done"
            and unit["contract"]["exists"]
            and (
                not unit["contract"]["interface_definition_closure_check_present"]
                or not unit["contract"]["uml_closure_check_present"]
                or not unit["contract"]["sequence_closure_check_present"]
                or not unit["contract"]["test_closure_check_present"]
            )
        ],
        key=lambda item: item["binding_row_id"],
    )
    if missing_closure_check_rows:
        warnings.append(
            {
                "code": "closure_check_rows_missing",
                "message": "Some done contract rows are missing one or more required `Closure Check` rows.",
                "details": {"rows": missing_closure_check_rows},
            }
        )

    unresolved_field_gap_rows = sorted(
        [
            unit["binding_row_id"]
            for unit in unit_inventory
            if unit["contract"]["status"] == "done"
            and unit["contract"]["exists"]
            and unit["contract"]["has_unresolved_field_gaps"]
        ]
    )
    if unresolved_field_gap_rows:
        warnings.append(
            {
                "code": "contract_field_gap_unresolved",
                "message": "Some done contract rows still carry unresolved field-level gaps.",
                "details": {"binding_row_ids": unresolved_field_gap_rows},
            }
        )

    known_binding_ids = {row["binding_row_id"] for row in binding_projection_index if row.get("binding_row_id")}
    orphan_contract_rows = sorted(
        [
            row["binding_row_id"]
            for row in contract_rows
            if row.get("binding_row_id") and row["binding_row_id"] not in known_binding_ids
        ]
    )
    if orphan_contract_rows:
        warnings.append(
            {
                "code": "orphan_contract_artifact_rows",
                "message": "Some contract rows do not map to Binding Projection Index rows.",
                "details": {"binding_row_ids": orphan_contract_rows},
            }
        )

    return {
        "ready_for_task_generation": len(errors) == 0,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def build_unit_inventory(
    binding_rows: list[dict[str, str]],
    artifact_rows: list[dict[str, str]],
    feature_dir: Path,
    binding_packets: dict[str, dict[str, Any]],
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
        contract_target_path_abs = resolve_target_path(feature_dir, contract_row.get("Target Path", ""))
        contract_exists = bool(contract_target_path_abs) and Path(contract_target_path_abs).is_file()
        contract_inspection = inspect_contract_artifact(contract_target_path_abs)

        uc_id = clean_cell(row.get("UC ID", ""))
        uif_id = clean_cell(row.get("UIF ID", ""))
        fr_id = clean_cell(row.get("FR ID", ""))
        if_scope = clean_cell(row.get("IF ID / IF Scope", ""))
        tm_id = clean_cell(row.get("TM ID", ""))
        tc_ids = split_ref_cell(row.get("TC IDs", ""))
        operation_id = clean_cell(row.get("Operation ID", ""))
        uif_path_refs = split_ref_cell(row.get("UIF Path Ref(s)", ""))
        udd_refs = split_ref_cell(row.get("UDD Ref(s)", ""))
        test_scope = clean_cell(row.get("Test Scope", ""))
        packet = binding_packets.get(binding_row_id, {})

        missing_binding_projection_fields = [
            field_name
            for field_name, field_value in (
                ("UC ID", uc_id),
                ("UIF ID", uif_id),
                ("FR ID", fr_id),
                ("IF ID / IF Scope", if_scope),
                ("TM ID", tm_id),
                ("TC IDs", tc_ids),
                ("Operation ID", operation_id),
                ("UIF Path Ref(s)", uif_path_refs),
                ("UDD Ref(s)", udd_refs),
                ("Test Scope", test_scope),
            )
            if not field_value
        ]

        missing_binding_packet_fields = []
        if packet:
            for field_name, field_value in (
                ("Operation ID", packet.get("operation_id", "")),
                ("IF Scope", packet.get("if_scope", "")),
                ("UIF Path Ref(s)", packet.get("uif_path_refs", [])),
                ("UDD Ref(s)", packet.get("udd_refs", [])),
                ("TM ID", packet.get("tm_id", "")),
                ("TC IDs", packet.get("tc_ids", [])),
                ("Test Scope", packet.get("test_scope", "")),
                ("Spec Ref(s)", packet.get("spec_refs", [])),
                ("Scenario Ref(s)", packet.get("scenario_refs", [])),
                ("Success Ref(s)", packet.get("success_refs", [])),
                ("Edge Ref(s)", packet.get("edge_refs", [])),
            ):
                if not field_value:
                    missing_binding_packet_fields.append(field_name)

        has_projection_drift = bool(packet) and any(
            (
                operation_id != packet.get("operation_id", ""),
                if_scope != packet.get("if_scope", ""),
                tm_id != packet.get("tm_id", ""),
                tc_ids != packet.get("tc_ids", []),
                uif_path_refs != packet.get("uif_path_refs", []),
                udd_refs != packet.get("udd_refs", []),
                test_scope != packet.get("test_scope", ""),
            )
        )

        unit = {
            "binding_row_id": binding_row_id,
            "uc_id": uc_id,
            "uif_id": uif_id,
            "fr_id": fr_id,
            "if_scope": if_scope,
            "operation_id": operation_id,
            "tm_id": tm_id,
            "tc_ids": tc_ids,
            "uif_path_refs": uif_path_refs,
            "udd_refs": udd_refs,
            "test_scope": test_scope,
            "missing_binding_projection_fields": missing_binding_projection_fields,
            "missing_binding_packet_fields": missing_binding_packet_fields,
            "binding_packet": {
                "present": bool(packet),
                "operation_id": packet.get("operation_id", ""),
                "if_scope": packet.get("if_scope", ""),
                "uif_path_refs": packet.get("uif_path_refs", []),
                "udd_refs": packet.get("udd_refs", []),
                "tm_id": packet.get("tm_id", ""),
                "tc_ids": packet.get("tc_ids", []),
                "test_scope": packet.get("test_scope", ""),
                "spec_refs": packet.get("spec_refs", []),
                "scenario_refs": packet.get("scenario_refs", []),
                "success_refs": packet.get("success_refs", []),
                "edge_refs": packet.get("edge_refs", []),
                "has_projection_drift": has_projection_drift,
            },
            "contract": {
                "status": clean_cell(contract_row.get("Status", "")),
                "target_path": clean_cell(contract_row.get("Target Path", "")),
                "target_path_abs": contract_target_path_abs,
                "exists": contract_exists,
                "full_field_dictionary_present": contract_inspection["full_field_dictionary_present"],
                "field_dictionary_tier_present": contract_inspection["field_dictionary_tier_present"],
                "test_projection_section_present": contract_inspection["test_projection_section_present"],
                "closure_check_section_present": contract_inspection["closure_check_section_present"],
                "interface_definition_closure_check_present": contract_inspection[
                    "interface_definition_closure_check_present"
                ],
                "uml_closure_check_present": contract_inspection["uml_closure_check_present"],
                "sequence_closure_check_present": contract_inspection["sequence_closure_check_present"],
                "test_closure_check_present": contract_inspection["test_closure_check_present"],
                "has_unresolved_field_gaps": contract_inspection["has_unresolved_field_gaps"],
                "placeholder_names_present": contract_inspection["placeholder_names_present"],
                "placeholder_names": contract_inspection["placeholder_names"],
            },
        }
        unit_inventory.append(unit)

        if (
            not missing_binding_projection_fields
            and packet
            and not missing_binding_packet_fields
            and not has_projection_drift
            and unit["contract"]["status"] == "done"
            and contract_exists
            and unit["contract"]["full_field_dictionary_present"]
            and unit["contract"]["field_dictionary_tier_present"]
            and unit["contract"]["test_projection_section_present"]
            and unit["contract"]["closure_check_section_present"]
            and unit["contract"]["interface_definition_closure_check_present"]
            and unit["contract"]["uml_closure_check_present"]
            and unit["contract"]["sequence_closure_check_present"]
            and unit["contract"]["test_closure_check_present"]
            and not unit["contract"]["has_unresolved_field_gaps"]
            and not unit["contract"]["placeholder_names_present"]
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

    if not plan_path.is_file():
        print(f"ERROR: plan.md not found: {plan_path}", file=sys.stderr)
        return 1

    document = plan_path.read_text(encoding="utf-8")
    sections = {heading: extract_section(document, heading) for heading in SECTION_HEADINGS}
    required_sections = {
        "summary": sections["Summary"] is not None,
        "shared_context_snapshot": sections["Shared Context Snapshot"] is not None,
        "stage_queue": sections["Stage Queue"] is not None,
        "binding_projection_index": sections["Binding Projection Index"] is not None,
        "artifact_status": sections["Artifact Status"] is not None,
        "handoff_protocol": sections["Handoff Protocol"] is not None,
    }
    missing_sections = [name for name, present in required_sections.items() if not present]

    stage_rows = parse_markdown_table(sections["Stage Queue"])
    binding_rows = parse_markdown_table(sections["Binding Projection Index"])
    artifact_rows = parse_markdown_table(sections["Artifact Status"])
    binding_packets = load_binding_contract_packets(test_matrix_path)

    stage_queue = [
        {
            "stage_id": clean_cell(row.get("Stage ID", "")),
            "status": clean_cell(row.get("Status", "")),
            "output_path": clean_cell(row.get("Output Path", "")),
            "output_path_abs": resolve_target_path(feature_dir, row.get("Output Path", "")),
            "blocker": clean_cell(row.get("Blocker", "")),
        }
        for row in stage_rows
    ]

    binding_projection_index = [
        {
            "binding_row_id": clean_cell(row.get("BindingRowID", "")),
            "uc_id": clean_cell(row.get("UC ID", "")),
            "uif_id": clean_cell(row.get("UIF ID", "")),
            "fr_id": clean_cell(row.get("FR ID", "")),
            "if_scope": clean_cell(row.get("IF ID / IF Scope", "")),
            "tm_id": clean_cell(row.get("TM ID", "")),
            "tc_ids": split_ref_cell(row.get("TC IDs", "")),
            "operation_id": clean_cell(row.get("Operation ID", "")),
            "uif_path_refs": split_ref_cell(row.get("UIF Path Ref(s)", "")),
            "udd_refs": split_ref_cell(row.get("UDD Ref(s)", "")),
            "test_scope": clean_cell(row.get("Test Scope", "")),
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
            "blocker": clean_cell(row.get("Blocker", "")),
        }
        for row in artifact_rows
    ]

    required_stage_ids = set(TASK_REQUIRED_STAGE_IDS)
    data_model_required = "data-model" in required_stage_ids

    incomplete_stage_ids = normalize_stage_ids(
        [
            row["stage_id"]
            for row in stage_queue
            if is_active_status(row.get("status", "")) and row["stage_id"] in required_stage_ids
        ]
    )

    unit_inventory, ready_unit_inventory = build_unit_inventory(
        binding_rows,
        artifact_rows,
        feature_dir,
        binding_packets,
    )
    execution_readiness = build_execution_readiness(
        missing_sections=missing_sections,
        incomplete_stage_ids=incomplete_stage_ids,
        binding_projection_index=binding_projection_index,
        artifact_status=artifact_status,
        unit_inventory=unit_inventory,
    )

    payload = {
        "schema_version": BOOTSTRAP_SCHEMA_VERSION,
        "feature_dir": str(feature_dir),
        "plan_path": str(plan_path),
        "spec_path": str(spec_path),
        "data_model_path": str(data_model_path),
        "test_matrix_path": str(test_matrix_path),
        "contracts_dir": str(contracts_dir),
        "required_sections": required_sections,
        "missing_sections": missing_sections,
        "stage_queue": stage_queue,
        "stage_queue_status_summary": summarize_stage_queue(stage_queue),
        "data_model_required": data_model_required,
        "required_stage_ids_for_tasks": sorted(required_stage_ids),
        "incomplete_stage_ids": incomplete_stage_ids,
        "binding_row_count": len(binding_projection_index),
        "binding_projection_index": binding_projection_index,
        "binding_contract_packet_count": len(binding_packets),
        "artifact_status": artifact_status,
        "artifact_status_summary": summarize_status_rows(artifact_rows),
        "unit_inventory": unit_inventory,
        "ready_unit_inventory": ready_unit_inventory,
        "execution_readiness": execution_readiness,
    }

    json.dump(payload, sys.stdout, ensure_ascii=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Packaged task bootstrap extractor."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from specify_cli.runtime_common import (
    clean_cell,
    extract_section,
    normalize_stage_ids,
    parse_markdown_table,
    resolve_target_path,
    split_csv_cell,
    summarize_stage_queue,
    summarize_status_rows,
)


TASK_BOOTSTRAP_SCHEMA_VERSION = "1.2"
TASK_SECTION_HEADINGS = (
    "Shared Context Snapshot",
    "Stage Queue",
    "Binding Projection Index",
    "Artifact Status",
)
ENTRY_ANCHOR_LABEL_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?\*\*Implementation[ _-]*Entry[ _-]*Anchor(?:\s*\([^)]*\))?\*\*:\s*(.+?)\s*$"
)
NON_CONTROLLER_ENTRY_RE = re.compile(r"(?i)(service|facade|manager|repository|dao|mapper)")
ANCHOR_STATUS_VALUES = {"existing", "extended", "new", "todo"}
UNRESOLVED_CONTRACT_NAME_RE = re.compile(r"<([A-Z][A-Za-z0-9]+)>")
TASK_REQUIRED_STAGE_IDS = {"research", "test-matrix", "data-model"}


def normalize_anchor_status(value: str) -> str:
    return clean_cell(value).lower()


def has_required_strategy_evidence(value: str) -> bool:
    text = clean_cell(value).lower()
    return "existing" in text and "extended" in text


def is_active_status(status: str) -> bool:
    return clean_cell(status).lower() != "done"


def load_binding_contract_packets(test_matrix_path: Path) -> dict[str, dict[str, str]]:
    if not test_matrix_path.is_file():
        return {}

    document = test_matrix_path.read_text(encoding="utf-8")
    packet_rows = parse_markdown_table(
        extract_section(document, "Binding Contract Packets"),
        filter_placeholder_first_cell=True,
    )
    packets: dict[str, dict[str, str]] = {}
    for row in packet_rows:
        binding_row_id = clean_cell(row.get("BindingRowID", ""))
        if not binding_row_id:
            continue
        packets[binding_row_id] = {
            "binding_row_id": binding_row_id,
            "boundary_anchor": clean_cell(row.get("Boundary Anchor", "")),
            "boundary_anchor_status": normalize_anchor_status(row.get("Boundary Anchor Status", "")),
            "implementation_entry_anchor": clean_cell(row.get("Implementation Entry Anchor", "")),
            "implementation_entry_anchor_status": normalize_anchor_status(
                row.get("Implementation Entry Anchor Status", "")
            ),
            "boundary_anchor_strategy_evidence": clean_cell(row.get("Boundary Anchor Strategy Evidence", "")),
            "implementation_entry_anchor_strategy_evidence": clean_cell(
                row.get("Implementation Entry Anchor Strategy Evidence", "")
            ),
        }
    return packets


def inspect_contract_artifact(contract_path_abs: str, boundary_anchor: str) -> dict[str, Any]:
    inspection = {
        "full_field_dictionary_present": False,
        "has_unresolved_field_gaps": False,
        "controller_first_violation": False,
        "placeholder_names_present": False,
        "placeholder_names": [],
    }
    if not contract_path_abs or not Path(contract_path_abs).is_file():
        return inspection

    content = Path(contract_path_abs).read_text(encoding="utf-8")
    inspection["full_field_dictionary_present"] = "## Full Field Dictionary (Operation-scoped)" in content
    inspection["has_unresolved_field_gaps"] = "TODO(REPO_ANCHOR)" in content or re.search(r"(?i)\|\s*gap\s*\|", content) is not None
    placeholder_names = sorted(set(UNRESOLVED_CONTRACT_NAME_RE.findall(content)))
    inspection["placeholder_names_present"] = bool(placeholder_names)
    inspection["placeholder_names"] = placeholder_names
    if boundary_anchor.startswith("HTTP "):
        entry_match = ENTRY_ANCHOR_LABEL_RE.search(content)
        entry_anchor = clean_cell(entry_match.group(1)) if entry_match else ""
        entry_anchor_lower = entry_anchor.lower()
        inspection["controller_first_violation"] = (
            entry_anchor_lower.startswith("http ")
            or (
                bool(NON_CONTROLLER_ENTRY_RE.search(entry_anchor_lower))
                and "controller" not in entry_anchor_lower
                and "todo(repo_anchor)" not in entry_anchor_lower
            )
        )
    return inspection


def build_unit_inventory(
    binding_rows: list[dict[str, str]],
    artifact_rows: list[dict[str, str]],
    feature_dir: Path,
    binding_packets: dict[str, dict[str, str]],
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
        contract_inspection = inspect_contract_artifact(contract_target_path_abs, clean_cell(row.get("Boundary Anchor", "")))
        boundary_anchor = clean_cell(row.get("Boundary Anchor", ""))
        implementation_entry_anchor = clean_cell(row.get("Implementation Entry Anchor", ""))
        boundary_anchor_status = normalize_anchor_status(row.get("Boundary Anchor Status", ""))
        implementation_entry_anchor_status = normalize_anchor_status(row.get("Implementation Entry Anchor Status", ""))
        test_scope = clean_cell(row.get("Test Scope", ""))
        packet = binding_packets.get(binding_row_id, {})

        missing_binding_projection_fields = [
            field_name
            for field_name, field_value in (
                ("IF ID / IF Scope", clean_cell(row.get("IF ID / IF Scope", ""))),
                ("TM ID", clean_cell(row.get("TM ID", ""))),
                ("TC IDs", clean_cell(row.get("TC IDs", ""))),
                ("Operation ID", clean_cell(row.get("Operation ID", ""))),
                ("Boundary Anchor", boundary_anchor),
                ("Implementation Entry Anchor", implementation_entry_anchor),
                ("Boundary Anchor Status", boundary_anchor_status),
                ("Implementation Entry Anchor Status", implementation_entry_anchor_status),
                ("Test Scope", test_scope),
            )
            if not field_value
        ]
        invalid_anchor_statuses = [
            field_name
            for field_name, field_value in (
                ("Boundary Anchor Status", boundary_anchor_status),
                ("Implementation Entry Anchor Status", implementation_entry_anchor_status),
            )
            if field_value and field_value not in ANCHOR_STATUS_VALUES
        ]
        tuple_drift_checks = (
            boundary_anchor != packet.get("boundary_anchor", ""),
            boundary_anchor_status != packet.get("boundary_anchor_status", ""),
            implementation_entry_anchor != packet.get("implementation_entry_anchor", ""),
            implementation_entry_anchor_status != packet.get("implementation_entry_anchor_status", ""),
        )
        missing_new_anchor_strategy_evidence = []
        if boundary_anchor_status == "new" and not has_required_strategy_evidence(packet.get("boundary_anchor_strategy_evidence", "")):
            missing_new_anchor_strategy_evidence.append("boundary_anchor")
        if implementation_entry_anchor_status == "new" and not has_required_strategy_evidence(
            packet.get("implementation_entry_anchor_strategy_evidence", "")
        ):
            missing_new_anchor_strategy_evidence.append("implementation_entry_anchor")

        unit = {
            "binding_row_id": binding_row_id,
            "if_scope": clean_cell(row.get("IF ID / IF Scope", "")),
            "operation_id": clean_cell(row.get("Operation ID", "")),
            "tm_id": clean_cell(row.get("TM ID", "")),
            "tc_ids": split_csv_cell(row.get("TC IDs", "")),
            "boundary_anchor": boundary_anchor,
            "implementation_entry_anchor": implementation_entry_anchor,
            "boundary_anchor_status": boundary_anchor_status,
            "implementation_entry_anchor_status": implementation_entry_anchor_status,
            "test_scope": test_scope,
            "missing_binding_projection_fields": missing_binding_projection_fields,
            "invalid_anchor_statuses": invalid_anchor_statuses,
            "missing_new_anchor_strategy_evidence": missing_new_anchor_strategy_evidence,
            "binding_packet": {
                "present": bool(packet),
                "boundary_anchor": packet.get("boundary_anchor", ""),
                "boundary_anchor_status": packet.get("boundary_anchor_status", ""),
                "implementation_entry_anchor": packet.get("implementation_entry_anchor", ""),
                "implementation_entry_anchor_status": packet.get("implementation_entry_anchor_status", ""),
                "boundary_anchor_strategy_evidence": packet.get("boundary_anchor_strategy_evidence", ""),
                "implementation_entry_anchor_strategy_evidence": packet.get("implementation_entry_anchor_strategy_evidence", ""),
                "has_tuple_drift": bool(packet) and any(tuple_drift_checks),
            },
            "contract": {
                "status": clean_cell(contract_row.get("Status", "")),
                "target_path": clean_cell(contract_row.get("Target Path", "")),
                "target_path_abs": contract_target_path_abs,
                "exists": contract_exists,
                "full_field_dictionary_present": contract_inspection["full_field_dictionary_present"],
                "has_unresolved_field_gaps": contract_inspection["has_unresolved_field_gaps"],
                "controller_first_violation": contract_inspection["controller_first_violation"],
                "placeholder_names_present": contract_inspection["placeholder_names_present"],
                "placeholder_names": contract_inspection["placeholder_names"],
            },
        }
        unit_inventory.append(unit)

        if (
            not missing_binding_projection_fields
            and not invalid_anchor_statuses
            and not missing_new_anchor_strategy_evidence
            and packet
            and not unit["binding_packet"]["has_tuple_drift"]
            and boundary_anchor_status != "todo"
            and implementation_entry_anchor_status != "todo"
            and unit["contract"]["status"] == "done"
            and contract_exists
            and unit["contract"]["full_field_dictionary_present"]
            and not unit["contract"]["has_unresolved_field_gaps"]
            and not unit["contract"]["controller_first_violation"]
            and not unit["contract"]["placeholder_names_present"]
        ):
            ready_unit_inventory.append(unit)

    return unit_inventory, ready_unit_inventory


def build_task_execution_readiness(
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
                "message": "Some binding rows are missing required tuple projection fields.",
                "details": {"rows": binding_projection_missing_required_fields},
            }
        )

    invalid_anchor_status_rows = sorted(
        [
            {"binding_row_id": unit["binding_row_id"], "statuses": unit["invalid_anchor_statuses"]}
            for unit in unit_inventory
            if unit["invalid_anchor_statuses"]
        ],
        key=lambda item: item["binding_row_id"],
    )
    if invalid_anchor_status_rows:
        errors.append(
            {
                "code": "invalid_anchor_status",
                "message": "Some binding rows use invalid anchor status values.",
                "details": {"rows": invalid_anchor_status_rows},
            }
        )

    todo_anchor_status_rows = sorted(
        [
            unit["binding_row_id"]
            for unit in unit_inventory
            if unit["boundary_anchor_status"] == "todo" or unit["implementation_entry_anchor_status"] == "todo"
        ]
    )
    if todo_anchor_status_rows:
        errors.append(
            {
                "code": "todo_anchor_status_blocker",
                "message": "Some binding rows still carry forward-looking todo anchor statuses.",
                "details": {"binding_row_ids": todo_anchor_status_rows},
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

    binding_projection_packet_drift_rows = sorted(
        [
            unit["binding_row_id"]
            for unit in unit_inventory
            if unit["binding_packet"]["present"] and unit["binding_packet"]["has_tuple_drift"]
        ]
    )
    if binding_projection_packet_drift_rows:
        warnings.append(
            {
                "code": "binding_projection_packet_drift",
                "message": "Some binding rows drift from their authoritative Binding Contract Packets.",
                "details": {"binding_row_ids": binding_projection_packet_drift_rows},
            }
        )

    new_anchor_strategy_evidence_missing_rows = sorted(
        [
            {"binding_row_id": unit["binding_row_id"], "anchors": unit["missing_new_anchor_strategy_evidence"]}
            for unit in unit_inventory
            if unit["missing_new_anchor_strategy_evidence"]
        ],
        key=lambda item: item["binding_row_id"],
    )
    if new_anchor_strategy_evidence_missing_rows:
        errors.append(
            {
                "code": "new_anchor_strategy_evidence_missing",
                "message": "Some executable tuples select `new` anchors without explicit rejection evidence for `existing` and `extended`.",
                "details": {"rows": new_anchor_strategy_evidence_missing_rows},
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
        warnings.append(
            {
                "code": "full_field_dictionary_missing",
                "message": "Some done contract rows are missing `Full Field Dictionary (Operation-scoped)`.",
                "details": {"binding_row_ids": missing_field_dictionary_rows},
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

    controller_first_violation_rows = sorted(
        [
            unit["binding_row_id"]
            for unit in unit_inventory
            if unit["contract"]["status"] == "done"
            and unit["contract"]["exists"]
            and unit["contract"]["controller_first_violation"]
        ]
    )
    if controller_first_violation_rows:
        warnings.append(
            {
                "code": "controller_first_violation",
                "message": "Some HTTP contract rows violate controller-first boundary rules.",
                "details": {"binding_row_ids": controller_first_violation_rows},
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


def build_task_bootstrap_payload(
    *,
    feature_dir: Path,
    plan_path: Path,
    spec_path: Path,
    data_model_path: Path,
    test_matrix_path: Path,
    contracts_dir: Path,
) -> dict[str, Any]:
    if not plan_path.is_file():
        raise FileNotFoundError(f"plan.md not found: {plan_path}")

    document = plan_path.read_text(encoding="utf-8")
    sections = {heading: extract_section(document, heading) for heading in TASK_SECTION_HEADINGS}
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
            "if_scope": clean_cell(row.get("IF ID / IF Scope", "")),
            "operation_id": clean_cell(row.get("Operation ID", "")),
            "tm_id": clean_cell(row.get("TM ID", "")),
            "tc_ids": split_csv_cell(row.get("TC IDs", "")),
            "boundary_anchor": clean_cell(row.get("Boundary Anchor", "")),
            "implementation_entry_anchor": clean_cell(row.get("Implementation Entry Anchor", "")),
            "boundary_anchor_status": normalize_anchor_status(row.get("Boundary Anchor Status", "")),
            "implementation_entry_anchor_status": normalize_anchor_status(
                row.get("Implementation Entry Anchor Status", "")
            ),
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
    execution_readiness = build_task_execution_readiness(
        missing_sections=missing_sections,
        incomplete_stage_ids=incomplete_stage_ids,
        binding_projection_index=binding_projection_index,
        artifact_status=artifact_status,
        unit_inventory=unit_inventory,
    )

    return {
        "schema_version": TASK_BOOTSTRAP_SCHEMA_VERSION,
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

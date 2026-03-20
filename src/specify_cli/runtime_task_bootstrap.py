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
from specify_cli.runtime_gate_protocol import build_repository_first_gate_protocol


TASK_BOOTSTRAP_SCHEMA_VERSION = "1.4"
TASK_SECTION_HEADINGS = (
    "Summary",
    "Shared Context Snapshot",
    "Stage Queue",
    "Binding Projection Index",
    "Artifact Status",
    "Handoff Protocol",
)
UNRESOLVED_CONTRACT_NAME_RE = re.compile(r"<([A-Z][A-Za-z0-9]+)>")
TASK_REQUIRED_STAGE_IDS = {"research", "test-matrix", "data-model"}
TASK_BASELINE_CODE_TO_CATEGORY = {
    "missing_required_sections": "missing",
    "empty_binding_projection_index": "missing",
    "missing_binding_contract_packet": "missing",
    "binding_contract_packet_missing_required_fields": "missing",
    "missing_contract_artifact_rows": "missing",
    "missing_contract_for_binding_rows": "missing",
    "contract_target_path_missing": "missing",
    "done_contract_target_missing": "missing",
    "incomplete_stage_queue": "stale",
    "contract_rows_not_done": "stale",
    "binding_projection_packet_drift": "stale",
    "binding_projection_missing_required_fields": "non_traceable",
    "contract_placeholder_names_present": "non_traceable",
    "contract_duplicate_required_sections": "non_traceable",
    "contract_binding_context_coverage_drift": "non_traceable",
    "contract_anchor_inventory_mismatch": "non_traceable",
    "full_field_dictionary_missing": "non_traceable",
    "field_dictionary_tier_missing": "non_traceable",
    "test_projection_section_missing": "non_traceable",
    "closure_check_section_missing": "non_traceable",
    "closure_check_rows_missing": "non_traceable",
    "contract_field_gap_unresolved": "non_traceable",
    "orphan_contract_artifact_rows": "non_traceable",
}


def split_ref_cell(value: str) -> list[str]:
    return split_csv_cell(value)


def is_active_status(status: str) -> bool:
    return clean_cell(status).lower() != "done"


def count_heading_occurrences(document: str, heading: str, level: int = 2) -> int:
    marker = "#" * level
    pattern = rf"(?m)^{re.escape(marker)}\s+{re.escape(heading)}\s*$"
    return len(re.findall(pattern, document))


def extract_subsection(document: str, heading: str, level: int = 3) -> str | None:
    marker = "#" * level
    same_level_marker = "#" * level
    parent_level_marker = "#" * (level - 1) if level > 1 else "#"
    pattern = (
        rf"^{re.escape(marker)}\s+{re.escape(heading)}\n"
        rf"(.*?)(?=^{re.escape(same_level_marker)}\s+|^{re.escape(parent_level_marker)}\s+|\Z)"
    )
    match = re.search(pattern, document, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()


def parse_binding_context(section: str | None) -> dict[str, str]:
    rows = parse_markdown_table(section)
    context: dict[str, str] = {}
    for row in rows:
        field = clean_cell(row.get("Field", ""))
        value = clean_cell(row.get("Value", ""))
        if field:
            context[field] = value
    return context


def normalize_symbol(value: str) -> str:
    return clean_cell(value).strip("`").strip()


def extract_required_anchor(content: str, label: str) -> str:
    pattern = rf"(?m)^\*\*{re.escape(label)}\*\*:\s*(.+?)\s*$"
    match = re.search(pattern, content)
    if not match:
        return ""
    return normalize_symbol(match.group(1))


def load_binding_contract_packets(test_matrix_path: Path) -> dict[str, dict[str, Any]]:
    if not test_matrix_path.is_file():
        return {}

    document = test_matrix_path.read_text(encoding="utf-8")
    packet_rows = parse_markdown_table(
        extract_section(document, "Binding Packets"),
        filter_placeholder_first_cell=True,
    )
    packets: dict[str, dict[str, Any]] = {}
    for row in packet_rows:
        binding_row_id = clean_cell(row.get("BindingRowID", ""))
        if not binding_row_id:
            continue
        packets[binding_row_id] = {
            "binding_row_id": binding_row_id,
            "trigger_refs": split_ref_cell(row.get("Trigger Ref(s)", "")),
            "if_scope": clean_cell(row.get("IF Scope", "")),
            "uif_path_refs": split_ref_cell(row.get("UIF Path Ref(s)", "")),
            "udd_refs": split_ref_cell(row.get("UDD Ref(s)", "")),
            "primary_tm_ids": split_ref_cell(row.get("Primary TM IDs", "")),
            "tc_ids": split_ref_cell(row.get("TC IDs", "")),
            "test_scope": clean_cell(row.get("Test Scope", "")),
            "spec_refs": split_ref_cell(row.get("Spec Ref(s)", "")),
            "scenario_refs": split_ref_cell(row.get("Scenario Ref(s)", "")),
            "success_refs": split_ref_cell(row.get("Success Ref(s)", "")),
            "edge_refs": split_ref_cell(row.get("Edge Ref(s)", "")),
        }
    return packets


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
        "duplicate_required_sections_present": False,
        "duplicate_required_sections": [],
        "binding_context_coverage_drift": False,
        "missing_uif_path_refs_in_behavior_or_test_projection": [],
        "missing_tm_ids_in_behavior_or_test_projection": [],
        "missing_tc_ids_in_behavior_or_test_projection": [],
        "anchor_inventory_mismatch": False,
        "anchor_inventory_mismatch_details": [],
        "operation_id": "",
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

    required_sections = [
        "Interface Definition",
        "UML Class Design",
        "Sequence Design",
        "Test Projection",
        "Closure Check",
        "Upstream References",
        "Boundary Notes",
    ]
    duplicate_sections = sorted(
        [heading for heading in required_sections if count_heading_occurrences(content, heading, level=2) > 1]
    )
    inspection["duplicate_required_sections_present"] = bool(duplicate_sections)
    inspection["duplicate_required_sections"] = duplicate_sections

    binding_context = parse_binding_context(extract_section(content, "Binding Context"))
    inspection["operation_id"] = extract_required_anchor(content, "Operation ID (Required)") or clean_cell(
        binding_context.get("Operation ID", "")
    )
    declared_uif_refs = split_ref_cell(binding_context.get("UIF Path Ref(s)", ""))
    declared_tm_ids = split_ref_cell(binding_context.get("TM IDs", ""))
    declared_tc_ids = split_ref_cell(binding_context.get("TC IDs", ""))

    behavior_paths = extract_subsection(content, "Behavior Paths", level=3) or ""
    test_projection_slice = extract_subsection(content, "Test Projection Slice", level=3) or ""
    behavior_and_test_projection = f"{behavior_paths}\n{test_projection_slice}"

    if declared_uif_refs and behavior_and_test_projection.strip():
        inspection["missing_uif_path_refs_in_behavior_or_test_projection"] = [
            ref for ref in declared_uif_refs if ref not in behavior_and_test_projection
        ]
    if declared_tm_ids and behavior_and_test_projection.strip():
        inspection["missing_tm_ids_in_behavior_or_test_projection"] = [
            ref for ref in declared_tm_ids if ref not in behavior_and_test_projection
        ]
    if declared_tc_ids and behavior_and_test_projection.strip():
        inspection["missing_tc_ids_in_behavior_or_test_projection"] = [
            ref for ref in declared_tc_ids if ref not in behavior_and_test_projection
        ]

    inspection["binding_context_coverage_drift"] = bool(
        inspection["missing_uif_path_refs_in_behavior_or_test_projection"]
        or inspection["missing_tm_ids_in_behavior_or_test_projection"]
        or inspection["missing_tc_ids_in_behavior_or_test_projection"]
    )

    top_boundary_anchor = extract_required_anchor(content, "Boundary Anchor (Required)")
    top_entry_anchor = extract_required_anchor(content, "Implementation Entry Anchor (Required)")
    resolved_type_inventory = parse_markdown_table(extract_subsection(content, "Resolved Type Inventory", level=3))
    boundary_inventory_anchor = ""
    entry_inventory_anchor = ""
    for row in resolved_type_inventory:
        role = normalize_symbol(row.get("Role", "")).lower()
        concrete_name = normalize_symbol(row.get("Concrete Name", ""))
        if role == "boundary-entry":
            boundary_inventory_anchor = concrete_name
        if role == "implementation-entry":
            entry_inventory_anchor = concrete_name

    anchor_mismatch_details: list[str] = []
    if top_boundary_anchor and boundary_inventory_anchor and top_boundary_anchor != boundary_inventory_anchor:
        anchor_mismatch_details.append("Boundary Anchor != Resolved Type Inventory boundary-entry")
    if top_entry_anchor and entry_inventory_anchor and top_entry_anchor != entry_inventory_anchor:
        anchor_mismatch_details.append("Implementation Entry Anchor != Resolved Type Inventory implementation-entry")
    inspection["anchor_inventory_mismatch"] = bool(anchor_mismatch_details)
    inspection["anchor_inventory_mismatch_details"] = anchor_mismatch_details
    return inspection


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
        trigger_refs = split_ref_cell(row.get("Trigger Ref(s)", ""))
        primary_tm_ids = split_ref_cell(row.get("Primary TM IDs", ""))
        tc_ids = split_ref_cell(row.get("TC IDs", ""))
        operation_id = contract_inspection["operation_id"]
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
                ("Trigger Ref(s)", trigger_refs),
                ("Primary TM IDs", primary_tm_ids),
                ("TC IDs", tc_ids),
                ("UIF Path Ref(s)", uif_path_refs),
                ("UDD Ref(s)", udd_refs),
                ("Test Scope", test_scope),
            )
            if not field_value
        ]

        missing_binding_packet_fields = []
        if packet:
            for field_name, field_value in (
                ("Trigger Ref(s)", packet.get("trigger_refs", [])),
                ("IF Scope", packet.get("if_scope", "")),
                ("UIF Path Ref(s)", packet.get("uif_path_refs", [])),
                ("UDD Ref(s)", packet.get("udd_refs", [])),
                ("Primary TM IDs", packet.get("primary_tm_ids", [])),
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
                trigger_refs != packet.get("trigger_refs", []),
                if_scope != packet.get("if_scope", ""),
                primary_tm_ids != packet.get("primary_tm_ids", []),
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
            "trigger_refs": trigger_refs,
            "primary_tm_ids": primary_tm_ids,
            "tc_ids": tc_ids,
            "uif_path_refs": uif_path_refs,
            "udd_refs": udd_refs,
            "test_scope": test_scope,
            "missing_binding_projection_fields": missing_binding_projection_fields,
            "missing_binding_packet_fields": missing_binding_packet_fields,
            "binding_packet": {
                "present": bool(packet),
                "trigger_refs": packet.get("trigger_refs", []),
                "if_scope": packet.get("if_scope", ""),
                "uif_path_refs": packet.get("uif_path_refs", []),
                "udd_refs": packet.get("udd_refs", []),
                "primary_tm_ids": packet.get("primary_tm_ids", []),
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
                "duplicate_required_sections_present": contract_inspection["duplicate_required_sections_present"],
                "duplicate_required_sections": contract_inspection["duplicate_required_sections"],
                "binding_context_coverage_drift": contract_inspection["binding_context_coverage_drift"],
                "missing_uif_path_refs_in_behavior_or_test_projection": contract_inspection[
                    "missing_uif_path_refs_in_behavior_or_test_projection"
                ],
                "missing_tm_ids_in_behavior_or_test_projection": contract_inspection[
                    "missing_tm_ids_in_behavior_or_test_projection"
                ],
                "missing_tc_ids_in_behavior_or_test_projection": contract_inspection[
                    "missing_tc_ids_in_behavior_or_test_projection"
                ],
                "anchor_inventory_mismatch": contract_inspection["anchor_inventory_mismatch"],
                "anchor_inventory_mismatch_details": contract_inspection["anchor_inventory_mismatch_details"],
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
            and not unit["contract"]["duplicate_required_sections_present"]
            and not unit["contract"]["binding_context_coverage_drift"]
            and not unit["contract"]["anchor_inventory_mismatch"]
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
                "message": "Some binding rows have no matching Binding Packet in test-matrix.md.",
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
                "message": "Some binding rows drift from their authoritative Binding Packets.",
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

    duplicate_required_sections_rows = sorted(
        [
            {
                "binding_row_id": unit["binding_row_id"],
                "sections": unit["contract"]["duplicate_required_sections"],
            }
            for unit in unit_inventory
            if unit["contract"]["status"] == "done"
            and unit["contract"]["exists"]
            and unit["contract"]["duplicate_required_sections_present"]
        ],
        key=lambda item: item["binding_row_id"],
    )
    if duplicate_required_sections_rows:
        errors.append(
            {
                "code": "contract_duplicate_required_sections",
                "message": "Some done contract rows contain duplicated required sections.",
                "details": {"rows": duplicate_required_sections_rows},
            }
        )

    binding_context_coverage_drift_rows = sorted(
        [
            {
                "binding_row_id": unit["binding_row_id"],
                "missing_uif_path_refs": unit["contract"]["missing_uif_path_refs_in_behavior_or_test_projection"],
                "missing_tm_ids": unit["contract"]["missing_tm_ids_in_behavior_or_test_projection"],
                "missing_tc_ids": unit["contract"]["missing_tc_ids_in_behavior_or_test_projection"],
            }
            for unit in unit_inventory
            if unit["contract"]["status"] == "done"
            and unit["contract"]["exists"]
            and unit["contract"]["binding_context_coverage_drift"]
        ],
        key=lambda item: item["binding_row_id"],
    )
    if binding_context_coverage_drift_rows:
        errors.append(
            {
                "code": "contract_binding_context_coverage_drift",
                "message": "Some done contract rows do not fully close Binding Context UIF/TM/TC refs in behavior paths or test projection.",
                "details": {"rows": binding_context_coverage_drift_rows},
            }
        )

    anchor_inventory_mismatch_rows = sorted(
        [
            {
                "binding_row_id": unit["binding_row_id"],
                "details": unit["contract"]["anchor_inventory_mismatch_details"],
            }
            for unit in unit_inventory
            if unit["contract"]["status"] == "done"
            and unit["contract"]["exists"]
            and unit["contract"]["anchor_inventory_mismatch"]
        ],
        key=lambda item: item["binding_row_id"],
    )
    if anchor_inventory_mismatch_rows:
        errors.append(
            {
                "code": "contract_anchor_inventory_mismatch",
                "message": "Some done contract rows mismatch top-level anchors vs Resolved Type Inventory anchors.",
                "details": {"rows": anchor_inventory_mismatch_rows},
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
        "summary": sections["Summary"] is not None,
        "shared_context_snapshot": sections["Shared Context Snapshot"] is not None,
        "stage_queue": sections["Stage Queue"] is not None,
        "binding_projection_index": sections["Binding Projection Index"] is not None,
        "artifact_status": sections["Artifact Status"] is not None,
        "handoff_protocol": sections["Handoff Protocol"] is not None,
    }
    missing_sections = [name for name, present in required_sections.items() if not present]

    stage_rows = parse_markdown_table(sections["Stage Queue"])
    binding_rows = parse_markdown_table(sections["Binding Projection Index"], filter_placeholder_first_cell=True)
    artifact_rows = parse_markdown_table(sections["Artifact Status"], filter_placeholder_first_cell=True)
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
            "trigger_refs": split_ref_cell(row.get("Trigger Ref(s)", "")),
            "primary_tm_ids": split_ref_cell(row.get("Primary TM IDs", "")),
            "tc_ids": split_ref_cell(row.get("TC IDs", "")),
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
    execution_readiness = build_task_execution_readiness(
        missing_sections=missing_sections,
        incomplete_stage_ids=incomplete_stage_ids,
        binding_projection_index=binding_projection_index,
        artifact_status=artifact_status,
        unit_inventory=unit_inventory,
    )
    repository_first_gate_protocol = build_repository_first_gate_protocol(
        gate_name="task_bootstrap",
        readiness=execution_readiness,
        ready_field="ready_for_task_generation",
        code_to_category=TASK_BASELINE_CODE_TO_CATEGORY,
        source_manifest_fingerprints=None,
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
        "repository_first_gate_protocol": repository_first_gate_protocol,
    }

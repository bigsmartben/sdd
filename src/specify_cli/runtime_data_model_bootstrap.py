"""Packaged data-model bootstrap extractor."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from specify_cli.runtime_common import (
    clean_cell,
    compute_sha256,
    extract_section,
    parse_markdown_table,
    resolve_target_path,
)


DATA_MODEL_BOOTSTRAP_SCHEMA_VERSION = "1.2"
DATA_MODEL_SECTION_HEADINGS = (
    "Summary",
    "Shared Context Snapshot",
    "Stage Queue",
    "Binding Projection Index",
    "Artifact Status",
    "Handoff Protocol",
)
DATA_MODEL_TEST_MATRIX_REQUIRED_SECTIONS = (
    "Interface Partition Decisions",
    "UIF Full Path Coverage Graph (Mermaid)",
    "UIF Path Coverage Ledger",
    "Scenario Matrix",
    "Verification Case Anchors",
    "Binding Packets",
)
DATA_MODEL_BINDING_PACKET_REQUIRED_FIELDS = (
    "BindingRowID",
    "IF Scope",
    "Trigger Ref(s)",
    "UIF Path Ref(s)",
    "UDD Ref(s)",
    "Primary TM IDs",
    "TM IDs",
    "TC IDs",
    "Test Scope",
    "Spec Ref(s)",
    "Scenario Ref(s)",
    "Success Ref(s)",
    "Edge Ref(s)",
)
STATE_MACHINE_POLICY = {
    "decision_owner": "/sdd.plan.data-model",
    "full_fsm_rule": "N > 3 or T >= 2N",
    "full_fsm_required_components": ["transition_table", "transition_pseudocode", "state_diagram"],
    "lightweight_model_required_components": [
        "state_field_definition",
        "allowed_transitions",
        "forbidden_transitions",
        "key_invariants",
    ],
    "full_fsm_below_threshold_requires_justification": True,
}


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


def build_test_matrix_validation(test_matrix_path: Path, binding_row_ids: list[str]) -> dict[str, Any]:
    required_sections = {heading: False for heading in DATA_MODEL_TEST_MATRIX_REQUIRED_SECTIONS}
    validation = {
        "required_sections": required_sections,
        "missing_required_sections": list(DATA_MODEL_TEST_MATRIX_REQUIRED_SECTIONS),
        "binding_packet_count": 0,
        "missing_binding_row_ids": [],
        "incomplete_binding_packets": [],
    }
    if not test_matrix_path.is_file():
        return validation

    document = test_matrix_path.read_text(encoding="utf-8")
    for heading in DATA_MODEL_TEST_MATRIX_REQUIRED_SECTIONS:
        required_sections[heading] = extract_section(document, heading) is not None
    validation["missing_required_sections"] = [
        heading for heading, present in required_sections.items() if not present
    ]

    packet_rows = parse_markdown_table(
        extract_section(document, "Binding Packets"),
        filter_placeholder_first_cell=True,
    )
    packets_by_binding: dict[str, dict[str, str]] = {}
    incomplete_packets: list[dict[str, Any]] = []
    for row in packet_rows:
        binding_row_id = clean_cell(row.get("BindingRowID", ""))
        if not binding_row_id:
            continue
        packets_by_binding[binding_row_id] = row
        missing_fields = [
            field_name for field_name in DATA_MODEL_BINDING_PACKET_REQUIRED_FIELDS if not clean_cell(row.get(field_name, ""))
        ]
        if missing_fields:
            incomplete_packets.append({"binding_row_id": binding_row_id, "fields": missing_fields})

    validation["binding_packet_count"] = len(packets_by_binding)
    validation["missing_binding_row_ids"] = [
        binding_row_id for binding_row_id in binding_row_ids if binding_row_id not in packets_by_binding
    ]
    validation["incomplete_binding_packets"] = sorted(
        incomplete_packets,
        key=lambda item: item["binding_row_id"],
    )
    return validation


def build_generation_readiness(
    *,
    missing_sections: list[str],
    spec_path: Path,
    test_matrix_path: Path,
    research_path: Path,
    data_model_path: Path,
    research_stage: dict[str, Any] | None,
    test_matrix_stage: dict[str, Any] | None,
    selected_stage: dict[str, Any] | None,
    test_matrix_validation: dict[str, Any],
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
        errors.append({"code": "spec_missing", "message": "spec.md is missing for the selected feature.", "details": {"path": str(spec_path)}})

    if not test_matrix_path.is_file():
        errors.append(
            {
                "code": "test_matrix_missing",
                "message": "test-matrix.md is missing for the selected feature.",
                "details": {"path": str(test_matrix_path)},
            }
        )
    elif test_matrix_validation["missing_required_sections"]:
        errors.append(
            {
                "code": "test_matrix_required_sections_missing",
                "message": "test-matrix.md is missing required sections for /sdd.plan.data-model.",
                "details": {"sections": test_matrix_validation["missing_required_sections"]},
            }
        )
    elif test_matrix_validation["missing_binding_row_ids"]:
        errors.append(
            {
                "code": "binding_packets_missing_for_projection_rows",
                "message": "test-matrix.md is missing Binding Packets for one or more projected binding rows.",
                "details": {"binding_row_ids": test_matrix_validation["missing_binding_row_ids"]},
            }
        )
    elif test_matrix_validation["incomplete_binding_packets"]:
        errors.append(
            {
                "code": "binding_packets_missing_required_fields",
                "message": "One or more Binding Packets are missing required fields for /sdd.plan.data-model.",
                "details": {"rows": test_matrix_validation["incomplete_binding_packets"]},
            }
        )

    if not research_path.is_file():
        warnings.append(
            {
                "code": "research_artifact_missing",
                "message": "research.md is missing for the selected feature; continuing because it is optional clarification input.",
                "details": {"path": str(research_path)},
            }
        )

    if research_stage is None:
        warnings.append(
            {
                "code": "research_stage_missing",
                "message": "Stage Queue does not contain a research row; continuing because research is optional for /sdd.plan.data-model.",
                "details": {},
            }
        )
    elif research_stage["status"] != "done":
        warnings.append(
            {
                "code": "research_stage_not_done",
                "message": "Research stage is not done; continuing because research is optional clarification input.",
                "details": {"status": research_stage["status"], "blocker": research_stage["blocker"]},
            }
        )

    if test_matrix_stage is None:
        errors.append(
            {
                "code": "test_matrix_stage_missing",
                "message": "Stage Queue does not contain a test-matrix row.",
                "details": {},
            }
        )
    elif test_matrix_stage["status"] != "done":
        errors.append(
            {
                "code": "test_matrix_stage_not_done",
                "message": "test-matrix prerequisite is not done.",
                "details": {"status": test_matrix_stage["status"], "blocker": test_matrix_stage["blocker"]},
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


def build_data_model_bootstrap_payload(
    *,
    feature_dir: Path,
    plan_path: Path,
    spec_path: Path,
    research_path: Path,
    data_model_path: Path,
) -> dict[str, Any]:
    if not plan_path.is_file():
        raise FileNotFoundError(f"plan.md not found: {plan_path}")

    document = plan_path.read_text(encoding="utf-8")
    sections = {heading: extract_section(document, heading) for heading in DATA_MODEL_SECTION_HEADINGS}
    shared_context_snapshot = sections["Shared Context Snapshot"] or ""
    has_repository_first_consumption_slice = bool(
        re.search(r"(?m)^###\s+Repository-First Consumption Slice\s*$", shared_context_snapshot)
    )
    required_sections = {
        "summary": sections["Summary"] is not None,
        "shared_context_snapshot": sections["Shared Context Snapshot"] is not None,
        "repository_first_consumption_slice": has_repository_first_consumption_slice,
        "stage_queue": sections["Stage Queue"] is not None,
        "binding_projection_index": sections["Binding Projection Index"] is not None,
        "artifact_status": sections["Artifact Status"] is not None,
        "handoff_protocol": sections["Handoff Protocol"] is not None,
    }
    missing_sections = [name for name, present in required_sections.items() if not present]

    stage_rows = parse_markdown_table(sections["Stage Queue"])
    binding_rows = parse_markdown_table(sections["Binding Projection Index"], filter_placeholder_first_cell=True)
    research_stage = build_stage_row(
        feature_dir,
        next((row for row in stage_rows if clean_cell(row.get("Stage ID", "")) == "research"), None),
    )
    test_matrix_stage = build_stage_row(
        feature_dir,
        next((row for row in stage_rows if clean_cell(row.get("Stage ID", "")) == "test-matrix"), None),
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

    test_matrix_path = (
        Path(test_matrix_stage["output_path_abs"])
        if test_matrix_stage and test_matrix_stage["output_path_abs"]
        else feature_dir / "test-matrix.md"
    )
    binding_row_ids = [
        clean_cell(row.get("BindingRowID", ""))
        for row in binding_rows
        if clean_cell(row.get("BindingRowID", ""))
    ]
    test_matrix_validation = build_test_matrix_validation(test_matrix_path, binding_row_ids)

    current_fingerprints = {
        "plan_sha256": compute_sha256(plan_path),
        "spec_sha256": compute_sha256(spec_path),
        "test_matrix_sha256": compute_sha256(test_matrix_path),
        "research_sha256": compute_sha256(research_path),
        "data_model_sha256": compute_sha256(data_model_path),
    }

    generation_readiness = build_generation_readiness(
        missing_sections=missing_sections,
        spec_path=spec_path,
        test_matrix_path=test_matrix_path,
        research_path=research_path,
        data_model_path=data_model_path,
        research_stage=research_stage,
        test_matrix_stage=test_matrix_stage,
        selected_stage=selected_stage,
        test_matrix_validation=test_matrix_validation,
    )

    return {
        "schema_version": DATA_MODEL_BOOTSTRAP_SCHEMA_VERSION,
        "feature_dir": str(feature_dir),
        "plan_path": str(plan_path),
        "spec_path": str(spec_path),
        "test_matrix_path": str(test_matrix_path),
        "research_path": str(research_path),
        "data_model_path": str(data_model_path),
        "required_sections": required_sections,
        "current_fingerprints": current_fingerprints,
        "research_stage": research_stage,
        "test_matrix_stage": test_matrix_stage,
        "selected_stage": selected_stage,
        "test_matrix_validation": test_matrix_validation,
        "repo_anchor_policy": {
            "decision_order": ["existing", "extended", "new"],
            "repo_anchor_input_limit": 5,
            "inv_requires_repo_evidence": True,
            "inv_forbids_todo": True,
            "lifecycle_stable_states_forbid_todo": True,
        },
        "state_machine_policy": STATE_MACHINE_POLICY,
        "generation_readiness": generation_readiness,
    }

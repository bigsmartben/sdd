"""Packaged data-model bootstrap extractor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from specify_cli.runtime_common import (
    clean_cell,
    compute_sha256,
    extract_section,
    parse_markdown_table,
    resolve_target_path,
)


DATA_MODEL_BOOTSTRAP_SCHEMA_VERSION = "1.1"
DATA_MODEL_SECTION_HEADINGS = (
    "Shared Context Snapshot",
    "Stage Queue",
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
        errors.append({"code": "spec_missing", "message": "spec.md is missing for the selected feature.", "details": {"path": str(spec_path)}})

    if not research_path.is_file():
        errors.append(
            {
                "code": "research_artifact_missing",
                "message": "research.md is missing for the selected feature.",
                "details": {"path": str(research_path)},
            }
        )

    if research_stage is None:
        errors.append({"code": "research_stage_missing", "message": "Stage Queue does not contain a research row.", "details": {}})
    elif research_stage["status"] != "done":
        errors.append(
            {
                "code": "research_stage_not_done",
                "message": "Research prerequisite is not done.",
                "details": {"status": research_stage["status"], "blocker": research_stage["blocker"]},
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

    return {
        "schema_version": DATA_MODEL_BOOTSTRAP_SCHEMA_VERSION,
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
        "state_machine_policy": STATE_MACHINE_POLICY,
        "generation_readiness": generation_readiness,
    }

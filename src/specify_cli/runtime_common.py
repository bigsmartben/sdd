"""Shared helpers for packaged SDD runtime extractors."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any


PLACEHOLDER_TOKEN_RE = re.compile(r"^\[[^\]]+\]$")
PACKET_SOURCE_RE = re.compile(
    r"(?i)^test-matrix\.md\s*#\s*binding(?:\s|-)?packets\s*:\s*([A-Za-z0-9_.-]+)\s*$"
)
BINDING_PACKET_REQUIRED_FIELDS = (
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


def canonical_packet_source(binding_row_id: str) -> str:
    normalized = clean_cell(binding_row_id)
    if not normalized:
        return ""
    return f"test-matrix.md#Binding Packets:{normalized}"


def normalize_packet_source_ref(value: str) -> str:
    text = clean_cell(value)
    if not text:
        return ""
    match = PACKET_SOURCE_RE.match(text)
    if not match:
        return text
    return canonical_packet_source(match.group(1))


def packet_source_binding_row_id(value: str) -> str:
    normalized = normalize_packet_source_ref(value)
    match = PACKET_SOURCE_RE.match(normalized)
    if not match:
        return ""
    return clean_cell(match.group(1))


def extract_section(document: str, heading: str) -> str | None:
    pattern = rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, document, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()


def parse_markdown_table(section: str | None, *, filter_placeholder_first_cell: bool = False) -> list[dict[str, str]]:
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
        if filter_placeholder_first_cell and cells and PLACEHOLDER_TOKEN_RE.fullmatch(cells[0]):
            continue
        row = {header: cell for header, cell in zip(headers, cells)}
        if any(value for value in row.values()):
            rows.append(row)
    return rows


def load_binding_index_entries(plan_document: str) -> list[dict[str, str]]:
    rows = parse_markdown_table(
        extract_section(plan_document, "Binding Projection Index"),
        filter_placeholder_first_cell=True,
    )
    entries: list[dict[str, str]] = []
    for row in rows:
        binding_row_id = clean_cell(row.get("BindingRowID", ""))
        if not binding_row_id:
            continue
        entries.append(
            {
                "binding_row_id": binding_row_id,
                "packet_source": normalize_packet_source_ref(row.get("Packet Source", "")),
                "expected_packet_source": canonical_packet_source(binding_row_id),
            }
        )
    return entries


def build_binding_packet_entry(row: dict[str, str]) -> dict[str, Any]:
    binding_row_id = clean_cell(row.get("BindingRowID", ""))
    return {
        "binding_row_id": binding_row_id,
        "trigger_refs": split_csv_cell(row.get("Trigger Ref(s)", "")),
        "if_scope": clean_cell(row.get("IF Scope", "")),
        "uif_path_refs": split_csv_cell(row.get("UIF Path Ref(s)", "")),
        "udd_refs": split_csv_cell(row.get("UDD Ref(s)", "")),
        "primary_tm_ids": split_csv_cell(row.get("Primary TM IDs", "")),
        "tm_ids": split_csv_cell(row.get("TM IDs", "")),
        "tc_ids": split_csv_cell(row.get("TC IDs", "")),
        "test_scope": clean_cell(row.get("Test Scope", "")),
        "spec_refs": split_csv_cell(row.get("Spec Ref(s)", "")),
        "scenario_refs": split_csv_cell(row.get("Scenario Ref(s)", "")),
        "success_refs": split_csv_cell(row.get("Success Ref(s)", "")),
        "edge_refs": split_csv_cell(row.get("Edge Ref(s)", "")),
    }


def load_binding_packet_catalog(test_matrix_path: Path) -> dict[str, Any]:
    catalog = {
        "packet_rows": [],
        "packets_by_binding": {},
        "binding_packet_count": 0,
        "duplicate_binding_row_ids": [],
        "incomplete_binding_packets": [],
    }
    if not test_matrix_path.is_file():
        return catalog

    document = test_matrix_path.read_text(encoding="utf-8")
    packet_rows = parse_markdown_table(
        extract_section(document, "Binding Packets"),
        filter_placeholder_first_cell=True,
    )
    rows_by_binding: dict[str, list[dict[str, str]]] = {}
    incomplete_packets: list[dict[str, Any]] = []
    for row in packet_rows:
        binding_row_id = clean_cell(row.get("BindingRowID", ""))
        if not binding_row_id:
            continue
        rows_by_binding.setdefault(binding_row_id, []).append(row)

    packets_by_binding: dict[str, dict[str, Any]] = {}
    for binding_row_id, rows in rows_by_binding.items():
        row = rows[0]
        packets_by_binding[binding_row_id] = build_binding_packet_entry(row)
        missing_fields = [
            field_name
            for field_name in BINDING_PACKET_REQUIRED_FIELDS
            if not clean_cell(row.get(field_name, ""))
        ]
        if missing_fields:
            incomplete_packets.append({"binding_row_id": binding_row_id, "fields": missing_fields})

    catalog["packet_rows"] = packet_rows
    catalog["packets_by_binding"] = packets_by_binding
    catalog["binding_packet_count"] = len(packets_by_binding)
    catalog["duplicate_binding_row_ids"] = sorted(
        binding_row_id for binding_row_id, rows in rows_by_binding.items() if len(rows) > 1
    )
    catalog["incomplete_binding_packets"] = sorted(
        incomplete_packets,
        key=lambda item: item["binding_row_id"],
    )
    return catalog


def build_binding_resolution_state(
    binding_projection_index: list[dict[str, str]],
    packet_catalog: dict[str, Any],
) -> dict[str, Any]:
    rows_by_binding: dict[str, list[dict[str, str]]] = {}
    rows_by_packet_source: dict[str, list[dict[str, str]]] = {}
    for entry in binding_projection_index:
        binding_row_id = clean_cell(entry.get("binding_row_id", ""))
        packet_source = normalize_packet_source_ref(entry.get("packet_source", ""))
        expected_packet_source = canonical_packet_source(binding_row_id)
        normalized_entry = {
            "binding_row_id": binding_row_id,
            "packet_source": packet_source,
            "expected_packet_source": expected_packet_source,
        }
        rows_by_binding.setdefault(binding_row_id, []).append(normalized_entry)
        if packet_source:
            rows_by_packet_source.setdefault(packet_source, []).append(normalized_entry)

    duplicate_binding_row_ids = sorted(
        binding_row_id for binding_row_id, rows in rows_by_binding.items() if binding_row_id and len(rows) > 1
    )
    duplicate_packet_sources = sorted(
        [
            {
                "packet_source": packet_source,
                "binding_row_ids": sorted(
                    entry["binding_row_id"] for entry in rows if entry.get("binding_row_id")
                ),
                "row_count": len(rows),
            }
            for packet_source, rows in rows_by_packet_source.items()
            if len(rows) > 1
        ],
        key=lambda item: item["packet_source"],
    )
    duplicate_binding_row_id_set = set(duplicate_binding_row_ids)
    duplicate_packet_source_set = {entry["packet_source"] for entry in duplicate_packet_sources}
    duplicate_packet_binding_row_id_set = set(packet_catalog.get("duplicate_binding_row_ids", []))
    packets_by_binding = packet_catalog.get("packets_by_binding", {})

    projection_missing_required_fields: list[dict[str, Any]] = []
    unresolved_packet_source_rows: list[dict[str, Any]] = []
    missing_binding_row_ids: list[str] = []
    resolution_entries: list[dict[str, Any]] = []

    for index_row in binding_projection_index:
        binding_row_id = clean_cell(index_row.get("binding_row_id", ""))
        packet_source = normalize_packet_source_ref(index_row.get("packet_source", ""))
        expected_packet_source = canonical_packet_source(binding_row_id)
        missing_fields = [
            field_name
            for field_name, field_value in (("Packet Source", packet_source),)
            if not clean_cell(field_value)
        ]
        source_binding_row_id = packet_source_binding_row_id(packet_source)
        resolution_error = ""
        if not missing_fields:
            if binding_row_id in duplicate_binding_row_id_set:
                resolution_error = "duplicate_binding_row_id"
            elif packet_source in duplicate_packet_source_set:
                resolution_error = "duplicate_packet_source"
            elif not source_binding_row_id:
                resolution_error = "invalid_packet_source"
            elif source_binding_row_id != binding_row_id:
                resolution_error = "packet_source_binding_row_mismatch"
            elif source_binding_row_id in duplicate_packet_binding_row_id_set:
                resolution_error = "duplicate_binding_packet_row_id"
            elif source_binding_row_id not in packets_by_binding:
                resolution_error = "binding_packet_not_found"
                missing_binding_row_ids.append(binding_row_id)

        packet = packets_by_binding.get(binding_row_id, {}) if not missing_fields and not resolution_error else {}
        resolution_entry = {
            "binding_row_id": binding_row_id,
            "packet_source": packet_source,
            "expected_packet_source": expected_packet_source,
            "source_binding_row_id": source_binding_row_id,
            "missing_fields": missing_fields,
            "resolution_error": resolution_error,
            "packet": packet,
        }
        resolution_entries.append(resolution_entry)
        if missing_fields:
            projection_missing_required_fields.append(
                {"binding_row_id": binding_row_id, "fields": missing_fields}
            )
        elif resolution_error:
            unresolved_packet_source_rows.append(
                {
                    "binding_row_id": binding_row_id,
                    "packet_source": packet_source,
                    "expected_packet_source": expected_packet_source,
                    "reason": resolution_error,
                }
            )

    return {
        "entries": resolution_entries,
        "binding_projection_duplicate_binding_row_ids": duplicate_binding_row_ids,
        "binding_projection_duplicate_packet_sources": duplicate_packet_sources,
        "binding_packets_duplicate_binding_row_ids": sorted(duplicate_packet_binding_row_id_set),
        "binding_projection_missing_required_fields": sorted(
            projection_missing_required_fields,
            key=lambda item: item["binding_row_id"],
        ),
        "unresolved_packet_source_rows": sorted(
            unresolved_packet_source_rows,
            key=lambda item: item["binding_row_id"],
        ),
        "missing_binding_row_ids": sorted(dict.fromkeys(missing_binding_row_ids)),
    }


def resolve_target_path(feature_dir: Path, raw_path: str) -> str:
    normalized = clean_cell(raw_path)
    if not normalized:
        return ""
    candidate = Path(normalized)
    if candidate.is_absolute():
        return str(candidate)
    # Accept repo-relative Stage Queue / Artifact Status paths when callers
    # accidentally write `specs/<feature>/...` instead of feature-local paths.
    # This avoids duplicating `specs/<feature>/` as
    # `<feature_dir>/specs/<feature>/...`.
    if candidate.parts and candidate.parts[0] == "specs" and feature_dir.parent.name == "specs":
        return str((feature_dir.parent.parent / candidate).resolve())
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

"""Shared helpers for packaged SDD runtime extractors."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path


PLACEHOLDER_TOKEN_RE = re.compile(r"^\[[^\]]+\]$")


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

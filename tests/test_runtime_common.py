from pathlib import Path

from specify_cli.runtime_common import (
    build_binding_resolution_state,
    canonical_packet_source,
    load_binding_index_entries,
    load_binding_packet_catalog,
    normalize_packet_source_ref,
    packet_source_binding_row_id,
    resolve_target_path,
)


def test_resolve_target_path_feature_relative_path():
    feature_dir = Path("/tmp/repo/specs/20260323-all-age-dictation-0313")

    resolved = resolve_target_path(feature_dir, "test-matrix.md")

    assert resolved == str((feature_dir / "test-matrix.md").resolve())


def test_resolve_target_path_accepts_repo_relative_specs_path_without_duplication():
    feature_dir = Path("/tmp/repo/specs/20260323-all-age-dictation-0313")

    resolved = resolve_target_path(
        feature_dir,
        "specs/20260323-all-age-dictation-0313/test-matrix.md",
    )

    assert resolved == str((Path("/tmp/repo") / "specs/20260323-all-age-dictation-0313/test-matrix.md").resolve())


def test_packet_source_helpers_normalize_and_extract_binding_row_id():
    raw = " test-matrix.md # Binding-Packets : BR-001 "

    normalized = normalize_packet_source_ref(raw)

    assert normalized == canonical_packet_source("BR-001")
    assert packet_source_binding_row_id(raw) == "BR-001"


def test_load_binding_index_entries_reads_registry_only_rows():
    document = """# Planning Control Plane

## Binding Projection Index

| BindingRowID | Packet Source |
|--------------|---------------|
| BR-001 | test-matrix.md#Binding Packets:BR-001 |
| [BindingRowID-002] | [test-matrix.md#Binding Packets:BR-002] |
"""

    entries = load_binding_index_entries(document)

    assert entries == [
        {
            "binding_row_id": "BR-001",
            "packet_source": "test-matrix.md#Binding Packets:BR-001",
            "expected_packet_source": "test-matrix.md#Binding Packets:BR-001",
        }
    ]


def test_binding_resolution_state_flags_duplicate_binding_rows_and_packet_sources(tmp_path: Path):
    test_matrix_path = tmp_path / "test-matrix.md"
    test_matrix_path.write_text(
        """# Test Matrix

## Binding Packets

| BindingRowID | IF Scope | User Intent | Trigger Ref(s) | Request Semantics | Visible Result | Side Effect | Boundary Notes | Repo Landing Hint | UIF Path Ref(s) | UDD Ref(s) | Primary TM IDs | TM IDs | TC IDs | Test Scope | Spec Ref(s) | Scenario Ref(s) | Success Ref(s) | Edge Ref(s) |
|--------------|----------|-------------|----------------|-------------------|----------------|-------------|----------------|-------------------|-----------------|------------|----------------|--------|--------|------------|-------------|-----------------|----------------|-------------|
| BR-001 | IF-001 | Demo | [UIF-001.trigger] | req | visible | none | N/A | demo | [UIF-Path-001] | [UDD-001] | [TM-001] | [TM-001] | [TC-001] | Integration | [UC-001] | [S1] | [SC-001] | [EC-001] |
""",
        encoding="utf-8",
    )

    resolution_state = build_binding_resolution_state(
        [
            {
                "binding_row_id": "BR-001",
                "packet_source": "test-matrix.md#Binding Packets:BR-001",
                "expected_packet_source": "test-matrix.md#Binding Packets:BR-001",
            },
            {
                "binding_row_id": "BR-001",
                "packet_source": "test-matrix.md#Binding Packets:BR-001",
                "expected_packet_source": "test-matrix.md#Binding Packets:BR-001",
            },
            {
                "binding_row_id": "BR-002",
                "packet_source": "test-matrix.md#Binding Packets:BR-001",
                "expected_packet_source": "test-matrix.md#Binding Packets:BR-002",
            },
        ],
        load_binding_packet_catalog(test_matrix_path),
    )

    assert resolution_state["binding_projection_duplicate_binding_row_ids"] == ["BR-001"]
    assert resolution_state["binding_projection_duplicate_packet_sources"] == [
        {
            "packet_source": "test-matrix.md#Binding Packets:BR-001",
            "binding_row_ids": ["BR-001", "BR-001", "BR-002"],
            "row_count": 3,
        }
    ]

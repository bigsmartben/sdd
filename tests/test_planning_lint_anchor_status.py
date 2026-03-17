import json
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
LINT_SCRIPT = REPO_ROOT / "scripts" / "bash" / "run-planning-lint.sh"
RULES_FILE = REPO_ROOT / "rules" / "planning-lint-rules.tsv"


def _write_feature_fixture(
    tmp_path: Path,
    test_matrix_status: str = "existing",
    contract_anchor_status: str = "`existing`",
) -> Path:
    feature_dir = tmp_path / "feature"
    (feature_dir / "contracts").mkdir(parents=True)

    (feature_dir / "data-model.md").write_text(
        "\n".join(
            [
                "# Data Model",
                "",
                "| Domain Element | Kind | Anchor Status | Repo Anchor |",
                "|---------------|------|---------------|-------------|",
                "| DemoAggregate | Aggregate | existing | src/domain/demo.py::DemoAggregate |",
            ]
        ),
        encoding="utf-8",
    )

    (feature_dir / "test-matrix.md").write_text(
        "\n".join(
            [
                "# Test Matrix",
                "",
                "| TM ID | Operation ID | Boundary Anchor | IF Scope | Repo Anchor | Anchor Status | Path Type |",
                "|------|--------------|-----------------|----------|-------------|---------------|-----------|",
                f"| TM-001 | demoOp | HTTP `GET /demo` | IF-001 | src/boundary/demo.py::DemoBoundary | {test_matrix_status} | Main |",
            ]
        ),
        encoding="utf-8",
    )

    (feature_dir / "contracts" / "demo.md").write_text(
        "\n".join(
            [
                "# Northbound Interface Design: Demo",
                "",
                "**Boundary Anchor (Required)**: HTTP `GET /demo`",
                f"**Anchor Status (Required)**: {contract_anchor_status}",
                "**Implementation Entry Anchor (Required)**: src/app/demo.py::DemoHandler.handle",
                "**Implementation Entry Anchor Status (Required)**: `existing`",
                "",
                "## Contract Binding",
                "- Repo Anchor: `src/boundary/demo.py::DemoBoundary`",
                "",
                "## Runtime Correctness Check",
                "",
                "| Runtime Check Item | Required Evidence | Anchor | Status |",
                "|--------------------|-------------------|--------|--------|",
                "| Boundary-to-entry reachability | sequence reaches entry | demo boundary chain | ok |",
                "| End-to-end chain continuity | contiguous request/response chain | demo contiguous steps | ok |",
                "| Field-ownership closure | contract fields mapped to UML owners | demo field owners | ok |",
                "| Sequence-participant UML closure | sequence participants mapped to UML classes/methods | demo participant mappings | ok |",
                "| New-field/method call linkage | new members and calls are marked and connected | demo new linkage | ok |",
            ]
        ),
        encoding="utf-8",
    )

    return feature_dir


def _run_planning_lint(feature_dir: Path) -> dict:
    def to_bash_path(p: Path) -> str:
        return str(p.resolve()).replace("\\", "/")

    completed = subprocess.run(
        [
            "bash",
            "scripts/bash/run-planning-lint.sh",
            "--feature-dir",
            to_bash_path(feature_dir),
            "--rules",
            to_bash_path(RULES_FILE),
            "--json",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_anchor_status_allowed_values_accepts_protocol_values(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path, test_matrix_status="existing")
    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] == 0


def test_anchor_status_allowed_values_rejects_out_of_enum_tokens(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path, test_matrix_status="anchored")
    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-RA-007" for f in payload["findings"])


def test_anchor_status_allowed_values_rejects_composite_table_tokens(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path, test_matrix_status="existing/new")
    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-RA-007" for f in payload["findings"])


def test_anchor_status_allowed_values_rejects_composite_label_tokens(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path, contract_anchor_status="`existing` and `new`")
    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-RA-007" for f in payload["findings"])


@pytest.mark.parametrize(
    ("row_marker", "rule_id"),
    [
        ("| End-to-end chain continuity |", "PLN-ID-007"),
        ("| Sequence-participant UML closure |", "PLN-ID-008"),
        ("| New-field/method call linkage |", "PLN-ID-009"),
    ],
)
def test_runtime_closure_rows_are_required_by_lint(tmp_path: Path, row_marker: str, rule_id: str):
    feature_dir = _write_feature_fixture(tmp_path)
    contract = feature_dir / "contracts" / "demo.md"
    lines = contract.read_text(encoding="utf-8").splitlines()
    filtered = [line for line in lines if row_marker not in line]
    contract.write_text("\n".join(filtered) + "\n", encoding="utf-8")

    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == rule_id for f in payload["findings"])

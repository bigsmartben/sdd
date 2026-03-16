import json
import subprocess
from pathlib import Path


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
    (feature_dir / "interface-details").mkdir(parents=True)

    (feature_dir / "data-model.md").write_text(
        "\n".join(
            [
                "# Data Model",
                "",
                "| Domain Element | Kind | Anchor Status | Repo Anchor |",
                "|---------------|------|---------------|-------------|",
                "| DemoAggregate | Aggregate | existing | src/domain/demo.py::DemoAggregate |",
            ]
        )
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
        )
    )

    (feature_dir / "contracts" / "demo.md").write_text(
        "\n".join(
            [
                "# Contract",
                "",
                "**Boundary Anchor**: HTTP `GET /demo`",
                f"**Anchor Status (Required)**: {contract_anchor_status}",
                "- Repo Anchor: `src/boundary/demo.py::DemoBoundary`",
            ]
        )
    )

    (feature_dir / "interface-details" / "demo.md").write_text(
        "\n".join(
            [
                "# Interface Detail",
                "",
                "**Boundary Anchor Status (Required)**: `existing`",
                "**Implementation Entry Anchor Status (Required)**: `existing`",
                "",
                "## Contract Binding Row",
                "",
                "## Implementation Entry Anchor",
                "",
                "## Runtime Correctness Check",
                "",
                "| Runtime Check Item | Required Evidence | Anchor | Status |",
                "|--------------------|-------------------|--------|--------|",
                "| Boundary-to-entry reachability | sequence reaches entry | demo boundary chain | ok |",
                "| Field-ownership closure | contract fields mapped to UML owners | demo field owners | ok |",
            ]
        )
    )

    return feature_dir


def _run_planning_lint(feature_dir: Path) -> dict:
    completed = subprocess.run(
        [
            "bash",
            str(LINT_SCRIPT),
            "--feature-dir",
            str(feature_dir.resolve()),
            "--rules",
            str(RULES_FILE.resolve()),
            "--json",
        ],
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

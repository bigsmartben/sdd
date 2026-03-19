import json
import shutil
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
    contract_boundary_anchor: str = "HTTP `GET /demo`",
    contract_entry_anchor: str | None = "src/app/demo.py::DemoHandler.handle",
    contract_entry_status: str = "`existing`",
    test_matrix_boundary_anchor: str = "HTTP `GET /demo`",
    packet_boundary_anchor: str = "HTTP GET /demo",
    packet_boundary_status: str = "existing",
    packet_entry_anchor: str = "src/app/demo.py::DemoHandler.handle",
    packet_entry_status: str = "existing",
    include_research_trigger: bool = False,
    plan_feature_status: str = "planning-in-progress",
    plan_boundary_anchor: str = "HTTP GET /demo",
    plan_entry_anchor: str = "src/app/demo.py::DemoHandler.handle",
    plan_boundary_status: str = "existing",
    plan_entry_status: str = "existing",
) -> Path:
    feature_dir = tmp_path / "feature"
    (feature_dir / "contracts").mkdir(parents=True)
    (tmp_path / "src" / "domain").mkdir(parents=True)
    (tmp_path / "src" / "boundary").mkdir(parents=True)
    (tmp_path / "src" / "app").mkdir(parents=True)

    (tmp_path / "src" / "domain" / "demo.py").write_text(
        "class DemoAggregate:\n    pass\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "boundary" / "demo.py").write_text(
        "class DemoBoundary:\n    def handle(self):\n        return 'ok'\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "app" / "demo.py").write_text(
        "class DemoHandler:\n    def handle(self):\n        return DemoResponse()\n\n"
        "class DemoResponse:\n    demoId = 'demo'\n",
        encoding="utf-8",
    )

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
                "## Scenario Matrix",
                "",
                "State Owner Anchor(s): src/domain/demo.py::DemoAggregate",
                "",
                "| TM ID | Operation ID | Boundary Anchor | IF Scope | Repo Anchor | Anchor Status | Path Type |",
                "|------|--------------|-----------------|----------|-------------|---------------|-----------|",
                f"| TM-001 | demoOp | {test_matrix_boundary_anchor} | IF-001 | src/boundary/demo.py::DemoBoundary | {test_matrix_status} | Main |",
                "",
                "## Verification Case Anchors",
                "",
                "| TC ID | TM ID | Operation ID | Boundary Anchor | IF Scope | Repo Anchor | Anchor Status | Verification Goal | Observability / Signal |",
                "|-------|-------|--------------|-----------------|----------|-------------|---------------|-------------------|------------------------|",
                f"| TC-001 | TM-001 | demoOp | {test_matrix_boundary_anchor} | IF-001 | src/boundary/demo.py::DemoBoundary | {test_matrix_status} | Verify demo payload | Demo payload is visible |",
                "",
                "## Binding Contract Packets",
                "",
                "| BindingRowID | Operation ID | IF Scope | Boundary Anchor | Boundary Anchor Status | Implementation Entry Anchor | Implementation Entry Anchor Status | Request DTO Anchor | Response DTO Anchor | Primary Collaborator Anchor | State Owner Anchor(s) | TM ID | TC IDs | Spec Ref(s) | Scenario Ref(s) | Success Ref(s) | Edge Ref(s) | Lifecycle Ref(s) | Invariant Ref(s) | Main Pass Anchor | Branch/Failure Anchor(s) |",
                "|--------------|--------------|----------|-----------------|------------------------|-----------------------------|------------------------------------|--------------------|--------------------|-----------------------------|-----------------------|-------|--------|-------------|-----------------|----------------|-------------|------------------|------------------|------------------|--------------------------|",
                f"| BR-001 | demoOp | IF-001 | {packet_boundary_anchor} | {packet_boundary_status} | {packet_entry_anchor} | {packet_entry_status} | N/A | src/app/demo.py::DemoResponse | N/A | [src/domain/demo.py::DemoAggregate] | TM-001 | [TC-001] | [UC-001, FR-001] | [S1] | [SC-001] | [EC-001] | [Lifecycle: DemoAggregate] | [INV-001] | happy path | retry path |",
            ]
        ),
        encoding="utf-8",
    )

    contract_lines = [
        "# Northbound Interface Design: Demo",
        "",
        f"**Boundary Anchor (Required)**: {contract_boundary_anchor}",
        f"**Anchor Status (Required)**: {contract_anchor_status}",
        "",
        "## Northbound Contract Summary",
        "",
        "### External I/O Summary",
        "- Request: GET /demo",
        "- Success Output: demo payload",
        "- Failure Output: error payload",
        "",
        "## Full Field Dictionary (Operation-scoped)",
        "",
        "| Field | Owner Class | Direction | Required/Optional | Default | Validation/Enum | Persisted | Contract-visible | Used in demoOp | Source Anchor |",
        "|-------|-------------|-----------|-------------------|---------|-----------------|-----------|------------------|----------------|---------------|",
        "| demoId | DemoResponse | output | required | none | uuid | no | yes | yes | `src/app/demo.py::DemoResponse.demoId` |",
    ]
    if contract_entry_anchor is not None:
        contract_lines.append(f"**Implementation Entry Anchor (Required)**: {contract_entry_anchor}")
    contract_lines.extend(
        [
            f"**Implementation Entry Anchor Status (Required)**: {contract_entry_status}",
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
    )
    (feature_dir / "contracts" / "demo.md").write_text("\n".join(contract_lines), encoding="utf-8")

    (feature_dir / "plan.md").write_text(
        "\n".join(
            [
                "# Planning Control Plane: Demo",
                "",
                "## Summary",
                "",
                "Demo planning control plane.",
                "",
                "## Shared Context Snapshot",
                "",
                "### Feature Identity",
                "",
                "- Feature: Demo",
                "- Scope anchor: `spec.md`",
                f"- Status: {plan_feature_status}",
                "",
                "### Stable Shared Inputs",
                "",
                "- Actors: Demo User",
                "- In Scope: demo flow",
                "- Out of Scope: none",
                "- Shared blockers: none",
                "",
                "### Repository-First Consumption Slice",
                "",
                "- Relevant dependency usage rows / `SIG-*`: none",
                "- Relevant module-edge rules: none",
                "",
                "## Stage Queue",
                "",
                "| Stage ID | Command | Required Inputs | Output Path | Status | Source Fingerprint | Output Fingerprint | Blocker |",
                "|----------|---------|-----------------|-------------|--------|--------------------|--------------------|---------|",
                "| research | `/sdd.plan.research` | `plan.md`, `spec.md` | `research.md` | done | spec | research | none |",
                "| data-model | `/sdd.plan.data-model` | `plan.md`, `spec.md`, `research.md` | `data-model.md` | done | spec+research | data-model | none |",
                "| test-matrix | `/sdd.plan.test-matrix` | `plan.md`, `spec.md`, `research.md`, `data-model.md` | `test-matrix.md` | done | spec+research+data-model | test-matrix | none |",
                "",
                "## Binding Projection Index",
                "",
                "| BindingRowID | UC ID | UIF ID | FR ID | IF ID / IF Scope | TM ID | TC IDs | Operation ID | Boundary Anchor | Implementation Entry Anchor | Boundary Anchor Status | Implementation Entry Anchor Status | Test Scope |",
                "|--------------|-------|--------|-------|------------------|-------|--------|--------------|-----------------|-----------------------------|------------------------|------------------------------------|------------|",
                f"| BR-001 | UC-001 | UIF-001 | FR-001 | IF-001 | TM-001 | TC-001 | demoOp | {plan_boundary_anchor} | {plan_entry_anchor} | {plan_boundary_status} | {plan_entry_status} | Integration |",
                "",
                "## Artifact Status",
                "",
                "| BindingRowID | Unit Type | Target Path | Status | Source Fingerprint | Output Fingerprint | Blocker |",
                "|--------------|-----------|-------------|--------|--------------------|--------------------|---------|",
                "| BR-001 | contract | `contracts/demo.md` | pending | test-matrix:demo | pending | none |",
                "",
                "## Handoff Protocol",
                "",
                "- `/sdd.plan` initializes this file and starts the queue.",
                "- `/sdd.plan.contract` advances `Artifact Status` one row at a time.",
                "- `/sdd.tasks` starts only after all required stage and artifact rows are `done`.",
                "",
                "## Complexity Tracking",
                "",
                "| Violation | Why Needed | Simpler Alternative Rejected Because |",
                "|-----------|------------|-------------------------------------|",
                "| none | n/a | n/a |",
            ]
        ),
        encoding="utf-8",
    )

    if include_research_trigger:
        (feature_dir / "research.md").write_text(
            "northbound APIs in web/controller should stay controller-first for HTTP routes\n"
            "web -> service handoff must happen after controller entry\n",
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


def _run_planning_lint_powershell(feature_dir: Path) -> dict:
    if shutil.which("pwsh") is None:
        pytest.skip("pwsh is not available")

    completed = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            "scripts/powershell/run-planning-lint.ps1",
            "-FeatureDir",
            str(feature_dir.resolve()),
            "-Rules",
            str(RULES_FILE.resolve()),
            "-Json",
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


def test_northbound_rule_flags_missing_label_entry_anchor_in_bash(tmp_path: Path):
    feature_dir = _write_feature_fixture(
        tmp_path,
        contract_entry_anchor=None,
        contract_boundary_anchor="HTTP GET /demo",
        include_research_trigger=True,
        test_matrix_boundary_anchor="event.demo.created",
    )

    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(
        f["rule_id"] == "PLN-NB-001" and "requires an Implementation Entry Anchor" in f["message"]
        for f in payload["findings"]
    )


def test_northbound_rule_flags_missing_label_entry_anchor_in_powershell(tmp_path: Path):
    feature_dir = _write_feature_fixture(
        tmp_path,
        contract_entry_anchor=None,
        contract_boundary_anchor="HTTP GET /demo",
        include_research_trigger=True,
        test_matrix_boundary_anchor="event.demo.created",
    )

    payload = _run_planning_lint_powershell(feature_dir)
    assert payload["findings_total"] > 0
    assert any(
        f["rule_id"] == "PLN-NB-001" and "requires an Implementation Entry Anchor" in f["message"]
        for f in payload["findings"]
    )


def test_northbound_rule_accepts_escaped_pipe_in_boundary_anchor_cells_bash(tmp_path: Path):
    feature_dir = _write_feature_fixture(
        tmp_path,
        include_research_trigger=True,
        contract_boundary_anchor=r"HTTP GET /demo\|v2",
        test_matrix_boundary_anchor=r"HTTP GET /demo\|v2",
        packet_boundary_anchor=r"HTTP GET /demo\|v2",
        plan_boundary_anchor=r"HTTP GET /demo\|v2",
    )
    payload = _run_planning_lint(feature_dir)
    assert not any(f["rule_id"] == "PLN-NB-001" for f in payload["findings"])


def test_northbound_rule_accepts_escaped_pipe_in_boundary_anchor_cells_powershell(tmp_path: Path):
    feature_dir = _write_feature_fixture(
        tmp_path,
        include_research_trigger=True,
        contract_boundary_anchor=r"HTTP GET /demo\|v2",
        test_matrix_boundary_anchor=r"HTTP GET /demo\|v2",
        packet_boundary_anchor=r"HTTP GET /demo\|v2",
        plan_boundary_anchor=r"HTTP GET /demo\|v2",
    )
    payload = _run_planning_lint_powershell(feature_dir)
    assert not any(f["rule_id"] == "PLN-NB-001" for f in payload["findings"])


def test_binding_tuple_projection_sync_accepts_aligned_artifacts(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    payload = _run_planning_lint(feature_dir)
    assert not any(f["rule_id"] == "PLN-BP-002" for f in payload["findings"])


def test_binding_tuple_projection_sync_flags_plan_projection_drift(tmp_path: Path):
    feature_dir = _write_feature_fixture(
        tmp_path,
        plan_entry_status="new",
        packet_entry_status="existing",
    )
    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-BP-002" for f in payload["findings"])


def test_repo_anchor_paths_must_resolve_to_real_files(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    data_model = feature_dir / "data-model.md"
    data_model.write_text(
        data_model.read_text(encoding="utf-8").replace(
            "src/domain/demo.py::DemoAggregate",
            "src/domain/missing_demo.py::DemoAggregate",
            1,
        ),
        encoding="utf-8",
    )

    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-RA-009" for f in payload["findings"])


def test_repo_anchor_paths_must_resolve_to_real_files_in_powershell(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    data_model = feature_dir / "data-model.md"
    data_model.write_text(
        data_model.read_text(encoding="utf-8").replace(
            "src/domain/demo.py::DemoAggregate",
            "src/domain/missing_demo.py::DemoAggregate",
            1,
        ),
        encoding="utf-8",
    )

    payload = _run_planning_lint_powershell(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-RA-009" for f in payload["findings"])


@pytest.mark.parametrize(
    ("section_marker", "rule_id"),
    [
        ("## Summary", "PLN-CP-001"),
        ("## Handoff Protocol", "PLN-CP-002"),
        ("## Complexity Tracking", "PLN-CP-003"),
    ],
)
def test_plan_required_sections_are_enforced(section_marker: str, rule_id: str, tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    plan = feature_dir / "plan.md"
    lines = plan.read_text(encoding="utf-8").splitlines()
    filtered = [line for line in lines if line != section_marker]
    plan.write_text("\n".join(filtered) + "\n", encoding="utf-8")

    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == rule_id for f in payload["findings"])


def test_plan_required_sections_accept_crlf_line_endings(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    plan = feature_dir / "plan.md"
    plan.write_bytes(plan.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))

    payload = _run_planning_lint(feature_dir)
    assert not any(
        f["rule_id"] in {"PLN-CP-001", "PLN-CP-002", "PLN-CP-003"}
        for f in payload["findings"]
    )


def test_plan_status_must_match_stage_and_artifact_progress(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path, plan_feature_status="planning-not-started")
    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-CP-004" for f in payload["findings"])


def test_binding_projection_index_rejects_todo_anchor_status_rows(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path, plan_boundary_status="todo")
    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-BP-001" for f in payload["findings"])

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
    contract_entry_anchor: str | None = "src/web/demo_controller.py::DemoController.handle",
    contract_entry_status: str = "`existing`",
    test_matrix_boundary_anchor: str = "HTTP `GET /demo`",
    packet_boundary_anchor: str = "HTTP GET /demo",
    packet_boundary_status: str = "existing",
    packet_entry_anchor: str = "src/web/demo_controller.py::DemoController.handle",
    packet_entry_status: str = "existing",
    include_research_trigger: bool = False,
    plan_feature_status: str = "planning-in-progress",
    plan_uif_path_refs: str = "[UIF-Path-001]",
    plan_udd_refs: str = "[UDD-001]",
    plan_test_scope: str = "Integration",
) -> Path:
    feature_dir = tmp_path / "feature"
    (feature_dir / "contracts").mkdir(parents=True)
    (tmp_path / "src" / "domain").mkdir(parents=True)
    (tmp_path / "src" / "boundary").mkdir(parents=True)
    (tmp_path / "src" / "app").mkdir(parents=True)
    (tmp_path / "src" / "web").mkdir(parents=True)

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
    (tmp_path / "src" / "web" / "demo_controller.py").write_text(
        "class DemoController:\n    def handle(self):\n        return 'ok'\n",
        encoding="utf-8",
    )

    (feature_dir / "data-model.md").write_text(
        "\n".join(
            [
                "# Data Model",
                "",
                "| Domain Element | Kind | Anchor Status | Repo Anchor | Anchor Role |",
                "|---------------|------|---------------|-------------|-------------|",
                "| DemoAggregate | Aggregate | existing | src/domain/demo.py::DemoAggregate | owner |",
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
                "| TM ID | Operation ID | Boundary Anchor | IF Scope | Repo Anchor | Repo Anchor Role | Anchor Status | Path Type |",
                "|------|--------------|-----------------|----------|-------------|------------------|---------------|-----------|",
                f"| TM-001 | demoOp | {test_matrix_boundary_anchor} | IF-001 | src/boundary/demo.py::DemoBoundary | boundary-owner | {test_matrix_status} | Main |",
                "",
                "## Verification Case Anchors",
                "",
                "| TC ID | TM ID | Operation ID | Boundary Anchor | IF Scope | Repo Anchor | Repo Anchor Role | Anchor Status | Verification Goal | Observability / Signal |",
                "|-------|-------|--------------|-----------------|----------|-------------|------------------|---------------|-------------------|------------------------|",
                f"| TC-001 | TM-001 | demoOp | {test_matrix_boundary_anchor} | IF-001 | src/boundary/demo.py::DemoBoundary | boundary-owner | {test_matrix_status} | Verify demo payload | Demo payload is visible |",
                "",
                "## Binding Contract Packets",
                "",
                "| BindingRowID | Operation ID | IF Scope | UIF Path Ref(s) | UDD Ref(s) | Boundary Anchor | Boundary Anchor Status | Implementation Entry Anchor | Implementation Entry Anchor Status | Request DTO Anchor | Response DTO Anchor | Primary Collaborator Anchor | State Owner Anchor(s) | TM ID | TC IDs | Test Scope | Spec Ref(s) | Scenario Ref(s) | Success Ref(s) | Edge Ref(s) | Lifecycle Ref(s) | Invariant Ref(s) | Main Pass Anchor | Branch/Failure Anchor(s) |",
                "|--------------|--------------|----------|-----------------|------------|-----------------|------------------------|-----------------------------|------------------------------------|--------------------|--------------------|-----------------------------|-----------------------|-------|--------|------------|-------------|-----------------|----------------|-------------|------------------|------------------|------------------|--------------------------|",
                f"| BR-001 | demoOp | IF-001 | [UIF-Path-001] | [UDD-001] | {packet_boundary_anchor} | {packet_boundary_status} | {packet_entry_anchor} | {packet_entry_status} | N/A | src/app/demo.py::DemoResponse | N/A | [src/domain/demo.py::DemoAggregate] | TM-001 | [TC-001] | Integration | [UC-001, FR-001] | [S1] | [SC-001] | [EC-001] | [Lifecycle: DemoAggregate] | [INV-001] | happy path | retry path |",
            ]
        ),
        encoding="utf-8",
    )

    contract_lines = [
        "# Northbound Interface Design: Demo",
        "",
        "**BindingRowID (Required)**: BR-001",
        "**Operation ID (Required)**: demoOp",
        "**IF Scope (Required)**: IF-001",
        f"**Boundary Anchor (Required)**: {contract_boundary_anchor}",
        f"**Anchor Status (Required)**: {contract_anchor_status}",
        "",
        "## Binding Context",
        "",
        "| Field | Value |",
        "|-------|-------|",
        "| `BindingRowID` | BR-001 |",
        "| `Operation ID` | demoOp |",
        "| `IF Scope` | IF-001 |",
        "| `UIF Path Ref(s)` | [UIF-Path-001] |",
        "| `UDD Ref(s)` | [UDD-001] |",
        "| `TM ID` | TM-001 |",
        "| `TC IDs` | [TC-001] |",
        "| `Test Scope` | Integration |",
        "| `Spec Ref(s)` | [UC-001, FR-001] |",
        "| `Scenario Ref(s)` | [S1] |",
        "| `Success Ref(s)` | [SC-001] |",
        "| `Edge Ref(s)` | [EC-001] |",
        "",
        "## Interface Definition",
        "",
        "### Contract Summary",
        "| Aspect | Definition |",
        "|--------|------------|",
        "| External Input | GET /demo |",
        "| Success Output | demo payload |",
        "| Failure Output | error payload |",
        "",
        "### Resolved Type Inventory",
        "| Role | Concrete Name | Resolution | Source / Evidence | Notes |",
        "|------|---------------|------------|-------------------|-------|",
        "| boundary-entry | src/web/demo_controller.py::DemoController.handle | existing | spec ref + repo anchor | controller entry |",
        "| request-dto | src/app/demo.py::DemoRequest | contract-defined | contract-local rationale | demo request type |",
        "| response-dto | src/app/demo.py::DemoResponse | existing | repo anchor | demo response type |",
        "",
        "## Full Field Dictionary (Operation-scoped)",
        "",
        "| Field | Owner Class | Dictionary Tier | Direction | Required/Optional | Default | Validation/Enum | Persisted | Contract-visible | Used in demoOp | Source Anchor |",
        "|-------|-------------|-----------------|-----------|-------------------|---------|-----------------|-----------|------------------|----------------|---------------|",
        "| demoId | DemoResponse | operation-critical | output | required | none | uuid | no | yes | yes | `src/app/demo.py::DemoResponse.demoId` |",
    ]
    if contract_entry_anchor is not None:
        contract_lines.append(f"**Implementation Entry Anchor (Required)**: {contract_entry_anchor}")
    contract_lines.extend(
        [
            f"**Implementation Entry Anchor Status (Required)**: {contract_entry_status}",
            "",
            "## Sequence Design",
            "- Boundary call enters controller and then reaches app handler.",
            "",
            "## Test Projection",
            "",
            "### Test Projection Slice",
            "",
            "| IF Scope | Operation ID | Test Scope | TM ID | TC ID(s) | Main Pass Anchor | Branch/Failure Anchor(s) | Command / Assertion Signal |",
            "|----------|--------------|------------|-------|----------|------------------|--------------------------|----------------------------|",
            "| IF-001 | demoOp | Integration | TM-001 | TC-001 | happy path | retry path | pytest -k demo |",
            "",
            "### Cross-Interface Smoke Candidate",
            "",
            "| Smoke Candidate ID | IF Scope | Operation ID | Candidate Role | Depends On Candidate ID(s) | Trigger | Main Pass Anchor | Branch/Failure Anchor(s) | Command / Assertion Signal |",
            "|--------------------|----------|--------------|----------------|----------------------------|---------|------------------|--------------------------|----------------------------|",
            "| SMK-001 | IF-001 | demoOp | entry | N/A | demo trigger | happy path | retry path | pytest -k demo |",
            "",
            "## Closure Check",
            "",
            "| Check Item | Required Evidence | Status |",
            "|------------|-------------------|--------|",
            "| Interface-definition closure | request/response surface + full field dictionary + shared semantic reuse are all present | ok |",
            "| UML closure | class diagram and two-party package relations both present and consistent with sequence | ok |",
            "| Sequence closure | success/failure paths include mandatory second-party, third-party, and middleware calls | ok |",
            "| Test closure | `TM/TC`, pass/failure anchors, and command/assertion signal are present | ok |",
            "",
            "## Upstream References",
            "- repo anchors: [src/boundary/demo.py::DemoBoundary, src/app/demo.py::DemoResponse]",
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
                "| test-matrix | `/sdd.plan.test-matrix` | `plan.md`, `spec.md` | `test-matrix.md` | done | spec | test-matrix | none |",
                "| data-model | `/sdd.plan.data-model` | `plan.md`, `spec.md`, `test-matrix.md` | `data-model.md` | done | spec+test-matrix | data-model | none |",
                "",
                "## Binding Projection Index",
                "",
                "| BindingRowID | UC ID | UIF ID | FR ID | IF ID / IF Scope | TM ID | TC IDs | Operation ID | UIF Path Ref(s) | UDD Ref(s) | Test Scope |",
                "|--------------|-------|--------|-------|------------------|-------|--------|--------------|-----------------|------------|------------|",
                f"| BR-001 | UC-001 | UIF-001 | FR-001 | IF-001 | TM-001 | TC-001 | demoOp | {plan_uif_path_refs} | {plan_udd_refs} | {plan_test_scope} |",
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
        ("| Sequence closure |", "PLN-ID-007"),
        ("| UML closure |", "PLN-ID-008"),
        ("| Test closure |", "PLN-ID-009"),
        ("### Cross-Interface Smoke Candidate", "PLN-ID-014"),
        ("### Resolved Type Inventory", "PLN-ID-015"),
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


def test_udd_refs_are_required_in_test_matrix(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    test_matrix = feature_dir / "test-matrix.md"
    content = test_matrix.read_text(encoding="utf-8")
    content = content.replace("UDD Ref(s)", "UDD References")
    test_matrix.write_text(content, encoding="utf-8")

    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-RA-012" for f in payload["findings"])


def test_test_projection_slice_is_required_in_contract(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    contract = feature_dir / "contracts" / "demo.md"
    content = contract.read_text(encoding="utf-8")
    content = content.replace("### Test Projection Slice", "### Projection Slice")
    contract.write_text(content, encoding="utf-8")

    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-ID-012" for f in payload["findings"])


def test_dictionary_tier_is_required_in_contract_field_dictionary(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    contract = feature_dir / "contracts" / "demo.md"
    content = contract.read_text(encoding="utf-8")
    content = content.replace("Dictionary Tier", "Tier")
    contract.write_text(content, encoding="utf-8")

    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-ID-013" for f in payload["findings"])


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
        plan_udd_refs="[UDD-999]",
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
        f["rule_id"] in {"PLN-CP-001", "PLN-CP-002"}
        for f in payload["findings"]
    )


def test_plan_status_must_match_stage_and_artifact_progress(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path, plan_feature_status="planning-not-started")
    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-CP-004" for f in payload["findings"])


def test_binding_projection_index_rejects_contract_design_columns(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    plan = feature_dir / "plan.md"
    plan.write_text(
        plan.read_text(encoding="utf-8").replace(
            "| BindingRowID | UC ID | UIF ID | FR ID | IF ID / IF Scope | TM ID | TC IDs | Operation ID | UIF Path Ref(s) | UDD Ref(s) | Test Scope |",
            "| BindingRowID | UC ID | UIF ID | FR ID | IF ID / IF Scope | TM ID | TC IDs | Operation ID | UIF Path Ref(s) | UDD Ref(s) | Boundary Anchor | Test Scope |",
        ),
        encoding="utf-8",
    )
    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-BP-001" for f in payload["findings"])

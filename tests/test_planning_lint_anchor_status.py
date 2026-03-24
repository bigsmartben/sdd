import json
import shutil
import subprocess
from pathlib import Path

import pytest

ANCHOR_STATUSES = {"existing", "extended", "new", "todo"}


REPO_ROOT = Path(__file__).resolve().parents[1]
LINT_SCRIPT = REPO_ROOT / "scripts" / "bash" / "run-planning-lint.sh"
RULES_FILE = REPO_ROOT / "rules" / "planning-lint-rules.tsv"


def _replace_exact(content: str, old: str, new: str, count: int = 1) -> str:
    updated = content.replace(old, new, count)
    assert updated != content, f"expected marker not found: {old}"
    return updated


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
    plan_packet_source: str = "test-matrix.md#Binding Packets:BR-001",
    plan_test_scope: str = "Integration",
    data_model_strategy_evidence: str | None = None,
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

    if data_model_strategy_evidence is None:
        data_model_strategy_evidence = (
            "existing and extended reviewed; new shared semantic owner is required"
            if test_matrix_status == "new"
            else "N/A"
        )

    (feature_dir / "data-model.md").write_text(
        "\n".join(
            [
                "# Data Model",
                "",
                "## Shared Semantic Class Model",
                "",
                "```mermaid",
                "classDiagram",
                "    class DemoAggregate",
                "```",
                "",
                "## Shared Lifecycle State Machines",
                "",
                "### Lifecycle Summary",
                "",
                "| Lifecycle Ref | State Owner | Stable States | Invariant Ref(s) | Consumed By BindingRowID(s) | Required Model |",
                "|---------------|-------------|---------------|------------------|-----------------------------|----------------|",
                "| LC-001 | DemoAggregate.status | [`Open`, `Closed`] | [INV-001] | [BR-001] | Lightweight |",
                "",
                "### State Transition Table",
                "",
                "| Lifecycle Ref | From State | Trigger / Condition | To State | Transition Type | Notes / Invariant Ref(s) | Consumed By BindingRowID(s) |",
                "|---------------|------------|---------------------|----------|-----------------|--------------------------|-----------------------------|",
                "| LC-001 | `Open` | complete | `Closed` | allowed | [INV-001] | [BR-001] |",
                "",
                "| SSE ID | Kind | Name | Business Meaning | Primary UDD Ref(s) | Primary Spec Ref(s) | Consumed By BindingRowID(s) | Anchor Status | Repo-First Strategy Evidence | Repo Anchor | Anchor Role | Status |",
                "|--------|------|------|------------------|--------------------|---------------------|-----------------------------|---------------|------------------------------|-------------|-------------|--------|",
                f"| SSE-001 | entity | DemoAggregate | demo | [UDD-001] | [FR-001] | [BR-001] | {test_matrix_status} | {data_model_strategy_evidence} | src/domain/demo.py::DemoAggregate | owner | defined |",
                "",
                "## Owner / Source Alignment",
                "",
                "| OSA ID | Semantic Ref | Owner Class / Semantic Owner | Source Type | Source Ref(s) | Consumed Field / Concept | Consumed By BindingRowID(s) | Notes |",
                "|--------|--------------|------------------------------|-------------|---------------|--------------------------|-----------------------------|-------|",
                "| OSA-001 | SSE-001 | DemoAggregate | authoritative | [UDD-001] | Demo aggregate | [BR-001] | Stable owner |",
                "",
                "## Shared Field Vocabulary",
                "",
                "| SFV ID | Semantic Owner | Meaning | Primary UDD Ref(s) | Required Semantics | Null / Boundary Rule | Shared By BindingRowID(s) |",
                "|--------|----------------|---------|--------------------|--------------------|----------------------|---------------------------|",
                "| SFV-001 | DemoAggregate.demoId | Demo identifier | [UDD-001] | Stable demo identity | Never null | [BR-001] |",
                "",
                "## Downstream Contract Constraints",
                "",
                "| DCC ID | BindingRowID | Required Shared Semantic Ref(s) | Constraint Type | Contract Impact |",
                "|--------|--------------|---------------------------------|-----------------|-----------------|",
                "| DCC-001 | BR-001 | [SSE-001, OSA-001, SFV-001] | owner | Reuse shared demo aggregate semantics |",
            ]
        ),
        encoding="utf-8",
    )

    (feature_dir / "test-matrix.md").write_text(
        "\n".join(
            [
                "# Test Matrix",
                "",
                "## Interface Partition Decisions",
                "",
                "| BindingRowID | User Intent | Trigger Ref(s) | Request Semantics | Visible Result | Side Effect | Repo Landing Hint | Split Rationale |",
                "|--------------|-------------|----------------|-------------------|----------------|-------------|-------------------|-----------------|",
                "| BR-001 | Demo intent | [UIF-001.trigger] | Input semantics only | Visible demo result | none | demo-entry-family | Single northbound demo action |",
                "",
                "## UIF Full Path Coverage Graph (Mermaid)",
                "",
                "```mermaid",
                "flowchart TD",
                "    Start --> Success",
                "```",
                "",
                "## UIF Path Coverage Ledger",
                "",
                "| UIF Path Ref | Path Type | Included in Graph | Omission Reason |",
                "|--------------|-----------|-------------------|-----------------|",
                "| UIF-Path-001 | Happy | yes | N/A |",
                "",
                "## Scenario Matrix",
                "",
                "Purpose: test semantics only; no interface-design closure.",
                "",
                "| TM ID | BindingRowID | Path Type | Scenario | Preconditions | Expected Outcome | Related Ref |",
                "|-------|--------------|-----------|----------|---------------|------------------|-------------|",
                f"| TM-001 | BR-001 | Happy | Scenario summary | Required setup | Observable outcome | [UC-001] |",
                "",
                "## Verification Case Anchors",
                "",
                "| TC ID | BindingRowID | TM ID | Verification Goal | Observability / Signal | Related Ref |",
                "|-------|--------------|-------|-------------------|------------------------|-------------|",
                f"| TC-001 | BR-001 | TM-001 | Verify demo payload | Demo payload is visible | [FR-001] |",
                "",
                "## Binding Packets",
                "",
                "| BindingRowID | IF Scope | User Intent | Trigger Ref(s) | Request Semantics | Visible Result | Side Effect | Boundary Notes | Repo Landing Hint | UIF Path Ref(s) | UDD Ref(s) | Primary TM IDs | TM IDs | TC IDs | Test Scope | Spec Ref(s) | Scenario Ref(s) | Success Ref(s) | Edge Ref(s) |",
                "|--------------|----------|-------------|----------------|-------------------|----------------|-------------|----------------|-------------------|-----------------|------------|----------------|--------|--------|------------|-------------|-----------------|----------------|-------------|",
                f"| BR-001 | IF-001 | Northbound action summary | [UIF-001.trigger] | Input semantics only | Visible result semantics | none | N/A | {packet_boundary_anchor} | [UIF-Path-001] | [UDD-001] | [TM-001] | [TM-001] | [TC-001] | {plan_test_scope} | [UC-001, FR-001] | [S1] | [SC-001] | [EC-001] |",
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
        "**Boundary Anchor Strategy Evidence (Required)**: N/A",
        "",
        "## Artifact Quality Signals (Normative)",
        "- Must: be strong enough for implementation to start without reopening basics.",
        "",
        "## Northbound Entry Rules (Normative)",
        "- Boundary Anchor MUST remain the first consumer-callable entry.",
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
        "| `Primary TM IDs` | [TM-001] |",
        "| `TM IDs` | [TM-001] |",
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
        "### Shared Semantic Reuse",
        "| Shared Semantic Ref | Constraint Type (Required Enum) | Applied To | Impact on Contract |",
        "|---------------------|---------------------------------|------------|--------------------|",
        "| SSE-001 | shared-semantic-element | request | Reuse shared semantic naming and meaning from data model. |",
        "",
        "## UML Class Design",
        "",
        "### Resolved Type Inventory",
        "| Role | Concrete Name | Resolution | Source / Evidence | Notes |",
        "|------|---------------|------------|-------------------|-------|",
        "| boundary-entry | src/web/demo_controller.py::DemoController.handle | existing | spec ref + repo anchor | controller entry |",
        "| request-dto | src/app/demo.py::DemoRequest | new | contract-local rationale | demo request type |",
        "| response-dto | src/app/demo.py::DemoResponse | existing | repo anchor | demo response type |",
        "",
        "### Two-Party Package Relations",
        "| From Package | To Package | Relation Type | Covered Classes | Reason |",
        "|--------------|------------|---------------|-----------------|--------|",
        "| web | app | calls | DemoController, DemoHandler | HTTP boundary handoff |",
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
            "**Implementation Entry Anchor Strategy Evidence (Required)**: N/A",
            "",
            "## Sequence Design",
            "- Boundary call enters controller and then reaches app handler.",
            "",
            "## Test Projection",
            "",
            "### Test Projection Slice",
            "",
            "| IF Scope | Operation ID | Test Scope | Primary TM IDs | TM ID(s) | TC ID(s) | Main Pass Anchor | Branch/Failure Anchor(s) | Command / Assertion Signal |",
            "|----------|--------------|------------|----------------|----------|----------|------------------|--------------------------|----------------------------|",
            "| IF-001 | demoOp | Integration | [TM-001] | [TM-001] | [TC-001] | happy path | retry path | pytest -k demo |",
            "",
            "### Cross-Interface Smoke Candidate (Required)",
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
            "",
            "## Boundary Notes",
            "- Demo contract stays controller-first and keeps shared semantics upstream.",
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
                "| Stage ID | Command | Required Inputs | Output Path | Status | Blocker |",
                "|----------|---------|-----------------|-------------|--------|---------|",
                "| research | `/sdd.plan.research` | `plan.md`, `spec.md` | `research.md` | done | none |",
                "| test-matrix | `/sdd.plan.test-matrix` | `plan.md`, `spec.md` | `test-matrix.md` | done | none |",
                "| data-model | `/sdd.plan.data-model` | `plan.md`, `spec.md`, `test-matrix.md` | `data-model.md` | done | none |",
                "",
                "## Binding Projection Index",
                "",
                "| BindingRowID | Packet Source |",
                "|--------------|---------------|",
                f"| BR-001 | {plan_packet_source} |",
                "",
                "## Artifact Status",
                "",
                "| BindingRowID | Unit Type | Target Path | Status | Blocker |",
                "|--------------|-----------|-------------|--------|---------|",
                "| BR-001 | contract | `contracts/demo.md` | pending | none |",
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


def test_anchor_status_allowed_values_accepts_new(tmp_path: Path):
    feature_dir = _write_feature_fixture(
        tmp_path,
        test_matrix_status="new",
        contract_anchor_status="`new`",
        contract_boundary_anchor="DemoBoundary.start",
        contract_entry_anchor="DemoEntry.handle",
        contract_entry_status="`new`",
        test_matrix_boundary_anchor="DemoBoundary.start",
        packet_boundary_anchor="DemoBoundary.start",
        packet_boundary_status="new",
        packet_entry_anchor="DemoEntry.handle",
        packet_entry_status="new",
    )
    # Override strategy evidence to provide proper format for "new" anchors
    contract = feature_dir / "contracts" / "demo.md"
    content = contract.read_text(encoding="utf-8")
    content = content.replace(
        "**Boundary Anchor Strategy Evidence (Required)**: N/A",
        "**Boundary Anchor Strategy Evidence (Required)**: existing rejected: none; extended rejected: none",
    )
    content = content.replace(
        "**Implementation Entry Anchor Strategy Evidence (Required)**: N/A",
        "**Implementation Entry Anchor Strategy Evidence (Required)**: existing rejected: none; extended rejected: none",
    )
    contract.write_text(content, encoding="utf-8")

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
    # Filter for RA-007 as other rules might trigger too (like strategy evidence)
    assert any(f["rule_id"] == "PLN-RA-007" for f in payload["findings"])


def test_anchor_strategy_evidence_required_when_new_anchor_missing_rejections(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path, contract_anchor_status="`new`")
    contract = feature_dir / "contracts" / "demo.md"
    content = contract.read_text(encoding="utf-8")
    content = _replace_exact(
        content,
        "**Boundary Anchor Strategy Evidence (Required)**: N/A",
        "**Boundary Anchor Strategy Evidence (Required)**: logic required it",
    )
    contract.write_text(content, encoding="utf-8")

    payload = _run_planning_lint(feature_dir)
    assert any(f["rule_id"] == "PLN-RA-017" for f in payload["findings"])


def test_anchor_strategy_evidence_accepts_required_rejections(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path, contract_anchor_status="`new`")
    contract = feature_dir / "contracts" / "demo.md"
    content = contract.read_text(encoding="utf-8")
    content = _replace_exact(
        content,
        "**Boundary Anchor Strategy Evidence (Required)**: N/A",
        "**Boundary Anchor Strategy Evidence (Required)**: existing rejected: none; extended rejected: none",
    )
    contract.write_text(content, encoding="utf-8")

    payload = _run_planning_lint(feature_dir)
    assert not any(f["rule_id"] == "PLN-RA-017" for f in payload["findings"])


@pytest.mark.parametrize(
    ("row_marker", "rule_id"),
    [
        ("## Artifact Quality Signals (Normative)", "PLN-ID-016"),
        ("## Northbound Entry Rules (Normative)", "PLN-ID-017"),
        ("### Two-Party Package Relations", "PLN-ID-018"),
        ("| Sequence closure |", "PLN-ID-007"),
        ("| UML closure |", "PLN-ID-008"),
        ("| Test closure |", "PLN-ID-009"),
        ("### Cross-Interface Smoke Candidate (Required)", "PLN-ID-014"),
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


@pytest.mark.parametrize(
    ("section_marker", "rule_id"),
    [
        ("## Interface Partition Decisions", "PLN-TM-001"),
        ("## UIF Full Path Coverage Graph (Mermaid)", "PLN-TM-002"),
        ("## UIF Path Coverage Ledger", "PLN-TM-003"),
        ("## Scenario Matrix", "PLN-TM-004"),
        ("## Verification Case Anchors", "PLN-TM-005"),
    ],
)
def test_latest_test_matrix_sections_are_required_by_lint(tmp_path: Path, section_marker: str, rule_id: str):
    feature_dir = _write_feature_fixture(tmp_path)
    test_matrix = feature_dir / "test-matrix.md"
    lines = test_matrix.read_text(encoding="utf-8").splitlines()
    filtered = [line for line in lines if line != section_marker]
    test_matrix.write_text("\n".join(filtered) + "\n", encoding="utf-8")

    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == rule_id for f in payload["findings"])


@pytest.mark.parametrize(
    ("section_marker", "rule_id"),
    [
        ("## Shared Semantic Class Model", "PLN-DM-001"),
        ("## Owner / Source Alignment", "PLN-DM-002"),
        ("## Shared Field Vocabulary", "PLN-DM-003"),
        ("## Downstream Contract Constraints", "PLN-DM-004"),
        ("### State Transition Table", "PLN-DM-005"),
    ],
)
def test_latest_data_model_sections_are_required_by_lint(tmp_path: Path, section_marker: str, rule_id: str):
    feature_dir = _write_feature_fixture(tmp_path)
    data_model = feature_dir / "data-model.md"
    lines = data_model.read_text(encoding="utf-8").splitlines()
    filtered = [line for line in lines if line != section_marker]
    data_model.write_text("\n".join(filtered) + "\n", encoding="utf-8")

    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == rule_id for f in payload["findings"])


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


def test_shared_semantic_reuse_enum_validation(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    contract = feature_dir / "contracts" / "demo.md"
    content = contract.read_text(encoding="utf-8")
    content = _replace_exact(
        content,
        "| SSE-001 | shared-semantic-element | request | Reuse shared semantic naming and meaning from data model. |",
        "| SSE-001 | invalid-type | request | Reuse shared semantic naming and meaning from data model. |",
    )
    contract.write_text(content, encoding="utf-8")

    payload = _run_planning_lint(feature_dir)
    assert any(f["rule_id"] == "PLN-RA-015" for f in payload["findings"])


def test_contract_placeholder_detection(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    contract = feature_dir / "contracts" / "demo.md"
    content = contract.read_text(encoding="utf-8")
    content += "\nSome placeholder like [operationId] or <BoundaryRequestModel>\n"
    contract.write_text(content, encoding="utf-8")

    payload = _run_planning_lint(feature_dir)
    assert any(f["rule_id"] == "PLN-RA-016" for f in payload["findings"])


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
        plan_packet_source="test-matrix.md#Binding Packets:BR-999",
    )
    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-BP-002" for f in payload["findings"])


def test_data_model_requires_repo_first_strategy_evidence_column(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    data_model = feature_dir / "data-model.md"
    data_model.write_text(
        data_model.read_text(encoding="utf-8").replace("Repo-First Strategy Evidence | ", "", 1),
        encoding="utf-8",
    )

    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-DM-006" for f in payload["findings"])


def test_data_model_contract_flavored_names_are_rejected(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    data_model = feature_dir / "data-model.md"
    data_model.write_text(
        data_model.read_text(encoding="utf-8").replace("DemoAggregate", "DemoViewDTO"),
        encoding="utf-8",
    )

    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-DM-007" for f in payload["findings"])


def test_data_model_interface_role_names_are_rejected(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    data_model = feature_dir / "data-model.md"
    data_model.write_text(
        data_model.read_text(encoding="utf-8").replace("DemoAggregate", "DemoService"),
        encoding="utf-8",
    )

    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-DM-008" for f in payload["findings"])


def test_data_model_new_anchors_require_strategy_evidence(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path, test_matrix_status="new", data_model_strategy_evidence="N/A")
    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-DM-009" for f in payload["findings"])


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


def test_research_repo_anchors_reject_directory_only_paths(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    (feature_dir / "research.md").write_text(
        "\n".join(
            [
                "# Research",
                "",
                "## Repository Reuse Anchors (Source Code Only)",
                "",
                "| Anchor | Source Path / Symbol | Reuse Intent |",
                "|--------|----------------------|--------------|",
                "| `aidm-api` | `aidm-api/` | Reuse as contract boundary. |",
            ]
        ),
        encoding="utf-8",
    )

    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-RA-014" for f in payload["findings"])


def test_research_repo_anchors_reject_directory_only_paths_in_powershell(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    (feature_dir / "research.md").write_text(
        "\n".join(
            [
                "# Research",
                "",
                "## Repository Reuse Anchors (Source Code Only)",
                "",
                "| Anchor | Source Path / Symbol | Reuse Intent |",
                "|--------|----------------------|--------------|",
                "| `aidm-api` | `aidm-api/` | Reuse as contract boundary. |",
            ]
        ),
        encoding="utf-8",
    )

    payload = _run_planning_lint_powershell(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-RA-014" for f in payload["findings"])


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


def test_plan_status_missing_marker_reports_clean_message_in_bash(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    plan = feature_dir / "plan.md"
    plan.write_text(
        plan.read_text(encoding="utf-8").replace("- Status: planning-in-progress\n", ""),
        encoding="utf-8",
    )

    payload = _run_planning_lint(feature_dir)
    finding = next(f for f in payload["findings"] if f["rule_id"] == "PLN-CP-004")
    assert "Feature Identity -> Status" in finding["message"]
    assert "command not found" not in finding["message"]


def test_binding_projection_index_rejects_contract_design_columns(tmp_path: Path):
    feature_dir = _write_feature_fixture(tmp_path)
    plan = feature_dir / "plan.md"
    plan.write_text(
        plan.read_text(encoding="utf-8").replace(
            "| BindingRowID | Packet Source |",
            "| BindingRowID | Packet Source | Boundary Anchor |",
        ),
        encoding="utf-8",
    )
    payload = _run_planning_lint(feature_dir)
    assert payload["findings_total"] > 0
    assert any(f["rule_id"] == "PLN-BP-001" for f in payload["findings"])

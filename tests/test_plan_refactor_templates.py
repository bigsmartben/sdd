from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_plan_command_uses_new_workflow_order_and_drops_quickstart():
    content = read("templates/commands/plan.md")

    assert "quickstart.md" not in content
    assert "Data Model & Contracts" not in content
    assert "Agent Context Update" not in content

    stage_markers = [
        "## Stage 0: Research",
        "## Stage 1: Data Model",
        "## Stage 2: Feature Verification Design",
        "## Stage 3: Contracts",
        "## Stage 4: Interface Detailed Design",
    ]

    positions = [content.index(marker) for marker in stage_markers]
    assert positions == sorted(positions)

    stage_templates = [
        "templates/research-template.md",
        "templates/data-model-template.md",
        "templates/test-matrix-template.md",
        "templates/contract-template.md",
        "templates/interface-detail-template.md",
    ]

    for template in stage_templates:
        assert template in content


def test_plan_command_uses_context_minimization_and_sequential_generation():
    content = read("templates/commands/plan.md")

    assert "Bootstrap shared context only" in content
    assert "Do not preload stage templates or completed stage artifacts before they are needed." in content
    assert "Treat `plan.md` as the planning compression ledger" in content
    assert "read only that stage's template plus the minimum upstream artifacts required for that stage" in content
    assert "write a 3-7 bullet downstream projection note set" in content
    assert "Do not write retrospective recaps or generic stage summaries" in content
    assert "generate one contract artifact at a time" in content
    assert "generate one detail artifact at a time" in content
    assert "keep only the active tuple (`Operation ID`, `Boundary Anchor`, `IF Scope`) in working context" in content


def test_plan_template_is_structure_only_for_new_workflow():
    content = read("templates/plan-template.md")

    assert "Stage Overview" not in content
    assert "Design Terminology Boundaries" not in content
    assert "Stage 3 Quality Gate" not in content
    assert "quickstart.md" not in content

    required_sections = [
        "## Workflow Loop",
        "## Stage 0 Research",
        "## Stage 1 Data Model",
        "## Stage 2 Feature Verification Design",
        "## Stage 3 Contracts",
        "## Stage 4 Interface Detailed Design",
    ]

    for section in required_sections:
        assert section in content

    assert "templates/" in content
    assert "## Contract Binding" not in content
    assert "## Behavior Paths" not in content
    assert "## Sequence Diagram" not in content
    assert "`Compress`" in content
    assert content.count("### Downstream Projection") == 5


def test_planning_stage_templates_exist_and_define_split_artifacts():
    expected_templates = {
        "templates/research-template.md": [
            "# Research: [FEATURE]",
            "## Decisions",
            "## Repository Reuse Anchors",
        ],
        "templates/data-model-template.md": [
            "# Data Model: [FEATURE]",
            "## Backbone UML",
            "## Shared Invariants",
        ],
        "templates/test-matrix-template.md": [
            "# Feature Verification Design: [FEATURE]",
            "## Scenario Matrix",
            "## Verification Case Anchors",
        ],
        "templates/contract-template.md": [
            "# Contract: [BOUNDARY OR OPERATION]",
            "This template is format-agnostic.",
            "## External I/O Summary",
        ],
        "templates/interface-detail-template.md": [
            "# Interface Detail: [operationId]",
            "**Operation ID (Required)**: [operationId]",
            "## Sequence Diagram",
        ],
    }

    for rel_path, markers in expected_templates.items():
        content = read(rel_path)
        for marker in markers:
            assert marker in content


def test_downstream_templates_docs_and_scripts_match_refactor_baseline():
    assert "quickstart.md" not in read("templates/commands/tasks.md")
    assert "quickstart.md" not in read("templates/tasks-template.md")
    assert "quickstart.md" not in read("templates/commands/implement.md")
    assert "quickstart.md" not in read("templates/spec-template.md")
    assert "quickstart.md" not in read("scripts/bash/check-prerequisites.sh")
    assert "quickstart.md" not in read("scripts/powershell/check-prerequisites.ps1")
    assert "QUICKSTART" not in read("scripts/bash/common.sh")
    assert "QUICKSTART" not in read("scripts/powershell/common.ps1")
    assert "quickstart.md" not in read("README.md")
    assert "quickstart.md" not in read("spec-driven.md")

    tasks_command = read("templates/commands/tasks.md")
    assert (
        "**Required**: `plan.md`, `spec.md`, `data-model.md`, `test-matrix.md`, `contracts/`, `interface-details/`"
        in tasks_command
    )

    tasks_template = read("templates/tasks-template.md")
    assert "| `test-matrix.md` | feature verification anchors (`TM-*` / `TC-*`) | Yes |" in tasks_template

    mapping_doc = read("docs/command-template-mapping.md")
    assert "`plan-template.md` plus `research-template.md`, `data-model-template.md`, `test-matrix-template.md`, `contract-template.md`, and `interface-detail-template.md`" in mapping_doc
    assert "`research-template.md` defines `research.md`." in mapping_doc

    readme = read("README.md")
    assert "contract-template.md" in readme
    assert "/sdd.plan` uses `plan-template.md` for `plan.md`, and the planning templates in `templates/`" in readme


def test_template_hard_binding_fields_for_test_contract_and_interface_are_present():
    test_matrix = read("templates/test-matrix-template.md")
    assert "## Stable Binding Keys (Required)" in test_matrix
    assert "| TM ID | Operation ID | Boundary Anchor | IF Scope |" in test_matrix
    assert "| TC ID | TM ID | Operation ID | Boundary Anchor | IF Scope |" in test_matrix
    assert "Keep the matrix minimal-but-sufficient" in test_matrix

    contract = read("templates/contract-template.md")
    assert "**IF Scope (Required)**: [IF-### or N/A]" in contract
    assert "**Operation ID (Required)**: [operationId or N/A]" in contract
    assert "**Boundary Anchor (Required)**:" in contract
    assert "| Operation ID | Boundary Anchor | Operation / Interaction |" in contract

    interface_detail = read("templates/interface-detail-template.md")
    assert "**Boundary Anchor (Required)**:" in interface_detail
    assert "**Contract Binding Row (Required)**:" in interface_detail
    assert "| Path | Trigger | Key Steps | Outcome | Contract-Visible Failure | Sequence Ref | TM/TC Anchor |" in interface_detail
    assert "Keep this document operation-local and minimal" in interface_detail
    assert "Keep only materially distinct paths." in interface_detail

    tasks_command = read("templates/commands/tasks.md")
    assert "stable tuple keys (`Operation ID`, `Boundary Anchor`, `IF Scope`)" in tasks_command
    assert "tuple alignment" in tasks_command

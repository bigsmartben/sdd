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
    assert "Build the runtime work queue before each stage" in content
    assert "This runtime scheduling guidance is execution-only." in content
    assert "Keep only three context tiers active" in content
    assert "Turn each stage into one parent task with bounded subtasks: `Discover -> Generate -> Compress`." in content
    assert "discard its detailed working set and carry forward only stable anchors" in content
    assert "read only that stage's template plus the minimum upstream artifacts required for that stage" in content
    assert "write a 3-7 bullet downstream projection note set" in content
    assert "Do not write retrospective recaps or generic stage summaries" in content
    assert "generate one contract artifact at a time" in content
    assert "generate one detail artifact at a time" in content
    assert "keep only the active tuple (`Operation ID`, `Boundary Anchor`, `IF Scope`) in working context" in content
    assert "repo anchor` means source-code files/symbols plus `.specify/memory/constitution.md` only" in content
    assert "`README.md`, `docs/**`, `specs/**`, historical examples, and generated artifacts" in content
    assert "Parallelism inside `/sdd.plan`" not in content
    assert "Prefer facade / boundary / stable symbol anchors before implementation-layer internals" not in content


def test_tasks_command_uses_context_scheduling_without_semantic_drift():
    content = read("templates/commands/tasks.md")

    assert "Build the runtime task-generation queue before broad reads" in content
    assert "This runtime scheduling guidance is execution-only." in content
    assert "Keep only three context tiers active" in content
    assert "**Bootstrap packet**" in content
    assert "**Unit workset**" in content
    assert "**Task card**: exactly one active generation target at a time" in content
    assert "GLOBAL inventory and foundation -> one IF Scope at a time -> final DAG synthesis and document assembly" in content
    assert "Discover -> Generate -> Compress" in content
    assert "hard execution safety gates only" in content
    assert "substitute for the centralized comprehensive audit in `/sdd.analyze`" in content
    assert "discard its detailed local working set and carry forward only stable delivery anchors" in content
    assert "Prefer section-level or row-level rereads over whole-file replay" in content
    assert "synthesize the full **Task DAG** adjacency list from the compressed unit outputs" in content


def test_tasks_command_requires_manifest_sidecar_generation_with_minimum_fields():
    content = read("templates/commands/tasks.md")

    assert "Generate/refresh `tasks.manifest.json` sidecar" in content
    assert "same directory as `tasks.md`" in content
    assert "machine-readable projection" in content
    assert "task_id" in content
    assert "dependencies" in content
    assert "if_scope" in content
    assert "refs" in content
    assert "target_paths" in content
    assert "completion_anchors" in content
    assert "conflict_hints" in content
    assert "status` (initialize to `pending`)" in content


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
    assert "Quality Snapshot" not in content
    assert "`Compress`" in content
    assert content.count("### Downstream Projection") == 5


def test_planning_stage_templates_exist_and_define_split_artifacts():
    expected_templates = {
        "templates/research-template.md": [
            "# Research: [FEATURE]",
            "## Decisions",
            "## Repository Reuse Anchors",
            "Do not treat `README.md`, `docs/**`, `specs/**`, demos, or generated artifacts as repo anchors",
        ],
        "templates/data-model-template.md": [
            "# Data Model: [FEATURE]",
            "## Backbone UML",
            "## Shared Invariants",
            "Repo Anchor Status",
        ],
        "templates/test-matrix-template.md": [
            "# Feature Verification Design: [FEATURE]",
            "## Scenario Matrix",
            "## Verification Case Anchors",
        ],
        "templates/contract-template.md": [
            "# Contract: [BOUNDARY OR OPERATION]",
            "This template is format-agnostic.",
            "## Minimal Binding References",
            "## External I/O Summary",
        ],
        "templates/interface-detail-template.md": [
            "# Interface Detail: [operationId]",
            "**Operation ID (Required)**: [operationId]",
            "## Sequence Diagram",
            "Do not use `README.md`, `docs/**`, `specs/**`, or generated artifacts as repo anchors",
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
    assert "interface delivery units are IF-scoped work packages" in mapping_doc

    readme = read("README.md")
    assert "contract-template.md" in readme
    assert "/sdd.plan` uses `plan-template.md` for `plan.md`, and the planning templates in `templates/`" in readme
    assert "`tasks.manifest.json`" in mapping_doc
    assert "machine-readable sidecar projection" in mapping_doc


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
    assert "| Operation ID | Boundary Anchor | Operation / Interaction | IF Scope | Repo Anchor |" in contract

    interface_detail = read("templates/interface-detail-template.md")
    assert "**Boundary Anchor (Required)**:" in interface_detail
    assert "**Contract Binding Row (Required)**:" in interface_detail
    assert "| Path | Trigger | Key Steps | Outcome | Contract-Visible Failure | Sequence Ref | TM/TC Anchor |" in interface_detail
    assert "Keep this document operation-local and minimal" in interface_detail
    assert "Keep only materially distinct paths." in interface_detail

    tasks_command = read("templates/commands/tasks.md")
    assert "stable tuple keys (`Operation ID`, `Boundary Anchor`, `IF Scope`)" in tasks_command
    assert "tuple alignment" in tasks_command
    assert "execution work package" in tasks_command


def test_repo_anchor_policy_excludes_helper_docs_across_templates():
    plan = read("templates/commands/plan.md")
    research = read("templates/research-template.md")
    analyze = read("templates/commands/analyze.md")

    assert "README.md" in plan
    assert "docs/**" in plan
    assert "specs/**" in plan
    assert "Do not list `README.md`, `docs/**`, `specs/**`, or generated artifacts here." in research
    assert "Misuse of `README.md`, `docs/**`, `specs/**`, demos, or generated artifacts as repo semantic anchors" in analyze


def test_implement_command_prefers_manifest_has_fallback_and_single_parse_rule():
    content = read("templates/commands/implement.md")

    assert "Manifest probe (preferred runtime source)" in content
    assert "Manifest validation (when present)" in content
    assert "Fallback trigger" in content
    assert "Prefer `tasks.manifest.json` as the runtime execution metadata source." in content
    assert "tasks.md` remains the human-review and execution-orchestration authority" in content
    assert "Build the in-memory scheduling graph exactly once per run" in content
    assert "reuse that graph for scheduling/checkpoints/completion validation" in content
    assert "do not re-run full markdown parsing loops during the same `/sdd.implement` run" in content

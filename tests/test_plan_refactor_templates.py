from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_plan_command_is_now_orchestration_only():
    content = read("templates/commands/plan.md")

    assert "quickstart.md" not in content
    assert "Stage 0 -> `research.md`" not in content
    assert "Stage 4 -> `interface-details/`" not in content
    assert "Stage 0 `Shared Context Snapshot`" in content
    assert "planning control plane" in content
    assert "does **not** generate downstream planning-stage artifacts directly" in content
    assert "agent: sdd.plan.research" in content
    assert "Binding Projection Index" in content
    assert "Artifact Status" in content
    assert "Frontmatter `handoffs` are static advisory metadata only" in content


def test_plan_child_command_templates_exist_and_define_single_unit_scope():
    expected = {
        "templates/commands/plan.research.md": [
            "first pending `research` row",
            "Generate exactly one `research.md` artifact",
            ".specify/templates/research-template.md",
            "Read only `FEATURE_DIR/plan.md`",
            "User-provided non-`plan.md` file paths may be consumed only when they fall within this command's `Allowed Inputs` scope.",
            "## Handoff Decision",
            "`Next Command`: `/sdd.plan.data-model`",
            "`Selected Stage ID`: selected `research` stage row id",
        ],
        "templates/commands/plan.data-model.md": [
            "first pending `data-model` row",
            "Generate exactly one `data-model.md` artifact",
            "Use `.specify/templates/data-model-template.md` as the structural source of truth",
            "Read only `FEATURE_DIR/plan.md`",
            "User-provided non-`plan.md` file paths may be consumed only when they fall within this command's `Allowed Inputs` scope.",
            "## Handoff Decision",
            "`Next Command`: `/sdd.plan.test-matrix`",
            "`Selected Stage ID`: selected `data-model` stage row id",
        ],
        "templates/commands/plan.test-matrix.md": [
            "first pending `test-matrix` row",
            ".specify/templates/test-matrix-template.md",
            "Read only `FEATURE_DIR/plan.md`",
            "User-provided non-`plan.md` file paths may be consumed only when they fall within this command's `Allowed Inputs` scope.",
            "Binding Projection Index",
            "Artifact Status",
            "## Handoff Decision",
            "`Next Command`: `/sdd.plan.contract`",
        ],
        "templates/commands/plan.contract.md": [
            "first pending `contract` row",
            "Generate exactly one minimum contract artifact",
            ".specify/templates/contract-template.md",
            "Read only `FEATURE_DIR/plan.md`",
            "matching `BindingRowID` row",
            "## Path Constraints",
            "Complete `BindingRowID` selection and prerequisite validation from `FEATURE_DIR/plan.md` before reading `spec.md`, `data-model.md`, `test-matrix.md`, or any repo anchors.",
            "User-provided non-`plan.md` file paths may be consumed only when they fall within this command's `Allowed Inputs` scope.",
            "## Handoff Decision",
            "If any `contract` rows remain `pending`, `Next Command = /sdd.plan.contract`",
            "`Ready/Blocked`",
        ],
        "templates/commands/plan.interface-detail.md": [
            "first pending `interface-detail` row",
            "Generate exactly one minimum interface-detail artifact",
            ".specify/templates/interface-detail-template.md",
            "Read only `FEATURE_DIR/plan.md`",
            "matching contract row",
            "## Path Constraints",
            "Complete `BindingRowID` selection, matching contract-row resolution, and prerequisite validation from `FEATURE_DIR/plan.md` before reading `research.md`, `data-model.md`, `test-matrix.md`, the matching contract artifact, or any repo anchors.",
            "User-provided non-`plan.md` file paths may be consumed only when they fall within this command's `Allowed Inputs` scope.",
            "## Handoff Decision",
            "If any `interface-detail` rows remain `pending`, `Next Command = /sdd.plan.interface-detail`",
            "`Next Command = /sdd.tasks`",
        ],
    }

    for rel_path, markers in expected.items():
        content = read(rel_path)
        for marker in markers:
            assert marker in content, f"Missing {marker!r} in {rel_path}"


def test_repeated_plan_commands_use_state_driven_handoff_not_static_frontmatter():
    contract = read("templates/commands/plan.contract.md")
    interface_detail = read("templates/commands/plan.interface-detail.md")

    assert "handoffs:" not in contract
    assert "handoffs:" not in interface_detail
    assert "agent: sdd.plan.interface-detail" not in contract
    assert "agent: sdd.tasks" not in interface_detail


def test_plan_child_commands_require_feature_dir_plan_and_allow_scoped_non_plan_inputs_only():
    child_commands = [
        "templates/commands/plan.research.md",
        "templates/commands/plan.data-model.md",
        "templates/commands/plan.test-matrix.md",
        "templates/commands/plan.contract.md",
        "templates/commands/plan.interface-detail.md",
    ]

    for rel_path in child_commands:
        content = read(rel_path)
        assert "Read only `FEATURE_DIR/plan.md`" in content
        assert "The only allowed planning control-plane input path is `FEATURE_DIR/plan.md` resolved from `{SCRIPT}`." in content
        assert "Do not accept, infer, or override any alternate `plan.md` path from `$ARGUMENTS`, environment variables, or repository scanning." in content
        assert "User-provided non-`plan.md` file paths may be consumed only when they fall within this command's `Allowed Inputs` scope." in content
        assert "User-provided files MUST NOT replace or redefine the planning control-plane source." in content


def test_plan_contract_and_interface_detail_defer_expensive_reads_until_selection():
    contract = read("templates/commands/plan.contract.md")
    interface_detail = read("templates/commands/plan.interface-detail.md")

    assert "Complete `BindingRowID` selection and prerequisite validation from `FEATURE_DIR/plan.md` before reading `spec.md`, `data-model.md`, `test-matrix.md`, or any repo anchors." in contract
    assert "Until the selected contract row is resolved and the `test-matrix` stage row is confirmed `done`, do not open repository files, generated artifacts, or run repository-wide discovery/search." in contract

    assert "Complete `BindingRowID` selection, matching contract-row resolution, and prerequisite validation from `FEATURE_DIR/plan.md` before reading `research.md`, `data-model.md`, `test-matrix.md`, the matching contract artifact, or any repo anchors." in interface_detail
    assert "Until the selected interface-detail row is resolved and the matching contract row is confirmed `done`, do not open repository files, generated artifacts, or run repository-wide discovery/search." in interface_detail


def test_plan_template_is_control_plane_not_stage_summary():
    content = read("templates/plan-template.md")

    assert "## Shared Context Snapshot" in content
    assert "## Stage Queue" in content
    assert "## Binding Projection Index" in content
    assert "## Artifact Status" in content
    assert "planning control plane" in content
    assert "Stage 0 Research" not in content
    assert "Stage 1 Data Model" not in content
    assert "Stage 4 Interface Detailed Design" not in content
    assert "Planning summary and downstream projection ledger" not in content


def test_tasks_command_requires_complete_plan_control_plane():
    content = read("templates/commands/tasks.md")

    assert "Treat `plan.md` as the planning control plane" in content
    assert "Shared Context Snapshot" in content
    assert "Stage Queue" in content
    assert "Binding Projection Index" in content
    assert "Artifact Status" in content
    assert "route to the relevant `/sdd.plan.*` child command" in content
    assert "Use `Binding Projection Index` from `plan.md` as the execution-unit inventory source" in content
    assert "stop and route to `/sdd.plan.test-matrix`" in content


def test_analyze_command_checks_stale_plan_fingerprints():
    content = read("templates/commands/analyze.md")

    assert "planning control plane" in content
    assert "source/output fingerprints" in content
    assert "planning queue / binding projection / fingerprint inventory" in content
    assert "stale planning outputs" in content
    assert "Source Fingerprint" in content
    assert "route stale `contract` rows to `/sdd.plan.contract`" in content
    assert "route stale `interface-detail` rows to `/sdd.plan.interface-detail`" in content


def test_downstream_docs_and_mapping_match_orchestrator_model():
    mapping_doc = read("docs/command-template-mapping.md")
    readme = read("README.md")
    spec_template = read("templates/spec-template.md")
    installation = read("docs/installation.md")
    quickstart = read("docs/quickstart.md")

    assert "`plan.md` | Planning control plane, binding projection ledger, queue/fingerprint state | Derived for planning semantics; authoritative for planning queue state |" in mapping_doc
    assert "Runtime template authority path for generation and output-structure commands is `.specify/templates/`." in mapping_doc
    assert "| `/sdd.plan.research` | Generate the queued research artifact | `.specify/templates/research-template.md` | `research.md` |" in mapping_doc
    assert "| `/sdd.plan.contract` | Generate one queued contract artifact | `.specify/templates/contract-template.md` | one file in `contracts/` |" in mapping_doc
    assert "The five `/sdd.plan.*` child commands (`/sdd.plan.research`, `/sdd.plan.data-model`, `/sdd.plan.test-matrix`, `/sdd.plan.contract`, `/sdd.plan.interface-detail`) must read planning queue/control-plane state from `FEATURE_DIR/plan.md` only." in mapping_doc
    assert "User-provided non-`plan.md` files may be consumed only if they are already permitted by the command's `Allowed Inputs`; they must not replace control-plane state." in mapping_doc
    assert "repeated `/sdd.plan.contract`" in mapping_doc
    assert "repeated `/sdd.plan.interface-detail`" in mapping_doc
    assert "state-dependent planning routing must be emitted through a runtime `Handoff Decision`" in mapping_doc
    assert "repeated routing stays on `/sdd.plan.contract` until no pending contract rows remain" in mapping_doc
    assert "repeated routing stays on `/sdd.plan.interface-detail` until planning is complete" in mapping_doc
    assert "render both `tasks.md` and `tasks.manifest.json` from that shared graph" in mapping_doc
    assert "explicit user waiver" in mapping_doc

    assert "Use the **`/sdd.plan`** command to create `plan.md` as the planning control plane." in readme
    assert "`/sdd.plan.research`" in readme
    assert "`/sdd.plan.interface-detail`" in readme
    assert "All generation commands must read runtime templates from `.specify/templates/`." in readme
    assert "`plan.md` queue state is the sole authority for planning handoff decisions." in readme
    assert "Static command frontmatter `handoffs` are advisory metadata only." in readme
    assert "default pre-implementation audit pass" in readme
    assert "analyze-first blocking reminder" in readme
    assert "planning control plane" in spec_template
    assert "Default pre-implementation audit" in spec_template
    assert "implementation should stop unless the user explicitly waives the audit step" in spec_template
    assert "`/sdd.plan.contract` - Generate one queued contract artifact" in installation
    assert "Repeated planning commands use runtime `Handoff Decision` output derived from `plan.md` queue state." in installation
    assert "Then run the planning queue one command at a time" in quickstart
    assert "use each command's runtime `Handoff Decision` output" in quickstart
    assert "Default pre-implementation gate" in quickstart


def test_planning_stage_templates_still_exist_for_child_commands():
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
            "## Stable Binding Keys (Required)",
            "## Scenario Matrix",
        ],
        "templates/contract-template.md": [
            "# Contract: [BOUNDARY OR OPERATION]",
            "**Operation ID (Required)**:",
            "## Minimal Binding References",
        ],
        "templates/interface-detail-template.md": [
            "# Interface Detail: [operationId]",
            "**Contract Binding Row (Required)**:",
            "## Sequence Diagram",
        ],
    }

    for rel_path, markers in expected_templates.items():
        content = read(rel_path)
        for marker in markers:
            assert marker in content


def test_plan_requires_canonical_repository_first_baseline_and_fail_fast():
    plan = read("templates/commands/plan.md")

    assert "MUST consume the canonical repository-first baseline produced by `/sdd.constitution`" in plan
    assert ".specify/memory/repository-first/technical-dependency-matrix.md" in plan
    assert ".specify/memory/repository-first/domain-boundary-responsibilities.md" in plan
    assert ".specify/memory/repository-first/module-invocation-spec.md" in plan
    assert "Fail fast and route to `/sdd.constitution`" in plan


def test_repo_anchor_policy_excludes_helper_docs_across_templates():
    plan = read("templates/commands/plan.md")
    research = read("templates/research-template.md")
    analyze = read("templates/commands/analyze.md")

    assert "README.md" in plan
    assert "docs/**" in plan
    assert "specs/**" in plan
    assert "Do not list `README.md`, `docs/**`, `specs/**`, or generated artifacts here." in research
    assert "Misuse of `README.md`, `docs/**`, `specs/**`, `tests/**`, `plans/**`, `templates/**`, demos, or generated artifacts as repo semantic anchors" in analyze


def test_generation_commands_require_runtime_template_authority_paths():
    expected = {
        "templates/commands/constitution.md": ".specify/templates/constitution-template.md",
        "templates/commands/specify.md": ".specify/templates/spec-template.md",
        "templates/commands/plan.md": ".specify/templates/plan-template.md",
        "templates/commands/plan.research.md": ".specify/templates/research-template.md",
        "templates/commands/plan.data-model.md": ".specify/templates/data-model-template.md",
        "templates/commands/plan.test-matrix.md": ".specify/templates/test-matrix-template.md",
        "templates/commands/plan.contract.md": ".specify/templates/contract-template.md",
        "templates/commands/plan.interface-detail.md": ".specify/templates/interface-detail-template.md",
        "templates/commands/tasks.md": ".specify/templates/tasks-template.md",
        "templates/commands/checklist.md": ".specify/templates/checklist-template.md",
        "templates/commands/analyze.md": ".specify/templates/lint-report-template.md",
    }

    forbidden = {
        "templates/commands/specify.md": "Load `templates/spec-template.md` to understand required sections.",
        "templates/commands/plan.md": "Use `templates/plan-template.md` as the structure source for `plan.md`.",
        "templates/commands/checklist.md": "following the canonical template in `templates/checklist-template.md`",
        "templates/commands/tasks.md": "Use `templates/tasks-template.md` as structure",
        "templates/commands/analyze.md": "governed by `templates/lint-report-template.md`",
    }

    for rel_path, marker in expected.items():
        assert marker in read(rel_path)

    for rel_path, marker in forbidden.items():
        assert marker not in read(rel_path)


def test_frontmatter_docs_define_static_only_handoffs():
    dev_guide = read("extensions/EXTENSION-DEVELOPMENT-GUIDE.md")
    api_reference = read("extensions/EXTENSION-API-REFERENCE.md")

    assert "handoffs:                                   # Optional, static handoff metadata only" in dev_guide
    assert "`handoffs` are advisory metadata only." in dev_guide
    assert "do not encode state-dependent or multi-result routing in frontmatter" in dev_guide

    assert "handoffs:             # Optional, static handoff metadata only" in api_reference
    assert "`handoffs` are advisory metadata only and may describe only unconditional next steps." in api_reference

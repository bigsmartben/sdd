from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_plan_command_requires_explicit_spec_path_and_documents_all_mode():
    content = read("templates/commands/plan.md")

    assert "quickstart.md" not in content
    assert "Stage 0 -> `research.md`" not in content
    assert "Stage 4 -> `interface-details/`" not in content
    assert "Stage 0 `Shared Context Snapshot`" in content
    assert "planning control plane" in content
    assert "does **not** generate downstream planning-stage artifacts directly" in content
    assert "The first positional token is mandatory and is `SPEC_FILE`" in content
    assert "`/sdd.plan <path/to/spec.md> [ALL] [technical-context...]`" in content
    assert "reserved uppercase literal `ALL`" in content
    assert "Run `{SCRIPT} --spec-file <SPEC_FILE>` once" in content
    assert "agent: sdd.plan.research" in content
    assert "Binding Projection Index" in content
    assert "Artifact Status" in content
    assert "Frontmatter `handoffs` are static advisory metadata only" in content


def test_static_handoff_prompts_reference_explicit_planning_paths():
    specify = read("templates/commands/specify.md")
    clarify = read("templates/commands/clarify.md")
    plan = read("templates/commands/plan.md")
    research = read("templates/commands/plan.research.md")
    data_model = read("templates/commands/plan.data-model.md")
    test_matrix = read("templates/commands/plan.test-matrix.md")

    assert "running /sdd.plan <path/to/spec.md> [ALL]" in specify
    assert "running /sdd.plan <path/to/spec.md> [ALL]" in clarify
    assert "running /sdd.plan.research <path/to/plan.md>" in plan
    assert "running /sdd.plan.data-model <path/to/plan.md>" in research
    assert "running /sdd.plan.test-matrix <path/to/plan.md>" in data_model
    assert "running /sdd.plan.contract <path/to/plan.md>" in test_matrix


def test_clarify_command_aligns_to_backbone_spec_template_sections():
    clarify = read("templates/commands/clarify.md")

    assert "current backbone-first spec template" in clarify
    assert "`1.3 UI Data Dictionary (UDD)`" in clarify
    assert "`2.1 Functional Requirements Index (FR Index)`" in clarify
    assert "`3.2 UX — User Interaction Flow`" in clarify
    assert "`3.4 UI — UI Element Definitions`" in clarify
    assert "`3.5 Component-Data Dependency Overview`" in clarify
    assert "`N.1 Success Criteria`" in clarify
    assert "`N.2 Environment Edge Cases`" in clarify
    assert "after `## Artifacts Overview & Navigation`" in clarify
    assert "do not create a free-floating `Non-Functional` or `Quality Attributes` heading" in clarify


def test_plan_child_command_templates_exist_and_define_single_unit_scope():
    expected = {
        "templates/commands/plan.research.md": [
            "first pending `research` row",
            "Generate exactly one `research.md` artifact",
            ".specify/templates/research-template.md",
            "Parse the first positional token from `$ARGUMENTS` as `PLAN_FILE`",
            "Read only the resolved `IMPL_PLAN`",
            "Use only the explicit `PLAN_FILE` resolved through `{SCRIPT}` as planning control plane.",
            "they never redefine control-plane state.",
            "## Handoff Decision",
            "`Next Command`: `/sdd.plan.data-model <absolute path to plan.md>`",
            "`Selected Stage ID`: selected `research` stage row id",
        ],
        "templates/commands/plan.data-model.md": [
            "first pending `data-model` row",
            "Generate exactly one `data-model.md` artifact",
            ".specify/templates/data-model-template.md",
            "Parse the first positional token from `$ARGUMENTS` as `PLAN_FILE`",
            "Read only the resolved `IMPL_PLAN`",
            "Use only the explicit `PLAN_FILE` resolved through `{SCRIPT}` as planning control plane.",
            "they never redefine control-plane state.",
            "## Handoff Decision",
            "`Next Command`: `/sdd.plan.test-matrix <absolute path to plan.md>`",
            "`Selected Stage ID`: selected `data-model` stage row id",
        ],
        "templates/commands/plan.test-matrix.md": [
            "first pending `test-matrix` row",
            ".specify/templates/test-matrix-template.md",
            "Parse the first positional token from `$ARGUMENTS` as `PLAN_FILE`",
            "Read only the resolved `IMPL_PLAN`",
            "Use only the explicit `PLAN_FILE` resolved through `{SCRIPT}` as planning control plane.",
            "they never redefine control-plane state.",
            "Binding Projection Index",
            "Artifact Status",
            "## Handoff Decision",
            "`Next Command`: `/sdd.plan.contract <absolute path to plan.md>`",
        ],
        "templates/commands/plan.contract.md": [
            "first pending `contract` row",
            "Generate exactly one minimum contract artifact",
            ".specify/templates/contract-template.md",
            "Parse the first positional token from `$ARGUMENTS` as `PLAN_FILE`",
            "Read only the resolved `IMPL_PLAN`",
            "matching `BindingRowID` row",
            "## Path Constraints",
            "Complete `BindingRowID` selection and prerequisite validation from the explicit `PLAN_FILE` before reading `spec.md`, `data-model.md`, `test-matrix.md`, or any repo anchors.",
            "## Boundary Anchor Selection (Client Entry First)",
            "Select `Boundary Anchor` as the first consumer-callable entry",
            "If the operation is consumer-called via HTTP, prefer `HTTP METHOD /path`",
            "Use only the explicit `PLAN_FILE` resolved through `{SCRIPT}` as planning control plane.",
            "they never redefine control-plane state.",
            "## Handoff Decision",
            "If any `contract` rows remain `pending`, `Next Command = /sdd.plan.contract <absolute path to plan.md>`",
            "`Ready/Blocked`",
        ],
        "templates/commands/plan.interface-detail.md": [
            "first pending `interface-detail` row",
            "Generate exactly one minimum interface-detail artifact",
            ".specify/templates/interface-detail-template.md",
            "Parse the first positional token from `$ARGUMENTS` as `PLAN_FILE`",
            "Read only the resolved `IMPL_PLAN`",
            "matching contract row",
            "## Path Constraints",
            "Complete `BindingRowID` selection, matching contract-row resolution, and prerequisite validation from the explicit `PLAN_FILE` before reading `research.md`, `data-model.md`, `test-matrix.md`, the matching contract artifact, or any repo anchors.",
            "## Internal Handoff Design Requirements",
            "Add and anchor `Implementation Entry Anchor`",
            "Sequence design must start from client/consumer entry",
            "Require UML field-level ownership for all contract-visible request/response fields",
            "Use only the explicit `PLAN_FILE` resolved through `{SCRIPT}` as planning control plane.",
            "they never redefine control-plane state.",
            "## Handoff Decision",
            "If any `interface-detail` rows remain `pending`, `Next Command = /sdd.plan.interface-detail <absolute path to plan.md>`",
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


def test_plan_child_commands_require_explicit_plan_file_and_allow_scoped_non_plan_inputs_only():
    child_commands = [
        "templates/commands/plan.research.md",
        "templates/commands/plan.data-model.md",
        "templates/commands/plan.test-matrix.md",
        "templates/commands/plan.contract.md",
        "templates/commands/plan.interface-detail.md",
    ]

    for rel_path in child_commands:
        content = read(rel_path)
        assert "Parse the first positional token from `$ARGUMENTS` as `PLAN_FILE`" in content
        assert "Read only the resolved `IMPL_PLAN`" in content
        assert "Use only the explicit `PLAN_FILE` resolved through `{SCRIPT}` as planning control plane." in content
        assert "Ignore alternate `plan.md` paths from environment variables or repository discovery." in content
        assert "they never redefine control-plane state." in content


def test_plan_contract_and_interface_detail_defer_expensive_reads_until_selection():
    contract = read("templates/commands/plan.contract.md")
    interface_detail = read("templates/commands/plan.interface-detail.md")

    assert "Complete `BindingRowID` selection and prerequisite validation from the explicit `PLAN_FILE` before reading `spec.md`, `data-model.md`, `test-matrix.md`, or any repo anchors." in contract
    assert "Before that point, do not open repository files, generated artifacts, or run repository-wide discovery/search." in contract

    assert "Complete `BindingRowID` selection, matching contract-row resolution, and prerequisite validation from the explicit `PLAN_FILE` before reading `research.md`, `data-model.md`, `test-matrix.md`, the matching contract artifact, or any repo anchors." in interface_detail
    assert "Before that point, do not open repository files, generated artifacts, or run repository-wide discovery/search." in interface_detail


def test_plan_contract_and_interface_detail_describe_output_authority_as_post_generation():
    contract = read("templates/commands/plan.contract.md")
    interface_detail = read("templates/commands/plan.interface-detail.md")

    assert "After generation, the selected artifact under `contracts/` becomes the authoritative source for interface semantics for that binding." in contract
    assert "`contracts/` remains the authoritative source for interface semantics." not in contract

    assert "After generation, the selected artifact under `interface-details/` becomes the authoritative source for operation-local design semantics for that binding." in interface_detail
    assert "`interface-details/` remains the authoritative source for operation-local design semantics." not in interface_detail


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


def test_analyze_command_reads_backbone_spec_sections_and_routes_constitution_repairs():
    analyze = read("templates/commands/analyze.md")

    assert "`1.3 UI Data Dictionary (UDD)`" in analyze
    assert "`3.4 UI — UI Element Definitions`" in analyze
    assert "`N.1 Success Criteria`" in analyze
    assert "flag `Entity.field` references in FR/UIF/UI sections" in analyze
    assert "remediation owner command (`/sdd.constitution`, `/sdd.specify`, `/sdd.plan.*`, or `/sdd.tasks`)" in analyze
    assert "Keep command suggestions explicit and short (`/sdd.constitution`, `/sdd.specify`, `/sdd.plan.*`, `/sdd.tasks`)." in analyze


def test_downstream_docs_and_mapping_match_orchestrator_model():
    mapping_doc = read("docs/command-template-mapping.md")
    readme = read("README.md")
    spec_template = read("templates/spec-template.md")
    installation = read("docs/installation.md")
    quickstart = read("docs/quickstart.md")
    upgrade = read("docs/upgrade.md")

    assert "`plan.md` | Planning control plane, binding projection ledger, queue/fingerprint state | Derived for planning semantics; authoritative for planning queue state |" in mapping_doc
    assert "Runtime template authority path for generation and output-structure commands is `.specify/templates/`." in mapping_doc
    assert "| `/sdd.plan.research <plan.md>` | Generate the queued research artifact | `.specify/templates/research-template.md` | `research.md` |" in mapping_doc
    assert "| `/sdd.plan.contract <plan.md>` | Generate one queued contract artifact | `.specify/templates/contract-template.md` | one file in `contracts/` |" in mapping_doc
    assert "The five `/sdd.plan.*` child commands (`/sdd.plan.research`, `/sdd.plan.data-model`, `/sdd.plan.test-matrix`, `/sdd.plan.contract`, `/sdd.plan.interface-detail`) must read planning queue/control-plane state from the explicit `plan.md` path provided by the user." in mapping_doc
    assert "User-provided non-`plan.md` files may be consumed only if they are already permitted by the command's `Allowed Inputs`; they must not replace control-plane state." in mapping_doc
    assert "repeated `/sdd.plan.contract <plan.md>`" in mapping_doc
    assert "repeated `/sdd.plan.interface-detail <plan.md>`" in mapping_doc
    assert "state-dependent planning routing must be emitted through a runtime `Handoff Decision`" in mapping_doc
    assert "repeated routing stays on `/sdd.plan.contract` until no pending contract rows remain" in mapping_doc
    assert "repeated routing stays on `/sdd.plan.interface-detail` until planning is complete" in mapping_doc
    assert "render both `tasks.md` and `tasks.manifest.json` from that shared graph" in mapping_doc
    assert "explicit user waiver" in mapping_doc

    assert "with an explicit `spec.md` path to create `plan.md` as the planning control plane" in readme
    assert "`/sdd.plan.research <plan.md>`" in readme
    assert "`/sdd.plan.interface-detail <plan.md>`" in readme
    assert "All generation commands must read runtime templates from `.specify/templates/`." in readme
    assert "`plan.md` queue state is the sole authority for planning handoff decisions." in readme
    assert "Static command frontmatter `handoffs` are advisory metadata only." in readme
    assert "default pre-implementation audit pass" in readme
    assert "analyze-first blocking reminder" in readme
    assert "planning control plane" in spec_template
    assert "Default pre-implementation audit" in spec_template
    assert "implementation should stop unless the user explicitly waives the audit step" in spec_template
    assert "`/sdd.plan.contract <plan.md>` - Generate one queued contract artifact" in installation
    assert "Repeated planning commands use runtime `Handoff Decision` output derived from `plan.md` queue state." in installation
    assert "Then run the planning queue one command at a time when you are not using `ALL`" in quickstart
    assert "use each command's runtime `Handoff Decision` output with the explicit `plan.md` path" in quickstart
    assert "For planning commands, pass explicit file paths" in upgrade
    assert "only for commands that still rely on active-feature discovery" in upgrade
    assert "Planning commands now use explicit file paths instead." in upgrade
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
            "**Implementation Entry Anchor (Required)**:",
            "## Sequence Diagram",
            "## UML Class Design",
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


def test_repository_first_references_avoid_bare_filenames_in_runtime_templates():
    files = [
        "templates/commands/analyze.md",
        "templates/commands/tasks.md",
        "templates/constitution-template.md",
        "templates/technical-dependency-matrix-template.md",
        "templates/domain-boundary-responsibilities-template.md",
        "templates/module-invocation-spec-template.md",
    ]
    bare_markers = [
        "`technical-dependency-matrix.md`",
        "`domain-boundary-responsibilities.md`",
        "`module-invocation-spec.md`",
    ]

    for rel_path in files:
        content = read(rel_path)
        for marker in bare_markers:
            assert marker not in content


def test_contract_and_interface_detail_templates_encode_entry_and_field_level_rules():
    contract_template = read("templates/contract-template.md")
    interface_detail_template = read("templates/interface-detail-template.md")
    contract_command = read("templates/commands/plan.contract.md")
    interface_detail_command = read("templates/commands/plan.interface-detail.md")

    assert "first client-callable entry" in contract_template
    assert "If clients call an HTTP route directly, prefer HTTP `METHOD /path` as `Boundary Anchor`" in contract_template
    assert "Client entry rationale:" in contract_template

    assert "**Implementation Entry Anchor (Required)**" in interface_detail_template
    assert "client-entry signature surface (HTTP route/controller or facade/RPC method)" in interface_detail_template
    assert "Use `Direction = input` / `output` only for contract-visible request/response fields" in interface_detail_template
    assert "do not duplicate full request/response prose here" in interface_detail_template
    assert "Sequence MUST start from consumer/client entry and reach `Implementation Entry Anchor` within the first two request hops." in interface_detail_template
    assert "If both controller and facade exist for this operation, show both participants in order and keep their handoff explicit." in interface_detail_template
    assert "If `Boundary Anchor` and `Implementation Entry Anchor` resolve to the same repo-backed symbol, reuse one participant instead of inventing a fake handoff hop." in interface_detail_template
    assert "show both forward and return handoff messages explicitly" in interface_detail_template
    assert 'participant Entry as "<ImplementationEntryAnchor>"' in interface_detail_template
    assert "request/response DTOs and nested DTOs at field level for all contract-visible input/output fields" in interface_detail_template
    assert "Boundary-to-entry reachability" in interface_detail_template
    assert "Field-ownership closure" in interface_detail_template
    assert 'class ContractBoundaryEntry["<ContractBoundaryEntry>"]' in interface_detail_template
    assert 'class ImplementationEntry["<ImplementationEntryAnchor>"]' in interface_detail_template
    assert 'class RequestDTO["<RequestDTO>"]' in interface_detail_template
    assert 'class ResponseDTO["<ResponseDTO>"]' in interface_detail_template

    assert "## Boundary Anchor Selection (Client Entry First)" in contract_command
    assert "Select `Boundary Anchor` as the first consumer-callable entry" in contract_command

    assert "## Internal Handoff Design Requirements" in interface_detail_command
    assert "Add and anchor `Implementation Entry Anchor`" in interface_detail_command
    assert "Keep contract restatement out: explain only behavior-significant field semantics" in interface_detail_command
    assert "Require UML field-level ownership for all contract-visible request/response fields" in interface_detail_command


def test_binding_projection_and_validation_follow_client_entry_and_handoff_rules():
    test_matrix_template = read("templates/test-matrix-template.md")
    plan_test_matrix = read("templates/commands/plan.test-matrix.md")
    plan_template = read("templates/plan-template.md")
    analyze = read("templates/commands/analyze.md")
    lint_rules = read("rules/planning-lint-rules.tsv")

    assert "first consumer-callable entry used for contract binding" in test_matrix_template
    assert "`Implementation Entry Anchor` belongs only in `interface-details/`" in test_matrix_template

    assert "Project `Boundary Anchor` as the client-facing contract binding key only" in plan_test_matrix
    assert "Do not add `Implementation Entry Anchor` or other internal handoff fields to `Binding Projection Index`" in plan_test_matrix

    assert "`Boundary Anchor` is the client-facing contract binding key projected from `test-matrix.md`" in plan_template
    assert "Internal handoff anchors such as `Implementation Entry Anchor` belong in `interface-details/`, not `plan.md`." in plan_template

    assert "flag interface-detail docs missing `Implementation Entry Anchor`" in analyze
    assert "flag sequence designs that do not reach `Implementation Entry Anchor` within the first two request hops" in analyze
    assert "flag UML ownership gaps where contract-visible request/response fields or behavior-significant `Field Semantics` fields do not have an explicit owning class/interface" in analyze

    assert "PLN-ID-003" in lint_rules
    assert "PLN-ID-004" in lint_rules
    assert "PLN-ID-005" in lint_rules
    assert "PLN-ID-006" in lint_rules
    assert "Implementation details are missing explicit Implementation Entry Anchor" not in lint_rules
    assert "Interface details are missing explicit Implementation Entry Anchor required by the interface-detail template." in lint_rules
    assert "Interface details are missing the Runtime Correctness Check section required for operation-local closure validation." in lint_rules
    assert "Interface details are missing the Boundary-to-entry reachability runtime check row." in lint_rules
    assert "Interface details are missing the Field-ownership closure runtime check row." in lint_rules


def test_frontmatter_docs_define_static_only_handoffs():
    dev_guide = read("extensions/EXTENSION-DEVELOPMENT-GUIDE.md")
    api_reference = read("extensions/EXTENSION-API-REFERENCE.md")

    assert "handoffs:                                   # Optional, static handoff metadata only" in dev_guide
    assert "`handoffs` are advisory metadata only." in dev_guide
    assert "do not encode state-dependent or multi-result routing in frontmatter" in dev_guide

    assert "handoffs:             # Optional, static handoff metadata only" in api_reference
    assert "`handoffs` are advisory metadata only and may describe only unconditional next steps." in api_reference

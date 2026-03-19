from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def read_if_exists(rel_path: str) -> str | None:
    path = REPO_ROOT / rel_path
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def test_plan_command_is_control_plane_only():
    content = read("templates/commands/plan.md")
    assert "does **not** generate downstream planning-stage artifacts directly" in content
    assert "Treat all `$ARGUMENTS` as user planning context." in content
    assert "Planning Sharding Model (Mandatory)" in content
    assert "Stage sharding (fixed): delivery path `research -> test-matrix -> data-model`" in content
    assert "Binding sharding (fixed): `/sdd.plan.contract` consumes one `BindingRowID` row per run" in content
    assert "`contract` is not a `Stage Queue` row" in content
    assert "explicit handoff order: `sdd.plan.research -> sdd.plan.test-matrix -> sdd.plan.data-model -> sdd.plan.contract`" in content


def test_plan_child_commands_are_contract_only():
    assert not (REPO_ROOT / "templates/commands/plan.interface-detail.md").exists()
    assert not (REPO_ROOT / "templates/interface-detail-template.md").exists()

    plan = read("templates/commands/plan.md")
    test_matrix = read("templates/commands/plan.test-matrix.md")
    contract = read("templates/commands/plan.contract.md")

    assert "/sdd.plan.contract" in plan
    assert "/sdd.plan.interface-detail" not in plan
    assert "`Unit Type = contract`" in test_matrix
    assert "If any `contract` rows remain `blocked`, `Next Command = /sdd.plan.contract`" in contract
    assert "Otherwise, if any `contract` rows remain `pending`, `Next Command = /sdd.plan.contract`" in contract
    assert "Otherwise, if all required planning rows (`research`, `test-matrix`, `data-model`, and all queued `contract` rows) are complete, `Next Command = /sdd.tasks`" in contract
    assert "unified northbound interface design artifact" in contract
    assert "minimum northbound interface design artifact" not in contract


def test_plan_template_tracks_only_contract_artifacts():
    content = read("templates/plan-template.md")
    assert "`contract` is tracked as the single per-binding interface design artifact." in content
    assert "| BindingRowID | UC ID | UIF ID | FR ID | IF ID / IF Scope | TM ID | TC IDs | Operation ID | UIF Path Ref(s) | UDD Ref(s) | Test Scope |" in content
    assert "minimal selection and scheduling fields" in content
    assert "regenerate the projection instead of letting downstream commands rewrite it" in content
    assert "<!-- Keep table body empty until /sdd.plan.test-matrix projects stable binding rows. -->" in content
    assert "<!-- Keep table body empty until binding rows exist. -->" in content
    assert "[BindingRowID-001]" not in content
    assert "interface-detail" not in content


def test_plan_and_test_matrix_templates_precompute_contract_bootstrap_inputs():
    plan = read("templates/commands/plan.md")
    test_matrix_command = read("templates/commands/plan.test-matrix.md")
    test_matrix_template = read("templates/test-matrix-template.md")

    assert "- `UIF Path Ref(s)`" in plan
    assert "- `UDD Ref(s)`" in plan
    assert "- `Test Scope`" in plan
    assert "Do not add `Boundary Anchor`" in plan

    assert "## Binding Contract Packet Requirements" in test_matrix_command
    assert "Do not read `research.md` in this stage." not in test_matrix_command
    assert "Read only:" in test_matrix_command
    assert "- `UIF Path Ref(s)`" in test_matrix_command
    assert "- `UDD Ref(s)`" in test_matrix_command
    assert "stable binding projection from `spec.md`" in test_matrix_command

    assert "## Binding Contract Packets" in test_matrix_template
    assert "Purpose: minimal binding locator packet for the selected interaction unit." in test_matrix_template
    assert "**Inputs**: `spec.md`" in test_matrix_template
    assert "Read only spec-grounded semantics here." in test_matrix_template
    assert "| BindingRowID | Operation ID | IF Scope | UIF Path Ref(s) | UDD Ref(s) | TM ID | TC IDs | Test Scope | Spec Ref(s) | Scenario Ref(s) | Success Ref(s) | Edge Ref(s) |" in test_matrix_template


def test_contract_command_uses_test_matrix_as_default_semantic_source():
    content = read("templates/commands/plan.contract.md")

    assert "Treat the matched `Binding Projection Index` row as a minimal locator ledger only" in content
    assert "Treat the selected packet as demand projection only through" in content
    assert "Do not treat the selected packet as a predesigned contract seed." in content
    assert "if absent, stop and route back to `/sdd.plan.test-matrix`" in content
    assert "Reconstruct request / response meaning from `UC`, `FR`, `UIF`, `UDD`, and scenario refs before reading repo evidence." in content
    assert "If repo-backed verification finds a binding-projection error or shared-semantic gap" in content
    assert "Use the repo-anchor decision protocol in `.specify/templates/contract-template.md` as the authority for this stage." in content
    assert "Keep repo-backed verification bounded to the selected `BindingRowID` and active blockers" in content
    assert "- required collaborators and middleware" in content
    assert "- required owner/source symbols" in content
    assert "Sequence design MUST explicitly render every mandatory repo-backed collaborator hop" in content
    assert "Sequence design MUST NOT collapse multiple mandatory collaborators/dependencies into one synthetic participant label" in content
    assert "`opt` blocks are valid only for truly conditional branches" in content
    assert "UML request/response class labels should use anchored symbols or repository boundary naming conventions; do not synthesize placeholder DTO labels." in content
    assert "MAY refine operation-scoped VO/DTO/field mappings" in content
    assert "MUST NOT mint new shared-semantic classes, owners/sources, lifecycle vocabulary, or invariants." in content
    assert "## Concrete Naming Closure (Mandatory)" in content
    assert "Apply the repository decision order `existing -> extended -> new`." in content
    assert "Stop local refinement and route upstream when continuing would require a new upstream shared semantic" in content
    assert "new shared semantic owner/source, a new backbone semantic element, a new cross-operation stable owner field, new shared lifecycle/invariant vocabulary" in content
    assert "## Feature-Level Smoke Readiness (Queue-Complete Gate)" in content
    assert "Cross-Interface Smoke Candidate (Required)" in content
    assert "do not rewrite upstream planning artifacts from this command" in content


def test_contract_selection_rules_handle_empty_queue_before_packet_resolution():
    content = read("templates/commands/plan.contract.md")
    no_pending_idx = content.index("If no pending or blocked contract row exists, stop and report that the contract queue is complete")
    resolve_packet_idx = content.index("Attempt to resolve one selected binding packet in `test-matrix.md` by the same `BindingRowID`; if absent, stop and route back to `/sdd.plan.test-matrix`")
    assert no_pending_idx < resolve_packet_idx


def test_research_data_model_and_test_matrix_are_packet_first():
    research = read("templates/commands/plan.research.md")
    data_model = read("templates/commands/plan.data-model.md")
    test_matrix = read("templates/commands/plan.test-matrix.md")

    assert "Stage Packet (Research Unit)" in research
    assert "Keep repo-backed reads bounded to the selected unit and active blocker." in research
    assert "Use this packet as the default context for generation." in research

    assert "Stage Packet (Data-Model Unit)" in data_model
    assert "Treat `DATA_MODEL_BOOTSTRAP.generation_readiness` as the primary queue/readiness gate" in data_model
    assert "optional `research.md` path only when `spec.md` + `test-matrix.md` wording leaves the shared-semantic boundary ambiguous" in data_model
    assert "The output MUST define only the shared, stable, reusable semantics" in data_model
    assert "Do not define HTTP routes, controller/service/DTO names, request/response shapes, operation-scoped command/result models, or repo interface-anchor placement here; those belong to `/sdd.plan.contract`." in data_model
    assert "`DATA_MODEL_BOOTSTRAP.state_machine_policy`" in data_model
    assert "If `N > 3` or `T >= 2N`, emit a full FSM package" in data_model
    assert "If `existing` and `extended` are both insufficient, `new` is the required outcome for this stage" in data_model
    assert "If `existing` and `extended` cannot safely close a confirmed shared semantic, this stage MUST explicitly choose `new` here" in data_model
    assert "Shared semantics that are confirmed by `spec.md` + `test-matrix.md` MUST be closed here at owner/source/lifecycle level" in data_model
    assert "- `Next Command`: `/sdd.plan.contract`" in data_model
    assert "continue contract generation directly without rerunning `test-matrix`" in data_model

    assert "Stage Packet (Test-Matrix Unit)" in test_matrix
    assert "Use this packet as the default context for generation and binding projection." in test_matrix
    assert "stable binding projection from `spec.md`" in test_matrix
    assert "prefer section-level rereads over whole-file replay for the selected unit" in test_matrix
    assert "Do not require `research` or `data-model` rows to be `done` before this stage" in test_matrix
    assert "Do not consume `research.md`, `data-model.md`, repo anchors, or generated contract artifacts in this stage." in test_matrix
    assert "If the selected packet cannot be closed from `spec.md` and selected plan-row context" in test_matrix
    assert "`UDD Ref(s)`" in test_matrix


def test_contract_template_contains_unified_realization_requirements():
    content = read("templates/contract-template.md")
    assert "# Northbound Interface Design:" in content
    assert "## Interface Definition" in content
    assert "### Contract Summary" in content
    assert "### Full Field Dictionary (Operation-scoped)" in content
    assert "## UML Class Design" in content
    assert "## Sequence Design" in content
    assert "## Closure Check" in content
    assert "| `Test Scope` | [binding-scoped test coverage summary] |" in content
    assert "## Test Projection" in content
    assert "### Cross-Interface Smoke Candidate" in content
    assert "### Resolved Type Inventory" in content
    assert "Angle-bracket labels in the examples below are template scaffolding only and MUST be replaced before the artifact can be `done`." in content
    assert "| Sequence closure | success/failure paths include mandatory second-party, third-party, and middleware calls | [ok / gap] |" in content
    assert "| UML closure | class diagram and two-party package relations both present and consistent with sequence | [ok / gap] |" in content
    assert "- If repo evidence is missing, this stage may design `new` operation-scoped boundary/entry/DTO/collaborator/middleware surfaces when they remain bounded to this binding." in content
    assert "#### Sequence Variant A (Boundary != Entry)" in content
    assert "#### Sequence Variant B (Boundary == Entry)" in content
    assert "#### UML Variant A (Boundary != Entry)" in content
    assert "#### UML Variant B (Boundary == Entry)" in content
    assert "Sequence MUST NOT merge multiple mandatory collaborators/dependencies into one synthetic participant label." in content
    assert "Sequence MUST NOT merge multiple mandatory collaborators/dependencies into one synthetic participant label" in content
    assert "- If repo evidence is missing, this stage may design `new` operation-scoped boundary/entry/DTO/collaborator/middleware surfaces when they remain bounded to this binding." in content
    assert "- repo anchors: [boundary / entry / request-response model / collaborator / middleware / dependency symbols]" in content
    assert "- `contract` is responsible for first-time production of `Boundary Anchor`, `Implementation Entry Anchor`, request/response surface, UML closure, sequence closure, and test projection for this binding." in content


def test_data_model_template_requires_new_anchor_evidence_and_owner_closure():
    content = read("templates/data-model-template.md")

    assert "**Stage**: Stage 3 Shared Semantic Alignment" in content
    assert "If a semantic is used by only one `BindingRowID`, leave it to `/sdd.plan.contract`" in content
    assert "Leave complete request/response expansion to `/sdd.plan.contract`." in content
    assert "## Owner / Source Alignment" in content
    assert "Every shared projection, derivation, counter, badge, role label, or lifecycle guard MUST identify the owner class/field/state that sustains it." in content
    assert "- Owner/source for confirmed shared semantics MUST be closed in this stage; use `gap` only when required input/evidence is genuinely missing." in content
    assert "If a confirmed shared semantic cannot land as `existing` or `extended`, introduce the required `new` class/owner/lifecycle here instead of deferring the decision." in content
    assert "- Otherwise keep the lifecycle lightweight, but still include the transition table because it is a primary reader view." in content
    assert "- Apply the constitution lifecycle policy per shared lifecycle." in content
    assert "| Lifecycle Ref | State Owner | Stable States | Invariant Ref(s) | Consumed By BindingRowID(s) | Required Model |" in content


def test_test_matrix_template_forbids_backfilling_missing_stage_one_model():
    content = read("templates/test-matrix-template.md")

    assert "**Inputs**: `spec.md`" in content
    assert "[Coverage scope: which `UC / FR / UIF / UDD` paths must be verified and why]" in content
    assert "Downstream stages may consume these packets, but they must not rewrite `BindingRowID` or binding meaning." in content
    assert "Do not emit a binding packet for pure internal steps" in content


def test_tasks_command_uses_contract_as_realization_source():
    content = read("templates/commands/tasks.md")
    assert "selected `contracts/` slices" in content
    assert "Treat `TASKS_BOOTSTRAP.execution_readiness` as the primary hard gate." in content
    assert "perform one bounded fallback validation from `plan.md` control-plane fields" in content
    assert "Keep contract projection authoritative for the current run." in content
    assert "On projection drift, emit upstream writeback actions only:" in content
    assert "/sdd.specify" in content
    assert "/sdd.plan.test-matrix" in content
    assert "Repository-first explainable evidence" in content
    assert "/sdd.plan.interface-detail" not in content
    assert "interface-details/" not in content
    assert "Terminology note (compatibility, non-normative)" not in content
    assert "detail doc defines a narrower repo-backed internal handoff entry" not in content
    assert "Any selected `contract` row is missing `Full Field Dictionary (Operation-scoped)`" in content
    assert "binding-packet projection stability" in content


def test_tasks_template_is_contract_only():
    content = read("templates/tasks-template.md")
    assert "contracts/<operationId>.md" in content
    assert "Spec Slice:" in content
    assert "Test Slice:" in content
    assert "## 2.1) Upstream Alignment Repair (Required On Projection Drift)" in content
    assert "keep contract projection as execution truth for this run and emit explicit upstream writeback repair actions" in content
    assert "`/sdd.specify`" in content
    assert "`/sdd.plan.test-matrix`" in content
    assert "Cross-Interface Smoke Candidate (Required)" in content
    assert "interface detail" not in content.lower()


def test_analyze_routes_stale_contract_rows_only():
    content = read("templates/commands/analyze.md")
    assert "centralized audit entry and single concentrated audit step before `/sdd.implement`." in content
    assert "contract-projection drift governance" in content
    assert "stale `contract` -> `/sdd.plan.contract`" in content
    assert "Projection drift routing:" in content
    assert "upstream binding-projection drift across `plan.md` / `test-matrix.md`" in content
    assert "unresolved placeholder class/type labels in contract artifacts" in content
    assert "CRITICAL/HIGH findings MUST cite the authoritative source artifact(s) with concise supporting facts." in content
    assert "interface-detail" not in content
    assert "contract/interface DTO drift" not in content
    assert "contract/interface field drift from anchored DTOs/signatures" not in content


def test_docs_describe_contract_only_planning_queue():
    mapping = read_if_exists("docs/command-template-mapping.md")
    readme = read("README.md")
    installation = read_if_exists("docs/installation.md")
    quickstart = read_if_exists("docs/quickstart.md")
    spec_driven = read("spec-driven.md")

    if mapping is not None:
        assert "repeated `/sdd.plan.contract`" in mapping
        assert "/sdd.plan.interface-detail" not in mapping
        assert "interface-details/" not in mapping

    assert "/sdd.plan.contract" in readme
    assert "/sdd.plan.interface-detail" not in readme
    assert "interface-details/" not in readme

    if installation is not None:
        assert "/sdd.plan.contract" in installation
        assert "/sdd.plan.interface-detail" not in installation

    if quickstart is not None:
        assert "/sdd.plan.contract" in quickstart
        assert "/sdd.plan.interface-detail" not in quickstart

    assert "/sdd.plan.contract" in spec_driven
    assert "/sdd.plan.interface-detail" not in spec_driven


def test_docs_follow_canonical_planning_queue_order():
    readme = read("README.md")
    spec_driven = read("spec-driven.md")
    spec_template = read("templates/spec-template.md")

    assert readme.index("/sdd.plan.research") < readme.index("/sdd.plan.test-matrix") < readme.index("/sdd.plan.data-model")
    assert spec_driven.index("/sdd.plan.research") < spec_driven.index("/sdd.plan.test-matrix") < spec_driven.index("/sdd.plan.data-model")
    assert spec_template.index("`research.md` via `/sdd.plan.research`") < spec_template.index("`test-matrix.md` via `/sdd.plan.test-matrix`") < spec_template.index("`data-model.md` via `/sdd.plan.data-model`")


def test_readme_positions_analyze_as_main_flow_default():
    readme = read("README.md")
    assert "| `/sdd.analyze`   | Default pre-implementation unified audit entrypoint" in readme
    optional_section = readme.split("#### Optional Commands", 1)[1].split("### Environment Variables", 1)[0]
    assert "/sdd.analyze" not in optional_section


def test_readme_walkthrough_orders_tasks_before_analyze():
    readme = read("README.md")
    assert readme.index("### **STEP 6:** Generate task breakdown with `/sdd.tasks`") < readme.index("### **STEP 7:** Audit model and optional checklist (`/sdd.analyze`, `/sdd.checklist`)")


def test_cli_skill_descriptions_and_next_steps_drop_interface_detail():
    content = read("src/specify_cli/__init__.py")
    assert '"plan.contract": "Generate one queued full-field contract artifact' in content
    assert "plan.interface-detail" not in content
    assert "repeated [cyan]/{COMMAND_NAMESPACE}.plan.contract[/]" in content


def test_generation_commands_reference_runtime_templates_only():
    expected = {
        "templates/commands/constitution.md": ".specify/templates/constitution-template.md",
        "templates/commands/specify.md": ".specify/templates/spec-template.md",
        "templates/commands/specify.ui-html.md": ".specify/templates/ui-html-template.html",
        "templates/commands/plan.md": ".specify/templates/plan-template.md",
        "templates/commands/plan.research.md": ".specify/templates/research-template.md",
        "templates/commands/plan.data-model.md": ".specify/templates/data-model-template.md",
        "templates/commands/plan.test-matrix.md": ".specify/templates/test-matrix-template.md",
        "templates/commands/plan.contract.md": ".specify/templates/contract-template.md",
        "templates/commands/tasks.md": ".specify/templates/tasks-template.md",
        "templates/commands/checklist.md": ".specify/templates/checklist-template.md",
    }
    for rel_path, marker in expected.items():
        assert marker in read(rel_path)


def test_lint_rules_for_unified_contract_runtime_rows():
    content = read("rules/planning-lint-rules.tsv")
    assert "PLN-BP-002" in content
    assert "PLN-ID-007" in content
    assert "PLN-ID-008" in content
    assert "PLN-ID-009" in content
    assert "PLN-ID-012" in content
    assert "PLN-ID-013" in content
    assert "PLN-ID-014" in content
    assert "PLN-ID-015" in content
    assert "PLN-RA-011" in content
    assert "PLN-RA-012" in content
    assert "PLN-RA-013" in content
    assert "\tcontracts\tcontracts/*\t" in content
    assert "Interface details are missing" not in content


def test_plan_required_sections_are_consistent_across_lint_and_preflights():
    rules = read("rules/planning-lint-rules.tsv")
    task_preflight = read("scripts/task_preflight.py")
    data_model_preflight = read("scripts/data_model_preflight.py")
    required_sections = [
        "Summary",
        "Shared Context Snapshot",
        "Stage Queue",
        "Binding Projection Index",
        "Artifact Status",
        "Handoff Protocol",
    ]
    for section in required_sections:
        assert section in rules
        assert section in task_preflight
        assert section in data_model_preflight


def test_checklist_command_uses_branch_inferred_plan_input_with_hard_gate():
    content = read("templates/commands/checklist.md")
    assert "Treat all `$ARGUMENTS` as checklist context input." in content
    assert "Resolve `PLAN_FILE` from current feature branch using `{SCRIPT}` defaults." in content
    assert "If branch-derived `PLAN_FILE` is missing or invalid, stop immediately and report the blocker." in content
    assert "Run `{SCRIPT}` from repo root. Parse JSON for FEATURE_DIR and AVAILABLE_DOCS list." in content
    assert "plan.md (required; must match resolved PLAN_FILE)" in content
    assert "If present, the first positional token is `PLAN_FILE`" not in content
    assert "`/sdd.checklist <path/to/plan.md> [checklist-context...]`" not in content
    assert "--plan-file <PLAN_FILE>" not in content


def test_checklist_docs_and_templates_use_branch_inferred_invocation():
    readme = read("README.md")
    spec_template = read("templates/spec-template.md")
    specify_command = read("templates/commands/specify.md")
    checklist_template = read("templates/checklist-template.md")
    cli_init = read("src/specify_cli/__init__.py")

    assert "/sdd.checklist" in readme
    assert "/sdd.checklist <plan.md>" not in readme
    assert "/sdd.checklist specs/001-create-taskify/plan.md" not in readme
    assert "/sdd.checklist" in spec_template
    assert "/sdd.checklist <path/to/plan.md>" not in spec_template
    assert "/sdd.checklist" in specify_command
    assert "/sdd.checklist <path/to/plan.md>" not in specify_command
    assert "/sdd.checklist" in checklist_template
    assert "/sdd.checklist <path/to/plan.md>" not in checklist_template
    assert '/{COMMAND_NAMESPACE}.checklist[/]' in cli_init
    assert '/{COMMAND_NAMESPACE}.checklist <plan.md>' not in cli_init

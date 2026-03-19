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
    assert "Stage sharding (fixed): `research -> data-model -> test-matrix -> contract`" in content
    assert "Binding sharding (fixed): `/sdd.plan.contract` consumes one `BindingRowID` row per run" in content


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
    assert "Otherwise, if all required planning rows are complete, `Next Command = /sdd.tasks`" in contract
    assert "unified northbound interface design artifact" in contract
    assert "minimum northbound interface design artifact" not in contract


def test_plan_template_tracks_only_contract_artifacts():
    content = read("templates/plan-template.md")
    assert "`contract` is tracked as the single per-binding interface design artifact." in content
    assert "| BindingRowID | UC ID | UIF ID | FR ID | IF ID / IF Scope | TM ID | TC IDs | Operation ID | Boundary Anchor | Implementation Entry Anchor | Boundary Anchor Status | Implementation Entry Anchor Status | Test Scope |" in content
    assert "compact bootstrap fields only" in content
    assert "regenerate the projection instead of letting downstream commands rewrite it" in content
    assert "interface-detail" not in content


def test_plan_and_test_matrix_templates_precompute_contract_bootstrap_inputs():
    plan = read("templates/commands/plan.md")
    test_matrix_command = read("templates/commands/plan.test-matrix.md")
    test_matrix_template = read("templates/test-matrix-template.md")

    assert "- `Implementation Entry Anchor`" in plan
    assert "- `Boundary Anchor Status`" in plan
    assert "- `Implementation Entry Anchor Status`" in plan
    assert "- `Test Scope`" in plan

    assert "contract seed packet" in test_matrix_command
    assert "Do not read `research.md` in this stage." not in test_matrix_command
    assert "- `Implementation Entry Anchor`" in test_matrix_command
    assert "- `Boundary Anchor Status`" in test_matrix_command
    assert "- `Implementation Entry Anchor Status`" in test_matrix_command
    assert "- `Request DTO Anchor`" in test_matrix_command
    assert "- `State Owner Anchor(s)`" in test_matrix_command
    assert "- `Branch/Failure Anchor(s)`" in test_matrix_command

    assert "## Binding Contract Packets" in test_matrix_template
    assert "authoritative per-binding contract seed packet consumed by `/sdd.plan.contract`" in test_matrix_template
    assert "State Owner Anchor(s)" in test_matrix_template
    assert "MUST NOT be added to `Scenario Matrix` or `Verification Case Anchors` tuple keys" in test_matrix_template
    assert "| BindingRowID | Operation ID | IF Scope | Boundary Anchor | Boundary Anchor Status | Implementation Entry Anchor |" in test_matrix_template


def test_contract_command_uses_test_matrix_as_default_semantic_source():
    content = read("templates/commands/plan.contract.md")

    assert "treat the selected binding packet in `test-matrix.md` as the default semantic source for the contract run." in content
    assert "if absent, stop and route back to `/sdd.plan.test-matrix`" in content
    assert "Do not read `spec.md`, `research.md`, or `data-model.md` unless the selected binding packet is missing required fields or cannot resolve contract-visible owner/source evidence." in content
    assert "mark tuple drift, set an explicit blocker, and route `/sdd.plan.test-matrix`" in content
    assert "Keep repo-backed verification bounded to the selected `BindingRowID` and active blockers" in content
    assert "- request DTO anchor target, when present" in content
    assert "- response DTO anchor target, when present" in content
    assert "- one primary collaborator anchor, when required for contract-visible behavior" in content
    assert "- up to three `State Owner Anchor(s)` targets, when present" in content
    assert "Sequence design MUST explicitly render every mandatory repo-backed collaborator hop" in content
    assert "Sequence design MUST NOT collapse multiple mandatory collaborators/dependencies into one synthetic participant label" in content
    assert "`opt` blocks are valid only for truly conditional branches" in content
    assert "do not synthesize `RequestDTO` / `ResponseDTO` labels unless the anchored symbol itself uses those names." in content
    assert "MAY refine operation-scoped VO/DTO/field mappings" in content
    assert "MUST NOT mint new globally stable model concepts" in content
    assert "Stop local refinement and route upstream when continuing would require a new upstream semantic owner" in content
    assert "contract-visible field has no stable owner/source in `data-model.md`" in content
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
    assert "Keep repo-backed reads bounded to the selected unit and lifecycle/invariant blockers." in data_model
    assert "Prefer section-level reads of `spec.md` and `research.md`" in data_model
    assert "full spec-scoped abstract data-model class set" in data_model
    assert "Every selected `new` anchor in normative content MUST record:" in data_model
    assert "A planned-but-missing file path is not sufficient evidence for normative `new`" in data_model
    assert "downstream `test-matrix.md` and `contracts/` MUST NOT invent missing state owners or owner fields" in data_model

    assert "Stage Packet (Test-Matrix Unit)" in test_matrix
    assert "Use this packet as the default context for generation and binding projection." in test_matrix
    assert "coverage scope, path decomposition, verification goals, observability signals, and the contract seed packets" in test_matrix
    assert "prefer section-level rereads over whole-file replay for the selected unit" in test_matrix
    assert "Treat `data-model.md` as authoritative for globally stable owner classes/fields/states" in test_matrix
    assert "Do not introduce new globally stable state owners, owner fields, or lifecycle vocabulary that are absent from `data-model.md`" in test_matrix
    assert "send the issue back to `/sdd.plan.data-model` instead of widening Stage 2 scope" in test_matrix


def test_contract_template_contains_unified_realization_requirements():
    content = read("templates/contract-template.md")
    assert "# Northbound Interface Design:" in content
    assert "## Northbound Contract Summary" in content
    assert "## Full Field Dictionary (Operation-scoped)" in content
    assert "## Contract Realization Design" in content
    assert "## Runtime Correctness Check" in content
    assert "**Test Scope (Required)**" in content
    assert "## Downstream Projection Input (Required)" in content
    assert "### Spec Projection Slice" in content
    assert "### Test Projection Slice" in content
    assert "### Cross-Interface Smoke Candidate (Required)" in content
    assert "End-to-end chain continuity" in content
    assert "Sequence-participant UML closure" in content
    assert "New-field/method call linkage" in content
    assert "If `Boundary Anchor` and `Implementation Entry Anchor` resolve to the same repo-backed symbol, render **Sequence Variant B only**." in content
    assert "MUST NOT declare a separate `Entry` participant or any boundary-to-entry handoff message." in content
    assert "#### Sequence Variant A (Boundary != Entry)" in content
    assert "#### Sequence Variant B (Boundary == Entry)" in content
    assert "#### UML Variant A (Boundary != Entry)" in content
    assert "#### UML Variant B (Boundary == Entry)" in content
    assert "Sequence MUST explicitly represent every mandatory repo-backed collaborator hop" in content
    assert "Sequence MUST NOT merge multiple mandatory collaborators/dependencies into one synthetic participant label" in content
    assert "mandatory main-path collaborator/dependency calls MUST remain outside `opt`." in content
    assert "UML request/response class labels should reuse anchored symbol names or repository boundary naming conventions" in content
    assert "Collaborator-chain coverage" in content


def test_data_model_template_requires_new_anchor_evidence_and_owner_closure():
    content = read("templates/data-model-template.md")

    assert "full spec-scoped abstract data-model class set" in content
    assert "MAY refine operation-scoped VO/DTO/field mappings from the classes and owners declared here" in content
    assert "## State Ownership Closure" in content
    assert "Every globally stable derived/projection semantic above MUST cite the owner class/field/state that sustains it." in content
    assert "route back to `/sdd.plan.data-model` instead of inventing the model later" in content
    assert "## New Anchor Evidence" in content
    assert "Every normative `new` anchor MUST include explicit rejection evidence for both `existing` and `extended`" in content
    assert "Planned-but-missing files/symbols are not sufficient evidence for normative `new`" in content
    assert "When a lifecycle uses `extended`, keep `Stable states` in the anchored vocabulary" in content


def test_test_matrix_template_forbids_backfilling_missing_stage_one_model():
    content = read("templates/test-matrix-template.md")

    assert "[Coverage scope: which spec paths must be verified and why]" in content
    assert "[How the selected strategy seeds downstream `Binding Contract Packets`]" in content
    assert "/sdd.plan.contract` MUST consume these tuple keys verbatim and MUST NOT redefine them." in content
    assert "[Where projections/derivations depend on globally stable owner classes or owner fields from `data-model.md`]" in content
    assert "Do not invent new globally stable owner classes, owner fields, or lifecycle vocabulary here" in content
    assert "`State Owner Anchor(s)` MUST trace back to owner classes/fields already modeled as globally stable in `data-model.md`" in content


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
    assert "Tuple drift routing" in content
    assert "upstream tuple-seed drift across `plan.md` / `test-matrix.md`" in content
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
    assert "\tcontracts\tcontracts/*\t" in content
    assert "Interface details are missing" not in content


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

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
    assert "The first positional token is mandatory and is `SPEC_FILE`" in content
    assert "`/sdd.plan <path/to/spec.md> [technical-context...]`" in content
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
    assert "If any `contract` rows remain `blocked`, `Next Command = /sdd.plan.contract <absolute path to plan.md>`" in contract
    assert "Otherwise, if any `contract` rows remain `pending`, `Next Command = /sdd.plan.contract <absolute path to plan.md>`" in contract
    assert "Otherwise, if all required planning rows are complete, `Next Command = /sdd.tasks <absolute path to plan.md>`" in contract
    assert "unified northbound interface design artifact" in contract
    assert "minimum northbound interface design artifact" not in contract


def test_plan_template_tracks_only_contract_artifacts():
    content = read("templates/plan-template.md")
    assert "`contract` is tracked as the single per-binding interface design artifact." in content
    assert "| BindingRowID | UC ID | UIF ID | FR ID | IF ID / IF Scope | TM ID | TC IDs | Operation ID | Boundary Anchor | Implementation Entry Anchor | Boundary Anchor Status | Implementation Entry Anchor Status | Test Scope |" in content
    assert "compact bootstrap fields only" in content
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
    assert "Compatibility Fallback (Legacy `test-matrix.md`)" in content
    assert "compatibility seed packet from" in content
    assert "if absent, enter compatibility fallback mode" in content
    assert "Do not read `spec.md`, `research.md`, or `data-model.md` unless the selected binding packet is missing required fields." in content
    assert "keep fallback bounded to `PLAN_FILE` + `test-matrix.md` + conditional `spec.md`/`research.md`/`data-model.md` only" in content
    assert "Keep repo-backed verification bounded to no more than eight files in one contract run" in content
    assert "- request DTO anchor target, when present" in content
    assert "- response DTO anchor target, when present" in content
    assert "- one primary collaborator anchor, when required for contract-visible behavior" in content
    assert "- up to three `State Owner Anchor(s)` targets, when present" in content


def test_contract_selection_rules_handle_empty_queue_before_packet_resolution():
    content = read("templates/commands/plan.contract.md")
    no_pending_idx = content.index("If no pending or blocked contract row exists, stop and report that the contract queue is complete")
    resolve_packet_idx = content.index("Attempt to resolve one selected binding packet in `test-matrix.md` by the same `BindingRowID`; if absent, enter compatibility fallback mode")
    assert no_pending_idx < resolve_packet_idx


def test_research_data_model_and_test_matrix_are_packet_first():
    research = read("templates/commands/plan.research.md")
    data_model = read("templates/commands/plan.data-model.md")
    test_matrix = read("templates/commands/plan.test-matrix.md")

    assert "Stage Packet (Research Unit)" in research
    assert "Read at most three repo-backed files per research run." in research
    assert "Use this packet as the default context for generation." in research

    assert "Stage Packet (Data-Model Unit)" in data_model
    assert "Read at most five repo-backed files per data-model run." in data_model
    assert "Prefer section-level reads of `spec.md` and `research.md`" in data_model

    assert "Stage Packet (Test-Matrix Unit)" in test_matrix
    assert "Use this packet as the default context for generation and binding projection." in test_matrix
    assert "prefer section-level rereads over whole-file replay for the selected unit" in test_matrix


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
    assert "End-to-end chain continuity" in content
    assert "Sequence-participant UML closure" in content
    assert "New-field/method call linkage" in content
    assert "If `Boundary Anchor` and `Implementation Entry Anchor` resolve to the same repo-backed symbol, render **Sequence Variant B only**." in content
    assert "MUST NOT declare a separate `Entry` participant or any boundary-to-entry handoff message." in content
    assert "#### Sequence Variant A (Boundary != Entry)" in content
    assert "#### Sequence Variant B (Boundary == Entry)" in content
    assert "#### UML Variant A (Boundary != Entry)" in content
    assert "#### UML Variant B (Boundary == Entry)" in content


def test_tasks_command_uses_contract_as_realization_source():
    content = read("templates/commands/tasks.md")
    assert "required execution anchors are missing from `Binding Projection Index`, completed `Artifact Status` rows, `contracts/`, or `test-matrix.md`" in content
    assert "Use `contracts/` as the authoritative realization design source for execution targeting" in content
    assert "Downstream Projection Input (Required)" in content
    assert "For each active IF unit, treat contract `Downstream Projection Input (Required)` (`Spec Projection Slice`, `Test Projection Slice`) as the authoritative downstream execution projection." in content
    assert "keep contract projection as execution truth for this run and emit explicit upstream writeback repair actions" in content
    assert "`/sdd.specify` for spec drift, `/sdd.plan.test-matrix` for test-matrix drift" in content
    assert "route back to `/sdd.plan.contract`" in content
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
    assert "interface detail" not in content.lower()


def test_analyze_routes_stale_contract_rows_only():
    content = read("templates/commands/analyze.md")
    assert "route stale `contract` rows to `/sdd.plan.contract`" in content
    assert "contract-projection drift governance" in content
    assert "treat contract projection as current downstream execution baseline" in content
    assert "route spec writeback repairs to `/sdd.specify`; route test-matrix writeback repairs to `/sdd.plan.test-matrix`" in content
    assert "unresolved contract projection drift requiring upstream writeback" in content
    assert "interface-detail" not in content
    assert "contract/interface DTO drift" not in content
    assert "contract/interface field drift from anchored DTOs/signatures" not in content
    assert "runtime correctness (from unified contract realization design)" in content


def test_docs_describe_contract_only_planning_queue():
    mapping = read_if_exists("docs/command-template-mapping.md")
    readme = read("README.md")
    installation = read_if_exists("docs/installation.md")
    quickstart = read_if_exists("docs/quickstart.md")
    spec_driven = read("spec-driven.md")

    if mapping is not None:
        assert "repeated `/sdd.plan.contract <plan.md>`" in mapping
        assert "/sdd.plan.interface-detail" not in mapping
        assert "interface-details/" not in mapping

    assert "/sdd.plan.contract" in readme
    assert "/sdd.plan.interface-detail" not in readme
    assert "interface-details/" not in readme

    if installation is not None:
        assert "/sdd.plan.contract <plan.md>" in installation
        assert "/sdd.plan.interface-detail" not in installation

    if quickstart is not None:
        assert "/sdd.plan.contract specs/001-create-taskify/plan.md" in quickstart
        assert "/sdd.plan.interface-detail" not in quickstart

    assert "/sdd.plan.contract <plan.md>" in spec_driven
    assert "/sdd.plan.interface-detail" not in spec_driven


def test_cli_skill_descriptions_and_next_steps_drop_interface_detail():
    content = read("src/specify_cli/__init__.py")
    assert '"plan.contract": "Generate one queued full-field contract artifact' in content
    assert "plan.interface-detail" not in content
    assert "repeated [cyan]/{COMMAND_NAMESPACE}.plan.contract <plan.md>[/]" in content


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
        "templates/commands/analyze.md": ".specify/templates/lint-report-template.md",
    }
    for rel_path, marker in expected.items():
        assert marker in read(rel_path)


def test_lint_rules_for_unified_contract_runtime_rows():
    content = read("rules/planning-lint-rules.tsv")
    assert "PLN-ID-007" in content
    assert "PLN-ID-008" in content
    assert "PLN-ID-009" in content
    assert "\tcontracts\tcontracts/*\t" in content
    assert "Interface details are missing" not in content


def test_checklist_command_requires_explicit_plan_input_and_hard_gate():
    content = read("templates/commands/checklist.md")
    assert "The first positional token is mandatory and is `PLAN_FILE`" in content
    assert "`/sdd.checklist <path/to/plan.md> [checklist-context...]`" in content
    assert "Run `{SCRIPT} --plan-file <PLAN_FILE>` from repo root" in content
    assert "Do not use current-branch feature inference for checklist target selection." in content
    assert "plan.md (required; must match resolved PLAN_FILE)" in content


def test_checklist_docs_and_templates_use_plan_path_invocation():
    readme = read("README.md")
    spec_template = read("templates/spec-template.md")
    specify_command = read("templates/commands/specify.md")
    checklist_template = read("templates/checklist-template.md")
    cli_init = read("src/specify_cli/__init__.py")

    assert "/sdd.checklist <plan.md>" in readme
    assert "/sdd.checklist specs/001-create-taskify/plan.md" in readme
    assert "/sdd.checklist <path/to/plan.md>" in spec_template
    assert "/sdd.checklist <path/to/plan.md>" in specify_command
    assert "/sdd.checklist <path/to/plan.md>" in checklist_template
    assert '/{COMMAND_NAMESPACE}.checklist <plan.md>' in cli_init



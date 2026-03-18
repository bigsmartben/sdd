from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_command_mapping_documents_authority_model():
    mapping_path = REPO_ROOT / "docs" / "command-template-mapping.md"
    if not mapping_path.exists():
        return

    content = mapping_path.read_text(encoding="utf-8")

    assert "Authoritative artifacts own semantics" in content
    assert "Repo semantic evidence for `/sdd.plan` comes from source anchors plus engineering assembly facts" in content
    assert "Repository-first projections are canonical only under `.specify/memory/repository-first/`" in content
    assert "Runtime template authority path for generation and output-structure commands is `.specify/templates/`." in content
    assert "| `plan.md` | Planning control plane, binding projection ledger, queue/fingerprint state | Derived for planning semantics; authoritative for planning queue state |" in content
    assert "| `/sdd.plan.test-matrix <plan.md>` | Generate the queued verification matrix and initialize binding rows | `.specify/templates/test-matrix-template.md` | `test-matrix.md`, `plan.md` binding rows |" in content
    assert "selected contract `Spec Projection Slice` and `Test Projection Slice` are the authoritative downstream projection input" in content
    assert "keep contract projection for current execution output and issue explicit upstream writeback repair actions" in content
    assert "must stop when `plan.md` queue rows show incomplete planning stages or pending contract units" in content
    assert "owns final stale-planning detection" in content


def test_specify_and_plan_define_authority_vs_derived_views():
    specify = read("templates/commands/specify.md")
    plan = read("templates/commands/plan.md")
    plan_template = read("templates/plan-template.md")

    assert "Authority and derivation rules" in specify
    assert "`spec.md` becomes the authoritative feature-semantics artifact" in specify
    assert "`ui.html` generated later by `/sdd.specify.ui-html` is a derived prototype artifact" in specify
    assert ".specify/templates/spec-template.md" in specify
    assert "does **not** generate downstream planning-stage artifacts directly" in plan
    assert "`plan.md` is the sole planning control plane" in plan
    assert "derived planning control plane" in plan
    assert ".specify/templates/plan-template.md" in plan
    assert "`plan.md` is the planning control plane for this feature." in plan_template
    assert "It is authoritative for planning queue state, binding-projection rows, and source/output fingerprints only." in plan_template


def test_tasks_implement_and_analyze_enforce_authority_protocol():
    tasks = read("templates/commands/tasks.md")
    tasks_template = read("templates/tasks-template.md")
    implement = read("templates/commands/implement.md")
    analyze = read("templates/commands/analyze.md")
    constitution = read("templates/commands/constitution.md")

    assert "Treat `plan.md` as the planning control plane" in tasks
    assert "This runtime scheduling guidance is execution-only. It MUST NOT change artifact authority" in tasks
    assert "Any tuple indexes, execution maps, or working summaries created during `/sdd.tasks` are derived views only" in tasks
    assert "Temporary derived views created during `/sdd.tasks` are run-local only" in tasks
    assert "treat contract `Downstream Projection Input (Required)` (`Spec Projection Slice`, `Test Projection Slice`) as the authoritative downstream execution projection" in tasks
    assert "keep contract projection as execution truth for this run and emit explicit upstream writeback repair actions" in tasks
    assert "Binding Projection Index" in tasks
    assert "does **not** own coverage completeness, uncovered MUST requirement analysis, ambiguity sweeps" in tasks
    assert "helper-doc leakage checks" in tasks
    assert ".specify/templates/tasks-template.md" in tasks
    assert "Inline task summaries, local execution notes, and other derived views must yield to the authoritative artifacts above" in tasks_template
    assert "If contract projection slices drift from `spec.md` or `test-matrix.md`, keep contract projection as execution truth for this run" in tasks_template
    assert "same run-local execution graph used to render `tasks.md`" in tasks_template

    assert "Analyze-first is a blocking reminder by default" in implement
    assert "Analyze-first blocking reminder" in implement
    assert "explicitly waives that audit step for this run" in implement
    assert "runtime batching notes, ready-task summaries, and local execution shortcuts as derived views only" in implement
    assert "use the authoritative artifact for semantics" in implement
    assert ".specify/memory/repository-first/technical-dependency-matrix.md" in implement

    assert "`plan.md` is the planning control plane for queue state, binding-projection rows, and source/output fingerprints only" in analyze
    assert "owns comprehensive implementation-readiness analysis and audit responsibilities" in analyze
    assert "Treat task-local summaries or inline mirrors as derived views only" in analyze
    assert "contract-projection drift governance" in analyze
    assert "route spec writeback repairs to `/sdd.specify`; route test-matrix writeback repairs to `/sdd.plan.test-matrix`" in analyze
    assert ".specify/templates/lint-report-template.md" in analyze
    assert "stale planning outputs" in analyze
    assert "route stale `test-matrix` rows or missing binding rows to `/sdd.plan.test-matrix`" in analyze

    assert "Treat `.specify/memory/constitution.md` as the authoritative project-level rule source." in constitution


def test_constitution_declares_repo_anchor_whitelist_and_blacklist():
    constitution = read(".specify/memory/constitution.md")

    assert "### Repo-Anchor Evidence Protocol" in constitution
    assert "**Source anchors**: source-code files/symbols" in constitution
    assert "**Engineering assembly facts**: build/module manifests" in constitution
    assert "Repository-first projections are project-level authoritative artifacts located only at `.specify/memory/repository-first/`." in constitution
    assert "Dependency evidence MUST come from build-manifest auto-detection with deterministic priority" in constitution
    assert "planning artifacts, docs, tests, demos, and generated outputs may be read as context only" in constitution
    assert "MUST NOT be promoted into repo semantic evidence" in constitution


def test_tasks_boundary_stays_execution_gates_only_not_comprehensive_audit():
    tasks = read("templates/commands/tasks.md")

    assert "hard execution safety gates" in tasks
    assert "does **not** own coverage completeness" in tasks
    assert "uncovered MUST requirement analysis" in tasks
    assert "Handoff all non-mainline comprehensive audit concerns to `/sdd.analyze`" in tasks


def test_tasks_runtime_projection_and_hook_boundaries_stay_narrow():
    tasks = read("templates/commands/tasks.md")

    assert "Treat `TASKS_BOOTSTRAP.execution_readiness` as the primary preflight hard-gate source when present and parseable." in tasks
    assert "If `TASKS_BOOTSTRAP.execution_readiness.ready_for_task_generation = true`, skip duplicate whole-table gate recomputation and proceed directly to scoped unit generation checks." in tasks
    assert "Hook dispatch here is phase-boundary execution only" in tasks
    assert "same run-local execution graph used to render `tasks.md`" in tasks
    assert "do not re-parse the just-written markdown to construct the manifest" in tasks
    assert "invalidate run-local derived views" in tasks


def test_analyze_boundary_owns_centralized_cross_artifact_audit_and_stale_gate():
    analyze = read("templates/commands/analyze.md")

    assert "centralized audit entry and single concentrated audit step before `/sdd.implement`" in analyze
    assert "owns comprehensive implementation-readiness analysis and audit responsibilities" in analyze
    assert "cross-artifact contradiction detection" in analyze
    assert "stale planning outputs where `plan.md` source fingerprints no longer match the current upstream artifact state" in analyze



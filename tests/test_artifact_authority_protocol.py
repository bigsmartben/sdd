from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_command_mapping_documents_authority_model():
    mapping_path = REPO_ROOT / "docs" / "command-template-mapping.md"
    if not mapping_path.exists():
        return

    content = mapping_path.read_text(encoding="utf-8")

    assert "Authoritative artifacts own semantics" in content
    assert "Repository-first projections are canonical only under `.specify/memory/repository-first/`" in content
    assert "Runtime template authority path for generation and output-structure commands is `.specify/templates/`." in content


def test_specify_and_plan_define_authority_vs_derived_views():
    specify = read("templates/commands/specify.md")
    plan = read("templates/commands/plan.md")
    plan_template = read("templates/plan-template.md")

    assert "`spec.md` becomes the authoritative feature-semantics artifact" in specify
    assert "`ui.html` generated later by `/sdd.specify.ui-html` is a derived prototype artifact" in specify
    assert "`/sdd.specify` writes `spec.md` only and MUST NOT directly generate `ui.html`." in specify
    assert "`/sdd.specify.ui-html` is an optional sidecar command; users decide if/when to invoke it." in specify
    assert "`plan.md` is the sole planning control plane" in plan
    assert "does **not** generate downstream planning-stage artifacts directly" in plan
    assert "orchestration authority for queue state, binding projection, and artifact execution status" in plan_template


def test_tasks_implement_and_analyze_use_compact_contract_sections():
    tasks = read("templates/commands/tasks.md")
    implement = read("templates/commands/implement.md")
    analyze = read("templates/commands/analyze.md")

    for marker in ("## Goal", "## Read Only", "## Write Only", "## Final Output"):
        assert marker in tasks
        assert marker in implement
        assert marker in analyze

    assert "## Stop Conditions" in tasks
    assert "## Stop Conditions" in implement

    assert "Treat `TASKS_BOOTSTRAP.execution_readiness` as the primary hard gate." in tasks
    assert "`TASKS_BOOTSTRAP.execution_readiness.errors` contains blockers" in tasks
    assert "Active executable tuples select `new` repo anchors but lack explicit rejection evidence for `existing` and `extended`" in tasks
    assert "LOCAL_EXECUTION_PROTOCOL" in tasks
    assert "LOCAL_EXECUTION_PROTOCOL.python.runner_cmd" in tasks
    assert "LOCAL_EXECUTION_PROTOCOL.runtime_tools" in tasks
    assert "Repository-first explainable evidence" in tasks
    assert "Unified Repository-First Gate Protocol (`URFGP`)" in tasks
    assert "Repository-First Evidence Bundle (`RFEB`)" in tasks
    assert "`source_refs`" in tasks
    assert "`signal_ids` (`SIG-*`" in tasks
    assert "`module_edge_ids`" in tasks
    assert "Top-level keys: `schema_version`, `generated_at`, `generated_from`, `tasks`" in tasks

    assert "Treat `IMPLEMENT_BOOTSTRAP.analyze_readiness` as the primary analyze hard gate." in implement
    assert "stop immediately and report the runtime bootstrap blocker" in implement
    assert "waive-analyze-gate" in implement
    assert "`IMPLEMENT_BOOTSTRAP.analyze_readiness.errors` contains blockers" in implement
    assert "LOCAL_EXECUTION_PROTOCOL" in implement
    assert "LOCAL_EXECUTION_PROTOCOL.python.runner_cmd" in implement
    assert "LOCAL_EXECUTION_PROTOCOL.runtime_tools" in implement
    assert "no bypass of repo-anchor strategy priority (`existing -> extended -> new`)" in implement
    assert "Unified Repository-First Gate Protocol (`URFGP`)" in implement
    assert "Repository-First Evidence Bundle (`RFEB`)" in implement
    assert "Read `plan.md` only as control-plane context (`Shared Context Snapshot`, `Stage Queue`, `Artifact Status`, `Binding Projection Index`)" in implement
    assert "Repository-first Validation Trace" in implement

    assert "centralized audit entry and single concentrated audit step before `/sdd.implement`" in analyze
    assert "CRITICAL/HIGH findings MUST cite the authoritative source artifact(s) with concise supporting facts." in analyze
    assert "repo-anchor strategy priority compliance (`existing -> extended -> new`)" in analyze
    assert "any active tuple selecting `new` anchors without explicit rejection evidence for both `existing` and `extended` is `FAIL`" in analyze
    assert "matrix dependency facts plus `SIG-*` governance signals including divergence, version-source-mix, and `unresolved`" in analyze
    assert "using concrete module-to-module rows as the primary representation" in analyze
    assert "Unified Repository-First Gate Protocol (`URFGP`)" in analyze
    assert "Repository-First Evidence Bundle (`RFEB`)" in analyze
    assert "Gate Decision" in analyze
    assert "<!-- SDD_ANALYZE_RUN_BEGIN -->" in analyze
    assert "<!-- SDD_ANALYZE_RUN_END -->" in analyze


def test_constitution_declares_repo_anchor_whitelist_and_blacklist():
    constitution = read("templates/constitution-template.md")

    assert "### Repo-Anchor Evidence Protocol" in constitution
    assert "**Source anchors**: source-code files/symbols" in constitution
    assert "**Engineering assembly facts**: build/module manifests" in constitution
    assert "evaluate and apply in strict order: `existing` -> `extended` -> `new`" in constitution
    assert ".specify/memory/repository-first/technical-dependency-matrix.md" in constitution
    assert ".specify/memory/repository-first/module-invocation-spec.md" in constitution
    assert "## Local Execution Protocol Governance" in constitution
    assert "LOCAL_EXECUTION_PROTOCOL" in constitution
    assert "`specify-cli` tool runtime" in constitution


def test_tasks_runtime_projection_and_hook_boundaries_stay_narrow():
    tasks = read("templates/commands/tasks.md")

    assert "Treat `TASKS_BOOTSTRAP.execution_readiness` as the primary hard gate." in tasks
    assert "do not recompute full hard gates by re-deriving complete `plan.md` tables" in tasks
    assert "Hook dispatch here is phase-boundary execution only" in tasks
    assert "same run-local execution graph used to render `tasks.md`" in tasks
    assert "Do not re-parse the just-written markdown to construct the manifest" in tasks
    assert "Invalidate run-local derived views" in tasks


def test_analyze_boundary_owns_centralized_cross_artifact_audit_and_stale_gate():
    analyze = read("templates/commands/analyze.md")

    assert "centralized audit entry and single concentrated audit step before `/sdd.implement`" in analyze
    assert "stale planning outputs where `plan.md` source fingerprints no longer match the current upstream artifact state" in analyze
    assert "stale `contract` -> `/sdd.plan.contract`" in analyze


def test_research_template_keeps_repo_first_as_optional_reference_not_primary_audit_input():
    research = read("templates/research-template.md")

    assert "For `/sdd.plan.research`, repository reuse evidence comes from source code and `.specify/memory/constitution.md`." in research
    assert "Repository-first baseline files are consumed by `/sdd.plan` as shared bootstrap inputs" in research

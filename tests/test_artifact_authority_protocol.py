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


def test_supporting_governance_templates_define_artifact_quality_signals():
    agent_template = read("templates/agent-file-template.md")
    dep_matrix = read("templates/technical-dependency-matrix-template.md")
    invocation = read("templates/module-invocation-spec-template.md")
    ui_html_template = read("templates/ui-html-template.html")

    assert "## Artifact Quality Signals" in agent_template
    assert "Must: read like actionable project guidance for engineers and agents." in agent_template

    assert "## Artifact Quality Signals" in dep_matrix
    assert "Must: read like an exhaustive dependency-fact projection." in dep_matrix

    assert "## Artifact Quality Signals" in invocation
    assert "Must: read like concrete module-governance rules for the real repository." in invocation

    assert "Artifact Quality Signals" in ui_html_template
    assert "Must: feel like one coherent review prototype." in ui_html_template


def test_docs_describe_compact_prompt_governance_style():
    readme = read("README.md")
    spec_driven = read("spec-driven.md")

    assert "### Prompt Governance Style" in readme
    assert "- `Must`" in readme
    assert "- `Must not`" in readme
    assert "- `Strictly`" in readme
    assert "- `Reasoning Order`" in readme

    assert "### Prompt Governance Style" in spec_driven
    assert "- `Must`" in spec_driven
    assert "- `Must not`" in spec_driven
    assert "- `Strictly`" in spec_driven
    assert "- `Reasoning Order`" in spec_driven


def test_constitution_and_issue_projection_commands_define_artifact_quality_contracts():
    constitution = read("templates/commands/constitution.md")
    taskstoissues = read("templates/commands/taskstoissues.md")

    assert "## Artifact Quality Contract" in constitution
    assert "## Reasoning Order" in constitution
    assert "Must: output a durable governance artifact senior maintainers can rely on." in constitution
    assert "Strictly: keep rules normative, long-lived, and the single shortest source of truth." in constitution

    assert "## Artifact Quality Contract" in taskstoissues
    assert "## Reasoning Order" in taskstoissues
    assert "Must: convert tasks into actionable execution tickets." in taskstoissues
    assert "Skip anything that cannot become a clean ticket without inventing semantics." in taskstoissues


def test_specify_and_plan_define_authority_vs_derived_views():
    specify = read("templates/commands/specify.md")
    plan = read("templates/commands/plan.md")
    plan_template = read("templates/plan-template.md")

    assert "`spec.md` becomes the authoritative feature-semantics artifact" in specify
    assert "## Artifact Quality Contract" in specify
    assert "Must: output one professional `spec.md`" in specify
    assert "## Reasoning Order" in specify
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

    for marker in ("## Goal", "## Allowed Inputs"):
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
    assert "## Artifact Quality Contract" in tasks
    assert "## Reasoning Order" in tasks
    assert "## Writeback Contract" in tasks
    assert "## Output Contract" in tasks
    assert "Must: generate execution-ready work packages with clear dependencies, targets, and completion anchors." in tasks
    assert "Create or refresh `tasks.md` and `tasks.manifest.json` only." in tasks
    assert "do not repair upstream artifacts locally" in tasks

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
    assert "## Artifact Quality Contract" in implement
    assert "## Writeback Contract" in implement
    assert "## Output Contract" in implement
    assert "Produce implementation results that feel native to the repository" in implement
    assert "Update task-state transitions in `tasks.md` only for tasks actually executed in this run." in implement
    assert "Do not rewrite `plan.md`, `spec.md`, `research.md`, `test-matrix.md`, `data-model.md`, or `contracts/`" in implement

    assert "centralized audit entry and single concentrated audit step before `/sdd.implement`" in analyze
    assert "CRITICAL/HIGH findings MUST cite the authoritative source artifact(s) with concise supporting facts." in analyze
    assert "repo-anchor strategy priority compliance (`existing -> extended -> new`)" in analyze
    assert "any active tuple selecting `new` anchors without explicit rejection evidence for both `existing` and `extended` is `FAIL`" in analyze
    assert "matrix dependency facts plus `SIG-*` governance signals including divergence, version-source-mix, and `unresolved`" in analyze
    assert "using concrete module-to-module rows as the primary representation" in analyze
    assert "Repository-First Evidence Bundle (`RFEB`)" in analyze
    assert "Gate Decision" in analyze
    assert "<!-- SDD_ANALYZE_RUN_BEGIN -->" in analyze
    assert "<!-- SDD_ANALYZE_RUN_END -->" in analyze
    assert "## Artifact Quality Contract" in analyze
    assert "## Reasoning Order" in analyze
    assert "## Writeback Contract" in analyze
    assert "## Output Contract" in analyze
    assert "Must: produce one action-ready audit with prioritized findings and one authoritative gate decision." in analyze
    assert "Append exactly one analyze run block to `ANALYZE_HISTORY`." in analyze
    assert "never perform local repair in this stage" in analyze


def test_clarify_ui_and_checklist_commands_define_artifact_quality_contracts():
    clarify = read("templates/commands/clarify.md")
    ui_html = read("templates/commands/specify.ui-html.md")
    checklist = read("templates/commands/checklist.md")

    assert "## Artifact Quality Contract" in clarify
    assert "## Reasoning Order" in clarify
    assert "Must: leave `spec.md` reading like a deliberate refinement" in clarify
    assert "Strictly: preserve feature voice and synchronize all impacted `UC` / `FR` / `UIF` / `UDD` / `EC` anchors." in clarify

    assert "## Artifact Quality Contract" in ui_html
    assert "## Reasoning Order" in ui_html
    assert "Must: produce one coherent review prototype that makes the dominant user intent obvious in one pass." in ui_html
    assert "Strictly: every demonstrated interaction and state must trace back to `spec.md` and teach something real." in ui_html

    assert "## Artifact Quality Contract" in checklist
    assert "## Reasoning Order" in checklist
    assert "Must: generate a checklist a strong reviewer would actually use." in checklist
    assert "Strictly: every item must protect a real requirements-quality failure mode." in checklist


def test_constitution_declares_repo_anchor_whitelist_and_blacklist():
    constitution = read("templates/constitution-template.md")

    assert "## Artifact Quality Signals" in constitution
    assert "Must: read like durable repository governance." in constitution
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
    assert "Write only execution decomposition artifacts." in tasks


def test_analyze_boundary_owns_centralized_cross_artifact_audit_and_stale_gate():
    analyze = read("templates/commands/analyze.md")

    assert "centralized audit entry and single concentrated audit step before `/sdd.implement`" in analyze
    assert "contract-projection drift governance" in analyze
    assert "route `/sdd.plan.test-matrix` to repair the upstream binding projection" in analyze
    assert "Write only append-only audit history." in analyze


def test_research_template_keeps_repo_first_as_optional_reference_not_primary_audit_input():
    research = read("templates/research-template.md")

    assert "## Artifact Quality Signals" in research
    assert "Must: read like a bounded decision memo." in research
    assert "For `/sdd.plan.research`, repository reuse evidence comes from source code and `.specify/memory/constitution.md`." in research
    assert "Repository-first baseline files are consumed by `/sdd.plan` as shared bootstrap inputs" in research


def test_spec_template_declares_artifact_quality_signals():
    spec_template = read("templates/spec-template.md")

    assert "## Artifact Quality Signals *(mandatory)*" in spec_template
    assert "Must: read like a professional product/requirements artifact." in spec_template
    assert "Strictly: every section must sharpen scope, user-visible behavior, or downstream planning input." in spec_template


def test_checklist_template_declares_artifact_quality_signals():
    checklist_template = read("templates/checklist-template.md")

    assert "## Artifact Quality Signals" in checklist_template
    assert "Must: read like a real review checklist." in checklist_template
    assert "Strictly: every item should expose a concrete requirements-quality risk." in checklist_template

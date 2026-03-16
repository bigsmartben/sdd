from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_command_mapping_documents_authority_model():
    content = read("docs/command-template-mapping.md")

    assert "Authoritative artifacts own semantics" in content
    assert "Repo semantic evidence for `/sdd.plan` comes from source anchors plus engineering assembly facts" in content
    assert "constitution is rule authority and MUST NOT be treated as component-boundary evidence" in content
    assert "Repository-first projections are canonical only under `.specify/memory/repository-first/`" in content
    assert "When a derived view conflicts with or lags behind its source artifact" in content
    assert "## Authority Model" in content
    assert "| `.specify/memory/repository-first/*` | Canonical repository-first dependency/boundary/invocation projections | Authoritative |" in content
    assert "`plan.md` | Planning summary and downstream projection ledger | Derived view |" in content
    assert "`tasks.md` | Execution mapping and DAG scheduling authority | Authoritative for execution order; derived for upstream semantics |" in content
    assert "rule authority, not component-boundary evidence" in content
    assert "generation loop is `Discover -> Generate -> Compress`" in content
    assert "must not absorb comprehensive audit responsibilities" in content
    assert "owns comprehensive non-mainline audit responsibilities" in content


def test_specify_and_plan_define_authority_vs_derived_views():
    specify = read("templates/commands/specify.md")
    plan = read("templates/commands/plan.md")
    plan_template = read("templates/plan-template.md")

    assert "Authority and derivation rules" in specify
    assert "`spec.md` becomes the authoritative feature-semantics artifact" in specify
    assert "discard stale derived notes and re-derive from the current `spec.md` content before handoff" in specify

    assert "`.specify/memory/constitution.md` and `spec.md` are the authoritative upstream semantics for `/sdd.plan`." in plan
    assert "they MUST NOT be promoted into repo semantic anchors" in plan
    assert "`plan.md` downstream projection notes and any temporary extraction tables or summaries are derived views only" in plan
    assert "discard the stale derived view and reread the authoritative slice before continuing downstream generation" in plan

    assert "`plan.md` is a derived planning view and MUST NOT supersede the stage artifacts it summarizes." in plan_template
    assert "Do not record audit metrics, coverage percentages, traceability/accounting tables" in plan_template


def test_tasks_implement_and_analyze_enforce_authority_protocol():
    tasks = read("templates/commands/tasks.md")
    tasks_template = read("templates/tasks-template.md")
    implement = read("templates/commands/implement.md")
    analyze = read("templates/commands/analyze.md")
    constitution = read("templates/commands/constitution.md")

    assert "Treat `plan.md` as a planning summary / structure guide" in tasks
    assert "This runtime scheduling guidance is execution-only. It MUST NOT change artifact authority" in tasks
    assert "Any tuple indexes, execution maps, or working summaries created during `/sdd.tasks` are derived views only" in tasks
    assert "Interface Delivery Units` are IF-scoped execution work packages" in tasks
    assert "hard execution safety gates" in tasks
    assert "does **not** own coverage completeness, ambiguity sweeps, terminology/diagram drift detection, repo-anchor misuse audits, audit hygiene checks, or cross-artifact contradiction analysis" in tasks
    assert "Inline task summaries, local execution notes, and other derived views must yield to the authoritative artifacts above" in tasks_template
    assert "Interface delivery units are IF-scoped execution work packages" in tasks_template

    assert "runtime batching notes, ready-task summaries, and local execution shortcuts as derived views only" in implement
    assert "use the authoritative artifact for semantics" in implement
    assert "Interface Delivery Units` (treated as IF-scoped execution work packages)" in implement
    assert ".specify/memory/repository-first/technical-dependency-matrix.md" in implement

    assert "**Artifact Authority**" in analyze
    assert "owns comprehensive implementation-readiness analysis and audit responsibilities" in analyze
    assert "CRITICAL/HIGH findings MUST cite the authoritative source artifact(s)" in analyze
    assert "Treat task-local summaries or inline mirrors as derived views only" in analyze
    assert "repo-anchor misuse" in analyze
    assert ".specify/memory/repository-first/" in analyze
    assert "Misuse of `README.md`, `docs/**`, `specs/**`, `tests/**`, `plans/**`, `templates/**`, demos, or generated artifacts as repo semantic anchors" in analyze

    assert "Treat `.specify/memory/constitution.md` as the authoritative project-level rule source." in constitution


def test_constitution_declares_repo_anchor_whitelist_and_blacklist():
    constitution = read(".specify/memory/constitution.md")

    assert "### Repo-Anchor Evidence Protocol" in constitution
    assert "**Source anchors**: source-code files/symbols" in constitution
    assert "**Engineering assembly facts**: build/module manifests" in constitution
    assert "Repository-first projections are project-level authoritative artifacts located only at `.specify/memory/repository-first/`." in constitution
    assert "Dependency evidence MUST come from build-manifest auto-detection with deterministic priority" in constitution
    assert "Maven: `pom.xml`" in constitution
    assert "Node: `package.json`" in constitution
    assert "Python: `pyproject.toml`" in constitution
    assert "Go: `go.mod`" in constitution
    assert "`Version Source` values MUST be `direct`, `dependencyManagement`, `module-dependencyManagement`, or `unresolved`." in constitution
    assert "Component/domain capability boundary evidence MUST come from source anchors" in constitution
    assert "planning artifacts, docs, tests, demos, and generated outputs may be read as context only" in constitution
    assert "MUST NOT be promoted into repo semantic evidence" in constitution



def test_tasks_boundary_stays_execution_gates_only_not_comprehensive_audit():
    tasks = read("templates/commands/tasks.md")

    assert "hard execution safety gates" in tasks, (
        "Boundary regression: /sdd.tasks must stay limited to hard execution safety gates."
    )
    assert "does **not** own coverage completeness" in tasks, (
        "Boundary regression: comprehensive audit responsibilities leaked back into /sdd.tasks."
    )
    assert "Handoff all non-mainline comprehensive audit concerns to `/sdd.analyze`" in tasks, (
        "Boundary regression: /sdd.tasks must explicitly hand off comprehensive audit to /sdd.analyze."
    )



def test_analyze_boundary_owns_centralized_cross_artifact_audit():
    analyze = read("templates/commands/analyze.md")

    assert "centralized audit entry and single concentrated audit step before `/sdd.implement`" in analyze, (
        "Boundary regression: /sdd.analyze must remain the centralized audit step before implementation."
    )
    assert "owns comprehensive implementation-readiness analysis and audit responsibilities" in analyze, (
        "Boundary regression: /sdd.analyze must explicitly own comprehensive implementation-readiness audits."
    )
    assert "cross-artifact contradiction detection" in analyze, (
        "Boundary regression: cross-artifact contradiction analysis must stay in /sdd.analyze."
    )



def test_mapping_keeps_tasks_and_analyze_responsibility_split_consistent():
    mapping = read("docs/command-template-mapping.md")

    assert "checks inside `/sdd.tasks` are limited to hard execution safety gates" in mapping, (
        "Boundary regression: mapping must keep /sdd.tasks scoped to hard execution safety gates."
    )
    assert "must not absorb comprehensive implementation-readiness audit responsibilities" in mapping, (
        "Boundary regression: mapping must prohibit comprehensive audit responsibilities in /sdd.tasks."
    )
    assert "owns comprehensive non-mainline implementation-readiness/audit responsibilities" in mapping, (
        "Boundary regression: mapping must assign comprehensive audit ownership to /sdd.analyze."
    )

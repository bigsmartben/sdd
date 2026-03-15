from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_command_mapping_documents_authority_model():
    content = read("docs/command-template-mapping.md")

    assert "Authoritative artifacts own semantics" in content
    assert "When a derived view conflicts with or lags behind its source artifact" in content
    assert "## Authority Model" in content
    assert "`plan.md` | Planning summary and downstream projection ledger | Derived view |" in content
    assert "`tasks.md` | Execution mapping and DAG scheduling authority | Authoritative for execution order; derived for upstream semantics |" in content


def test_specify_and_plan_define_authority_vs_derived_views():
    specify = read("templates/commands/specify.md")
    plan = read("templates/commands/plan.md")
    plan_template = read("templates/plan-template.md")

    assert "Authority and derivation rules" in specify
    assert "`spec.md` becomes the authoritative feature-semantics artifact" in specify
    assert "discard stale derived notes and re-derive from the current `spec.md` content before handoff" in specify

    assert "`/memory/constitution.md` and `spec.md` are the authoritative upstream semantics for `/sdd.plan`." in plan
    assert "`plan.md` downstream projection notes and any temporary extraction tables or summaries are derived views only" in plan
    assert "discard the stale derived view and reread the authoritative slice before continuing downstream generation" in plan

    assert "`plan.md` is a derived planning view and MUST NOT supersede the stage artifacts it summarizes." in plan_template


def test_tasks_implement_and_analyze_enforce_authority_protocol():
    tasks = read("templates/commands/tasks.md")
    tasks_template = read("templates/tasks-template.md")
    implement = read("templates/commands/implement.md")
    analyze = read("templates/commands/analyze.md")
    constitution = read("templates/commands/constitution.md")

    assert "Treat `plan.md` as a planning summary / structure guide" in tasks
    assert "Any tuple indexes, execution maps, or working summaries created during `/sdd.tasks` are derived views only" in tasks
    assert "Inline task summaries, local execution notes, and other derived views must yield to the authoritative artifacts above" in tasks_template

    assert "runtime batching notes, ready-task summaries, and local execution shortcuts as derived views only" in implement
    assert "use the authoritative artifact for semantics" in implement

    assert "**Artifact Authority**" in analyze
    assert "CRITICAL/HIGH findings MUST cite the authoritative source artifact(s)" in analyze
    assert "Treat task-local summaries or inline mirrors as derived views only" in analyze

    assert "Treat `.specify/memory/constitution.md` as the authoritative project-level rule source." in constitution

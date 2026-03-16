from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_constitution_template_defines_owner_boundaries_and_terms():
    content = read("templates/constitution-template.md")

    assert (
        "At least one principle MUST define ownership boundaries for `Generation Rule`, `Validation Rule`, and `Hard Execution Gate`."
        in content
    )
    assert '"Generation Rule" means long-lived constraints enforced during artifact generation.' in content
    assert '"Validation Rule" means centralized audit checks that detect cross-artifact inconsistencies.' in content
    assert '"Hard Execution Gate" means minimum run-blocking checks required for safe execution.' in content

    assert "### Dependency Matrix Baseline" not in content
    assert "## Project-Level Fact Sources" not in content
    assert "### Repository-First Principle" not in content
    assert "### Ownership Boundary Baseline" not in content
    assert "### Repo-Anchor Evidence Protocol" in content
    assert ".specify/memory/repository-first/technical-dependency-matrix.md" in content
    assert ".specify/memory/repository-first/domain-boundary-responsibilities.md" in content
    assert ".specify/memory/repository-first/module-invocation-spec.md" in content
    assert "dependency evidence MUST come from build-manifest auto-detection with deterministic priority" in content
    assert "Maven: `pom.xml`" in content
    assert "Node: `package.json`" in content
    assert "Python: `pyproject.toml`" in content
    assert "Go: `go.mod`" in content
    assert "normalize `Dependency (G:A)` as" in content
    assert "`Version Source` values MUST be `direct`, `dependencyManagement`, `module-dependencyManagement`, or `unresolved`" in content
    assert "/sdd.analyze" in content
    assert "/sdd.tasks" in content
    assert "/sdd.implement" in content
    assert content.index("## Terminology & Boundary Definitions") < content.index("### Repo-Anchor Evidence Protocol")
    assert content.index("### Repo-Anchor Evidence Protocol") < content.index("## State Machine Applicability Gate")


def test_constitution_command_blocks_lint_detail_embedding_and_dual_authority_expansion():
    content = read("templates/commands/constitution.md")

    assert "Adding or materially expanding generation/validation/execution ownership boundaries is always `MINOR`." in content
    assert "do not embed mechanical lint catalog details" in content
    assert "does not include lint-catalog implementation details" in content
    assert "Do not duplicate one normative rule into competing expansions across multiple command templates" in content


def test_constitution_command_groups_alignment_work_and_avoids_redundant_restatements():
    content = read("templates/commands/constitution.md")

    assert "Review and refresh impacted artifact families only; avoid mechanical full-repo rewrites of unchanged downstream files." in content
    assert "Prefer targeted references over restating the same rule text across multiple downstream templates." in content
    assert "Keep this report delta-oriented; do not restate unchanged template inventories or canonical baseline details beyond status." in content
    assert "reference the Sync Impact Report instead of restating it" in content


def test_constitution_command_uses_active_agent_command_directory_guidance():
    content = read("templates/commands/constitution.md")

    assert "Read each command file in the active agent command directory" in content
    assert ".roo/commands/*.md" in content
    assert ".claude/commands/*.md" in content
    assert ".github/agents/*.agent.md" in content
    assert ".gemini/commands/*.toml" in content
    assert "if `templates/commands/*.md` exists in this repository, review it as well" in content
    assert "Runtime template authority path is `.specify/templates/`" in content
    assert "use the `templates/` mirror for the same files" in content


def test_constitution_command_uses_current_constitution_state_not_placeholder_premise():
    content = read("templates/commands/constitution.md")

    assert "Treat the current file as the authoritative working constitution" in content
    assert ".specify/templates/constitution-template.md" in content
    assert "stop and report the blocker" in content
    assert "Do not substitute `templates/constitution-template.md` or any other template location." in content
    assert "do not force a template-token rewrite pass" in content
    assert "This file is a TEMPLATE containing placeholder tokens" not in content


def test_constitution_command_owns_repository_first_baseline_pipeline():
    content = read("templates/commands/constitution.md")

    assert "Repository-first global baseline pipeline (mandatory)" in content
    assert ".specify/memory/repository-first/" in content
    assert "technical-dependency-matrix.md" in content
    assert "domain-boundary-responsibilities.md" in content
    assert "module-invocation-spec.md" in content
    assert "Detect build manifests from repo root using deterministic priority" in content
    assert "Maven: `pom.xml`" in content
    assert "Node: `package.json`" in content
    assert "Python: `pyproject.toml`" in content
    assert "Go: `go.mod`" in content
    assert "never read or stat bare projection filenames from repo root" in content
    assert "`created`" in content
    assert "`updated`" in content
    assert "`unchanged`" in content


def test_constitution_command_defines_runtime_fast_path_and_bounded_reads():
    content = read("templates/commands/constitution.md")

    assert "Build one run-local **change impact map** before broad reads" in content
    assert "`governance-only`" in content
    assert "`template-affecting`" in content
    assert "`repo-first-affecting`" in content
    assert "Resolve impacted families from the change impact map first, then read/update only those families." in content
    assert "Do not run directory-wide or repository-wide exploratory scans" in content
    assert "Repository-first fast path gate (evaluate before regeneration)" in content
    assert "If no trigger is true, keep canonical baseline files as-is and mark each artifact `unchanged` without template re-render." in content
    assert "Apply a **bounded evidence budget** for this run" in content
    assert "Runtime guidance docs (`README.md`, `docs/quickstart.md`, agent docs) are **opt-in by trigger** only" in content
    assert "Keep runtime output concise: no unchanged-file inventories" in content

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
    assert "### Ownership Boundary Baseline" in content
    assert "/sdd.analyze" in content
    assert "/sdd.tasks" in content
    assert "/sdd.implement" in content


def test_constitution_command_blocks_lint_detail_embedding_and_dual_authority_expansion():
    content = read("templates/commands/constitution.md")

    assert "Adding or materially expanding generation/validation/execution ownership boundaries is always `MINOR`." in content
    assert "do not embed mechanical lint catalog details" in content
    assert "does not include lint-catalog implementation details" in content
    assert "Do not duplicate one normative rule into competing expansions across multiple command templates" in content


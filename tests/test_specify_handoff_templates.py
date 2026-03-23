from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_specify_command_keeps_current_flow_and_treats_ui_html_as_optional_sidecar():
    specify = read("templates/commands/specify.md")
    ui_html = read("templates/commands/specify.ui-html.md")

    assert "Clarify Spec Requirements" in specify
    assert "Build Technical Plan" in specify
    assert "Create or update the feature specification from a natural language feature description." in specify
    assert "`ui.html` generated later by `/sdd.specify.ui-html` is a derived prototype artifact" in specify
    assert "`/sdd.specify` writes `spec.md` only and MUST NOT directly generate `ui.html`." in specify
    assert "`/sdd.specify.ui-html` is an optional sidecar command; users decide if/when to invoke it." in specify
    assert "run `/sdd.specify.ui-html` for an interactive prototype if needed" not in specify

    assert "Treat all `$ARGUMENTS` as optional direction." in ui_html
    assert ".specify/templates/ui-html-template.html" in ui_html
    assert "Generate one review-ready `ui.html` prototype for walkthroughs, UX review, and interaction validation." in ui_html
    assert "## Interaction & Coverage Rules (MUST)" in ui_html
    assert "**UIF Coverage**: Prototype MUST trace to explicit `UIF` nodes." in ui_html
    assert "**UDD Binding**: Visible data MUST trace to completed `Entity.field` rows." in ui_html
    assert "**Review Surfaces**: Dedicate areas to `UIF Interaction View` and `UDD-backed View State` for audit." in ui_html
    assert "`ui.html` is a derived artifact." in ui_html
    assert "No planning governance semantics (tuples/anchors/contracts) in the prototype." in ui_html
    assert "`Next Command`: `/sdd.clarify`" in ui_html
    assert "`/sdd.plan`" in ui_html


def test_spec_template_stays_unsplit_and_ui_html_template_exists():
    spec_template = read("templates/spec-template.md")
    ui_html_template = read("templates/ui-html-template.html")

    assert "# Feature Specification: [FEATURE NAME]" in spec_template
    assert "**Input**: \"$ARGUMENTS\"" in spec_template
    assert "## § 1 Global Context *(mandatory)*" in spec_template
    assert "## § 2 UC Overview *(mandatory)*" in spec_template
    assert "## § N Global Acceptance Criteria *(mandatory)*" in spec_template
    assert "`research.md` via `/sdd.plan.research`" in spec_template
    assert "`test-matrix.md` via `/sdd.plan.test-matrix`" in spec_template
    assert "`data-model.md` via `/sdd.plan.data-model`" in spec_template
    assert "UI Preview" in ui_html_template
    assert "spec.md" in ui_html_template
    assert "Primary Tool Loop" in ui_html_template
    assert "Tool Intent" in ui_html_template
    assert "Loop Steps" in ui_html_template
    assert "Next Action" in ui_html_template
    assert "UIF + UDD Focus" in ui_html_template
    assert "UIF Interaction View" in ui_html_template
    assert "UDD-backed View State" in ui_html_template
    assert "Render one ordered item per selected `UIF` node." in ui_html_template
    assert "map each selected `UIF` node to its step-level feedback and rule-driven state" in ui_html_template
    assert "who is trying to complete what" in ui_html_template
    assert "proves spec.md's intended outcome" in ui_html_template
    assert "grid-template-areas:" in ui_html_template
    assert '"context action"' in ui_html_template
    assert ".tool-stage::before" in ui_html_template
    assert "@media (max-width: 640px)" in ui_html_template
    assert "position: static;" in ui_html_template
    assert 'grid-template-areas:' in ui_html_template


def test_spec_and_commands_require_semantically_aligned_edge_case_refs():
    spec_template = read("templates/spec-template.md")
    specify = read("templates/commands/specify.md")
    clarify = read("templates/commands/clarify.md")

    assert "Treat `EC-*` as semantic anchors, not a fixed four-item bucket list." in specify
    assert "Use `validation` as a first-class `Path Inventory` scenario type" in specify
    assert "`Path Inventory` scenario types stay within the allowed enum (`happy/alternate/validation/exception/retry/recovery/cancel/timeout/permission/duplicate`)" in specify
    assert "EC-*` references remain semantically aligned across `Path Inventory`, `Exception Paths`, FR blocks, and `N.2 Environment Edge Cases`" in specify
    assert "every FR block includes `Capability`, `Given/When/Then`, `UDD (user-visible data) refs`, and `Success criteria`" in specify
    assert "add `EC-005+` instead of overloading an unrelated edge-case id" in clarify
    assert "`EC-*` IDs are semantic anchors" in spec_template
    assert "Overloading IDs for unrelated behaviors" in spec_template
    assert "### N.2 Environment Edge Cases" in spec_template
    assert "EC-001" in spec_template and "EC-005" in spec_template


def test_docs_and_cli_describe_optional_ui_html_command():
    readme = read("README.md")
    spec_driven = read("spec-driven.md")
    cli_init = read("src/specify_cli/__init__.py")

    assert "Use **`/sdd.specify.ui-html`**" in readme
    assert "/sdd.specify.srs" not in readme
    assert "/sdd.specify.ui <spec.md>" not in readme

    assert "/sdd.specify.ui-html" in spec_driven
    assert "focused interaction tool" in spec_driven
    assert "/sdd.specify.srs" not in spec_driven
    assert "/sdd.specify.ui specs/003-chat-system/spec.md" not in spec_driven

    assert "focused interaction tool" in readme
    assert '"specify.ui-html": "Generate the derived ui.html focused interaction tool artifact from the current feature branch spec.md. This is an optional sidecar command' in cli_init
    assert '"specify.srs"' not in cli_init
    assert '"specify.ui": "Generate the derived ui.md artifact' not in cli_init
    assert "generate a focused interaction tool when needed" in cli_init
    assert '/{COMMAND_NAMESPACE}.specify.ui-html[/]' in cli_init

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

    assert "Treat all `$ARGUMENTS` as optional prototype direction." in ui_html
    assert ".specify/templates/ui-html-template.html" in ui_html
    assert "Generate exactly one review-ready `ui.html` interactive prototype" in ui_html
    assert "## UIF + UDD Coverage Protocol (MUST)" in ui_html
    assert "Every demonstrated user interaction MUST trace back to an explicit `UIF` node." in ui_html
    assert "Only surface the subset of completed `Entity.field` rows needed to make the selected interaction understandable from the user's point of view." in ui_html
    assert "Every business-significant datum that appears inside the demonstrated interaction MUST trace back to explicit completed `Entity.field` rows." in ui_html
    assert "Do not make IDs, coverage ledgers, or audit-style badges the dominant visible content of the prototype." in ui_html
    assert "`UIF Coverage Summary`" in ui_html
    assert "`UDD Coverage Summary`" in ui_html
    assert "`Next Command`: `/sdd.clarify`" in ui_html
    assert "`/sdd.plan`" in ui_html


def test_spec_template_stays_unsplit_and_ui_html_template_exists():
    spec_template = read("templates/spec-template.md")
    ui_html_template = read("templates/ui-html-template.html")

    assert "### This Stage Outputs" in spec_template
    assert "[spec.md](spec.md) (this document)" in spec_template
    assert "[ui.html](ui.html)" not in spec_template
    assert "UI Preview" in ui_html_template
    assert "spec.md" in ui_html_template
    assert "User-Visible Completion" in ui_html_template
    assert "Completed State" in ui_html_template
    assert "Entry Context" in ui_html_template
    assert "Visible Outcome" in ui_html_template


def test_spec_and_commands_require_semantically_aligned_edge_case_refs():
    spec_template = read("templates/spec-template.md")
    specify = read("templates/commands/specify.md")
    clarify = read("templates/commands/clarify.md")

    assert "Treat `EC-*` as semantic anchors, not a fixed four-item bucket list." in specify
    assert "EC-*` references remain semantically aligned across `Path Inventory`, `Exception Paths`, FR blocks, and `N.2 Environment Edge Cases`" in specify
    assert "add `EC-005+` instead of overloading an unrelated edge-case id" in clarify
    assert "`EC-*` identifiers are semantic anchors, not a fixed four-slot checklist." in spec_template
    assert "Do not point a retry path at a re-entry EC, or a permission path at a duplicate-click EC." in spec_template
    assert "Every `EC-*` cited from `Path Inventory`, `Exception Paths`, FR blocks, `test-matrix.md`, or `contracts/` MUST describe the same edge semantics textually." in spec_template


def test_docs_and_cli_describe_optional_ui_html_command():
    readme = read("README.md")
    spec_driven = read("spec-driven.md")
    cli_init = read("src/specify_cli/__init__.py")

    assert "Use **`/sdd.specify.ui-html`**" in readme
    assert "/sdd.specify.srs" not in readme
    assert "/sdd.specify.ui <spec.md>" not in readme

    assert "/sdd.specify.ui-html" in spec_driven
    assert "/sdd.specify.srs" not in spec_driven
    assert "/sdd.specify.ui specs/003-chat-system/spec.md" not in spec_driven

    assert '"specify.ui-html": "Generate the derived ui.html interactive prototype artifact from the current feature branch spec.md. This is an optional sidecar command' in cli_init
    assert '"specify.srs"' not in cli_init
    assert '"specify.ui": "Generate the derived ui.md artifact' not in cli_init
    assert '/{COMMAND_NAMESPACE}.specify.ui-html[/]' in cli_init

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_specify_command_keeps_current_flow_and_adds_ui_html_handoff():
    specify = read("templates/commands/specify.md")
    ui_html = read("templates/commands/specify.ui-html.md")

    assert "Clarify Spec Requirements" in specify
    assert "Generate Interactive Prototype" in specify
    assert "Build Technical Plan" in specify
    assert "Create or update the feature specification from a natural language feature description." in specify
    assert "`ui.html` generated later by `/sdd.specify.ui-html` is a derived prototype artifact" in specify
    assert "run `/sdd.specify.ui-html` for an interactive prototype if needed" in specify

    assert "Treat all `$ARGUMENTS` as optional prototype direction." in ui_html
    assert ".specify/templates/ui-html-template.html" in ui_html
    assert "Generate exactly one review-ready `ui.html` interactive prototype" in ui_html
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

    assert '"specify.ui-html": "Generate the derived ui.html interactive prototype artifact' in cli_init
    assert '"specify.srs"' not in cli_init
    assert '"specify.ui": "Generate the derived ui.md artifact' not in cli_init
    assert '/{COMMAND_NAMESPACE}.specify.ui-html[/]' in cli_init

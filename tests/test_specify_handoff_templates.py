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
    assert "Generate one self-contained interactive ui.html prototype from the resolved spec.md." in ui_html
    assert "This command generates presentation and interaction only. It does **not** run gates, audits, or downstream checks." in ui_html
    assert "Must: read like a polished product prototype, not a requirements document." in ui_html
    assert "Strictly: default to one primary path plus zero or one branch." in ui_html
    assert "do not make audit language the primary reading experience." in ui_html
    assert "`ui.html` is a derived artifact." in ui_html
    assert "`Next Command`: `None`" in ui_html
    assert "`Selected Artifact`: `ui.html`" in ui_html


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
    assert "Interactive Prototype" in ui_html_template
    assert "spec.md" in ui_html_template
    assert "Prototype Surface" in ui_html_template
    assert "Visible Completion" in ui_html_template
    assert "Review Notes" in ui_html_template
    assert "Visible States" in ui_html_template
    assert "prototypeModel" in ui_html_template
    assert "branch: null" in ui_html_template
    assert "renderScenario" in ui_html_template
    assert "self-contained, high-fidelity prototype" in ui_html_template
    assert "must stay grounded in spec.md" in ui_html_template
    assert ".prototype-grid" in ui_html_template
    assert "textarea" in ui_html_template
    assert "@media (max-width: 720px)" in ui_html_template


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
    assert "interactive prototype" in spec_driven
    assert "/sdd.specify.srs" not in spec_driven
    assert "/sdd.specify.ui specs/003-chat-system/spec.md" not in spec_driven

    assert "interactive prototype" in readme
    assert "does not run gates or downstream checks" in readme
    assert '"specify.ui-html": "Generate a self-contained interactive ui.html prototype from the current feature branch spec.md. This is an optional sidecar command for reviewable product flows only; it does not run gates or downstream checks."' in cli_init
    assert '"specify.srs"' not in cli_init
    assert '"specify.ui": "Generate the derived ui.md artifact' not in cli_init
    assert "generate an interactive prototype when needed" in cli_init
    assert '/{COMMAND_NAMESPACE}.specify.ui-html[/]' in cli_init

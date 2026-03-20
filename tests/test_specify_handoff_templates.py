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
    assert "Generate exactly one review-ready `ui.html` focused interactive tool" in ui_html
    assert "## UIF + UDD Coverage Protocol (MUST)" in ui_html
    assert "## Deterministic Prototype Selection Protocol (MUST)" in ui_html
    assert "Every demonstrated user interaction MUST trace back to an explicit `UIF` node." in ui_html
    assert "The prototype should visibly dedicate a primary review surface to the selected `UIF` path/node progression" in ui_html
    assert "Only surface the subset of completed `Entity.field` rows needed to make the selected interaction understandable from the user's point of view." in ui_html
    assert "Every business-significant datum that appears inside the demonstrated interaction MUST trace back to explicit completed `Entity.field` rows." in ui_html
    assert "The prototype should visibly dedicate a peer review surface to step-level `UDD` feedback" in ui_html
    assert "Otherwise, choose exactly one primary walkthrough by this priority order:" in ui_html
    assert "`UIF Interaction View` MUST enumerate the selected `UIF` nodes in execution order" in ui_html
    assert "`UDD-backed View State` MUST map each selected `UIF` node to the user-visible feedback or state change" in ui_html
    assert "If any required tie cannot be broken using explicit refs, spec order, or completed UDD evidence, stop and report the blocker instead of choosing heuristically." in ui_html
    assert "Do not make IDs, coverage ledgers, or audit-style badges the dominant visible content of the prototype." in ui_html
    assert "`ui.html` should deliver a tool, not a document page." in ui_html
    assert "Organize the experience around a closed interaction loop: context -> action -> system feedback -> completion/result -> next action" in ui_html
    assert "`ui.html` MUST make the core expression of `spec.md` easier to perceive through interaction" in ui_html
    assert "Start by extracting one plain-language expression sentence from `spec.md`" in ui_html
    assert "the one dominant semantic through-line the user should understand after one pass" in ui_html
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
    assert "Scenario Type (happy/alternate/validation/exception/retry/recovery/cancel/timeout/permission/duplicate)" in spec_template
    assert "Do not collapse later FRs to capability-only shorthand." in spec_template
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
    assert "`EC-*` identifiers are semantic anchors, not a fixed four-slot checklist." in spec_template
    assert "Do not point a retry path at a re-entry EC, or a permission path at a duplicate-click EC." in spec_template
    assert "Use `validation` for user-visible guardrails that block progression on empty, invalid, or incomplete input while the user remains on the current step." in spec_template
    assert "Every `EC-*` cited from `Path Inventory`, `Exception Paths`, FR blocks, `test-matrix.md`, or `contracts/` MUST describe the same edge semantics textually." in spec_template


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

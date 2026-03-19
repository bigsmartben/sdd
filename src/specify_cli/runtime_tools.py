"""SDD core runtime tool inventory."""

from __future__ import annotations

from typing import Any


CORE_RUNTIME_TOOLS: dict[str, Any] = {
    "schema_version": "1.0",
    "core_runtime_tools": [
        {
            "tool": "specify-cli",
            "role": "sdd_runtime",
            "required": True,
            "capabilities": [
                "content_extraction",
                "preflight_bootstrap",
                "lint_entrypoints",
                "validation_entrypoints",
            ],
            "notes": "Runs inside the UV-managed specify-cli Python runtime.",
        },
        {
            "tool": "git",
            "role": "repo_inspection",
            "required": False,
            "capabilities": [
                "branch_resolution",
                "status",
                "diff",
                "history",
            ],
            "notes": "Used only for repository inspection and branch-derived feature resolution.",
        },
        {
            "tool": "rg",
            "role": "repo_search",
            "required": False,
            "capabilities": [
                "list_files",
                "search_text",
            ],
            "notes": "Preferred repository search tool; git search remains the bounded fallback.",
        },
    ],
    "excluded_runtime_families": [
        "node",
        "npm",
        "pnpm",
        "yarn",
        "user_python",
        "inline_runtime_scripts",
    ],
    "project_specific_commands_policy": "Project-specific build/test/lint commands remain repo-anchored task commands, not SDD core runtime tools.",
}


def runtime_tools_manifest() -> dict[str, Any]:
    return CORE_RUNTIME_TOOLS

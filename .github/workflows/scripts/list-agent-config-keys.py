#!/usr/bin/env python3
"""Print AGENT_CONFIG keys from src/specify_cli/__init__.py, one per line.

This script intentionally parses source via AST instead of importing runtime modules,
so release scripts can use it in minimal environments without third-party deps.
"""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
INIT_FILE = REPO_ROOT / "src" / "specify_cli" / "__init__.py"


def _extract_agent_keys(init_file: Path) -> list[str]:
    tree = ast.parse(init_file.read_text(encoding="utf-8"), filename=str(init_file))

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1:
            continue

        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id != "AGENT_CONFIG":
            continue

        if not isinstance(node.value, ast.Dict):
            raise RuntimeError("AGENT_CONFIG must be a dict literal")

        keys: list[str] = []
        for key_node in node.value.keys:
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                raise RuntimeError("AGENT_CONFIG keys must be string literals")
            keys.append(key_node.value)
        return keys

    raise RuntimeError("AGENT_CONFIG assignment not found")


def main() -> None:
    for key in _extract_agent_keys(INIT_FILE):
        print(key)


if __name__ == "__main__":
    main()

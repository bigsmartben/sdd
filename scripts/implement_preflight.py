#!/usr/bin/env python3
"""Delegate implement bootstrap extraction to the runtime authority."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_runtime_builder():
    try:
        from specify_cli.runtime_implement_bootstrap import build_implement_bootstrap_payload
    except ModuleNotFoundError:
        repo_src = Path(__file__).resolve().parents[1] / "src"
        if str(repo_src) not in sys.path:
            sys.path.insert(0, str(repo_src))
        sys.modules.pop("specify_cli", None)
        from specify_cli.runtime_implement_bootstrap import build_implement_bootstrap_payload
    return build_implement_bootstrap_payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract compact implement bootstrap packet")
    parser.add_argument("--feature-dir", required=True, help="Absolute or repo-relative feature directory")
    parser.add_argument("--spec", required=True, help="Path to spec.md")
    parser.add_argument("--plan", required=True, help="Path to plan.md")
    parser.add_argument("--tasks", required=True, help="Path to tasks.md")
    parser.add_argument("--analyze-history", required=True, help="Path to audits/analyze-history.md")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    build_implement_bootstrap_payload = _load_runtime_builder()
    payload = build_implement_bootstrap_payload(
        feature_dir=Path(args.feature_dir).resolve(),
        spec_path=Path(args.spec).resolve(),
        plan_path=Path(args.plan).resolve(),
        tasks_path=Path(args.tasks).resolve(),
        analyze_history_path=Path(args.analyze_history).resolve(),
    )
    json.dump(payload, sys.stdout, ensure_ascii=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Shared repository-first gate protocol helpers for runtime bootstrap payloads."""

from __future__ import annotations

from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from typing import Any


REPOSITORY_FIRST_GATE_PROTOCOL_SCHEMA_VERSION = "1.0"
BASELINE_CHECK_CATEGORIES = ("missing", "stale", "non_traceable")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def resolve_generator_version() -> tuple[str | None, str]:
    try:
        return importlib_metadata.version("specify-cli"), "available"
    except importlib_metadata.PackageNotFoundError:
        return None, "unknown"
    except Exception:
        return None, "unknown"


def _normalize_check_entry(*, severity: str, finding: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": finding.get("code", ""),
        "severity": severity,
        "message": finding.get("message", ""),
        "details": finding.get("details", {}),
    }


def normalize_baseline_checks(
    *,
    readiness: dict[str, Any],
    code_to_category: dict[str, str],
) -> dict[str, list[dict[str, Any]]]:
    normalized: dict[str, list[dict[str, Any]]] = {category: [] for category in BASELINE_CHECK_CATEGORIES}
    for severity_key, severity in (("errors", "error"), ("warnings", "warning")):
        for finding in readiness.get(severity_key, []):
            code = str(finding.get("code", ""))
            category = code_to_category.get(code, "non_traceable")
            if category not in normalized:
                category = "non_traceable"
            normalized[category].append(_normalize_check_entry(severity=severity, finding=finding))
    return normalized


def build_repository_first_gate_protocol(
    *,
    gate_name: str,
    readiness: dict[str, Any],
    ready_field: str,
    code_to_category: dict[str, str],
) -> dict[str, Any]:
    generator_version, generator_status = resolve_generator_version()
    checks = normalize_baseline_checks(readiness=readiness, code_to_category=code_to_category)

    return {
        "schema_version": REPOSITORY_FIRST_GATE_PROTOCOL_SCHEMA_VERSION,
        "gate_name": gate_name,
        "ready": bool(readiness.get(ready_field, False)),
        "baseline_checks": checks,
        "baseline_check_summary": {category: len(entries) for category, entries in checks.items()},
        "baseline_freshness": {
            "generated_at_utc": {
                "status": "available",
                "value": _utc_now_iso(),
                "reason": "",
            },
            "generator_version": {
                "status": generator_status,
                "value": generator_version,
                "reason": "" if generator_status == "available" else "generator_version_unavailable",
            },
        },
    }

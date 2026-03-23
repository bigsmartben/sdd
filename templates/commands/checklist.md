---
description: Generate a custom requirements-quality checklist from the current feature branch plan.md.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Treat all `$ARGUMENTS` as checklist context input.
Resolve `PLAN_FILE` from the current feature branch using `{SCRIPT}` defaults.

## Goal

Generate a requirements-quality checklist — "unit tests for English" — from the current feature branch artifacts.

- **Target**: completeness, clarity, consistency, measurability, and scenario/edge coverage.
- **Non-target**: execution behavior such as click/navigation/render/API-pass assertions.

## Governance / Authority

- **Authority rule**: `plan.md` is the hard gate; `spec.md` is the requirements authority.
- **Stage boundary rule**: Checklist validates requirements quality only. MUST NOT backfill, repair, or redefine main-flow artifacts.
- **Protocol rule**: Final audit/PASS/FAIL is owned by `/sdd.analyze`.

## Allowed Inputs

Read only from `FEATURE_DIR`:
- `spec.md` (required)
- `plan.md` (required; must match resolved `PLAN_FILE`)
- `tasks.md` (optional)
- `.specify/templates/checklist-template.md` (structure; required)

Read only sections needed for selected focus areas. **Prohibited**: broad symbol scans, unrelated feature folders.

## Reasoning Order

1. Run `{SCRIPT}` from repo root; parse `FEATURE_DIR` and `AVAILABLE_DOCS`. Treat resolved `PLAN_FILE` as canonical; all paths must be absolute.
2. Build a compact `Checklist Intent Packet` from `$ARGUMENTS` and feature context: focus areas, risk signals, actor/timing (`author`/`reviewer`/`release gate`), depth (`lightweight|standard|formal`), inclusions/exclusions, unresolved scenario classes.
3. Clarify if needed: ask at most 2 initial questions; up to 5 total only for remaining high-impact gaps; skip questions already answered by `$ARGUMENTS`.
4. Load feature context; read only sections relevant to selected focus areas.
5. Generate or append checklist under `FEATURE_DIR/checklists/[domain].md`:
   - Create with `CHK001` if absent; append and continue numbering if present.
   - Use `.specify/templates/checklist-template.md` as mandatory structure source.
   - Never delete or overwrite existing checklist content.

## Artifact Quality Contract

- Must: generate a checklist a strong reviewer would actually use.
- Must not: devolve into implementation tests, lint slogans, or audit theater.
- Strictly: every item must protect a real requirements-quality failure mode.
- Output only: concise, high-signal requirement-quality questions; group by risk; consolidate near-duplicates.

**Item rules**:
- Each item checks at least one quality dimension: completeness, clarity, consistency, measurability, scenario/edge coverage, dependencies/assumptions, or ambiguity/conflict.
- Write items as requirement-quality questions (example: "Are timeout requirements defined for all user-visible async actions?"). Do not write runtime assertions.
- At least 80% of items MUST include traceability markers (`[Spec §X.Y]`, `[Gap]`, `[Ambiguity]`, `[Conflict]`, `[Assumption]`).
- Merge near-duplicate items; prioritize high-risk gaps first.

## Writeback Contract

- Create or append to `FEATURE_DIR/checklists/[domain].md` only.
- **MUST NOT** modify `spec.md`, `plan.md`, `tasks.md`, or other artifacts.

## Stop Conditions

Stop immediately if:
1. `{SCRIPT}` fails to resolve `FEATURE_DIR` or `PLAN_FILE`.
2. `spec.md` or `plan.md` is missing or unreadable.
3. `.specify/templates/checklist-template.md` is missing or unreadable.

## Handoff Decision

Emit exactly these fields:
- `Next Command`: `/sdd.plan` (if run before planning) or context-derived next step.
- `Decision Basis`: Checklist path, item count, create-vs-append status, resolved `PLAN_FILE`, selected focus contract.
- `Ready/Blocked`: Local readiness only.

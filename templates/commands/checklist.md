---
description: Generate a custom requirements-quality checklist from the current feature branch plan.md.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## Checklist Purpose: "Unit Tests for English"

Checklists here validate **requirements quality**, not implementation behavior.

- Target: completeness, clarity, consistency, measurability, and scenario/edge coverage.
- Non-target: execution correctness checks such as click/navigation/render/API-pass assertions.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Argument Parsing

Treat all `$ARGUMENTS` as checklist context input.
Resolve `PLAN_FILE` from current feature branch using `{SCRIPT}` defaults.
If branch-derived `PLAN_FILE` is missing or invalid, stop immediately and report the blocker.

## Execution Steps

1. Setup (hard gate): Run `{SCRIPT}` from repo root. Parse JSON for FEATURE_DIR and AVAILABLE_DOCS list.
   - Treat resolved `PLAN_FILE` as canonical for this run.
   - All file paths must be absolute.
2. Build a compact `Checklist Intent Packet` from `$ARGUMENTS` and authoritative artifacts:
   - focus areas and risk signals
   - actor/timing (author, reviewer, release gate)
   - depth (`lightweight` | `standard` | `formal`)
   - must-have inclusions and exclusions
   - unresolved scenario classes
3. Clarify only when needed:
   - ask at most 2 initial questions by default; use up to 5 total only when ambiguity is still high-impact
   - skip questions already answered by `$ARGUMENTS`
   - avoid speculative categories and repeated questions
4. Load feature context from `FEATURE_DIR`:
   - `spec.md` (required)
   - `plan.md (required; must match resolved PLAN_FILE)`
   - `tasks.md` (optional)
   - read only sections needed for selected focus areas
5. Generate/append checklist under `FEATURE_DIR/checklists/[domain].md`:
   - create file with `CHK001` if absent; otherwise append and continue numbering
   - never delete or overwrite existing checklist content
6. Use `.specify/templates/checklist-template.md` as mandatory structure source. If missing/unreadable, stop and report blocker.
7. Report checklist path, item count, create-vs-append status, resolved `PLAN_FILE`, and selected focus contract.

## Item Quality Rules

Core principle: test requirements quality, not implementation behavior.

- Each item checks at least one quality dimension: completeness, clarity, consistency, measurability, scenario/edge coverage, dependencies/assumptions, or ambiguity/conflict.
- Write checklist items as requirement-quality questions (for example: "Are timeout requirements defined for all user-visible async actions?").
- Do not write implementation-behavior assertions (click/render/navigation/API runtime checks).
- At least 80% of items must include traceability markers (`[Spec §X.Y]`, `[Gap]`, `[Ambiguity]`, `[Conflict]`, `[Assumption]`).
- Merge near-duplicate items; prioritize high-risk gaps first.

## Output Contract

- Keep checklist concise and non-redundant.
- Prefer grouped high-impact gaps over long low-signal tails.
- If candidate items are excessive, consolidate by risk and scenario class.

## Output Style Notes

- Keep checklist items concise and non-redundant.
- Prefer high-risk/high-impact requirement gaps first when item count is large.
- Merge near-duplicate checks that validate the same requirement quality property.

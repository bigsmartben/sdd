---
description: Create or update the feature specification from a natural language feature description.
handoffs:
  - label: Clarify Spec Requirements
    agent: sdd.clarify
    prompt: Clarify specification requirements
    send: true
  - label: Build Technical Plan
    agent: sdd.plan
    prompt: Create a plan by running /sdd.plan in the same active feature branch context. I am building with...
scripts:
  sh: scripts/bash/create-new-feature.sh "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 "{ARGS}"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/sdd.specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `{ARGS}` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

## Backbone-First Guardrails (mandatory)

When generating or updating `spec.md`, keep output backbone-first and scoped to feature semantics.

- Keep backbone order stable: global context -> boundaries -> UC/FR -> UDD -> UX/UI -> acceptance/edge cases -> assumptions.
- Focus on WHAT/WHY, not HOW (no tech stack, API contracts, or implementation choreography).
- Do **not** hardcode sample domains, entities, UC names, or project identifiers not grounded in current user input.
- Keep template outputs reusable and domain-neutral unless the user gives explicit domain details.

## Stage Boundary Rules (mandatory)

- `/sdd.specify` owns feature semantics (`WHAT/WHY`) only.
- Do **not** emit planning-stage governance payloads in `spec.md` (for example: repo-anchor strategy states, boundary tuple keys, `Repo Anchor Role`, contract packet schemas, or realization choreography).
- Local quality checks are required for this artifact, but `/sdd.specify` MUST NOT produce cross-artifact final PASS/FAIL decisions.
- Cross-artifact final PASS/FAIL ownership remains centralized in `/sdd.analyze`.

## Runtime Setup

1. Generate a concise short name (2-4 words, action-noun style when possible).
2. Run `{SCRIPT}` exactly once with `--short-name` and JSON mode; do not pass `--number`.
3. Parse script output and capture `BRANCH_NAME` and `SPEC_FILE`.
4. Load `.specify/templates/spec-template.md` as the mandatory output structure. If missing/unreadable, stop and report blocker.

Script rules:

- Bash example: `{SCRIPT} --json --short-name "user-auth" "Add user authentication"`
- PowerShell example: `{SCRIPT} -Json -ShortName "user-auth" "Add user authentication"`
- `/sdd.specify` is the only command allowed to create/switch feature branches.
- Downstream `/sdd.*` commands must use the already-active branch and branch inference only.

## Authority and Derivation Rules

- Any extracted actor lists, term sets, requirement drafts, or working summaries used during `/sdd.specify` are derived working views only.
- `spec.md` becomes the authoritative feature-semantics artifact only after the current refinement/validation cycle is written successfully.
- `ui.html` generated later by `/sdd.specify.ui-html` is a derived prototype artifact and MUST NOT override `spec.md`.
- `/sdd.specify` writes `spec.md` only and MUST NOT directly generate `ui.html`.
- `/sdd.specify.ui-html` is an optional sidecar command; users decide if/when to invoke it.
- If clarification answers, validation rewrites, or scope edits change feature meaning, discard stale derived notes and re-derive from current `spec.md`.

## Generation Flow

1. Parse feature description from `$ARGUMENTS`; if empty, stop with `No feature description provided`.
2. Extract actors, actions, data, constraints, and business outcomes.
3. Apply informed defaults first. Add `[NEEDS CLARIFICATION: ...]` only for high-impact ambiguities with no safe default. Max 5 markers.
4. Build required template sections in order:
   - `§ 1 Global Context` (`1.1 Actors`, `1.2 System Boundary`, `1.3 UI Data Dictionary`)
   - `§ 2 UC Overview` and FR index
   - per-UC UX/UI blocks (`3.1`~`3.5`) for interactive and user-facing flows
   - `N.1 Success Criteria`, `N.2 Environment Edge Cases`, `Assumptions / Open Questions`
5. Enforce edge-case anchor semantics:
   - Treat `EC-*` as semantic anchors, not a fixed four-item bucket list.
   - Add `EC-005+` whenever retry, re-entry, permission/access, duplicate/dedup, timeout/transport, validation, or recovery behavior is semantically distinct.
   - Use `validation` as a first-class `Path Inventory` scenario type when the user-visible behavior is a guardrail that blocks progression on empty, invalid, or incomplete input while preserving the current step.
   - Keep `Path Inventory`, `Exception Paths`, FR blocks, and `N.2 Environment Edge Cases` textually aligned on the same `EC-*` meaning.
6. Write `SPEC_FILE` using template heading order; do not add governance/process-control payload sections.

## Self-Validation

Run an anti-solidification pass before finalizing:

- Build allowed terminology from user input + neutral template vocabulary + explicit assumptions.
- Replace unsupported carry-over domain/project/entity terms from prior context.

Validate the generated `spec.md`:

- all mandatory template sections complete
- no implementation detail leakage
- UDD is field-level (`Entity.field`) for user-visible data
- `Path Inventory` scenario types stay within the allowed enum (`happy/alternate/validation/exception/retry/recovery/cancel/timeout/permission/duplicate`)
- interactive UCs include required UX flow tables; user-facing UCs include UI definitions and component-data dependency mappings
- every FR block includes `Capability`, `Given/When/Then`, `UDD (user-visible data) refs`, and `Success criteria`; FRs that cite exception or `EC-*` behavior also include `Failure / edge behavior`
- requirements are testable and unambiguous
- success criteria are measurable and technology-agnostic
- no unresolved `[NEEDS CLARIFICATION]` markers remain
- `EC-*` references remain semantically aligned across `Path Inventory`, `Exception Paths`, FR blocks, and `N.2 Environment Edge Cases`
- no planning-stage governance payload sections are introduced
- no cross-artifact final PASS/FAIL conclusion is emitted

Handling failures:

- Non-clarification issues: fix and re-validate, up to 3 iterations.
- Clarification markers remain: ask focused clarification questions (max 5 total), update spec, then re-validate.

## Completion Report

Report:

- `BRANCH_NAME`
- `SPEC_FILE` absolute path
- readiness recommendation (`/sdd.clarify` first, then `/sdd.plan`)
- if user explicitly skips clarification, warn about increased downstream rework risk
- if checklist-style requirements quality validation is requested, route to `/sdd.checklist` after `/sdd.plan`

Note: the script initializes `specs/<feature-key>/spec.md` and, in Git repos, switches to the resolved feature branch.

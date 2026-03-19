---
description: Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.
handoffs: 
  - label: Build Technical Plan
    agent: sdd.plan
    prompt: Create a plan by running /sdd.plan in the same active feature branch context. I am building with...
scripts:
   sh: scripts/bash/check-prerequisites.sh --json --paths-only
   ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

Goal: Detect and reduce ambiguity or missing decision points in the active feature specification and record the clarifications directly in the spec file.

Anti-solidification rule (mandatory): clarification must refine the current spec context only. Do not introduce domain/project/entity names that are not grounded in current spec content, current user input, or explicitly stated assumptions.

Note: This clarification workflow is expected to run (and be completed) BEFORE invoking `/sdd.plan`. If the user explicitly states they are skipping clarification (e.g., exploratory spike), you may proceed, but must warn that downstream rework risk increases.

Authority rule (mandatory):

- `FEATURE_SPEC` (`spec.md`) is the authoritative feature-semantics source during this command.
- ambiguity map, question queue, and session notes are derived working views only and MUST NOT override `spec.md`.

Stage boundary rule (mandatory):

- `/sdd.clarify` refines feature semantics in `spec.md` only.
- Do not introduce planning/contract/task governance payloads (for example: repo-anchor strategy states, boundary tuple keys, `Repo Anchor Role`, contract schema fields, task orchestration directives, or implementation choreography).

Gate ownership rule (mandatory):

- `/sdd.clarify` MAY report local clarification coverage (`Resolved/Deferred/Clear/Outstanding`) for this spec only.
- `/sdd.clarify` MUST NOT emit cross-artifact final PASS/FAIL decisions.
- Cross-artifact final PASS/FAIL ownership remains centralized in `/sdd.analyze`.

Execution steps:

1. Resolve file paths once by running `{SCRIPT}` from repo root (`--json --paths-only` / `-Json -PathsOnly`):
   - required payload: `FEATURE_DIR`, `FEATURE_SPEC`
   - if JSON parsing fails, stop and route user to re-run `/sdd.specify` or fix feature-branch context
2. Load `FEATURE_SPEC` and build an internal ambiguity map (Clear / Partial / Missing) across:
   - Backbone & Boundaries (`1.1`, `1.2`, terminology)
   - User-Visible Data Backbone (`1.3 UI Data Dictionary`)
   - UC / FR Backbone (`§ 2`, `2.1`, `3.1`, `3.3`)
   - UX / UIF Backbone (`2.2`, `3.2`)
   - UI Surface Definition (`3.4`, `3.5`)
   - Outcome & Edge Signals (`N.1`, `N.2`)
   - Dependencies, Constraints, and Open Questions
3. Build a prioritized question queue:
   - ask only high-impact questions that change spec semantics or planning/test inputs
   - ask at most 2 by default, maximum 5 total
   - skip low-impact wording/style questions and already-resolved details
4. Run a sequential Q/A loop:
   - ask exactly one question at a time
   - answer format is compact multiple-choice or short answer (`<=5 words`)
   - stop when critical ambiguities are resolved, user ends (`done/good/no more`), or 5 accepted questions are reached
5. After each accepted answer, update spec immediately:
   - ensure `## Clarifications` exists and add `### Session YYYY-MM-DD` on first write
   - append `- Q: <question> -> A: <final answer>`
   - patch the most relevant section directly, replacing obsolete text instead of adding contradictory duplicates
   - keep stage boundaries intact:
     - do not add planning control-plane, contract realization, task orchestration, audit tables, or implementation choreography to `spec.md`
     - keep terminology context-pure (no legacy/example domain leakage)
   - for flow/edge updates, keep `Scenario`, `Path`, `UIF`, `FR`, and `EC` references aligned, and add `EC-005+` instead of overloading an unrelated edge-case id.
6. Validate after each write and at finalization:
   - one clarification bullet per accepted answer, no duplicates
   - total accepted questions <= 5
   - mandatory backbone headings remain intact
   - updated `Entity.field` rows keep mandatory UDD columns
   - `UC`, `FR`, `Scenario`, `UIF`, `SC`, and `EC` references stay textually consistent
   - `Assumptions / Open Questions` retains only truly blocking items
   - only allowed new headings: `## Clarifications`, `### Session YYYY-MM-DD`
   - no planning/contract/task governance payload sections are introduced
   - no cross-artifact final PASS/FAIL conclusion is emitted
7. Write back `FEATURE_SPEC` and report:
   - questions asked/answered
   - updated spec path
   - sections touched
   - coverage summary by area (`Resolved` / `Deferred` / `Clear` / `Outstanding`)
   - recommended next command

Behavior rules:

- If no meaningful ambiguities found (or all potential questions would be low-impact), respond: "No critical ambiguities detected worth formal clarification." and suggest proceeding.
- If spec file missing, instruct user to run `/sdd.specify` first (do not create a new spec here).
- Never exceed 5 total asked questions (clarification retries for a single question do not count as new questions).
- Avoid speculative tech stack questions unless the absence blocks functional clarity.
- Respect user early termination signals ("stop", "done", "proceed").
- If no questions asked due to full coverage, output a compact coverage summary (all categories Clear) then suggest advancing.
- If quota reached with unresolved high-impact categories remaining, explicitly flag them under Deferred with rationale.

Context for prioritization: {ARGS}

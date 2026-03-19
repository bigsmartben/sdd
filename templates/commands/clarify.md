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

Execution steps:

1. Run `{SCRIPT}` from repo root **once** (combined `--json --paths-only` mode / `-Json -PathsOnly`). Parse minimal JSON payload fields:
   - `FEATURE_DIR`
   - `FEATURE_SPEC`
   - (Optionally capture `IMPL_PLAN`, `TASKS` for future chained flows.)
   - If JSON parsing fails, abort and instruct user to re-run `/sdd.specify` or verify feature branch environment.

2. Load the current spec file. Perform a structured ambiguity & coverage scan aligned to the current backbone-first spec template. For each area, mark status: Clear / Partial / Missing. Produce an internal coverage map used for prioritization (do not output raw map unless no questions will be asked).

   Backbone & Boundaries:
   - `1.1 Actors` responsibilities, permissions, and role distinctions
   - `1.2 System Boundary` in-scope / out-of-scope clarity
   - Canonical business terminology used across the spec

   User-Visible Data Backbone:
   - `1.3 UI Data Dictionary (UDD)` entity coverage
   - Field completeness for each `Entity.field`: `Calculation / criteria`, `Boundaries & null/empty rules`, `Display rules`, and `Key Path`
   - Identity, uniqueness, lifecycle, or relationship rules that materially affect user-visible behavior

   UC / FR Backbone:
   - `§ 2 UC Overview` completeness and priority clarity
   - `2.1 Functional Requirements Index (FR Index)` coverage and linkage
   - Per-UC `3.1 User Story & Acceptance Scenarios` and `3.3 Functional Requirements` consistency

   UX / UIF Backbone:
   - `2.2 Global UX Flow Overview` for cross-UC backbone flow when needed
   - Per-UC `3.2 UX — User Interaction Flow` preconditions, path inventory, interaction steps, exception paths, and postconditions
   - User-visible failure, empty, retry, timeout, permission, or recovery behavior

   UI Surface Definition:
   - `3.4 UI — UI Element Definitions` page/view info, component copy, state rules, and triggered behavior
   - `3.5 Component-Data Dependency Overview` mappings between components, `Entity.field`, and FR/scenario refs

   Outcome & Edge Signals:
   - `N.1 Success Criteria` measurability and acceptance relevance
   - `N.2 Environment Edge Cases` completeness
   - Quality/security/privacy/compliance expectations only when they materially affect user-visible acceptance or validation

   Dependencies, Constraints, and Open Questions:
   - External integrations or dependencies only when they change visible behavior or acceptance
   - Explicit business constraints or tradeoffs that materially shape the spec
   - `Assumptions / Open Questions` only for truly blocking unresolved items
   - TODO markers / ambiguous adjectives ("robust", "intuitive") lacking concrete meaning

   For each area with Partial or Missing status, add a candidate question opportunity unless:
   - Clarification would not materially change spec meaning, downstream planning, or validation strategy
   - Information is better deferred to planning phase (note internally)

3. Generate (internally) a prioritized queue of clarification questions (maximum 5).
   - Keep only questions that materially change spec semantics, planning inputs, test strategy, UX behavior, or compliance acceptance.
   - Prefer fast-path operation: ask at most 2 questions unless unresolved high-impact ambiguity still exists.
   - Exclude already-answered items, style preferences, and non-blocking plan-level details.
   - If more than 5 candidates remain, keep the top 5 by impact * uncertainty.

4. Sequential questioning loop (interactive):
   - Ask EXACTLY ONE question at a time.
   - Use compact answer formats only:
     - multiple-choice: 2-5 mutually exclusive options, OR
     - short answer: `<=5 words`.
   - You MAY include one recommended option/suggested answer in one sentence when it reduces ambiguity.
   - Accept `yes/recommended/suggested` as approval of the latest recommendation.
   - If answer is ambiguous, ask one quick disambiguation and keep it inside the same question.
   - Stop when:
     - critical ambiguities are resolved, OR
     - user ends questioning (`done`, `good`, `no more`), OR
     - 5 accepted questions are reached.

5. Integration after EACH accepted answer (incremental update approach):
    - Maintain in-memory representation of the spec (loaded once at start) plus the raw file contents.
    - For the first integrated answer in this session:
       - Ensure a `## Clarifications` section exists (create it after `## Artifacts Overview & Navigation` when that section exists; otherwise insert it immediately before the first `## § 1` backbone section).
       - Under it, create (if not present) a `### Session YYYY-MM-DD` subheading for today.
    - Append a bullet line immediately after acceptance: `- Q: <question> → A: <final answer>`.
    - Then immediately apply the clarification to the most appropriate section(s):
       - Actor or scope ambiguity → Update `1.1 Actors` or `1.2 System Boundary` with the clarified responsibility, permission, or in/out-of-scope statement.
       - User-visible data clarification → Update `1.3 UI Data Dictionary (UDD)` inline; when adding or editing `Entity.field` rows, keep ordering stable and populate every mandatory column (`Calculation / criteria`, `Boundaries & null/empty rules`, `Display rules`, `Key Path`).
       - UC / FR clarification → Update `§ 2 UC Overview`, `2.1 Functional Requirements Index`, and the relevant per-UC `3.3 Functional Requirements` block together when the clarification changes capability scope or traceability.
       - Scenario / flow clarification → Update the relevant `3.1 User Story & Acceptance Scenarios`, `3.2 UX — User Interaction Flow`, or `2.2 Global UX Flow Overview`; keep `Scenario`, `Path`, `UIF`, `FR`, and `EC` references textually consistent, and add `EC-005+` instead of overloading an unrelated edge-case id.
       - UI surface clarification → Update `3.4 UI — UI Element Definitions` and/or `3.5 Component-Data Dependency Overview`; do not add UI behavior that lacks a matching `Entity.field`, FR, or scenario anchor.
       - Measurable outcome or quality constraint → Add or modify testable `SC-*` bullets in `N.1 Success Criteria`; do not create a free-floating `Non-Functional` or `Quality Attributes` heading.
       - Edge case / failure handling → Update `N.2 Environment Edge Cases` and the most relevant per-UC exception/failure section; keep each referenced `EC-*` semantically aligned with the exact retry/re-entry/permission/duplicate/timeout/recovery behavior it names, and do not create a generic `Error Handling` heading unless one already exists in the current spec.
       - Blocking unresolved item → Update `Assumptions / Open Questions` only when the item remains truly blocking at spec stage.
       - Do not create a standalone `Relationships` heading just to record a clarification; express relationship semantics in the relevant UDD, flow, or rule section unless a current section already provides a better home.
       - Terminology conflict → Normalize the term across Actors, UDD, UC/FR, UIF, UI, and Success/Edge sections; retain the original only once if needed as `(formerly referred to as "X")`.
    - If the clarification invalidates an earlier ambiguous statement, replace that statement instead of duplicating; leave no obsolete contradictory text.
    - Save the spec file AFTER each integration to minimize risk of context loss (atomic overwrite).
    - Preserve formatting: do not reorder unrelated sections; keep heading hierarchy intact.
    - Keep each inserted clarification minimal and testable (avoid narrative drift).
    - Keep stage boundaries intact:

- do not add planning control-plane content, contract realization design, task orchestration, audit tables, or implementation choreography into `spec.md`
  - Keep terminology context-pure:
    - Do not inject legacy/example domain identifiers from prior conversations.
    - If a candidate term is not present in current spec/user input/assumptions, replace it with neutral wording or ask a bounded clarification.

1. Validation (performed after EACH write plus final pass):
   - Clarifications session contains exactly one bullet per accepted answer (no duplicates).
   - Total asked (accepted) questions ≤ 5.
   - Updated sections contain no lingering vague placeholders the new answer was meant to resolve.
   - Mandatory spec backbone headings remain intact; do not replace template sections with ad-hoc headings.
   - Any updated `1.3 UI Data Dictionary` row still includes all mandatory completeness columns and explicit values.
   - `UC`, `FR`, `Scenario`, `UIF`, `SC`, and `EC` references remain textually consistent after edits.
   - `Assumptions / Open Questions` contains only truly blocking unresolved items.
   - No contradictory earlier statement remains (scan for now-invalid alternative choices removed).
   - Markdown structure valid; only allowed new headings: `## Clarifications`, `### Session YYYY-MM-DD`.
   - No planning, audit, or implementation-stage detail was injected into `spec.md`.
   - Terminology consistency: same canonical term used across all updated sections.
   - Anti-solidification: no newly added term should be traceable only to prior analysis/examples.

2. Write the updated spec back to `FEATURE_SPEC`.

3. Report completion (after questioning loop ends or early termination):
   - Number of questions asked & answered.
   - Path to updated spec.
   - Sections touched (list names).
   - Coverage summary table listing each template-aligned area (`Backbone & Boundaries`, `User-Visible Data Backbone`, `UC / FR Backbone`, `UX / UIF Backbone`, `UI Surface Definition`, `Outcome & Edge Signals`, `Dependencies, Constraints, and Open Questions`) with Status: Resolved (was Partial/Missing and addressed), Deferred (exceeds question quota or better suited for planning), Clear (already sufficient), Outstanding (still Partial/Missing but low impact).
   - If any Outstanding or Deferred remain, recommend whether to proceed to `/sdd.plan` or run `/sdd.clarify` again later post-plan.
   - Suggested next command.

Behavior rules:

- If no meaningful ambiguities found (or all potential questions would be low-impact), respond: "No critical ambiguities detected worth formal clarification." and suggest proceeding.
- If spec file missing, instruct user to run `/sdd.specify` first (do not create a new spec here).
- Never exceed 5 total asked questions (clarification retries for a single question do not count as new questions).
- Avoid speculative tech stack questions unless the absence blocks functional clarity.
- Respect user early termination signals ("stop", "done", "proceed").
- If no questions asked due to full coverage, output a compact coverage summary (all categories Clear) then suggest advancing.
- If quota reached with unresolved high-impact categories remaining, explicitly flag them under Deferred with rationale.

Context for prioritization: {ARGS}

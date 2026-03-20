---
description: Generate a high-value interactive HTML tool prototype from the current feature branch spec.md for walkthrough, review, and interaction validation.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Argument Parsing

Treat all `$ARGUMENTS` as optional prototype direction.
Resolve `SPEC_FILE` from current feature branch using these defaults:

- `feature-YYYYMMDD-slug` -> `specs/YYYYMMDD-slug/spec.md`
- `YYYYMMDD-slug` -> `specs/YYYYMMDD-slug/spec.md`
- legacy `NNN-slug` keeps legacy prefix mapping in `specs/`

If branch-derived `SPEC_FILE` is missing or invalid, stop immediately and report the blocker.

## Goal

Generate exactly one review-ready `ui.html` focused interactive tool from the resolved `SPEC_FILE`.

This artifact is for:

- stakeholder walkthrough
- UX review
- interaction validation
- copy/state validation
- early concept communication

This command should produce a focused interaction tool that is visually intentional, easy to demo, and immediately useful for discussion.

Use `.specify/templates/ui-html-template.html` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or previous outputs.

## Authority Rules

- `spec.md` remains the authoritative feature-semantics artifact.
- `ui.html` is a derived prototype artifact only.
- `ui.html` MUST reflect `spec.md`, not replace it.
- `ui.html` MUST make the core expression of `spec.md` easier to perceive through interaction, not harder to infer through layout or decoration.
- Treat `spec.md` as a fact ledger for prototype derivation, especially `1.3 UI Data Dictionary (UDD)`, `3.2 UX — User Interaction Flow`, `3.4 UI — UI Element Definitions`, and `3.5 Component-Data Dependency Overview`.
- If the prototype exposes semantic gaps or contradictions, route the repair back to `/sdd.specify` or `/sdd.clarify`.
- Do **not** invent new requirements, actors, entities, or product flows that are not traceable to `spec.md` or current user input.
- Do **not** introduce planning-stage governance semantics in `ui.html` (for example: tuple dispatch keys, repo-anchor strategy states, `Repo Anchor Role`, or contract packet fields).
- `Ready/Blocked` from this command is prototype-local readiness only; it MUST NOT be treated as cross-artifact final PASS/FAIL.
- Cross-artifact final PASS/FAIL ownership remains centralized in `/sdd.analyze`.

## Action Entry Executability Rules (MUST)

When `spec.md` implies a user-clickable action entry (for example: 查看/打开/进入/跳转/report/detail), enforce all rules below:

- Every clickable entry MUST map to explicit semantics in prototype data:
  - `entryLabel`
  - `targetMeaning`
  - `targetRoute` or a named click handler
- Rendering a clickable control without executable target binding is forbidden.
- Each rendered `.action-entry` MUST include either:
  - navigable target (`href`, `location.href`, `window.open`), or
  - `addEventListener("click", ...)` that resolves to a concrete in-prototype destination or flow.
- If target semantics cannot be resolved from `spec.md`, render non-clickable explanatory text and keep the current flow usable.
- Do not output a dead CTA (looks clickable but no-op).

Before finalizing `ui.html`, run an internal self-check table for each action entry:
`entryLabel | targetMeaning | targetRoute/handler | clickable(true/false)`.
If any row has `clickable=true` with empty `targetRoute/handler`, regenerate `ui.html` before returning.

## UIF + UDD Coverage Protocol (MUST)

Before generating `ui.html`, build an internal coverage ledger from the selected `spec.md` sections.

- Treat `3.2 UX — User Interaction Flow` as the primary interaction authority for prototype sequencing.
- Treat `1.3 UI Data Dictionary (UDD)` as the primary authority for user-visible business data and rule-driven states.
- Treat `3.4 UI — UI Element Definitions` and `3.5 Component-Data Dependency Overview` as the authority for view/component/data bindings when present.
- Build an internal coverage ledger before generating `ui.html` with these minimum slices:
  - `UC ID | selected Path IDs | selected UIF nodes | omitted Path IDs | omission reason`
  - `UIF Node | prototype screen/view | interaction/control | feedback/state | ref: Scenario/FR`
  - `Entity.field | user-visible interaction moment | displayed completion/content | consumed rule (calculation/boundary/display) | ref: FR/Scenario`
- Every demonstrated user interaction MUST trace back to an explicit `UIF` node. Do not simulate a business-significant user step that has no `UIF` anchor.
- The prototype should visibly dedicate a primary review surface to the selected `UIF` path/node progression so engineering can replay the user-perspective operation flow step by step.
- Do not render the full UDD inventory, raw field tables, or exhaustive `Entity.field` lists as visible prototype content unless `spec.md` explicitly defines such a screen.
- Only surface the subset of completed `Entity.field` rows needed to make the selected interaction understandable from the user's point of view.
- Every business-significant datum that appears inside the demonstrated interaction MUST trace back to explicit completed `Entity.field` rows. If it cannot be traced to UDD, omit it or render it as clearly non-authoritative placeholder text.
- If a selected completed `Entity.field` row has null/empty, boundary, formatting, or display rules in UDD, consume those rules in the demonstrated prototype states instead of showing labels only.
- The prototype should visibly dedicate a peer review surface to step-level `UDD` feedback so reviewers can see what the user perceives after each important `UIF` action or branch.
- For each selected interactive UC, demonstrate at least:
  - one happy path,
  - and one meaningful branch state (`alternate`, `exception`, `retry`, `recovery`, `cancel`, `timeout`, `permission`, or `duplicate`) when the spec makes that branch user-visible or acceptance-relevant.
- If an important branch exists in `Path Inventory` but is not demonstrated interactively, keep the current flow usable and report the omission explicitly in the final output.
- Do not collapse multiple `UIF` steps into one generic interaction when doing so would hide a user-visible decision, feedback signal, or state transition that matters to the selected path.

## Deterministic Prototype Selection Protocol (MUST)

Use deterministic selection rules before writing `ui.html`.

- If user input explicitly names `UC`, `UIP`, `UIF`, or `Entity.field` refs, use exactly those refs as prototype scope. Do not widen scope unless the user explicitly asks for broader coverage.
- Otherwise, choose exactly one primary walkthrough by this priority order:
  1. the first `happy` or primary-success `UIP-*` row in spec order that has explicit user-visible completion semantics
  2. if multiple rows qualify, prefer the one whose selected `UIF` nodes surface completed `Entity.field` rows with explicit UDD rules
  3. if still tied, keep the first qualifying row in spec order
- Choose at most one branch walkthrough unless the user explicitly asks for more:
  1. select the first acceptance-relevant branch attached to the same `UC` / path family in spec order
  2. if no same-family branch exists, omit branch walkthrough and report the omission explicitly
- Select `UIF` nodes deterministically:
  - include the selected path's entry, primary action, immediate feedback, and completion nodes in spec order
  - include only the minimum additional branch/recovery nodes needed to explain the chosen alternate or failure state
  - do not merge multiple path families into one synthetic `UIF` sequence
- Select `Entity.field` rows deterministically:
  - include only user-visible fields directly perceived at the selected `UIF` nodes
  - include fields for entry context, immediate feedback, completion/result, and selected branch feedback only
  - if multiple fields qualify at the same interaction moment, keep spec order
  - if an entity exposes many fields, keep the minimum subset needed to explain what changed for the user
- Map review surfaces deterministically:
  - `UIF Interaction View` MUST enumerate the selected `UIF` nodes in execution order
  - `UDD-backed View State` MUST map each selected `UIF` node to the user-visible feedback or state change the user perceives at that step
  - `Primary Tool Loop` MUST derive from the selected primary walkthrough only
- If any required tie cannot be broken using explicit refs, spec order, or completed UDD evidence, stop and report the blocker instead of choosing heuristically.

## Allowed Inputs

Read only:

- `.specify/templates/ui-html-template.html` for output structure
- resolved `SPEC_FILE`
- remaining prototype direction after argument parsing
- existing `ui.html` at the target path only when refreshing in place

Do **not** read planning-stage artifacts by default.
Do **not** scan unrelated feature folders.

## Experience-First Prototype Rules

Prioritize prototype usefulness over document-like completeness.

### 0. Tool-First Delivery

`ui.html` should deliver a tool, not a document page.

- Default to one dominant interaction tool with one primary user intention
- Organize the experience around a closed interaction loop: context -> action -> system feedback -> completion/result -> next action
- Start by extracting one plain-language expression sentence from `spec.md`: who is trying to finish what, under what context, to get what visible result
- Make that expression sentence legible across the tool intent, primary action, feedback, and completion content
- Make the main action visually dominant within seconds
- Keep supporting states, history, and guidance subordinate to the tool's main loop
- Avoid dashboard-style equal-weight cards, report-like sections, or artifact-review layouts unless `spec.md` explicitly requires them

### 1. Reviewability First

The prototype should let a reviewer understand the feature quickly by interacting with it.

- Prefer one coherent clickable interaction tool over a static page dump
- Make the main user flow obvious within seconds
- Surface key decisions, feedback, and state transitions visually
- Use clear headings, labels, calls to action, and UI hierarchy

### 2. Strong Visual Direction

Avoid generic placeholder-looking output.

- Choose a clear visual theme appropriate to the product implied by `spec.md`
- Use CSS variables
- Build atmosphere with layout, contrast, surfaces, spacing, and subtle background treatment
- Avoid default “plain dashboard” or “purple gradient SaaS” patterns unless the spec clearly implies them
- Make it feel like a deliberate product concept, not a wireframe unless the spec calls for low-fidelity output

### 3. Interaction Matters

Prototype interaction should be meaningful.

- Use light inline JavaScript when needed to simulate:
  - the primary tool loop
  - state switching
  - tool-mode changes
  - modal open/close
  - happy path transitions
  - empty/error/success states
- Keep JS minimal and readable
- Interaction is for demonstration, not implementation fidelity

### 4. Spec-Faithful Surface

Reflect the user-facing truth from `spec.md`.

Use the spec to derive:

- primary views/pages
- key use cases
- visible entities and fields
- user actions
- important feedback states
- acceptance-relevant interaction outcomes
- the one dominant semantic through-line the user should understand after one pass

Keep labels and terminology aligned with `spec.md`.
Prefer explicit `UC`, `UIP`, `UIF`, `FR`, and `Entity.field` anchors in lightweight review surfaces only when they improve traceability without turning the artifact into a document dump or replacing user-facing content.
If traceability markers are shown in `ui.html`, keep them secondary and compact. Do not make IDs, coverage ledgers, or audit-style badges the dominant visible content of the prototype.
If the generated surface is visually polished but does not make the dominant semantic through-line from `spec.md` obvious within one pass, it is not acceptable.

### 5. Selective Scope

Do not try to prototype everything.

Instead, cover the smallest set of screens and interactions that best represent the feature:

- one primary tool surface
- main happy path for each selected interactive UC
- one meaningful alternate/error/empty/permission/timeout branch when the selected path set makes it user-visible or acceptance-relevant
- visible data presentation anchored to the completed `Entity.field` subset needed by the selected interaction and FR/scenario context
- rule-driven state evidence for selected UDD fields (for example: empty, error, disabled, warning, formatting, or recovery state)
- one explicit `UIF Interaction View` that shows the operation path in user terms
- one explicit `UDD-backed View State` that shows per-step feedback/result in user-visible terms

When the interaction reaches a completion/result moment, show the completed UDD-backed content where the user would actually perceive it instead of listing UDD rows separately.
Default to keeping the user in the same tool shell while the content, mode, or state changes around the main interaction loop.

If the spec implies many views, keep only the views required by the deterministic primary walkthrough and selected branch; keep the rest implicit.

### 6. Safe Placeholder Policy

When the spec lacks detail:

- use neutral placeholder copy
- use believable example content only if clearly presented as illustrative
- do not invent business rules or product scope
- do not hardcode domain details not supported by the spec

### 7. Positioning-Led De-duplication

Use positioning to control redundancy.

- In hero/top summary, state positioning once using: target user, core scenario, visible value.
- Each downstream section must add new information; do not restate hero semantics with different wording.
- Prefer compact anchors (`UC`, `FR`, `VIEW`) instead of repeating long prose across cards.
- If two sections become semantically equivalent, keep detail in the more execution-relevant section and shorten the other.

## Output Quality Rules

The generated `ui.html` should:

- be self-contained in one file unless the user explicitly requests otherwise
- render correctly in a browser
- work on desktop and mobile
- use semantic HTML
- use organized CSS with readable structure
- use minimal, targeted JS only where it improves prototype value
- present one clearly dominant tool interaction instead of multiple equal-priority sections
- be suitable for screenshotting, walkthroughs, or user review sessions

## Execution Flow

1. Resolve `FEATURE_DIR` as the parent directory of `SPEC_FILE`
2. Set target output to `FEATURE_DIR/ui.html`
3. Read `SPEC_FILE` and extract a compact prototype packet:
   - feature goal
   - actors
   - one plain-language expression sentence summarizing what `spec.md` is trying to make true for the user
   - positioning tuple (target user / core scenario / visible value)
   - key user-facing use cases
   - selected path inventory rows (`UIP-*`) and `UIF` nodes for the prototype surface
   - the completed visible data elements (`Entity.field`) and their UDD rules that the selected interaction actually surfaces
   - important flows
   - visible state variations
   - UI component/data anchors when present
   - terminology and copy anchors
4. Apply the deterministic prototype selection protocol and lock:
   - primary `UIP-*` walkthrough
   - optional same-family branch walkthrough
   - selected `UIF` nodes in execution order
   - selected `Entity.field` rows in spec order
5. Build the internal coverage ledger for the locked paths, `UIF` nodes, components, and `Entity.field` rows
6. Decide the smallest high-value prototype surface from the locked walkthrough:
   - what single dominant tool surface to show
   - what interactions to simulate
   - what states must be demonstrated
   - how `UIF Interaction View` and `UDD-backed View State` expose the same step order
7. Generate `ui.html` using the runtime template and locked prototype packet
8. Prefer polished review fidelity over exhaustive breadth
9. If the spec is too ambiguous to support a stable prototype, stop and report the blocker rather than inventing semantics

## Validation

Before completing, validate that:

- the prototype clearly represents the feature described in `spec.md`
- the main flow is understandable through interaction
- the deliverable reads as a focused interaction tool with one dominant primary loop
- the core expression sentence from `spec.md` is obvious from the tool intent, main action, feedback, and completion content without reading supporting notes
- the selected primary walkthrough follows explicit user-scoped refs or the deterministic priority order above
- the selected branch walkthrough follows explicit user-scoped refs or the deterministic same-family branch rule above
- every demonstrated interaction step maps to selected `UIF` node(s)
- each selected happy/branch path has a visible entry, transition, and user-visible outcome
- the generated surface makes `UIF` operation flow legible to engineering without reading supporting notes first
- `UIF Interaction View` enumerates the selected `UIF` nodes in execution order
- the prototype does not dump the full UDD inventory as visible content unless the spec explicitly requires it
- every business-significant datum surfaced in the demonstrated interaction maps to selected completed `Entity.field` row(s)
- selected UDD fields consume their boundary/null/display rules in the demonstrated states
- the generated surface makes step-level `UDD` feedback legible to engineering as the user would perceive it
- `UDD-backed View State` maps each selected `UIF` node to its visible feedback or state change without mixing unrelated fields
- any traceability cues shown in `ui.html` stay secondary to the user-visible interaction and completion content
- visible terminology stays aligned with `spec.md`
- no unsupported feature semantics were introduced
- mobile and desktop both render reasonably
- the output feels intentional and demo-ready
- the artifact remains a prototype, not an implementation document
- no major semantic statement is duplicated across hero, view cards, and review notes
- omitted important paths or user-visible data are explicit in the final output

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`: `/sdd.clarify`
- `Decision Basis`: `ui.html` is a derived interactive prototype from `spec.md`; use clarification to resolve remaining ambiguity before planning, otherwise proceed to `/sdd.plan`
- `Selected Artifact`: `ui.html`
- `Ready/Blocked`: `Ready` when `ui.html` is written successfully; otherwise `Blocked`

Boundary note: This `Ready/Blocked` reflects `ui.html` generation readiness only and does not replace `/sdd.analyze` cross-artifact gating.

## Final Output

Report:

- resolved `SPEC_FILE`
- generated `ui.html` absolute path
- prototype focus summary:
  - views included
  - main flow demonstrated
  - interactive states demonstrated
- `Deterministic Selection Summary`:
  - selection mode (`explicit refs` or `spec-order deterministic`)
  - primary `UIP` walkthrough selected
  - branch walkthrough selected or omitted
  - selected `UIF` nodes in order
  - selected `Entity.field` rows in order
- `UIF Coverage Summary`:
  - selected UC / `UIP` paths demonstrated
  - key `UIF` nodes surfaced through interaction
  - omitted important paths with reason
- `UDD Coverage Summary`:
  - surfaced completed `Entity.field` anchors through interaction
  - rule-driven states demonstrated from UDD (`empty`, `error`, `boundary`, `display`, etc.)
  - omitted UDD areas intentionally left out because they are not needed for the selected interaction
- any placeholders or unresolved ambiguities left explicit
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected Artifact`, and `Ready/Blocked`

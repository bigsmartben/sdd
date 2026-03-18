---
description: Generate a high-value interactive HTML prototype from an explicit or branch-derived spec.md path for walkthrough, review, and interaction validation.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Argument Parsing

1. If present, the first positional token is `SPEC_FILE`
2. Optional `SPEC_FILE` MUST resolve from repo root to an existing file named `spec.md`
3. Optional `SPEC_FILE` MUST stay under `repo/specs/**`
4. Any remaining text after removing optional `SPEC_FILE` is optional prototype direction

If `SPEC_FILE` is omitted, resolve it from current feature branch using these defaults:

- `feature-YYYYMMDD-slug` -> `repo/specs/YYYYMMDD-slug/spec.md`
- `YYYYMMDD-slug` -> `repo/specs/YYYYMMDD-slug/spec.md`
- legacy `NNN-slug` keeps legacy prefix mapping in `repo/specs/`

If optional `SPEC_FILE` is present but invalid, stop immediately and report the required invocation shape:

`/sdd.specify.ui-html <path/to/spec.md> [prototype-direction...]`

## Goal

Generate exactly one review-ready `ui.html` interactive prototype from the explicit `SPEC_FILE`.

This artifact is for:

- stakeholder walkthrough
- UX review
- interaction validation
- copy/state validation
- early concept communication

This command should produce a prototype that is visually intentional, easy to demo, and immediately useful for discussion.

Use `.specify/templates/ui-html-template.html` only. If the runtime template is missing or unreadable, stop and report the blocker instead of inferring structure from mirrors or previous outputs.

## Authority Rules

- `spec.md` remains the authoritative feature-semantics artifact.
- `ui.html` is a derived prototype artifact only.
- `ui.html` MUST reflect `spec.md`, not replace it.
- If the prototype exposes semantic gaps or contradictions, route the repair back to `/sdd.specify` or `/sdd.clarify`.
- Do **not** invent new requirements, actors, entities, or product flows that are not traceable to `spec.md` or current user input.

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

### 1. Reviewability First

The prototype should let a reviewer understand the feature quickly by interacting with it.

- Prefer one coherent clickable prototype over a static page dump
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
  - navigation between views
  - state switching
  - tab/filter changes
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

Keep labels and terminology aligned with `spec.md`.

### 5. Selective Scope

Do not try to prototype everything.

Instead, cover the smallest set of screens and interactions that best represent the feature:

- primary entry view
- main happy path
- one or more meaningful alternate/error/empty states if they matter
- visible data presentation anchored to `Entity.field` and FR/scenario context when available

If the spec implies many views, choose the most representative subset and keep the rest implicit.

### 6. Safe Placeholder Policy

When the spec lacks detail:

- use neutral placeholder copy
- use believable example content only if clearly presented as illustrative
- do not invent business rules or product scope
- do not hardcode domain details not supported by the spec

## Output Quality Rules

The generated `ui.html` should:

- be self-contained in one file unless the user explicitly requests otherwise
- render correctly in a browser
- work on desktop and mobile
- use semantic HTML
- use organized CSS with readable structure
- use minimal, targeted JS only where it improves prototype value
- be suitable for screenshotting, walkthroughs, or user review sessions

## Execution Flow

1. Resolve `FEATURE_DIR` as the parent directory of `SPEC_FILE`
2. Set target output to `FEATURE_DIR/ui.html`
3. Read `SPEC_FILE` and extract a compact prototype packet:
   - feature goal
   - actors
   - key user-facing use cases
   - visible data elements
   - important flows
   - visible state variations
   - terminology and copy anchors
4. Decide the smallest high-value prototype surface:
   - what screens/views to show
   - what interactions to simulate
   - what states must be demonstrated
5. Generate `ui.html` using the runtime template and current prototype packet
6. Prefer polished review fidelity over exhaustive breadth
7. If the spec is too ambiguous to support a stable prototype, stop and report the blocker rather than inventing semantics

## Validation

Before completing, validate that:

- the prototype clearly represents the feature described in `spec.md`
- the main flow is understandable through interaction
- visible terminology stays aligned with `spec.md`
- no unsupported feature semantics were introduced
- mobile and desktop both render reasonably
- the output feels intentional and demo-ready
- the artifact remains a prototype, not an implementation document

## Handoff Decision

Emit a `Handoff Decision` section in the runtime output with exactly these fields:

- `Next Command`: `/sdd.clarify`
- `Decision Basis`: `ui.html` is a derived interactive prototype from `spec.md`; use clarification to resolve remaining ambiguity before planning, otherwise proceed to `/sdd.plan <absolute path to spec.md>`
- `Selected Artifact`: `ui.html`
- `Ready/Blocked`: `Ready` when `ui.html` is written successfully; otherwise `Blocked`

## Final Output

Report:

- resolved `SPEC_FILE`
- generated `ui.html` absolute path
- prototype focus summary:
  - views included
  - main flow demonstrated
  - interactive states demonstrated
- any placeholders or unresolved ambiguities left explicit
- `Handoff Decision` with `Next Command`, `Decision Basis`, `Selected Artifact`, and `Ready/Blocked`

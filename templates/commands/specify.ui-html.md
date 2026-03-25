---
description: Generate one self-contained interactive ui.html prototype from the resolved spec.md.
---

## User Input

```text
$ARGUMENTS
```

Treat all `$ARGUMENTS` as optional direction.
Resolve `SPEC_FILE` using branch defaults: `specs/YYYYMMDD-slug/spec.md`.

## Goal

Generate one high-fidelity, review-ready, interactive `ui.html` prototype from `SPEC_FILE`.

## Governance / Authority

- **Authority rule**: `spec.md` is the semantic authority; `ui.html` is a derived prototype artifact.
- `ui.html` is a derived artifact.
- **Scope rule**: This command generates presentation and interaction only. It does **not** run gates, audits, or downstream checks.
- **Output rule**: Produce a single-file prototype that opens directly in a browser with no build step and no external dependencies.

## Allowed Inputs

- `.specify/templates/ui-html-template.html`
- `SPEC_FILE`
- Optional user direction from `$ARGUMENTS`

**Prohibited**:
- planning artifacts
- unrelated feature folders
- remote assets, frameworks, or build-time dependencies
- business rules not grounded in `spec.md`

## Reasoning Order

1. Lock one dominant user journey from `SPEC_FILE`.
2. Add at most one critical branch only if it proves a core guard or recovery behavior.
3. Derive the minimum visible states, copy, and controls needed to make the journey reviewable.
4. Fill the runtime template with self-contained HTML, CSS, and JavaScript.

## Artifact Quality Contract

- Must: read like a polished product prototype, not a requirements document.
- Must: make the main user goal, primary action, visible feedback, and completion state obvious in one pass.
- Must: be interactive with live state changes in the page itself.
- Must: keep all visible copy and state names semantically grounded in `spec.md`.
- Must: keep one dominant path visually primary on desktop and mobile.
- Strictly: default to one primary path plus zero or one branch.
- Strictly: keep traceability secondary; do not make audit language the primary reading experience.
- Strictly: every clickable control must have a real inline handler or a real in-page target.
- **Prohibited**: document dumps, dead CTAs, multi-scenario simulators, hidden required steps, external fetches, downstream handoff logic.

## Writeback Contract

- Write `specs/YYYYMMDD-slug/ui.html` only.
- Do **not** modify `spec.md`, `plan.md`, or any other artifact.

## Stop Conditions

Stop immediately if:
1. `.specify/templates/ui-html-template.html` is missing or unreadable.
2. `SPEC_FILE` is missing or unreadable.
3. `SPEC_FILE` does not provide enough grounded user-visible behavior to produce a prototype without inventing product scope.

## Handoff Decision

Emit exactly these fields:
- `Next Command`: `None`
- `Decision Basis`: `ui.html` generated or blocked
- `Selected Artifact`: `ui.html`
- `Ready/Blocked`: local generation status only

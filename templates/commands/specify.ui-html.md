---
description: Generate an interactive HTML tool prototype from spec.md for review.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Argument Parsing

Treat all `$ARGUMENTS` as optional direction.
Resolve `SPEC_FILE` using branch defaults: `specs/YYYYMMDD-slug/spec.md`.

## Goal

Generate one review-ready `ui.html` prototype for walkthroughs, UX review, and interaction validation.
Use `.specify/templates/ui-html-template.html` only.

`/sdd.specify.ui-html` owns:
- Derived interaction tool that makes `spec.md` intent obvious.
- Visualizing core user flows, interaction moments, and data states.

## Governance / Authority

- **Authority rule**: `spec.md` is the semantic authority; `ui.html` is a derived artifact.
- **Stage boundary rule**: No planning governance semantics (tuples/anchors/contracts) in the prototype.
- **Protocol rule**: Final audit/PASS/FAIL is owned by `/sdd.analyze`.

## Allowed Inputs

- `.specify/templates/ui-html-template.html` (structure)
- `SPEC_FILE` (UDD / UX Flow / Page Definitions)

**Prohibited**: Planning artifacts, unrelated feature folders.

## Reasoning Order

1. **Selection**: Lock one primary walkthrough and one minimal branch from `spec.md`.
2. **Derivation**: Select minimal UIF/UDD slices for the locked walkthrough.
3. **Construction**: Build a dominant interactive surface; verify spec-faithfulness.

## Artifact Quality Contract

- Must: produce one coherent review prototype that makes the dominant user intent obvious in one pass.
- Strictly: every demonstrated interaction and state must trace back to `spec.md` and teach something real.
- **Tool-First**: Deliver an interactive tool, not a document dump.
- **Executable CTAs**: Every clickable entry MUST map to a target or handler; no "dead" CTAs.
- **Spec-Faithful**: Terminology and states MUST trace back to UDD and UIF nodes.
- **Positioning-Led**: State positioning once (actor / scenario / value).
- **Prohibited**: Invention of business rules or product scope not in spec.

## Interaction & Coverage Rules (MUST)

- **UIF Coverage**: Prototype MUST trace to explicit `UIF` nodes.
- **UDD Binding**: Visible data MUST trace to completed `Entity.field` rows.
- **Rule-Driven**: Consume UDD boundary/null/display rules in UI states.
- **Review Surfaces**: Dedicate areas to `UIF Interaction View` and `UDD-backed View State` for audit.

## Handoff Decision

Emit exactly these fields:
- `Next Command`: `/sdd.clarify` (to resolve ambiguity) or `/sdd.plan`.
- `Decision Basis`: `ui.html` generation outcome.
- `Selected Artifact`: `ui.html`.
- `Ready/Blocked`: Local readiness only.

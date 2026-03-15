<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0
- Modified principles:
  - N/A
- Added sections:
  - Repo-Anchor Evidence Protocol
- Removed sections:
  - None
- Templates requiring updates:
  - ✅ reviewed (no change required): templates/plan-template.md
  - ✅ reviewed (no change required): templates/spec-template.md
  - ✅ reviewed (no change required): templates/tasks-template.md
  - ✅ reviewed (no change required): templates/commands/constitution.md
  - ✅ reviewed (no change required): templates/commands/plan.md
  - ✅ reviewed (no change required): templates/commands/specify.md
  - ✅ reviewed (no change required): templates/commands/tasks.md
  - ✅ reviewed (no change required): templates/commands/implement.md
  - ✅ reviewed (no change required): templates/commands/analyze.md
  - ✅ reviewed (no change required): templates/commands/clarify.md
  - ✅ reviewed (no change required): templates/commands/checklist.md
  - ✅ reviewed (no change required): templates/commands/taskstoissues.md
  - ✅ reviewed (no change required): README.md
  - ✅ reviewed (no change required): docs/quickstart.md
- Follow-up TODOs:
  - None
-->

# Spec Kit Constitution

## Preamble

This constitution defines the long-lived rules and boundaries for Spec Kit.
It exists to keep decisions consistent across specification, planning,
task decomposition, and implementation.

All principles in this constitution MUST:

- be grounded in real project scenarios, risks, or boundary decisions;
- be specific enough to guide downstream decisions and reviews;
- define clear constraints, not aspirational slogans only.

If a required rule is not yet fully defined, it MUST be recorded explicitly as
`TODO(<TOPIC>): <reason>` rather than implied or silently omitted.

## Core Principles

> Each principle should be written as an enforceable rule.
> Recommended structure per principle:
>
> - **Rule**: what is required or prohibited
> - **Scope**: where it applies
> - **Rationale**: why it exists
> - **Exceptions**: when deviation is allowed and how it must be documented

### I. Backbone-First Semantic Purity

- **Rule**: Spec, plan, and tasks artifacts MUST express their own core semantics
  only, and MUST NOT include governance payload (such as stage dispatcher,
  registry, coverage audit, or conversion report data) in business/design content.
- **Scope**: All generated and manually edited artifacts under spec-driven workflow.
- **Rationale**: Semantic purity keeps artifacts reusable, readable, and stable.
- **Exceptions**: Exception is allowed only if a regulation or external contract
  requires embedded governance metadata; the artifact MUST record a
  `TODO(GOVERNANCE_EMBEDDING_JUSTIFICATION)` with owner and review date.

### II. Contract-Centric Continuity

- **Rule**: Contract semantics MUST be the canonical downstream interface source;
  plan/interface details/tasks MAY project or reference contracts but MUST NOT
  redefine or contradict contract behavior.
- **Scope**: `contracts/`, `plan.md`, `interface-details/`, `tasks.md`, and
  implementation outputs.
- **Rationale**: A single source of interface truth prevents drift and rework.
- **Exceptions**: Temporary divergence is allowed only during active refactor,
  and MUST include explicit migration notes and closure criteria in the same
  change set.

### III. Testable Requirement Traceability

- **Rule**: Every MUST-level requirement MUST map to at least one verifiable
  acceptance anchor (scenario, CaseID, TM/TC, or equivalent), and each
  implementation task MUST reference at least one requirement or verification
  anchor when such anchors exist upstream.
- **Scope**: `spec.md`, `test-matrix.md` (or equivalent), `tasks.md`, and
  verification tasks.
- **Rationale**: Traceability ensures changes are auditable and test-complete.
- **Exceptions**: Exploratory spikes may defer full mapping, but MUST be marked
  as time-boxed and include explicit follow-up tasks before release.

### IV. Agent-Neutral Workflow Compatibility

- **Rule**: Command templates and operational guidance MUST remain agent-neutral,
  using generic guidance or explicit placeholders rather than hard-coding a
  single assistant.
- **Scope**: templates, command files, onboarding docs, and scripts.
- **Rationale**: Spec Kit supports multiple agents and must preserve portability.
- **Exceptions**: Agent-specific files are allowed only within dedicated
  agent-scoped paths and must not leak assumptions into shared templates.

### V. Controlled Evolution and Simplicity

- **Rule**: Changes to long-lived workflow rules MUST prefer additive evolution,
  and any complexity increase MUST include explicit problem statement, rejected
  simpler alternative, and rollout impact.
- **Scope**: constitution updates, template evolution, and process-level scripts.
- **Rationale**: Controlled change reduces cognitive load while preserving growth.
- **Exceptions**: Breaking changes are permitted only with documented migration
  guidance and semantic version increment in this constitution.

## Terminology & Boundary Definitions

This section defines the key terms, boundaries, and semantic distinctions that MUST remain stable across downstream artifacts.

Include only project-critical concepts here, for example:

- core business terms that have precise meanings;
- distinctions between user-facing concepts and internal technical representations;
- phase or layer boundaries that must not be mixed;
- terms that are commonly confused and therefore require explicit separation.

- **Backbone Semantics**: the business/design meaning carried by `spec`, `plan`,
  and `tasks` artifacts.
- **Governance Payload**: workflow orchestration or audit metadata (dispatcher,
  registry, coverage audit, conversion report, origin trace).
- **Contract Semantics**: externally observable interface behavior and constraints,
  as defined in `contracts/`.
- **Projection Artifact**: downstream document that selectively maps upstream
  semantics for a narrower scope without redefining source semantics.
- **Verification Anchor**: stable reference used to prove behavior coverage,
  including scenario IDs, CaseID, TM/TC IDs, or equivalent identifiers.

### Repo-Anchor Evidence Protocol

- **Rule**: Repo semantic anchors come from source code plus `.specify/memory/constitution.md` only.
- **Whitelist (hard rule)**: `source-code files / source-code symbols + .specify/memory/constitution.md`.
- **Blacklist (hard rule)**: `README.md`, `docs/**`, `specs/**`, historical examples, demo documents, and generated artifacts MUST NOT be used as repo semantic evidence.
- **Boundary**: Blacklist items may be read as supporting context or background clues when explicitly needed, but they MUST NOT be promoted into repo semantic anchors.

## State Machine Applicability Gate

This section defines when a feature MUST include a full business lifecycle state machine,
and when a lightweight model is sufficient.

### Definitions

- `N`: number of distinct user-meaningful lifecycle states.
- `T`: number of effective transitions (`FromState -> ToState` unique edges).

### Applicability Rule

A **Full FSM** (transition table + transition pseudocode + state diagram) is required iff:

- `N > 3` **OR** `T >= 2N`

If the rule is not met, use a **Lightweight State Model** instead:

- state field definition (if any)
- allowed transitions
- forbidden transitions
- key invariants (if any)

### Exception Handling

If a Full FSM is used below threshold, the plan MUST include explicit justification under
complexity tracking (why lightweight is insufficient).

## Constraints & Evolution Rules

This section defines long-lived constraints that guide change over time.
These rules should focus on compatibility, simplicity, and controlled evolution.

- Prefer additive template and command changes over breaking rewrites.
- Breaking behavior changes MUST include migration guidance in docs and release notes.
- New mandatory sections in shared templates MUST include rationale and clear
  downstream consumption expectations.
- Any new workflow constraint MUST define where it is validated
  (spec/plan/tasks/analyze/implement).
- Repository-wide terminology changes MUST be applied consistently across
  templates and docs in the same change set.

## Compliance & Review Expectations

This section defines lightweight expectations for constitution checks in downstream work.

Each expectation SHOULD state:

- **Expectation**: what should be checked
- **Where Checked**: which artifact or stage should perform the check
- **Handling**: what to do when the expectation is not met

- **Expectation**: Backbone semantic purity is preserved.
  **Where Checked**: `/sdd.specify`, `/sdd.plan`, `/sdd.tasks`, `/sdd.analyze`.
  **Handling**: remove governance payload from affected artifact before proceeding.
- **Expectation**: Contract-centric continuity is preserved.
  **Where Checked**: `/sdd.plan` Stage 1/3 and `/sdd.tasks` generation.
  **Handling**: align downstream projection with `contracts/` and note resolution.
- **Expectation**: MUST requirements remain verifiable.
  **Where Checked**: spec checklist, test-matrix generation, tasks verification units.
  **Handling**: add missing verification anchors before implementation.
- **Expectation**: Agent-neutral guidance remains intact.
  **Where Checked**: template and command review, quickstart/README updates.
  **Handling**: replace agent-specific hard-coding with generic or scoped guidance.

## Governance

This constitution supersedes lower-level conventions when conflicts arise.
Amendments MUST be explicit, reviewed, and reflected in downstream guidance where applicable.

- Amendment procedure: propose change with impact summary, review against existing
  principles, and merge only after dependent template/doc sync review is complete.
- Versioning policy: semantic versioning is mandatory
  (`MAJOR` incompatible principle redefinition/removal,
  `MINOR` new principle/section or materially expanded guidance,
  `PATCH` clarification/editorial updates without semantic change).
- Compliance review expectations: each constitution update MUST include a
  Sync Impact Report listing affected templates/docs and update status.
- Exception governance: temporary exceptions MUST include owner, rationale,
  scope, and expiration or review date.

**Version**: 1.1.0 | **Ratified**: 2026-03-13 | **Last Amended**: 2026-03-15
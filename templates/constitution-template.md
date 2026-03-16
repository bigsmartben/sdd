# [PROJECT_NAME] Constitution
<!-- Example: Spec Constitution, TaskFlow Constitution, etc. -->

## Preamble

This constitution defines the long-lived rules and boundaries for this project.
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
> - At least one principle MUST define ownership boundaries for `Generation Rule`, `Validation Rule`, and `Hard Execution Gate`.

### [PRINCIPLE_1_NAME]
<!-- Example: I. Library-First -->
[PRINCIPLE_1_DESCRIPTION]
<!--
Suggested writing pattern:
- Rule: ...
- Scope: ...
- Rationale: ...
- Exceptions: ...
-->

### [PRINCIPLE_2_NAME]
<!-- Example: II. CLI Interface -->
[PRINCIPLE_2_DESCRIPTION]
<!--
Suggested writing pattern:
- Rule: ...
- Scope: ...
- Rationale: ...
- Exceptions: ...
-->

### [PRINCIPLE_3_NAME]
<!-- Example: III. Test-First (NON-NEGOTIABLE) -->
[PRINCIPLE_3_DESCRIPTION]
<!--
Suggested writing pattern:
- Rule: ...
- Scope: ...
- Rationale: ...
- Exceptions: ...
-->

### [PRINCIPLE_4_NAME]
<!-- Example: IV. Integration Testing -->
[PRINCIPLE_4_DESCRIPTION]
<!--
Suggested writing pattern:
- Rule: ...
- Scope: ...
- Rationale: ...
- Exceptions: ...
-->

### [PRINCIPLE_5_NAME]
<!-- Example: V. Observability, VI. Versioning & Breaking Changes, VII. Simplicity -->
[PRINCIPLE_5_DESCRIPTION]
<!--
Suggested writing pattern:
- Rule: ...
- Scope: ...
- Rationale: ...
- Exceptions: ...
-->

## Terminology & Boundary Definitions

This section defines the key terms, boundaries, and semantic distinctions that MUST remain stable across downstream artifacts.

Include only project-critical concepts here, for example:

- core business terms that have precise meanings;
- distinctions between user-facing concepts and internal technical representations;
- phase or layer boundaries that must not be mixed;
- terms that are commonly confused and therefore require explicit separation.
- generation/validation/execution boundary terms that define rule ownership.

[TERMINOLOGY_AND_BOUNDARIES]
<!-- Example:
- “User-visible field” means ...
- “Contract model” means ... and MUST NOT be confused with persistence schema.
- “Business state” MUST NOT be mixed with workflow status.
- "Generation Rule" means long-lived constraints enforced during artifact generation.
- "Validation Rule" means centralized audit checks that detect cross-artifact inconsistencies.
- "Hard Execution Gate" means minimum run-blocking checks required for safe execution.
-->

### Repo-Anchor Evidence Protocol

Constitution-level repository-first facts MUST define stable evidence classes, canonical baseline artifacts,
and dependency derivation policy used by downstream commands.

- Repository-first analysis is limited to three conclusions:
  - technical dependency matrix facts
  - domain/capability boundary responsibilities
  - module invocation and layering governance
- Evidence classes (hard rule):
  - **Source anchors**: source-code files/symbols for entities, boundaries, and invocation paths
  - **Engineering assembly facts**: build/module manifests for dependency and packaging conclusions
- Canonical baseline location (hard rule):
  - `.specify/memory/repository-first/technical-dependency-matrix.md`
  - `.specify/memory/repository-first/domain-boundary-responsibilities.md`
  - `.specify/memory/repository-first/module-invocation-spec.md`
  - feature-local copies are derived views only and MUST NOT override canonical semantics
- Technical dependency matrix derivation (hard rule):
  - dependency evidence MUST come from build-manifest auto-detection with deterministic priority:
    - Maven: `pom.xml`
    - Node: `package.json` (workspace-aware)
    - Python: `pyproject.toml` (plus `requirements*.txt` / lock hints when present)
    - Go: `go.mod`
  - normalize `Dependency (G:A)` as:
    - Maven: `group:artifact`
    - Node/Python/Go: `ecosystem:package_or_module`
  - `Type` values MUST be `2nd` or `3rd`
  - `Version Source` values MUST be `direct`, `dependencyManagement`, `module-dependencyManagement`, or `unresolved`
  - version divergence and `unresolved` MUST be preserved as governance signals (no silent normalization)
- Projection-boundary binding (hard rule):
  - domain/capability boundary evidence MUST come from source anchors only
  - invocation governance MUST consume dependency-governance signals from canonical dependency matrix
- Supporting-input boundary (hard rule):
  - planning artifacts, docs, tests, demos, and generated outputs are supporting context only and MUST NOT be promoted into repo semantic evidence
- Separation (hard rule):
  - `technical-dependency-matrix.md` (facts), `domain-boundary-responsibilities.md` (business boundary), and `module-invocation-spec.md` (execution constraints) are complementary and MUST NOT replace one another

## State Machine Applicability Gate

This section defines when a feature MUST include a full business lifecycle state machine,
and when a lightweight model is sufficient.

Boundary note:

- This constitution section defines long-lived applicability policy only.
- Generation-time implementation of this policy belongs to `/sdd.plan`.
- Cross-artifact compliance audit and gate decisions belong to `/sdd.analyze`.

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

If a Full FSM is used below threshold, downstream planning artifacts MUST record explicit
justification for why lightweight is insufficient.

## Constraints & Evolution Rules

This section defines long-lived constraints that guide change over time.
These rules should focus on compatibility, simplicity, and controlled evolution.

[SECTION_2_CONTENT]
<!-- Example:
- Prefer additive changes over breaking changes.
- Breaking changes MUST include explicit justification, migration plan, and rollout strategy.
- New complexity MUST be justified by concrete scenario needs.
- If a heavyweight design approach is used, document why a simpler approach is insufficient.
- Dependency boundary changes MUST update constitution fact sources first before downstream artifacts consume them.
-->

## Compliance & Review Expectations

This section defines lightweight expectations for constitution checks in downstream work.

Each expectation SHOULD state:

- **Expectation**: what should be checked
- **Where Checked**: which artifact or stage should perform the check
- **Handling**: what to do when the expectation is not met

[SECTION_3_CONTENT]
<!-- Example:
- Generation-rule boundary drift in `/sdd.specify` or `/sdd.plan` -> revise the generation artifact or source template before handoff.
- Cross-artifact inconsistency, contradiction, ambiguity, or coverage drift -> route to `/sdd.analyze` as centralized validation owner.
- Missing execution-critical prerequisites, non-consumable runtime source, or unsafe DAG closure -> block in `/sdd.tasks` or `/sdd.implement` as hard execution gate owners.
- Undocumented exception to a core principle -> document exception and decision owner.
-->

## Governance

This constitution supersedes lower-level conventions when conflicts arise.
Amendments MUST be explicit, reviewed, and reflected in downstream guidance where applicable.

[GOVERNANCE_RULES]
<!-- Example:
- All reviews MUST verify constitution compliance.
- Exceptions MUST be documented with rationale and approval.
- Amendments MUST include a summary of what changed, why it changed, and whether downstream artifacts require updates.
- Version increments MUST reflect the semantic impact of the amendment.
-->

**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFICATION_DATE] | **Last Amended**: [LAST_AMENDED_DATE]
<!-- Example: Version: 2.1.1 | Ratified: 2025-06-13 | Last Amended: 2025-07-16 -->

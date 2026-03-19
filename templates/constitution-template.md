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

<!--
Writing guidance only; do not surface this scaffold in the runtime constitution:
- Each principle should be written as an enforceable rule.
- Recommended structure per principle:
  - **Rule**: what is required or prohibited
  - **Scope**: where it applies
  - **Rationale**: why it exists
  - **Exceptions**: when deviation is allowed and how it must be documented
  - At least one principle MUST define ownership boundaries for `Generation Rule`, `Validation Rule`, and `Hard Execution Gate`.
-->

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

<!--
Writing guidance only; do not surface this scaffold in the runtime constitution:
- Include only project-critical concepts here, for example:
  - core business terms that have precise meanings
  - distinctions between user-facing concepts and internal technical representations
  - phase or layer boundaries that must not be mixed
  - terms that are commonly confused and therefore require explicit separation
  - generation/validation/execution boundary terms that define rule ownership
-->

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

Constitution-level repository-first facts MUST define stable evidence classes,
canonical baseline artifacts, and ownership boundaries used by downstream
commands.

- Repo-anchor strategy priority (hard rule):
  - evaluate and apply in strict order: `existing` -> `extended` -> `new`
  - `existing` (reuse) MUST be selected first when an existing repo-backed `path::symbol` already satisfies required semantics
  - `extended` is allowed only when reuse is insufficient and the change remains additive on the same owner/boundary (no responsibility or invocation-direction rewrite)
  - `new` is allowed only after explicit rejection evidence for both `existing` and `extended`
  - every selected `new` anchor MUST include:
    - why `existing` cannot satisfy the required semantics
    - why `extended` is insufficient or unsafe
    - target repo-backed `path::symbol` and required upstream synchronization actions
- Ownership binding for this strategy (hard rule):
  - generation commands (`/sdd.plan.*`) own recording the evaluation and selected strategy
  - `/sdd.analyze` owns compliance validation and MUST fail when `new` anchor evidence is missing
  - `/sdd.tasks` and `/sdd.implement` own execution blocking when active tuples still carry unresolved/todo anchors or missing strategy evidence
- Repository-first analysis is limited to two conclusions:
  - technical dependency matrix facts
  - module invocation and layering governance
- Evidence classes (hard rule):
  - **Source anchors**: source-code files/symbols for entities, boundaries, and invocation paths
  - **Engineering assembly facts**: build/module manifests for dependency and packaging conclusions
- Reasoning-fact minimality (hard rule):
  - downstream outputs MUST include concise reasoning facts that map
    `fact -> conclusion` (for example dependency/module reference plus why the
    rule decision follows)
  - path-level references are the default; line-level references are optional
    and SHOULD be used only when ambiguity or conflict requires precision
- Canonical baseline location (hard rule):
  - `.specify/memory/repository-first/technical-dependency-matrix.md`
  - `.specify/memory/repository-first/module-invocation-spec.md`
  - feature-local copies are derived views only and MUST NOT override canonical semantics
- Invocation-governance binding (hard rule):
  - invocation governance MUST consume dependency-governance signals from canonical dependency matrix
- Supporting-input boundary (hard rule):
  - planning artifacts, docs, tests, demos, and generated outputs are supporting context only and MUST NOT be promoted into repo semantic evidence
- Separation (hard rule):
  - `.specify/memory/repository-first/technical-dependency-matrix.md` (facts) and `.specify/memory/repository-first/module-invocation-spec.md` (execution constraints) are complementary and MUST NOT replace one another
- Detail ownership (hard rule):
  - matrix row schema, signal derivation details, and invocation row coverage
    details belong to the respective repository-first templates, not to this
    constitution section

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

## Local Execution Protocol Governance

This section defines long-lived governance for AI-local CLI execution inside
`/sdd.*` commands.

- Constitution authority (hard rule):
  - `.specify/memory/constitution.md` is the SSOT for local execution rules
  - `LOCAL_EXECUTION_PROTOCOL` is a run-local derived projection only and MUST
    NOT introduce competing policy
- Repository discovery and inspection (hard rule):
  - downstream `/sdd.*` commands MUST prefer the emitted
    `repo_search` / `repo_inspection` commands before alternates
- Python helper isolation (hard rule):
  - SDD-owned Python helper execution MUST use the `specify-cli` tool runtime
    exposed by `LOCAL_EXECUTION_PROTOCOL.python.runner_cmd`
  - do not call user-managed `python`, `python3`, `py`, project-local virtual
    environments, or repo-local `uv run python` for SDD helper execution
- Safe degradation (hard rule):
  - if a projected capability is unavailable, downstream commands MAY downgrade
    helper-dependent fast paths to warnings or null bootstrap packets, but MUST
    NOT invent substitute CLIs
- High-risk prohibitions (hard rule):
  - `/sdd.*` commands MUST NOT install missing tools, mutate `PATH`, or switch
    package managers/interpreters during a run
- Ownership binding (hard rule):
  - `specify-cli` owns provisioning the controlled Python runtime entry
  - prerequisite scripts emit the run-local projection packet
  - downstream command templates and agent guidance consume that packet without
    redefining competing execution policy

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

<!--
Writing guidance only; do not surface this scaffold in the runtime constitution:
- Each expectation SHOULD state:
  - **Expectation**: what should be checked
  - **Where Checked**: which artifact or stage should perform the check
  - **Handling**: what to do when the expectation is not met
-->

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

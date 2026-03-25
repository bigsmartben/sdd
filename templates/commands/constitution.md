---
description: Update the project constitution and repository-first baselines under .specify/memory/.
handoffs: 
  - label: Build Specification
    agent: sdd.specify
    prompt: Create the feature specification based on the updated constitution.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Update or initialize the project constitution and repository-first baselines under `.specify/memory/`.
Use `.specify/templates/constitution-template.md` only.

`/sdd.constitution` owns:
- Long-lived normative rules and ownership boundaries.
- Unified Repository-First Gate Protocol (URFGP) authority.
- Repository-First baseline generation (Dependency Matrix / Module Invocation Spec).

## Governance / Authority

- **Authority rule**: `constitution.md` is the Single Source of Truth for local execution policy.
- **Protocol rule**: **Unified Repository-First Gate Protocol (URFGP)** is the shared authority.
- **Stage boundary rule**: Constitution defines boundaries; commands implement them.

## Allowed Inputs

- `.specify/templates/constitution-template.md` (structure)
- `.specify/memory/constitution.md` (existing state)
- Repository manifests (pom.xml, package.json, pyproject.toml, go.mod)
- If `repo-first-affecting`, `.specify/templates/technical-dependency-matrix-template.md` (dependency baseline structure)
- If `repo-first-affecting`, `.specify/templates/module-invocation-spec-template.md` (invocation baseline structure)
- For repo-first refresh, each artifact MUST be projected from its corresponding template; MUST NOT synthesize structure from constitution prose alone.

**Prohibited**: `plan.md` queue state, `tasks.md`, or ad hoc CLI guesses.

## Reasoning Order

1. **Impact Mapping**: Identify if the change is `governance-only`, `template-affecting`, or `repo-first-affecting`.
2. **Constitution Update**: Amend `constitution.md` with semantic versioning (MAJOR/MINOR/PATCH).
3. **Downstream Alignment**: Update impacted alignment families only (skip if governance-only).
4. **Baseline Refresh**: Reproject both repo-first artifacts from template authority in every run.

## Artifact Quality Contract

- Must: output a durable governance artifact senior maintainers can rely on.
- Strictly: keep rules normative, long-lived, and the single shortest source of truth.
- **Normative Language**: Use `MUST`/`MUST NOT`/`SHOULD`.
- **Strategy Priority**: Preserve `existing -> extended -> new` for repo-anchors.
- **RFEB Format**: Standardize repository-first output evidence bundle format.
- **Prohibited**: Process explainers, template tutorials, or patch logs in the final artifact.

## Repo-First Baseline Pipeline (Mandatory)

1. **Manifest Detection**: Process Maven, Node, Python, and Go manifests.
2. **Template Authority**: Read `.specify/templates/technical-dependency-matrix-template.md` and `.specify/templates/module-invocation-spec-template.md` for structure authority.
3. **Canonical Paths**: Output only to `.specify/memory/repository-first/`.
4. **Generation Order**: Generate `technical-dependency-matrix.md` first, then `module-invocation-spec.md`; invocation governance MUST reference existing matrix facts/`SIG-*` rows only.
5. **Traceability**: Emit `fact -> conclusion` reasoning for all matrix rows.
6. **Matrix Completeness**: Dependency matrix MUST be exhaustive for the filtered product/runtime dependency set and MUST NOT emit highlight-only subsets.
7. **2nd/3rd Classification Completeness**: Organization-owned or organization-coordinated dependencies not produced in-repo and classified as `2nd` MUST NOT be omitted.
8. **Refined Invocation**: Directions MUST cover concrete first-party module edges.

## Writeback Contract

- MUST write exactly three files in every run:
  - `.specify/memory/constitution.md`
  - `.specify/memory/repository-first/technical-dependency-matrix.md`
  - `.specify/memory/repository-first/module-invocation-spec.md`
- **MUST NOT** modify `plan.md`, `tasks.md`, or any spec artifact.

## Stop Conditions

Stop immediately if:
1. `.specify/templates/constitution-template.md` is missing or unreadable.
2. Repository manifests cannot be located.

## Handoff Decision

Emit a **Sync Impact Report** (HTML comment) plus:
- `Next Command`: `/sdd.specify` or context-derived.
- `Decision Basis`: Constitution version and impact summary.
- `Ready/Blocked`: Local readiness only.

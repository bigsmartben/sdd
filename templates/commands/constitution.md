---
description: Update the project constitution at .specify/memory/constitution.md.
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

Update or initialize the project constitution at `.specify/memory/constitution.md`.
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

**Prohibited**: `plan.md` queue state, `tasks.md`, or ad hoc CLI guesses.

## Reasoning Order

1. **Impact Mapping**: Identify if the change is `governance-only`, `template-affecting`, or `repo-first-affecting`.
2. **Constitution Update**: Amend `constitution.md` with semantic versioning (MAJOR/MINOR/PATCH).
3. **Downstream Alignment**: Update impacted alignment families only (skip if governance-only).
4. **Baseline Refresh**: Reproject repo-first artifacts only when manifests change or `repo-first-affecting`.

## Artifact Quality Contract

- Must: output a durable governance artifact senior maintainers can rely on.
- Strictly: keep rules normative, long-lived, and the single shortest source of truth.
- **Normative Language**: Use `MUST`/`MUST NOT`/`SHOULD`.
- **Strategy Priority**: Preserve `existing -> extended -> new` for repo-anchors.
- **RFEB Format**: Standardize repository-first output evidence bundle format.
- **Prohibited**: Process explainers, template tutorials, or patch logs in the final artifact.

## Repo-First Baseline Pipeline (Mandatory)

1. **Manifest Detection**: Process Maven, Node, Python, and Go manifests.
2. **Canonical Paths**: Output only to `.specify/memory/repository-first/`.
3. **Traceability**: Emit `fact -> conclusion` reasoning for all matrix rows.
4. **Refined Invocation**: Directions MUST cover concrete first-party module edges.

## Writeback Contract

- Write to `.specify/memory/constitution.md` only.
- Refresh `.specify/memory/repository-first/*.md` only when the impact mapping identifies a `repo-first-affecting` change.
- **MUST NOT** modify `plan.md`, `tasks.md`, or any spec artifact.

## Stop Conditions

Stop immediately if:
1. `.specify/templates/constitution-template.md` is missing or unreadable.
2. Repository manifests cannot be located and the change is `repo-first-affecting`.

## Handoff Decision

Emit a **Sync Impact Report** (HTML comment) plus:
- `Next Command`: `/sdd.specify` or context-derived.
- `Decision Basis`: Constitution version and impact summary.
- `Ready/Blocked`: Local readiness only.

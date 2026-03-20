# Technical Dependency Matrix: [PROJECT]

**Projection Type**: Repository-First Projection  
**Canonical Path**: `.specify/memory/repository-first/technical-dependency-matrix.md`  
**Primary Evidence**: Engineering assembly facts only (build-manifest auto-detection)

Use this artifact to record 2nd/3rd-party dependency facts only.
In-repo first-party module-to-module dependencies MUST NOT be modeled here.
Exhaustiveness applies only after filtering out in-repo first-party module coordinates.

## Build-Manifest Detection Summary

Record detection outcome in deterministic priority:

1. Maven: `pom.xml`
2. Node: `package.json` (workspace-aware)
3. Python: `pyproject.toml` (plus `requirements*.txt` / lock hints when present)
4. Go: `go.mod`

| Ecosystem | Manifest(s) Found | Detection Status | Notes |
|-----------|-------------------|------------------|-------|
| [maven/node/python/go] | [path list or `none`] | [detected/not-detected] | [workspace/lock hints if any] |

## Evidence Rules

- Dependency facts MUST come from detected build manifests only.
- Source-code symbols, planning artifacts, and helper docs MUST NOT be used to prove dependency declarations.
- Before row emission, classify each dependency declaration as exactly one of:
  - `in_repo_first_party_module`
  - `external_second_party`
  - `third_party`
- Coordinates matching modules produced inside the current repository MUST be classified as `in_repo_first_party_module` and excluded from this artifact.
- The dependency matrix MUST be exhaustive for the filtered product/runtime dependency set; do not emit highlight-only subsets.
- Normalize `Dependency (G:A)` as:
  - Maven: `group:artifact`
  - Node/Python/Go: `ecosystem:package_or_module`
- `Type` MUST be either `2nd` or `3rd`.
- Classify organization-owned or organization-coordinated packages not produced inside the current repository as `2nd`; external ecosystem packages as `3rd`.
- `Version Source` MUST be one of: `direct`, `dependencyManagement`, `module-dependencyManagement`, `unresolved`.
- `Evidence` MUST be a minimal fact reference that supports the row conclusion.
  Path-level references are sufficient by default; include line-level precision
  only when ambiguity/conflict requires it.
- If a dependency declaration omits a local version but resolves from module,
  parent, or ancestor dependency management, explain the provider class in
  `Version Source` and keep `Evidence` concise.
- Tooling-only manifests that are outside the product/runtime build surface SHOULD stay in detection notes and MUST NOT displace product dependency rows.
- Keep version divergence and `unresolved` values visible as governance signals; do not silently normalize them.
- Mark a row `unresolved` only when its effective version cannot be resolved from the declaration, the current module, or the detected in-repo ancestor manifest chain.
- Every material version-source mix, version divergence, or unresolved signal MUST cite enough facts for review (manifest path minimum).

## Dependency Matrix

Emit one row per normalized dependency usage found in detected product/runtime manifests.
Do not collapse multiple modules, version sources, scopes, or evidence locations into one row.

| Dependency (G:A) | Type | Version | Scope | Version Source | Used By Module | Evidence |
|------------------|------|---------|-------|----------------|----------------|----------|
| [maven:group:artifact or ecosystem:package] | [2nd/3rd] | [x.y.z or `unresolved`] | [compile/runtime/test/provided/import/peer/dev/optional] | [direct/dependencyManagement/module-dependencyManagement/unresolved] | [module-a] | [manifest path; line refs when needed] |

## Signal Derivation Rules

- Emit `version-source-mix` only when the same dependency has 2 or more distinct `Version Source` values across emitted rows.
- Emit `version-divergence` only when the same dependency has 2 or more distinct effective versions across emitted rows.
- Emit `unresolved` only when at least one emitted row has `Version Source = unresolved` or `Version = unresolved`.
- Every `SIG-*` row MUST be derivable from emitted matrix rows only.

## Version Divergence & Unresolved Signals

Record only material governance signals that downstream invocation governance must consume.

| Signal ID | Dependency (G:A) | Signal Type | Affected Modules | Evidence | Handling Note |
|-----------|------------------|-------------|------------------|----------|---------------|
| [SIG-001] | [ecosystem:package] | [version-divergence / version-source-mix / unresolved] | [module-a, module-b] | [manifest paths or concise fact refs] | [Rule impact for module invocation governance] |

## Signal Consistency Note

- Keep each `SIG-*` entry explainable from emitted rows (`fact -> conclusion`).
- If ambiguity/conflict remains after path-level evidence, add line-level precision for the affected facts only.

## Boundary Notes

- This artifact is dependency-fact oriented; it does not define component/domain responsibilities.
- This artifact does not define allowed/forbidden invocation directions; those rules belong in `.specify/memory/repository-first/module-invocation-spec.md`.

# Technical Dependency Matrix: [PROJECT]

**Projection Type**: Repository-First Projection  
**Canonical Path**: `.specify/memory/repository-first/technical-dependency-matrix.md`  
**Primary Evidence**: Engineering assembly facts only (build-manifest auto-detection)

Use this artifact to record 2nd/3rd-party dependency facts only.
In-repo first-party module-to-module dependencies MUST NOT be modeled here.

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
- The dependency matrix MUST be exhaustive for detected product/runtime manifests; do not emit highlight-only subsets.
- Normalize `Dependency (G:A)` as:
  - Maven: `group:artifact`
  - Node/Python/Go: `ecosystem:package_or_module`
- `Type` MUST be either `2nd` or `3rd`.
- Classify organization-owned or organization-coordinated packages as `2nd`; external ecosystem packages as `3rd`.
- `Version Source` MUST be one of: `direct`, `dependencyManagement`, `module-dependencyManagement`, `unresolved`.
- Tooling-only manifests that are outside the product/runtime build surface SHOULD stay in detection notes and MUST NOT displace product dependency rows.
- Keep version divergence and `unresolved` values visible as governance signals; do not silently normalize them.
- Every material version-source mix, version divergence, or unresolved signal MUST cite manifest paths and line refs.

## Dependency Matrix

Emit one row per normalized dependency usage found in detected product/runtime manifests.
Do not collapse multiple modules, version sources, scopes, or evidence locations into one row.

| Dependency (G:A) | Type | Version | Scope | Version Source | Used By Module | Evidence |
|------------------|------|---------|-------|----------------|----------------|----------|
| [maven:group:artifact or ecosystem:package] | [2nd/3rd] | [x.y.z or `unresolved`] | [compile/runtime/test/provided/import/peer/dev/optional] | [direct/dependencyManagement/module-dependencyManagement/unresolved] | [module-a] | [manifest path + line refs] |

## Version Divergence & Unresolved Signals

Record only material governance signals that downstream invocation governance must consume.

| Signal ID | Dependency (G:A) | Signal Type | Affected Modules | Evidence | Handling Note |
|-----------|------------------|-------------|------------------|----------|---------------|
| [SIG-001] | [ecosystem:package] | [version-divergence / version-source-mix / unresolved] | [module-a, module-b] | [manifest paths + line refs] | [Rule impact for module invocation governance] |

## Boundary Notes

- This artifact is dependency-fact oriented; it does not define component/domain responsibilities.
- This artifact does not define allowed/forbidden invocation directions; those rules belong in `.specify/memory/repository-first/module-invocation-spec.md`.

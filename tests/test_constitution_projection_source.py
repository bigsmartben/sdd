from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_constitution_template_defines_owner_boundaries_and_terms():
    content = read("templates/constitution-template.md")

    assert "## Governance & Terminology" in content
    assert '"URFGP"** (Unified Repository-First Gate Protocol)' in content
    assert '"RFEB"** (Repository-First Evidence Bundle)' in content

    assert "### Repo-Anchor Evidence Protocol" in content
    assert ".specify/memory/repository-first/technical-dependency-matrix.md" in content
    assert ".specify/memory/repository-first/module-invocation-spec.md" in content
    assert "evaluate and apply in strict order: `existing` -> `extended` -> `new`" in content
    assert "`new` is only valid when both `existing` and `extended` are explicitly rejected with evidence" in content

    assert "## Local Execution Protocol Governance" in content
    assert "SSOT for local execution rules" in content
    assert "`specify-cli` tool runtime" in content
    assert "Installing missing tools, mutating `PATH`, or switching package managers during a run" in content
    assert content.index("## Governance & Terminology") < content.index("### Repo-Anchor Evidence Protocol")
    assert content.index("### Repo-Anchor Evidence Protocol") < content.index("## Local Execution Protocol Governance")


def test_constitution_command_blocks_lint_detail_embedding_and_dual_authority_expansion():
    content = read("templates/commands/constitution.md")

    assert "Use `.specify/templates/constitution-template.md` as constitution structure authority." in content
    assert "Use `.specify/templates/technical-dependency-matrix-template.md` and `.specify/templates/module-invocation-spec-template.md` as repository-first structure authority." in content
    assert "`/sdd.constitution` owns:" in content
    assert "Unified Repository-First Gate Protocol (URFGP) authority." in content
    assert "Constitution defines boundaries; commands implement them." in content


def test_constitution_command_groups_alignment_work_and_avoids_redundant_restatements():
    content = read("templates/commands/constitution.md")

    assert "**Impact Mapping**" in content
    assert "Identify if the change is `governance-only`, `template-affecting`, or `repo-first-affecting`" in content
    assert "**Downstream Alignment**: Update impacted alignment families only (skip if governance-only)." in content
    assert "MUST write exactly three files in every run:" in content
    assert "**MUST NOT** modify `plan.md`, `tasks.md`, or any spec artifact." in content


def test_constitution_command_uses_active_agent_command_directory_guidance():
    content = read("templates/commands/constitution.md")

    assert "## Allowed Inputs" in content
    assert "`.specify/templates/constitution-template.md` (structure)" in content
    assert "`.specify/memory/constitution.md` (existing state)" in content
    assert "Repository manifests (pom.xml, package.json, pyproject.toml, go.mod)" in content
    assert "`.specify/templates/technical-dependency-matrix-template.md` (dependency baseline structure)" in content
    assert "`.specify/templates/module-invocation-spec-template.md` (invocation baseline structure)" in content
    assert "For repo-first refresh, each artifact MUST be projected from its corresponding template; MUST NOT synthesize structure from constitution prose alone." in content
    assert "**Prohibited**: `plan.md` queue state, `tasks.md`, or ad hoc CLI guesses." in content


def test_constitution_command_uses_current_constitution_state_not_placeholder_premise():
    content = read("templates/commands/constitution.md")

    assert "Update or initialize the project constitution and repository-first baselines under `.specify/memory/`." in content
    assert ".specify/templates/constitution-template.md" in content
    assert "Stop immediately if:" in content
    assert ".specify/templates/technical-dependency-matrix-template.md" in content
    assert ".specify/templates/module-invocation-spec-template.md" in content
    assert ".specify/memory/constitution.md" in content
    assert ".specify/memory/repository-first/technical-dependency-matrix.md" in content
    assert ".specify/memory/repository-first/module-invocation-spec.md" in content
    assert "This file is a TEMPLATE containing placeholder tokens" not in content


def test_constitution_command_owns_repository_first_baseline_pipeline():
    content = read("templates/commands/constitution.md")

    assert "Repo-First Baseline Pipeline (Mandatory)" in content
    assert ".specify/memory/repository-first/" in content
    assert "Manifest Detection" in content
    assert "Template Authority" in content
    assert "Canonical Paths" in content
    assert "Generation Order" in content
    assert "Traceability" in content
    assert "Matrix Completeness" in content
    assert "2nd/3rd Classification Completeness" in content
    assert "Refined Invocation" in content
    assert "Generate `technical-dependency-matrix.md` first, then `module-invocation-spec.md`" in content
    assert "invocation governance MUST reference existing matrix facts/`SIG-*` rows only" in content
    assert "Dependency matrix MUST be exhaustive for the filtered product/runtime dependency set and MUST NOT emit highlight-only subsets." in content
    assert "Organization-owned or organization-coordinated dependencies not produced in-repo and classified as `2nd` MUST NOT be omitted." in content


def test_constitution_command_defines_runtime_fast_path_and_bounded_reads():
    content = read("templates/commands/constitution.md")

    assert "Impact Mapping" in content
    assert "`governance-only`" in content
    assert "`template-affecting`" in content
    assert "`repo-first-affecting`" in content
    assert "Baseline Refresh" in content
    assert "Reproject both repo-first artifacts from template authority in every run." in content


def test_constitution_command_enforces_repo_anchor_priority_and_ownership_split():
    content = read("templates/commands/constitution.md")

    assert "**Strategy Priority**: Preserve `existing -> extended -> new` for repo-anchors." in content
    assert "**Protocol rule**: **Unified Repository-First Gate Protocol (URFGP)** is the shared authority." in content
    assert "Repository-First baseline generation (Dependency Matrix / Module Invocation Spec)." in content
    assert "Unified Repository-First Gate Protocol (URFGP)" in content
    assert "**RFEB Format**: Standardize repository-first output evidence bundle format." in content


def test_repository_first_templates_require_complete_and_explainable_outputs():
    matrix = read("templates/technical-dependency-matrix-template.md")
    invocation = read("templates/module-invocation-spec-template.md")

    assert "The dependency matrix MUST be exhaustive for the filtered product/runtime dependency set; do not emit highlight-only subsets." in matrix
    assert "Exhaustiveness applies only after filtering out in-repo first-party module coordinates." in matrix
    assert "Before row emission, classify each dependency declaration as exactly one of:" in matrix
    assert "Coordinates matching modules produced inside the current repository MUST be classified as `in_repo_first_party_module` and excluded from this artifact." in matrix
    assert "Classify organization-owned or organization-coordinated packages not produced inside the current repository as `2nd`; external ecosystem packages as `3rd`." in matrix
    assert "Tooling-only manifests that are outside the product/runtime build surface SHOULD stay in detection notes" in matrix
    assert "Every material version-source mix, version divergence, or unresolved signal MUST cite enough facts for review (manifest path minimum)." in matrix
    assert "Emit one row per normalized dependency usage found in detected product/runtime manifests." in matrix
    assert "Do not collapse multiple modules, version sources, scopes, or evidence locations into one row." in matrix
    assert "`Evidence` MUST be a minimal fact reference that supports the row conclusion." in matrix
    assert "Path-level references are sufficient by default; include line-level precision" in matrix
    assert "If a dependency declaration omits a local version but resolves from module," in matrix
    assert "Mark a row `unresolved` only when its effective version cannot be resolved from the declaration, the current module, or the detected in-repo ancestor manifest chain." in matrix
    assert "| Dependency (G:A) | Type | Version | Scope | Version Source | Used By Module | Evidence |" in matrix
    assert "Used By Modules" not in matrix
    assert "## Signal Derivation Rules" in matrix
    assert "Emit `version-source-mix` only when the same dependency has 2 or more distinct `Version Source` values across emitted rows." in matrix
    assert "Emit `version-divergence` only when the same dependency has 2 or more distinct effective versions across emitted rows." in matrix
    assert "Emit `unresolved` only when at least one emitted row has `Version Source = unresolved` or `Version = unresolved`." in matrix
    assert "Every `SIG-*` row MUST be derivable from emitted matrix rows only." in matrix
    assert "[version-divergence / version-source-mix / unresolved]" in matrix
    assert "## Signal Consistency Note" in matrix
    assert "Keep each `SIG-*` entry explainable from emitted rows (`fact -> conclusion`)." in matrix
    assert "add line-level precision for the affected facts only" in matrix

    assert "Allowed and forbidden direction tables MUST cover the concrete first-party module edges found in the target runtime repo." in invocation
    assert "Do not collapse unmatched edges into broad grouped rows unless every covered edge shares the same rule and rationale." in invocation
    assert "Every observed first-party cross-module edge MUST be represented as allowed or forbidden." in invocation
    assert "| From Module | To Module | Layer View | Rule | Rationale |" in invocation
    assert "| From Module | To Module | Layer View | Rule | Violation Risk |" in invocation
    assert "From Module Layer" not in invocation
    assert "To Module Layer" not in invocation
    assert "Every governance rule MUST reference an existing `SIG-*` row from the matrix or an explicit matrix fact summary; do not emit speculative future-signal rows." in invocation
    assert "Use concise reasoning facts (`trigger fact -> governance action`)" in invocation
    assert "[existing `SIG-*` row]" in invocation
    assert "SIG-002" not in invocation
    assert "SIG-003" not in invocation

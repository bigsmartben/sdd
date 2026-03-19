from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_constitution_template_defines_owner_boundaries_and_terms():
    content = read("templates/constitution-template.md")

    assert (
        "At least one principle MUST define ownership boundaries for `Generation Rule`, `Validation Rule`, and `Hard Execution Gate`."
        in content
    )
    assert '"Generation Rule" means long-lived constraints enforced during artifact generation.' in content
    assert '"Validation Rule" means centralized audit checks that detect cross-artifact inconsistencies.' in content
    assert '"Hard Execution Gate" means minimum run-blocking checks required for safe execution.' in content

    assert "### Dependency Matrix Baseline" not in content
    assert "## Project-Level Fact Sources" not in content
    assert "### Repository-First Principle" not in content
    assert "### Ownership Boundary Baseline" not in content
    assert "### Repo-Anchor Evidence Protocol" in content
    assert ".specify/memory/repository-first/technical-dependency-matrix.md" in content
    assert ".specify/memory/repository-first/module-invocation-spec.md" in content
    assert "Reasoning-fact minimality (hard rule):" in content
    assert "downstream outputs MUST include concise reasoning facts that map" in content
    assert "path-level references are the default; line-level references are optional" in content
    assert "Detail ownership (hard rule):" in content
    assert "matrix row schema, signal derivation details, and invocation row coverage" in content
    assert "evaluate and apply in strict order: `existing` -> `extended` -> `new`" in content
    assert "`existing` (reuse) MUST be selected first" in content
    assert "`new` is allowed only after explicit rejection evidence for both `existing` and `extended`" in content
    assert "generation commands (`/sdd.plan.*`) own recording the evaluation and selected strategy" in content
    assert "`/sdd.analyze` owns compliance validation and MUST fail when `new` anchor evidence is missing" in content
    assert "`/sdd.tasks` and `/sdd.implement` own execution blocking" in content
    assert "/sdd.analyze" in content
    assert "/sdd.tasks" in content
    assert "/sdd.implement" in content
    assert "## Local Execution Protocol Governance" in content
    assert "SSOT for local execution rules" in content
    assert "`specify-cli` tool runtime" in content
    assert "MUST NOT install missing tools, mutate `PATH`, or switch" in content
    assert "Writing guidance only; do not surface this scaffold in the runtime constitution:" in content
    assert content.index("## Terminology & Boundary Definitions") < content.index("### Repo-Anchor Evidence Protocol")
    assert content.index("### Repo-Anchor Evidence Protocol") < content.index("## State Machine Applicability Gate")
    assert content.index("## State Machine Applicability Gate") < content.index("## Local Execution Protocol Governance")


def test_constitution_command_blocks_lint_detail_embedding_and_dual_authority_expansion():
    content = read("templates/commands/constitution.md")

    assert "Adding or materially expanding generation/validation/execution ownership boundaries is always `MINOR`." in content
    assert "do not embed mechanical lint catalog details" in content
    assert "does not include lint-catalog implementation details" in content
    assert "Do not duplicate one normative rule into competing expansions across multiple command templates" in content


def test_constitution_command_groups_alignment_work_and_avoids_redundant_restatements():
    content = read("templates/commands/constitution.md")

    assert "Review and refresh impacted artifact families only; avoid mechanical full-repo rewrites of unchanged downstream files." in content
    assert "Prefer targeted references over restating the same rule text across multiple downstream templates." in content
    assert "command templates and `LOCAL_EXECUTION_PROTOCOL` packets are derived execution views" in content
    assert "Keep this report delta-oriented; do not restate unchanged template inventories or canonical baseline details beyond status." in content
    assert "reference the Sync Impact Report instead of restating it" in content


def test_constitution_command_uses_active_agent_command_directory_guidance():
    content = read("templates/commands/constitution.md")

    assert "read only impacted command files in the active agent command directory" in content
    assert ".roo/commands/*.md" in content
    assert ".claude/commands/*.md" in content
    assert ".github/agents/*.agent.md" in content
    assert ".gemini/commands/*.toml" in content
    assert "If `templates/commands/*.md` exists in this repository, treat it as mirror/reference and update only impacted files." in content
    assert "Runtime template authority path is `.specify/templates/`" in content
    assert "Runtime workspace rule" in content


def test_constitution_command_uses_current_constitution_state_not_placeholder_premise():
    content = read("templates/commands/constitution.md")

    assert "Treat the current file as the authoritative working constitution" in content
    assert ".specify/templates/constitution-template.md" in content
    assert "stop and report the blocker" in content
    assert "Do not substitute `templates/constitution-template.md` or any other template location." in content
    assert "do not force a template-token rewrite pass" in content
    assert "This file is a TEMPLATE containing placeholder tokens" not in content
    assert "This command runs against the runtime workspace only." in content
    assert "Treat the target runtime repo and the Spec Kit source repo as different workspaces." not in content


def test_constitution_command_owns_repository_first_baseline_pipeline():
    content = read("templates/commands/constitution.md")

    assert "Repository-first global baseline pipeline (mandatory)" in content
    assert ".specify/memory/repository-first/" in content
    assert "technical-dependency-matrix.md" in content
    assert "module-invocation-spec.md" in content
    assert "Detect build manifests from repo root using deterministic priority" in content
    assert "Maven: `pom.xml`" in content
    assert "Node: `package.json`" in content
    assert "Python: `pyproject.toml`" in content
    assert "Go: `go.mod`" in content
    assert "never read or stat bare projection filenames from repo root" in content
    assert "`created`" in content
    assert "`updated`" in content
    assert "`unchanged`" in content
    assert "`deleted`" in content
    assert "Matrix rows MUST be exhaustive for the filtered product/runtime dependency set; do not emit highlight-only subsets." in content
    assert "Emit one row per dependency usage; do not collapse multiple modules, scopes, version sources, or evidence locations into one summary row." in content
    assert "Preserve version divergence, version-source-mix, and `unresolved` as governance signals" in content
    assert "Keep supporting evidence explainable as `fact -> conclusion`" in content
    assert "Every dependency-governance signal MUST be derivable from emitted matrix rows only." in content
    assert "Detailed matrix row schema, allowed value vocabularies, and signal derivation mechanics are owned by `.specify/templates/technical-dependency-matrix-template.md`" in content
    assert "Allowed/forbidden direction tables MUST cover the concrete first-party module edges found in the target runtime repo." in content
    assert "Use concrete module-to-module rows as the primary representation; layer summaries are optional metadata only." in content
    assert "do not emit speculative future-signal rows" in content
    assert "Every dependency-governance rule MUST reference an existing `SIG-*` row (or explicit matrix fact summary)" in content
    assert "Invocation row schema and field-level constraints are owned by `.specify/templates/module-invocation-spec-template.md`" in content


def test_constitution_command_defines_runtime_fast_path_and_bounded_reads():
    content = read("templates/commands/constitution.md")

    assert "Build one run-local **change impact map** before broad reads" in content
    assert "`governance-only`" in content
    assert "`template-affecting`" in content
    assert "`repo-first-affecting`" in content
    assert "Resolve impacted families from the change impact map first, then read/update only those families." in content
    assert "Do not run directory-wide or repository-wide exploratory scans" in content
    assert "Repository-first fast path gate (evaluate before regeneration)" in content
    assert "If no trigger is true, keep canonical baseline files as-is and mark each artifact `unchanged` without template re-render." in content
    assert "Apply a **bounded evidence budget** for this run" in content
    assert "Runtime guidance docs (`README.md`, `docs/quickstart.md`, agent docs) are **opt-in by trigger** only" in content
    assert "Keep runtime output concise: no unchanged-file inventories" in content


def test_constitution_command_enforces_repo_anchor_priority_and_ownership_split():
    content = read("templates/commands/constitution.md")

    assert "Ensure `Repo-Anchor Evidence Protocol` keeps the strict strategy priority `existing -> extended -> new`." in content
    assert "Ensure every `new` anchor policy statement includes mandatory rejection evidence requirements for `existing` and `extended`." in content
    assert "Keep command ownership boundaries explicit for repo-anchor strategy:" in content
    assert "`/sdd.plan.*` records strategy selection evidence" in content
    assert "`/sdd.analyze` validates `new`-anchor evidence and fails when missing" in content
    assert "`/sdd.tasks` and `/sdd.implement` block execution when active tuples remain unresolved or missing required strategy evidence" in content
    assert "Repo-anchor strategy wording preserves strict priority semantics (`existing -> extended -> new`) and explicit rejection-evidence requirements for `new`." in content
    assert "Unified Repository-First Gate Protocol (`URFGP`)" in content
    assert "/sdd.plan`, `/sdd.tasks`, `/sdd.implement`, and `/sdd.analyze` MUST reference `URFGP`" in content
    assert "Repository-First Evidence Bundle (`RFEB`)" in content
    assert "`source_refs`" in content
    assert "`signal_ids` (`SIG-*`" in content
    assert "`module_edge_ids`" in content


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

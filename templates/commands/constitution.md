---
description: Create or update the project constitution from interactive or provided principle inputs, maintaining project-level fact sources and syncing dependent templates.
handoffs: 
  - label: Build Specification
    agent: sdd.specify
    prompt: Implement the feature specification based on the updated constitution. I want to build...
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

You are updating the project constitution at `.specify/memory/constitution.md`. Treat the current file as the authoritative working constitution and amend it in-place based on user intent and governance rules.

**Runtime template path rule**: If `.specify/memory/constitution.md` does not exist yet, initialize it from `.specify/templates/constitution-template.md` first. If that runtime template is missing or non-consumable when initialization is required, stop and report the blocker. Do not substitute `templates/constitution-template.md` or any other template location. In the Spec Kit source repository, `templates/constitution-template.md` is the source mirror of that runtime template.
**Source/runtime boundary rule**: Treat the target runtime repo and the Spec Kit source repo as different workspaces. In a runtime repo, operate on `.specify/memory/**` and `.specify/templates/**`. When editing the Spec Kit source repo directly, edit `templates/**`, command mirrors, scripts, and tests only; do not create, inspect, or reconcile `.specify/memory/**` as if it were runtime output.

Follow this execution flow:

1. Load the existing constitution at `.specify/memory/constitution.md`.
   - If this run initialized the file from template, identify placeholder tokens of the form `[ALL_CAPS_IDENTIFIER]` and resolve them.
   - If the file already existed, treat it as live governance content and amend only the required deltas; do not force a template-token rewrite pass.
   **IMPORTANT**: The user might require less or more principles than the ones used in the template. If a number is specified, respect that - follow the general template shape while preserving existing ratification history unless explicitly changed.

2. Collect/derive required updates:
   - If initialized from template in this run, collect values for placeholder fields.
   - If amending an existing constitution, collect only changed principle/governance values and keep untouched sections stable.
   - If user input (conversation) supplies a value, use it.
   - Otherwise infer from existing repo context (README, docs, prior constitution versions if embedded).
   - For governance dates: `RATIFICATION_DATE` is the original adoption date (if unknown ask or mark TODO), `LAST_AMENDED_DATE` is today if changes are made, otherwise keep previous.
   - `CONSTITUTION_VERSION` must increment according to semantic versioning rules:
     - MAJOR: Backward incompatible governance/principle removals or redefinitions.
     - MINOR: New principle/section added or materially expanded guidance.
     - PATCH: Clarifications, wording, typo fixes, non-semantic refinements.
     - Adding or materially expanding generation/validation/execution ownership boundaries is always `MINOR`.
   - If version bump type ambiguous, propose reasoning before finalizing.
   - Build one run-local **change impact map** before broad reads:
     - `governance-only`: dates/version text/rationale clarifications with no downstream rule impact
     - `template-affecting`: principle/rule wording that changes downstream command or template behavior
     - `repo-first-affecting`: repository-first dependency/invocation evidence or governance-rule changes
   - Use this impact map to drive all follow-up reads/updates. Default to the smallest affected scope.
   - Apply a **bounded evidence budget** for this run:
     - Start with constitution file + only directly impacted files.
     - Read at section/slice level first; avoid whole-file replay unless a targeted slice is insufficient.
     - Hard cap broad context expansion to files required by active impact classes; do not expand "just in case".

3. Draft the updated constitution content:
   - For newly initialized files, replace every placeholder with concrete text (no bracketed tokens left except intentionally retained template slots that the project has chosen not to define yet—explicitly justify any left).
   - For existing files, preserve unaffected text and avoid mechanical full-template rewrites.
   - Preserve heading hierarchy and comments can be removed once replaced unless they still add clarifying guidance.
   - Do not carry visible template teaching text into the final markdown; any remaining scaffold guidance must stay inside HTML comments only.
   - Ensure each Principle section: succinct name line, paragraph (or bullet list) capturing non‑negotiable rules, explicit rationale if not obvious.
   - Ensure Governance section lists amendment procedure, versioning policy, and compliance review expectations.
   - Ensure `Repo-Anchor Evidence Protocol` keeps the strict strategy priority `existing -> extended -> new`.
   - Ensure every `new` anchor policy statement includes mandatory rejection evidence requirements for `existing` and `extended`.

4. Fact-source propagation and redundancy control:
   - Treat `.specify/memory/constitution.md` as the authoritative project-level rule source.
   - Treat `.specify/memory/constitution.md` as the authoritative project-level fact source. Any summaries, extracted rule lists, or downstream restatements of constitution content are derived views only and MUST be refreshed when constitution facts change.
   - Constitution content MUST stay at long-lived rule/terminology/ownership-boundary level; do not embed mechanical lint catalog details (rule IDs, regex patterns, script flags, payload schemas).
   - Runtime template authority path is `.specify/templates/`; when editing Spec Kit source directly, use the `templates/` mirror for the same files.
   - Review and refresh impacted artifact families only; avoid mechanical full-repo rewrites of unchanged downstream files.
   - Prefer targeted references over restating the same rule text across multiple downstream templates. When a downstream command or template only needs the constitution as authority, keep the downstream wording brief and aligned instead of cloning full rule prose.
   - Keep command ownership boundaries explicit for repo-anchor strategy:
     - `/sdd.plan.*` records strategy selection evidence
     - `/sdd.analyze` validates `new`-anchor evidence and fails when missing
     - `/sdd.tasks` and `/sdd.implement` block execution when active tuples remain unresolved or missing required strategy evidence
   - Required alignment families:
     - Planning control plane template: Read `.specify/templates/plan-template.md` and ensure any "Constitution Check" or rules align with updated principles.

- Planning-stage templates: Read the planning-stage templates in `.specify/templates/` (`research-template.md`, `data-model-template.md`, `test-matrix-template.md`, and `contract-template.md`) and ensure they reflect the updated principles and stage boundaries.
  - Feature/task templates: Read `.specify/templates/spec-template.md` for scope/requirements alignment and `.specify/templates/tasks-template.md` for principle-driven task categorization changes (for example observability, versioning, testing discipline).
  - Repository-first projection templates: Read `.specify/templates/technical-dependency-matrix-template.md` and `.specify/templates/module-invocation-spec-template.md` and keep them aligned with constitution repository-first rules.
  - Command templates: Read each command file in the active agent command directory (for example `.roo/commands/*.md`, `.claude/commands/*.md`, `.github/agents/*.agent.md`, `.gemini/commands/*.toml`); if `templates/commands/*.md` exists in this repository, review it as well. Verify no outdated references (agent-specific names like CLAUDE only) remain when generic guidance is required.
  - Runtime guidance docs: Read any runtime guidance docs (for example `README.md`, `docs/quickstart.md`, or agent-specific guidance files if present) and update references to principles changed.
  - Runtime efficiency protocol:
    - Resolve impacted families from the change impact map first, then read/update only those families.
    - If the change is `governance-only`, skip downstream family reads unless an explicit user request asks for broader synchronization.
    - Do not run directory-wide or repository-wide exploratory scans to "double check" unaffected families.
    - When a family is skipped, record `unchanged (not impacted)` in the Sync Impact Report.
    - For command templates, prioritize active agent command files first; inspect mirrors (`templates/commands/*`) only when active-agent files are absent or impacted rules are generic.
    - Runtime guidance docs (`README.md`, `docs/quickstart.md`, agent docs) are **opt-in by trigger** only:
      - read/update only when renamed principles/terms or invocation guidance text changed
      - otherwise skip and mark `unchanged (not impacted)`

1. Repository-first global baseline pipeline (mandatory):
   - Detect build manifests from repo root using deterministic priority and process all supported ecosystems detected:
     - Maven: `pom.xml`
     - Node: `package.json` (workspace-aware)
     - Python: `pyproject.toml` (and `requirements*.txt` / lock hints when present)
     - Go: `go.mod`
   - Repository-first fast path gate (evaluate before regeneration):
     - Reproject only when at least one trigger is true:
       - change impact map includes `repo-first-affecting`
       - any supported build-manifest set changed since last successful baseline update
       - any canonical repository-first artifact is missing
     - If no trigger is true, keep canonical baseline files as-is and mark each artifact `unchanged` without template re-render.
   - Use `.specify/memory/repository-first/` as the canonical output directory for repository-first projections:
     - `.specify/memory/repository-first/technical-dependency-matrix.md`
     - `.specify/memory/repository-first/module-invocation-spec.md`
   - Generate/refresh these files from their templates and constitution rules:
     - `.specify/templates/technical-dependency-matrix-template.md`
     - `.specify/templates/module-invocation-spec-template.md`
   - Legacy migration rule (mandatory):
     - If a legacy third baseline file exists under `.specify/memory/repository-first/`, remove it and record artifact status as `deleted`.
   - Always resolve repository-first artifacts by canonical paths under `.specify/memory/repository-first/`; never read or stat bare projection filenames from repo root.
   - Apply diff-based rewrite behavior:
     - `created`: file did not exist and is created
     - `updated`: file existed and content changed
     - `unchanged`: file existed and content is identical (do not rewrite)
     - `deleted`: legacy baseline file removed by migration
   - Dependency matrix generation policy:
     - Classify each dependency declaration before emission as exactly one of `in_repo_first_party_module`, `external_second_party`, or `third_party`.
     - Build the in-repo first-party module set from detected product/runtime manifests and exclude those coordinates from emitted dependency rows.
     - Normalize `Dependency (G:A)` as:
       - Maven: `group:artifact`
       - Node/Python/Go: `ecosystem:package_or_module`
     - Matrix rows MUST be exhaustive for the filtered product/runtime dependency set; do not emit highlight-only subsets.
     - Emit one row per dependency usage; do not collapse multiple modules, scopes, version sources, or evidence locations into one summary row.
     - Enforce `Type` values as `2nd` or `3rd` only.
     - Classify organization-owned or organization-coordinated dependencies not produced inside the current repository as `2nd`; do not default all rows to `3rd`.
     - Enforce `Version Source` values as `direct`, `dependencyManagement`, `module-dependencyManagement`, or `unresolved`.
     - Bind `Evidence` to the exact dependency declaration occurrence that produced the row; do not reuse the version-provider line as the declaration site.
     - If the same dependency is declared multiple times in one manifest, preserve one emitted row per occurrence with distinct line refs.
     - If version resolution is inherited, keep `Evidence` at the declaration site and set `Version Source` from the provider class.
     - Emit `unresolved` only when the effective version cannot be resolved from the declaration, the current module, or the detected in-repo ancestor manifest chain.
     - Emit `version-source-mix` only when 2 or more distinct `Version Source` values exist across emitted rows for the same dependency.
     - Emit `version-divergence` only when 2 or more distinct effective versions exist across emitted rows for the same dependency.
     - Preserve version divergence, version-source-mix, and `unresolved` as governance signals (no silent normalization).
     - Tooling-only manifests outside the product/runtime build surface SHOULD stay in detection notes and MUST NOT displace product dependency rows.
     - Every material signal MUST cite manifest paths and line refs.
     - Every dependency-governance signal MUST be derivable from emitted matrix rows only.
     - Run a final self-check to confirm `Evidence` lines map to the correct declaration occurrences and every emitted signal satisfies its trigger conditions.
   - Module invocation generation policy:
     - Allowed/forbidden direction tables MUST cover the concrete first-party module edges found in the target runtime repo.
     - Use concrete module-to-module rows as the primary representation; layer summaries are optional metadata only.
     - Do not collapse uncovered edges into broad grouped rows unless every covered edge shares the same rule and rationale.
     - Every dependency-governance rule MUST reference an existing `SIG-*` row from the dependency matrix; do not emit speculative future-signal rows.

2. Produce a Sync Impact Report (prepend as an HTML comment at top of the constitution file after update):
   - Keep this report delta-oriented; do not restate unchanged template inventories or canonical baseline details beyond status.
   - Version change: old → new
   - List of modified principles (old title → new title if renamed)
   - Added sections
   - Removed sections
   - Templates requiring updates (✅ updated / ⚠ pending) with file paths
   - Repository-first baseline status in `.specify/memory/repository-first/`:
     - Build-manifest detection outcome (ecosystems found / not found)
     - Artifact status per file (`created` / `updated` / `unchanged` / `deleted`)
   - Keep report compact:
     - include changed paths explicitly
     - for unchanged families, prefer one-line grouped summaries over per-file prose
   - Follow-up TODOs if any placeholders intentionally deferred.

3. Final quality check before output (constitution-local only):
   - No remaining unexplained bracket tokens.
   - Version line matches report.
   - Dates ISO format YYYY-MM-DD.
   - Principles are declarative, testable, and free of vague language ("should" → replace with MUST/SHOULD rationale where appropriate).
   - Constitution text does not include lint-catalog implementation details (rule IDs, regexes, script parameters, or execution payload shapes).
   - Do not duplicate one normative rule into competing expansions across multiple command templates; keep one constitution-level rule and downstream references aligned to that single authority.
   - Downstream alignment updates are minimal and delta-based; unchanged command/template text should not be rewritten just to restate existing authority.
   - Repo-anchor strategy wording preserves strict priority semantics (`existing -> extended -> new`) and explicit rejection-evidence requirements for `new`.
   - Do not introduce cross-artifact PASS/FAIL gates here; centralized consistency gating belongs to `/sdd.analyze`.
   - Repository-first canonical directory and files exist or are explicitly reported with unresolved blockers.

4. Write the completed constitution back to `.specify/memory/constitution.md` (overwrite).

5. Output a final summary to the user with:
   - New version and bump rationale.
   - Net-new fact source changes only (for example repository-first dependency/invocation baseline updates); reference the Sync Impact Report instead of restating it.
   - Repository-first baseline update summary only when status changed (`created` / `updated`) or blockers remain.
   - Any files flagged for manual follow-up.
   - Suggested commit message (e.g., `docs: amend constitution to vX.Y.Z (principle additions + governance update)`).
   - No cross-artifact PASS/FAIL gate decision in this command.
   - Keep runtime output concise: no unchanged-file inventories, no duplicated rule restatements, no repeated rationale blocks.

Formatting & Style Requirements:

- Use Markdown headings exactly as in the template (do not demote/promote levels).
- Wrap long rationale lines to keep readability (<100 chars ideally) but do not hard enforce with awkward breaks.
- Keep a single blank line between sections.
- Avoid trailing whitespace.

If the user supplies partial updates (e.g., only one principle revision), still perform validation and version decision steps.

If critical info missing (e.g., ratification date truly unknown), insert `TODO(<FIELD_NAME>): explanation` and include in the Sync Impact Report under deferred items.

Do not create a new template; always operate on the existing `.specify/memory/constitution.md` file.

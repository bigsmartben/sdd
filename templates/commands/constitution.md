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

**Runtime template path rule**: If `.specify/memory/constitution.md` does not exist yet, initialize it from `.specify/templates/constitution-template.md` first. In the Spec Kit source repository, `templates/constitution-template.md` is the source mirror of that runtime template.

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

3. Draft the updated constitution content:
   - For newly initialized files, replace every placeholder with concrete text (no bracketed tokens left except intentionally retained template slots that the project has chosen not to define yet—explicitly justify any left).
   - For existing files, preserve unaffected text and avoid mechanical full-template rewrites.
   - Preserve heading hierarchy and comments can be removed once replaced unless they still add clarifying guidance.
   - Ensure each Principle section: succinct name line, paragraph (or bullet list) capturing non‑negotiable rules, explicit rationale if not obvious.
   - Ensure Governance section lists amendment procedure, versioning policy, and compliance review expectations.

4. Fact-source propagation checklist:
   - Treat `.specify/memory/constitution.md` as the authoritative project-level rule source.
   - Treat `.specify/memory/constitution.md` as the authoritative project-level fact source. Any summaries, extracted rule lists, or downstream restatements of constitution content are derived views only and MUST be refreshed when constitution facts change.
   - Constitution content MUST stay at long-lived rule/terminology/ownership-boundary level; do not embed mechanical lint catalog details (rule IDs, regex patterns, script flags, payload schemas).
   - Runtime template authority path is `.specify/templates/`; when editing Spec Kit source directly, use the `templates/` mirror for the same files.
   - Read `.specify/templates/plan-template.md` and ensure any "Constitution Check" or rules align with updated principles.
   - Read the planning-stage templates in `.specify/templates/` (`research-template.md`, `data-model-template.md`, `test-matrix-template.md`, `contract-template.md`, and `interface-detail-template.md`) and ensure they reflect the updated principles and stage boundaries.
   - Read `.specify/templates/spec-template.md` for scope/requirements alignment—update if constitution adds/removes mandatory sections or constraints.
   - Read `.specify/templates/tasks-template.md` and ensure task categorization reflects new or removed principle-driven task types (e.g., observability, versioning, testing discipline).
   - Read repository-first projection templates (`.specify/templates/technical-dependency-matrix-template.md`, `.specify/templates/domain-boundary-responsibilities-template.md`, `.specify/templates/module-invocation-spec-template.md`) and keep them aligned with constitution repository-first rules.
   - Read each command file in the active agent command directory (for example `.roo/commands/*.md`, `.claude/commands/*.md`, `.github/agents/*.agent.md`, `.gemini/commands/*.toml`); if `templates/commands/*.md` exists in this repository, review it as well. Verify no outdated references (agent-specific names like CLAUDE only) remain when generic guidance is required.
   - Read any runtime guidance docs (e.g., `README.md`, `docs/quickstart.md`, or agent-specific guidance files if present). Update references to principles changed.

5. Repository-first global baseline pipeline (mandatory):
   - Detect build manifests from repo root using deterministic priority and process all supported ecosystems detected:
     - Maven: `pom.xml`
     - Node: `package.json` (workspace-aware)
     - Python: `pyproject.toml` (and `requirements*.txt` / lock hints when present)
     - Go: `go.mod`
   - Use `.specify/memory/repository-first/` as the canonical output directory for repository-first projections:
     - `.specify/memory/repository-first/technical-dependency-matrix.md`
     - `.specify/memory/repository-first/domain-boundary-responsibilities.md`
     - `.specify/memory/repository-first/module-invocation-spec.md`
   - Generate/refresh these files from their templates and constitution rules:
     - `.specify/templates/technical-dependency-matrix-template.md`
     - `.specify/templates/domain-boundary-responsibilities-template.md`
     - `.specify/templates/module-invocation-spec-template.md`
   - Apply diff-based rewrite behavior:
     - `created`: file did not exist and is created
     - `updated`: file existed and content changed
     - `unchanged`: file existed and content is identical (do not rewrite)
   - Dependency matrix generation policy:
     - Normalize `Dependency (G:A)` as:
       - Maven: `group:artifact`
       - Node/Python/Go: `ecosystem:package_or_module`
     - Enforce `Type` values as `2nd` or `3rd` only.
     - Enforce `Version Source` values as `direct`, `dependencyManagement`, `module-dependencyManagement`, or `unresolved`.
     - Preserve version divergence and `unresolved` as governance signals (no silent normalization).

6. Produce a Sync Impact Report (prepend as an HTML comment at top of the constitution file after update):
   - Version change: old → new
   - List of modified principles (old title → new title if renamed)
   - Added sections
   - Removed sections
   - Templates requiring updates (✅ updated / ⚠ pending) with file paths
   - Repository-first baseline status in `.specify/memory/repository-first/`:
     - Build-manifest detection outcome (ecosystems found / not found)
     - Artifact status per file (`created` / `updated` / `unchanged`)
   - Follow-up TODOs if any placeholders intentionally deferred.

7. Final quality check before output (constitution-local only):
   - No remaining unexplained bracket tokens.
   - Version line matches report.
   - Dates ISO format YYYY-MM-DD.
   - Principles are declarative, testable, and free of vague language ("should" → replace with MUST/SHOULD rationale where appropriate).
   - Constitution text does not include lint-catalog implementation details (rule IDs, regexes, script parameters, or execution payload shapes).
   - Do not duplicate one normative rule into competing expansions across multiple command templates; keep one constitution-level rule and downstream references aligned to that single authority.
   - Do not introduce cross-artifact PASS/FAIL gates here; centralized consistency gating belongs to `/sdd.analyze`.
   - Repository-first canonical directory and files exist or are explicitly reported with unresolved blockers.

8. Write the completed constitution back to `.specify/memory/constitution.md` (overwrite).

9. Output a final summary to the user with:
   - New version and bump rationale.
   - Fact source changes (for example repository-first definitions or ownership-boundary baseline updates).
   - Repository-first baseline update summary (`created` / `updated` / `unchanged` + detection outcome).
   - Any files flagged for manual follow-up.
   - Suggested commit message (e.g., `docs: amend constitution to vX.Y.Z (principle additions + governance update)`).
   - No cross-artifact PASS/FAIL gate decision in this command.

Formatting & Style Requirements:

- Use Markdown headings exactly as in the template (do not demote/promote levels).
- Wrap long rationale lines to keep readability (<100 chars ideally) but do not hard enforce with awkward breaks.
- Keep a single blank line between sections.
- Avoid trailing whitespace.

If the user supplies partial updates (e.g., only one principle revision), still perform validation and version decision steps.

If critical info missing (e.g., ratification date truly unknown), insert `TODO(<FIELD_NAME>): explanation` and include in the Sync Impact Report under deferred items.

Do not create a new template; always operate on the existing `.specify/memory/constitution.md` file.

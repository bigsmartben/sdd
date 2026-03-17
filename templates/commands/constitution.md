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

1. Bootstrap the authoritative source:
   - Load `.specify/memory/constitution.md`; if it does not exist, initialize it from `.specify/templates/constitution-template.md`.
   - If this run initialized the file, resolve placeholder tokens of the form `[ALL_CAPS_IDENTIFIER]`.
   - If the file already existed, treat it as live governance content and amend only the required deltas; do not force a template-token rewrite pass.
   - If the user specifies a principle count, respect it while preserving existing ratification history unless explicitly changed.

2. Derive the delta set before broad reads:
   - Prefer user input; otherwise infer from the current constitution plus minimal repo context.
   - For governance dates, keep `RATIFICATION_DATE` as the original adoption date (ask or TODO if unknown) and set `LAST_AMENDED_DATE` to today only when content changes.
   - `CONSTITUTION_VERSION` must increment according to semantic versioning rules:
     - MAJOR: backward incompatible governance/principle removals or redefinitions.
     - MINOR: new principle/section added or materially expanded guidance.
     - PATCH: clarifications, wording, typo fixes, non-semantic refinements.
     - Adding or materially expanding generation/validation/execution ownership boundaries is always `MINOR`.
   - If the bump type is ambiguous, state the reasoning before finalizing.

3. Build the sync workset before broad reads:
   - Treat `.specify/memory/constitution.md` as the authoritative project-level rule source.
   - Treat `.specify/memory/constitution.md` as the authoritative project-level fact source; summaries, extracted rule lists, and downstream restatements are derived views only and MUST be refreshed when constitution facts change.
   - Constitution content MUST stay at long-lived rule/terminology/ownership-boundary level; do not embed mechanical lint catalog details (rule IDs, regex patterns, script flags, payload schemas).
   - Runtime template authority path is `.specify/templates/`; when editing Spec Kit source directly, use the `templates/` mirror for the same files.
   - Read only files affected by the delta set, not the whole repo.
   - Always review `.specify/templates/plan-template.md`, `.specify/templates/technical-dependency-matrix-template.md`, and `.specify/templates/module-invocation-spec-template.md`.
   - Review changed planning-stage templates in `.specify/templates/` (`research-template.md`, `data-model-template.md`, `test-matrix-template.md`, `contract-template.md`, `interface-detail-template.md`) only when the delta affects their stage rules or boundaries.
   - Review `.specify/templates/spec-template.md` only when the delta changes required feature sections or constraints.
   - Review `.specify/templates/tasks-template.md` only when the delta changes execution/task categorization rules.
   - Review command files in the active agent command directory only when the delta affects command contracts or wording; common examples include `.roo/commands/*.md`, `.claude/commands/*.md`, `.github/agents/*.agent.md`, and `.gemini/commands/*.toml`. If `templates/commands/*.md` exists in this repository, review the matching mirror there as well.
   - Review runtime guidance docs (for example `README.md`, `docs/quickstart.md`, or agent-specific guidance files) only when they explicitly reference the changed principle or command contract.

4. Draft and apply the constitution update:
   - For newly initialized files, replace every placeholder with concrete text unless the project intentionally defers one; justify every retained placeholder explicitly.
   - For existing files, preserve unaffected text, keep the heading hierarchy, and avoid mechanical full-template rewrites.
   - Ensure each Principle section has a succinct name, declarative rules, and rationale when non-obvious.
   - Ensure Governance covers amendment procedure, versioning policy, and compliance review expectations.

5. Repository-first global baseline pipeline (mandatory):
   - Detect build manifests from repo root using deterministic priority and process supported ecosystems found:
     - Maven: `pom.xml`
     - Node: `package.json` (workspace-aware)
     - Python: `pyproject.toml` (and `requirements*.txt` / lock hints when present)
     - Go: `go.mod`
   - Canonical output directory: `.specify/memory/repository-first/`
     - `.specify/memory/repository-first/technical-dependency-matrix.md`
     - `.specify/memory/repository-first/module-invocation-spec.md`
   - Generate/refresh these files from `.specify/templates/technical-dependency-matrix-template.md` and `.specify/templates/module-invocation-spec-template.md`.
   - Apply diff-based rewrite behavior only:
     - `created`: file did not exist and is created
     - `updated`: file existed and content changed
     - `unchanged`: file existed and content is identical (do not rewrite)
   - Dependency matrix generation policy:
     - Normalize `Dependency (G:A)` as Maven = `group:artifact`; Node/Python/Go = `ecosystem:package_or_module`
     - Enforce `Type` values as `2nd` or `3rd` only.
     - Enforce `Version Source` values as `direct`, `dependencyManagement`, `module-dependencyManagement`, or `unresolved`.
     - Preserve version divergence and `unresolved` as governance signals.

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
- Keep spacing readable and avoid trailing whitespace.

Execution-speed rules:

- Decide the delta set before opening downstream templates or docs.
- Reuse current headings and nearby anchors instead of replaying full-file rewrites.
- Sync only the files touched by the delta set plus the mandatory repository-first templates.
- Stop after constitution, impacted mirrors, and canonical repository-first projections are aligned.

If the user supplies partial updates (e.g., only one principle revision), still perform delta, validation, and version-decision steps.

If critical info missing (e.g., ratification date truly unknown), insert `TODO(<FIELD_NAME>): explanation` and include in the Sync Impact Report under deferred items.

Do not create a new template; always operate on the existing `.specify/memory/constitution.md` file.

# Repository Guidance

This file provides workspace-level guidance for agents working in this repository.

## Scope and authority

- This guidance applies to the entire repository unless a more specific instruction file in a subdirectory explicitly overrides it.
- This repository is the **development/source repository** for the SDD platform. It contains the code and source assets that produce runtime SDD workspaces, but it is not itself the fully materialized runtime workspace that end users operate in after initialization.
- Treat `.specify/` as the **runtime authority** for SDD behavior, path detection, template resolution, and command-stage contracts.
- Treat `specify init` as a **runtime initialization command** implemented by this source repository. Its job is to materialize runtime assets into a target project workspace, including `.specify/templates/`, `.specify/scripts/`, `.specify/memory/`, and agent command directories.
- Treat `tests/`, `README.md`, docs, examples, and generated outputs as **validation or presentation artifacts only** unless they are explicitly documented as runtime sources.
- When runtime artifacts and source-side expectations disagree, prefer the runtime artifact under `.specify/`, then repair downstream validation and documentation to match.
- Never infer runtime semantics from tests, docs, or generated outputs when a `.specify/` artifact exists or can be read directly.
- **Prompt Style**: All command and template edits MUST follow the strict authoring rules in `rules/prompt-style-baseline.md`.

## Runtime vs source boundary

- Distinguish two layers explicitly:
  - **Source/development layer** in this repo: `src/`, `templates/`, `scripts/`, release-packaging code, and tests.
  - **Runtime layer** in an initialized project: `.specify/**`, agent command directories, and generated feature artifacts under `specs/`.
- Treat `.specify/` as the **SDD runtime directory**.
- Treat `.specify/memory/` as a **runtime directory**, not as a source-side mirror, fixture, or documentation sample.
- Treat `.specify/templates/` and `.specify/scripts/` as **runtime assets** even when their upstream sources live under workspace-side `templates/` and `scripts/`.
- Treat workspace-side `templates/` and `scripts/` as **source assets that are projected into runtime**, not as the final runtime authority by default.
- When `.specify/` is absent in this source repository checkout, treat `src/specify_cli/runtime_*.py` and the corresponding hidden `specify` internal bootstrap commands as the **source-repo-side runtime authority** for bootstrap packets and command-stage gate semantics.
- Treat `scripts/task_preflight.py`, `scripts/data_model_preflight.py`, and `scripts/implement_preflight.py` as **development-side wrapper entrypoints only**. They must delegate to `src/specify_cli/runtime_*.py` and must not carry an independent copy of runtime rules.
- Treat bootstrap packet production as a **hard runtime dependency**, not as an optional optimization. If a runtime bootstrap cannot be produced, consumed, or validated, stop and report the blocker; do not substitute `null`, fallback recomputation, or test-derived reconstruction.
- Treat the workspace `tests/` directory as **source-repository-side validation code**.
- When reasoning about SDD runtime behavior, path detection, or runtime template resolution, prefer `.specify/` artifacts over source-side mirrors or test fixtures.
- When reasoning about assertions, regressions, or validation coverage, treat `tests/` as repository tests, not as runtime authority.
- If a runtime artifact and a test-side expectation disagree, resolve the discrepancy in favor of the runtime boundary defined by `.specify/`, then update tests to match the intended runtime contract.
- If `.specify/` and `tests/` disagree, do not blend the two sources into one interpretation; identify the mismatch explicitly and fix the downstream side after confirming the runtime contract.
- If `.specify/` is absent in this source repository checkout, do not immediately treat tests or docs as replacement runtime authority. First determine whether the runtime artifact is expected to be materialized by `specify init`, release packaging, or other source-to-runtime projection logic.

## Reading order

- For SDD command behavior, check `.specify/` first, then compare the corresponding repository tests.
- For command templates, runtime packets, and stage handoff rules, prefer `.specify/templates/` and `.specify/memory/` before any workspace-side mirrors.
- For questions about how runtime artifacts are produced when `.specify/` is absent in the source repo, inspect the source-to-runtime projection chain in this order:
  1. `specify init` implementation under `src/specify_cli/`
  2. runtime bootstrap authority under `src/specify_cli/runtime_*.py` and hidden `internal-*-bootstrap` commands
  3. release-packaging scripts under `.github/workflows/scripts/`
  4. runtime consumer scripts under `scripts/bash/` and `scripts/powershell/`
  5. only then the corresponding repository tests
- For validation failures, inspect `tests/` after confirming the runtime contract, not before.
- If a requested runtime artifact is missing, report the blocker instead of reconstructing the artifact from tests or docs.

## Agent usage

- Prefer small, localized changes that preserve existing conventions.
- Avoid rewriting unrelated files when the task only affects one boundary or command path.
- Keep planning and documentation changes aligned with the runtime directory layout before making code changes.
- When adjusting boundary rules, update the authoritative runtime file first and only then repair downstream references.
- Do not expand scope by editing unrelated docs, tests, or examples unless they directly depend on the same runtime contract.
- If a fix requires more than one file, keep the change set minimal and explain the dependency chain before editing.

## Conflict resolution

- Runtime contract conflict: `.specify/` wins.
- Source-vs-runtime mapping conflict: runtime consumer paths and init/package projection logic win over assumptions drawn from source-side mirrors alone.
- Validation conflict: repository tests may expose regressions, but they must not redefine runtime behavior.
- Documentation conflict: docs should follow the runtime contract and may lag only temporarily while the runtime fix is being applied.
- Missing evidence: stop and report the blocker rather than guessing a path, template, or stage boundary.
- Ambiguous boundary: search for the nearest `.specify/` artifact that owns the behavior; if none exists, call out the gap explicitly.

## Validation mindset

- Check the relevant runtime artifacts first.
- If the runtime artifact is generated rather than checked in, verify the actual projection path from source asset -> packaged/init output -> runtime consumer before drawing conclusions.
- Then inspect the corresponding repository tests for coverage or drift.
- Report boundary mismatches explicitly rather than silently merging runtime and test responsibilities.
- Confirm that any downstream reference to a runtime concept points at `.specify/` and not at a source-side mirror.
- When a change touches runtime routing, also check whether `.specify/` memory, templates, or command docs need synchronized updates.
- Treat “it passed in tests” as insufficient if the runtime contract in `.specify/` was not validated.

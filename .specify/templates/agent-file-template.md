# [PROJECT NAME] Development Guidelines

Auto-generated from all feature plans. Last updated: [DATE]

## Active Technologies

[EXTRACTED FROM ALL PLAN.MD FILES]

## Project Structure

```text
[ACTUAL STRUCTURE FROM PLANS]
```

## Commands

[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]

## Stable Local Execution

- Treat the constitution-defined local execution policy as the authority; use the runtime `LOCAL_EXECUTION_PROTOCOL` emitted by `/sdd.*` prerequisite scripts as the run-local projection for repository search, git inspection, and Python helper execution.
- Default repository discovery order: `rg --files` / `rg -n`; if unavailable and the workspace is a git repo, use the emitted git commands instead of guessing alternates.
- Prefer the emitted `specify-cli` helper entrypoints (for example `specify internal-task-bootstrap`, `specify internal-data-model-bootstrap`, or `specify internal-implement-bootstrap`) over ad hoc interpreter guesses or repo-local `uv run python`.
- Do not install missing CLI tools, mutate PATH, or switch package managers/interpreters inside `/sdd.*` runs unless the task artifact explicitly requires it.

## Code Style

[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]

## Recent Changes

[LAST 3 FEATURES AND WHAT THEY ADDED]

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

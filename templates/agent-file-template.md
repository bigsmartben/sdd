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

- Prefer the runtime `LOCAL_EXECUTION_PROTOCOL` emitted by `/sdd.*` prerequisite scripts for repository search, git inspection, and Python helper execution.
- Default repository discovery order: `rg --files` / `rg -n`; if unavailable and the workspace is a git repo, use the emitted git commands instead of guessing alternates.
- Prefer the emitted Python runner (for example `uv run python` when selected by the runtime protocol) over ad hoc interpreter guesses.
- Do not install missing CLI tools, mutate PATH, or switch package managers inside `/sdd.*` runs unless the task artifact explicitly requires it.

## Code Style

[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]

## Recent Changes

[LAST 3 FEATURES AND WHAT THEY ADDED]

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

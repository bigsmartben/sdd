---
name: release-gate
description: Deterministic release workflow for this sdd repository. Use when preparing or publishing a version to enforce fixed repository paths, full AGENT_CONFIG template coverage (all agents x sh/ps), and fail-fast release gates with no path guessing.
---

# Release Gate

Use this skill when the user asks to release, publish, cut a version, or verify release readiness.

## Execute

1. Run the deterministic wrapper from anywhere:

```bash
bash .codex/skills/release-gate/scripts/release-run.sh vX.Y.Z
```

2. Publish only after preflight succeeds:

```bash
bash .codex/skills/release-gate/scripts/release-run.sh vX.Y.Z --publish
```

## Hard Rules

- Resolve repo root via git and use absolute script paths under `REPO_ROOT/.github/workflows/scripts/`.
- Do not use ad-hoc relative paths or alternate script locations.
- Do not bypass `create-release-packages.sh` / `create-github-release.sh`.
- Require complete template archives for every `AGENT_CONFIG` key and both `sh`/`ps`.
- Fail fast on any missing asset, count mismatch, missing dist artifact, or missing required tool.

## Expected Sequence

1. Validate tools and version format.
2. Build template archives via `create-release-packages.sh`.
3. Build Python distributions via `uv build`.
4. Generate `release_notes.md` via `generate-release-notes.sh`.
5. Enforce template coverage gate locally.
6. If `--publish` is present, run `create-github-release.sh` (which re-checks gates).


---
description: Convert existing tasks into actionable, dependency-ordered GitHub issues for the feature based on available design artifacts.
tools: ['github/github-mcp-server/issue_write']
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Run `{SCRIPT}` from repo root and parse `FEATURE_DIR` and `AVAILABLE_DOCS`. All paths must be absolute.
2. Resolve the path to `tasks.md` from the script output and stop if it is missing.
3. Get the Git remote:

   ```bash
   git config --get remote.origin.url
   ```

   > [!CAUTION]
   > ONLY PROCEED TO NEXT STEPS IF THE REMOTE IS A GITHUB URL

4. Parse tasks into dependency-ordered issue candidates (title, body, dependency refs, labels/milestone if available from context).
5. For each task, create one GitHub issue using the MCP server in the exact repository derived from the checked remote.
6. Report created issue URLs and any skipped tasks with reason.

   > [!CAUTION]
   > UNDER NO CIRCUMSTANCES EVER CREATE ISSUES IN REPOSITORIES THAT DO NOT MATCH THE REMOTE URL

<div align="center">
    <img src="./media/logo_large.webp" alt="Spec Kit Logo" width="200" height="200"/>
    <h1>🌱 Spec Kit</h1>
    <h3><em>Build high-quality software faster.</em></h3>
</div>

<p align="center">
    <strong>An open source toolkit that allows you to focus on product scenarios and predictable outcomes instead of vibe coding every piece from scratch.</strong>
</p>

<p align="center">
    <a href="https://github.com/bigsmartben/sdd/actions/workflows/release.yml"><img src="https://github.com/bigsmartben/sdd/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
    <a href="https://github.com/bigsmartben/sdd/stargazers"><img src="https://img.shields.io/github/stars/bigsmartben/sdd?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/bigsmartben/sdd/blob/main/LICENSE"><img src="https://img.shields.io/github/license/bigsmartben/sdd" alt="License"/></a>
    <a href="https://github.github.io/spec-kit/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="Documentation"/></a>
</p>

---

## Table of Contents

- [🤔 What is Spec-Driven Development?](#-what-is-spec-driven-development)
- [⚡ Get Started](#-get-started)
- [📽️ Video Overview](#️-video-overview)
- [🚶 Community Walkthroughs](#-community-walkthroughs)
- [🤖 Supported AI Agents](#-supported-ai-agents)
- [🔧 Specify CLI Reference](#-specify-cli-reference)
- [📚 Core Philosophy](#-core-philosophy)
- [🌟 Development Phases](#-development-phases)
- [🎯 Experimental Goals](#-experimental-goals)
- [🔧 Prerequisites](#-prerequisites)
- [📖 Learn More](#-learn-more)
- [📋 Detailed Process](#-detailed-process)
- [🔍 Troubleshooting](#-troubleshooting)
- [💬 Support](#-support)
- [🙏 Acknowledgements](#-acknowledgements)
- [📄 License](#-license)

## 🤔 What is Spec-Driven Development?

Spec-Driven Development **flips the script** on traditional software development. For decades, code has been king — specifications were just scaffolding we built and discarded once the "real work" of coding began. Spec-Driven Development changes this: **specifications become executable**, directly generating working implementations rather than just guiding them.

## ⚡ Get Started

### 1. Install Specify CLI

Choose your preferred installation method:

#### Option 1: Persistent Installation (Recommended)

Install once and use everywhere:

```bash
uv tool install specify-cli --from git+https://github.com/bigsmartben/sdd.git
```

Then use the tool directly:

```bash
# Create new project
specify init <PROJECT_NAME>

# Or initialize in existing project
specify init . --ai claude
# or
specify init --here --ai claude

# Check installed tools
specify check
```

To upgrade Specify, see the [Upgrade Guide](./docs/upgrade.md) for detailed instructions. Quick upgrade:

```bash
uv tool install specify-cli --force --from git+https://github.com/bigsmartben/sdd.git
```

#### Option 2: One-time Usage

Run directly without installing:

```bash
# Create new project
uvx --from git+https://github.com/bigsmartben/sdd.git specify init <PROJECT_NAME>

# Or initialize in existing project
uvx --from git+https://github.com/bigsmartben/sdd.git specify init . --ai claude
# or
uvx --from git+https://github.com/bigsmartben/sdd.git specify init --here --ai claude
```

**Benefits of persistent installation:**

- Tool stays installed and available in PATH
- No need to create shell aliases
- Better tool management with `uv tool list`, `uv tool upgrade`, `uv tool uninstall`
- Cleaner shell configuration

### 2. Establish project principles

Launch your AI assistant in the project directory. The `/sdd.*` commands are available in the assistant.

Use the **`/sdd.constitution`** command to create your project's governing principles and development guidelines that will guide all subsequent development.

```bash
/sdd.constitution Create principles focused on code quality, testing standards, user experience consistency, and performance requirements
```

### 3. Create the spec

Use the **`/sdd.specify`** command to describe what you want to build. Focus on the **what** and **why**, not the tech stack.

In Git repositories, `/sdd.specify` resolves a feature branch and switches to it before writing artifacts.
`/sdd.specify` is the only command that may create/switch branches; all downstream `/sdd.*` commands must run on the active feature branch via branch inference.

```bash
/sdd.specify Build an application that can help me organize my photos in separate photo albums. Albums are grouped by date and can be re-organized by dragging and dropping on the main page. Albums are never in other nested albums. Within each album, photos are previewed in a tile-like interface.
```

### 4. Generate a focused interaction tool (optional)

Use **`/sdd.specify.ui-html`** as an optional sidecar command when you need an HTML focused interaction tool derived from the current feature branch `spec.md`. Trigger it at your chosen time after `/sdd.specify`.

`spec.md` remains the authoritative feature-semantics artifact. `ui.html` is a derived review artifact only.

### 5. Create a planning control plane

Use the **`/sdd.plan`** command to create `plan.md` as the planning control plane. It captures Stage 0 shared context, the planning queue, and the binding projection ledger for later `sdd.plan.*` child commands.

```bash
/sdd.plan The application uses Vite with minimal number of libraries. Use vanilla HTML, CSS, and JavaScript as much as possible. Images are not uploaded anywhere and metadata is stored in a local SQLite database.
```

### 6. Run the planning queue

Use the `sdd.plan.*` child commands to generate planning artifacts one unit at a time:

- `/sdd.plan.research`
- `/sdd.plan.data-model`
- `/sdd.plan.test-matrix`
- repeated `/sdd.plan.contract`

`plan.md` queue state is the sole authority for planning handoff decisions.
For repeated `/sdd.plan.contract` runs, follow the runtime `Handoff Decision` output rather than any static frontmatter suggestion. Planning commands derive their target from the active feature branch (or `SPECIFY_FEATURE` in non-Git mode).

### 7. Break down into tasks

Use **`/sdd.tasks`** to convert approved planning artifacts into executable orchestration (`Task DAG`, `GLOBAL`, `IF-###`) without performing a unified semantic audit. This is an execution decomposition step only: it projects completed `plan`-stage design into work packages and hard-fails on missing execution anchors instead of supplementing design or writing placeholder tasks.

```bash
/sdd.tasks
```

### 8. Execute implementation

Use **`/sdd.implement`** to execute tasks with runtime hard gates and build your feature according to the plan. Run **`/sdd.analyze`** first as the default pre-implementation audit; missing/stale analyze evidence or a `Gate Decision: FAIL` should block implementation by default unless you explicitly waive the analyze gate for that run.

```bash
/sdd.implement
```

For detailed step-by-step instructions, see our [comprehensive guide](./spec-driven.md).

## 📽️ Video Overview

Want to see Spec Kit in action? Watch our [video overview](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)!

## Project Skills

This repository also carries project-local skills under `.codex/skills/` for
workflow enforcement.

- `release-gate`: deterministic release preflight and publish workflow
- `sdd-scenario-governance`: enforce architecture/module-boundary discipline and
  split work into `development` vs `release`

Example invocation:

```text
使用 $sdd-scenario-governance 处理这个需求
```

[![Spec Kit video header](/media/spec-kit-video-header.jpg)](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)

## 🚶 Community Walkthroughs

See Spec-Driven Development in action across different scenarios with these community-contributed walkthroughs:

- **[Greenfield .NET CLI tool](https://github.com/mnriem/spec-kit-dotnet-cli-demo)** — Builds a Timezone Utility as a .NET single-binary CLI tool from a blank directory, covering the full spec-kit workflow: constitution, specify, plan, tasks, and multi-pass implement using GitHub Copilot agents.

- **[Greenfield Spring Boot + React platform](https://github.com/mnriem/spec-kit-spring-react-demo)** — Builds an LLM performance analytics platform (REST API, graphs, iteration tracking) from scratch using Spring Boot, embedded React, PostgreSQL, and Docker Compose, with a clarify step and a cross-artifact consistency analysis pass included.

- **[Brownfield ASP.NET CMS extension](https://github.com/mnriem/spec-kit-aspnet-brownfield-demo)** — Extends an existing open-source .NET CMS (CarrotCakeCMS-Core) with two new features — cross-platform Docker Compose infrastructure and a token-authenticated headless REST API — demonstrating how spec-kit fits into existing codebases without prior specs or a constitution.

## 🤖 Supported AI Agents

| Agent                                                                                | Support | Notes                                                                                                                                     |
| ------------------------------------------------------------------------------------ | ------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| [Qoder CLI](https://qoder.com/cli)                                                   | ✅      |                                                                                                                                           |
| [Kiro CLI](https://kiro.dev/docs/cli/)                                               | ✅      | Use `--ai kiro-cli` (alias: `--ai kiro`)                                                                                                 |
| [Amp](https://ampcode.com/)                                                          | ✅      |                                                                                                                                           |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview)                              | ✅      |                                                                                                                                           |
| [Claude Code](https://www.anthropic.com/claude-code)                                 | ✅      |                                                                                                                                           |
| [CodeBuddy CLI](https://www.codebuddy.ai/cli)                                        | ✅      |                                                                                                                                           |
| [Codex CLI](https://github.com/openai/codex)                                         | ✅      |                                                                                                                                           |
| [Cursor](https://cursor.sh/)                                                         | ✅      |                                                                                                                                           |
| [Cline](https://github.com/cline/cline)                                              | ✅      | Slash commands are generated under `.clinerules/workflows/`                                                                             |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli)                            | ✅      |                                                                                                                                           |
| [GitHub Copilot](https://code.visualstudio.com/)                                     | ✅      |                                                                                                                                           |
| [IBM Bob](https://www.ibm.com/products/bob)                                          | ✅      | IDE-based agent with slash command support                                                                                                |
| [Jules](https://jules.google.com/)                                                   | ✅      |                                                                                                                                           |
| [Kilo Code](https://github.com/Kilo-Org/kilocode)                                    | ✅      |                                                                                                                                           |
| [opencode](https://opencode.ai/)                                                     | ✅      |                                                                                                                                           |
| [Qwen Code](https://github.com/QwenLM/qwen-code)                                     | ✅      |                                                                                                                                           |
| [Roo Code](https://roocode.com/)                                                     | ✅      |                                                                                                                                           |
| [SHAI (OVHcloud)](https://github.com/ovh/shai)                                       | ✅      |                                                                                                                                           |
| [Tabnine CLI](https://docs.tabnine.com/main/getting-started/tabnine-cli)             | ✅      |                                                                                                                                           |
| [Mistral Vibe](https://github.com/mistralai/mistral-vibe)                            | ✅      |                                                                                                                                           |
| [Kimi Code](https://code.kimi.com/)                                                  | ✅      |                                                                                                                                           |
| [Windsurf](https://windsurf.com/)                                                    | ✅      |                                                                                                                                           |
| [Antigravity (agy)](https://antigravity.google/)                                     | ✅      |                                                                                                                                           |
| Generic                                                                              | ✅      | Bring your own agent — use `--ai generic --ai-commands-dir <path>` for unsupported agents                                                 |

## 🔧 Specify CLI Reference

The `specify` command supports the following options:

### Commands

| Command | Description                                                                                                                                             |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `init`  | Initialize a new Specify project from the latest template                                                                                               |
| `check` | Check local tooling availability (`git`, supported agent CLIs, and `code`/`code-insiders`; IDE-only agents are reported as skipped) |

### `specify init` Arguments & Options

| Argument/Option        | Type     | Description                                                                                                                                                                                  |
| ---------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<project-name>`       | Argument | Name for your new project directory (optional if using `--here`, or use `.` for current directory)                                                                                           |
| `--ai`                 | Option   | AI assistant to use: `claude`, `gemini`, `copilot`, `cursor-agent`, `cline`, `qwen`, `opencode`, `codex`, `windsurf`, `kilocode`, `auggie`, `roo`, `codebuddy`, `amp`, `shai`, `kiro-cli` (`kiro` alias), `agy`, `bob`, `qodercli`, `vibe`, `kimi`, or `generic` (requires `--ai-commands-dir`) |
| `--ai-commands-dir`    | Option   | Directory for agent command files (required with `--ai generic`, e.g. `.myagent/commands/`)                                                                                                  |
| `--script`             | Option   | Script variant to use: `sh` (bash/zsh) or `ps` (PowerShell)                                                                                                                                  |
| `--ignore-agent-tools` | Flag     | Skip checks for AI agent tools like Claude Code                                                                                                                                              |
| `--no-git`             | Flag     | Skip git repository initialization                                                                                                                                                           |
| `--here`               | Flag     | Initialize project in the current directory instead of creating a new one                                                                                                                    |
| `--force`              | Flag     | Force merge/overwrite when initializing in current directory (skip confirmation)                                                                                                             |
| `--skip-tls`           | Flag     | Skip SSL/TLS verification (not recommended)                                                                                                                                                  |
| `--debug`              | Flag     | Enable detailed debug output for troubleshooting                                                                                                                                             |
| `--github-token`       | Option   | GitHub token for API requests (or set GH_TOKEN/GITHUB_TOKEN env variable)                                                                                                                    |
| `--ai-skills`          | Flag     | Install Prompt.MD templates as agent skills in agent-specific `skills/` directory (requires `--ai`)                                                                                          |

### Examples

```bash
# Basic project initialization
specify init my-project

# Initialize with specific AI assistant
specify init my-project --ai claude

# Initialize with Cursor support
specify init my-project --ai cursor-agent

# Initialize with Cline support
specify init my-project --ai cline

# Initialize with Qoder support
specify init my-project --ai qodercli

# Initialize with Windsurf support
specify init my-project --ai windsurf

# Initialize with Kiro CLI support
specify init my-project --ai kiro-cli

# Initialize with Amp support
specify init my-project --ai amp

# Initialize with SHAI support
specify init my-project --ai shai

# Initialize with Mistral Vibe support
specify init my-project --ai vibe

# Initialize with IBM Bob support
specify init my-project --ai bob

# Initialize with Antigravity support
specify init my-project --ai agy

# Initialize with an unsupported agent (generic / bring your own agent)
specify init my-project --ai generic --ai-commands-dir .myagent/commands/

# Initialize with PowerShell scripts (Windows/cross-platform)
specify init my-project --ai copilot --script ps

# Initialize in current directory
specify init . --ai copilot
# or use the --here flag
specify init --here --ai copilot

# Force merge into current (non-empty) directory without confirmation
specify init . --force --ai copilot
# or
specify init --here --force --ai copilot

# Skip git initialization
specify init my-project --ai gemini --no-git

# Enable debug output for troubleshooting
specify init my-project --ai claude --debug

# Use GitHub token for API requests (helpful for corporate environments)
specify init my-project --ai claude --github-token ghp_your_token_here

# Install agent skills with the project
specify init my-project --ai claude --ai-skills

# Initialize in current directory with agent skills
specify init --here --ai gemini --ai-skills

# Check system requirements
specify check
```

### Available Slash Commands

After running `specify init`, your AI coding agent will have access to these slash commands for structured development:

#### Core Commands

Essential commands for the Spec-Driven Development workflow:

| Command                 | Description                                                              |
| ----------------------- | ------------------------------------------------------------------------ |
| `/sdd.constitution` | Create or update project governing principles and development guidelines |
| `/sdd.specify`      | Define what you want to build (requirements and user stories)            |
| `/sdd.specify.ui-html` | Optional sidecar command: generate a derived `ui.html` focused interaction tool from active feature `spec.md` when needed |
| `/sdd.plan`         | Create `plan.md` as the planning control plane and Stage 0 shared context |
| `/sdd.plan.research` | Generate the queued `research.md` artifact |
| `/sdd.plan.data-model` | Generate the queued `data-model.md` artifact |
| `/sdd.plan.test-matrix` | Generate the queued `test-matrix.md` artifact and binding rows |
| `/sdd.plan.contract` | Generate one queued full-field contract artifact |
| `/sdd.tasks` | Produce executable orchestration from approved planning artifacts (no unified semantic audit) |
| `/sdd.implement`    | Execute tasks with runtime hard gates (expects fresh `/sdd.analyze` `PASS` evidence; missing/stale or `FAIL` blocks by default unless explicitly waived) |

#### Optional Commands

Additional commands for enhanced quality and validation:

| Command              | Description                                                                                                                          |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `/sdd.clarify`   | Clarify underspecified areas (recommended before `/sdd.plan`; formerly `/quizme`) |
| `/sdd.analyze`   | Lint-backed unified audit entrypoint: combines mechanical lint checks with cross-artifact semantic findings (traceability, drift, contradictions, and boundary violations) across `spec.md`, `plan.md`, and `tasks.md` |
| `/sdd.checklist` | Generate standalone checklist artifacts in `checklists/*.md` as a vertical validation pass from active feature `plan.md` (does not backfill or redefine main-flow artifacts) |

### Environment Variables

| Variable          | Description                                                                                                                                                                                                                                                                                            |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `SPECIFY_FEATURE` | Override feature detection for non-Git repositories. Set to the feature directory name (e.g., `20250708-photo-albums`) to work on a specific feature when not using Git branches. |

## 📚 Core Philosophy

Spec-Driven Development is a structured process that emphasizes:

- **Intent-driven development** where specifications define the "*what*" before the "*how*"
- **Rich specification creation** using guardrails and organizational principles
- **Multi-step refinement** rather than one-shot code generation from prompts
- **Heavy reliance** on advanced AI model capabilities for specification interpretation

## 🌟 Development Phases

| Phase                                    | Focus                    | Key Activities                                                                                                                                                     |
| ---------------------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **0-to-1 Development** ("Greenfield")    | Generate from scratch    | <ul><li>Start with high-level requirements</li><li>Generate specifications</li><li>Plan implementation steps</li><li>Build production-ready applications</li></ul> |
| **Creative Exploration**                 | Parallel implementations | <ul><li>Explore diverse solutions</li><li>Support multiple technology stacks & architectures</li><li>Experiment with UX patterns</li></ul>                         |
| **Iterative Enhancement** ("Brownfield") | Brownfield modernization | <ul><li>Add features iteratively</li><li>Modernize legacy systems</li><li>Adapt processes</li></ul>                                                                |

## 🎯 Experimental Goals

Our research and experimentation focus on:

### Technology independence

- Create applications using diverse technology stacks
- Validate the hypothesis that Spec-Driven Development is a process not tied to specific technologies, programming languages, or frameworks

### Enterprise constraints

- Demonstrate mission-critical application development
- Incorporate organizational constraints (cloud providers, tech stacks, engineering practices)
- Support enterprise design systems and compliance requirements

### User-centric development

- Build applications for different user cohorts and preferences
- Support various development approaches (from vibe-coding to AI-native development)

### Creative & iterative processes

- Validate the concept of parallel implementation exploration
- Provide robust iterative feature development workflows
- Extend processes to handle upgrades and modernization tasks

## 🔧 Prerequisites

- **Linux/macOS/Windows**
- [Supported](#-supported-ai-agents) AI coding agent.
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

If you encounter issues with an agent, please open an issue so we can refine the integration.

## 📖 Learn More

- **[Complete Spec-Driven Development Methodology](./spec-driven.md)** - Deep dive into the full process
- **[Detailed Walkthrough](#-detailed-process)** - Step-by-step implementation guide

---

## 📋 Detailed Process

<details>
<summary>Click to expand the detailed step-by-step walkthrough</summary>

You can use the Specify CLI to bootstrap your project, which will bring in the required artifacts in your environment. Run:

```bash
specify init <project_name>
```

Or initialize in the current directory:

```bash
specify init .
# or use the --here flag
specify init --here
# Skip confirmation when the directory already has files
specify init . --force
# or
specify init --here --force
```

![Specify CLI bootstrapping a new project in the terminal](./media/specify_cli.gif)

You will be prompted to select the AI agent you are using. You can also proactively specify it directly in the terminal:

```bash
specify init <project_name> --ai claude
specify init <project_name> --ai gemini
specify init <project_name> --ai copilot

# Or in current directory:
specify init . --ai claude
specify init . --ai codex

# or use --here flag
specify init --here --ai claude
specify init --here --ai codex

# Force merge into a non-empty current directory
specify init . --force --ai claude

# or
specify init --here --force --ai claude
```

During `specify init`, the CLI validates only the selected `--ai` tool when that agent requires a CLI binary. If you prefer to scaffold templates without that check, use `--ignore-agent-tools`:

```bash
specify init <project_name> --ai claude --ignore-agent-tools
```

### **STEP 1:** Establish project principles

Go to the project folder and run your AI agent. In our example, we're using `claude`.

![Bootstrapping Claude Code environment](./media/bootstrap-claude-code.gif)

You will know that things are configured correctly if you see the `/sdd.constitution`, `/sdd.specify`, `/sdd.plan`, `sdd.plan.*`, `/sdd.tasks`, and `/sdd.implement` commands available.

The first step should be establishing your project's governing principles using the `/sdd.constitution` command. This helps ensure consistent decision-making throughout all subsequent development phases:

```text
/sdd.constitution Create principles focused on code quality, testing standards, user experience consistency, and performance requirements. Include governance for how these principles should guide technical decisions and implementation choices.
```

This step creates or updates the `.specify/memory/constitution.md` file with your project's foundational guidelines that the AI agent will reference during specification, planning, and implementation phases.

### **STEP 2:** Create project specifications

With your project principles established, you can now create the functional specifications. Use the `/sdd.specify` command and then provide the concrete requirements for the project you want to develop.

> [!IMPORTANT]
> Be as explicit as possible about *what* you are trying to build and *why*. **Do not focus on the tech stack at this point**.

An example prompt:

```text
Develop Taskify, a team productivity platform. It should allow users to create projects, add team members,
assign tasks, comment and move tasks between boards in Kanban style. In this initial phase for this feature,
let's call it "Create Taskify," let's have multiple users but the users will be declared ahead of time, predefined.
I want five users in two different categories, one product manager and four engineers. Let's create three
different sample projects. Let's have the standard Kanban columns for the status of each task, such as "To Do,"
"In Progress," "In Review," and "Done." There will be no login for this application as this is just the very
first testing thing to ensure that our basic features are set up. For each task in the UI for a task card,
you should be able to change the current status of the task between the different columns in the Kanban work board.
You should be able to leave an unlimited number of comments for a particular card. You should be able to, from that task
card, assign one of the valid users. When you first launch Taskify, it's going to give you a list of the five users to pick
from. There will be no password required. When you click on a user, you go into the main view, which displays the list of
projects. When you click on a project, you open the Kanban board for that project. You're going to see the columns.
You'll be able to drag and drop cards back and forth between different columns. You will see any cards that are
assigned to you, the currently logged in user, in a different color from all the other ones, so you can quickly
see yours. You can edit any comments that you make, but you can't edit comments that other people made. You can
delete any comments that you made, but you can't delete comments anybody else made.
```

After this prompt is entered, you should see Claude Code kick off the planning and spec drafting process. Claude Code will also trigger some of the built-in scripts to set up the repository.

Once this step is completed, you should have a new branch created (e.g., `feature-20250708-create-taskify`), as well as a new specification in the `specs/20250708-create-taskify` directory.

The produced specification should contain a set of user stories and functional requirements, as defined in the template.

At this stage, your project folder contents should resemble the following:

```text
└── .specify
    ├── memory
    │  └── constitution.md
    ├── scripts
    │  ├── check-prerequisites.sh
    │  ├── common.sh
    │  ├── create-new-feature.sh
    │  ├── setup-plan.sh
    │  └── update-claude-md.sh
    ├── specs
    │  └── 20250708-create-taskify
    │      └── spec.md
    └── templates
        ├── contract-template.md
        ├── data-model-template.md
        ├── plan-template.md
        ├── research-template.md
        ├── spec-template.md
        ├── test-matrix-template.md
        └── tasks-template.md
```

### **STEP 3:** Functional specification clarification (required before planning)

With the baseline specification created, you can go ahead and clarify any of the requirements that were not captured properly within the first shot attempt.

You should run the structured clarification workflow **before** creating a technical plan to reduce rework downstream.

Preferred order:

1. Use `/sdd.clarify` (structured) – sequential, coverage-based questioning that records answers in a Clarifications section.
2. Optionally follow up with ad-hoc free-form refinement if something still feels vague.

If you intentionally want to skip clarification (e.g., spike or exploratory prototype), explicitly state that so the agent doesn't block on missing clarifications.

Example free-form refinement prompt (after `/sdd.clarify` if still needed):

```text
For each sample project or project that you create there should be a variable number of tasks between 5 and 15
tasks for each one randomly distributed into different states of completion. Make sure that there's at least
one task in each stage of completion.
```

Checklist validation is a post-plan vertical pass with a hard `plan.md` gate. After Step 4 creates `plan.md`, run:

```text
/sdd.checklist
```

It's important to use the interaction with Claude Code as an opportunity to clarify and ask questions around the specification - **do not treat its first attempt as final**.

### **STEP 4:** Initialize the planning control plane

You can now be specific about the tech stack and other technical requirements. Use `/sdd.plan`:

```text
/sdd.plan We are going to generate this using .NET Aspire, using Postgres as the database. The frontend should use
Blazor server with drag-and-drop task boards, real-time updates. There should be a REST API created with a projects API,
tasks API, and a notifications API.
```

The output of this step will initialize `plan.md` as the planning control plane. It contains:

- `Shared Context Snapshot`
- `Stage Queue`
- `Binding Projection Index`
- `Artifact Status`

At this point the downstream planning artifacts are still generated by `sdd.plan.*` child commands.

The directory tree after `/sdd.plan` will resemble this:

```text
.specify
├── memory
│  └── constitution.md
├── scripts
│  ├── check-prerequisites.sh
│  ├── common.sh
│  ├── create-new-feature.sh
│  ├── setup-plan.sh
│  └── update-claude-md.sh
└── templates
    ├── contract-template.md
    ├── data-model-template.md
    ├── CLAUDE-template.md
    ├── plan-template.md
    ├── research-template.md
    ├── spec-template.md
    ├── test-matrix-template.md
    └── tasks-template.md

specs/
└── 20250708-create-taskify
    ├── plan.md
    └── spec.md
```

All generation commands must read runtime templates from `.specify/templates/`. `/sdd.plan` uses `.specify/templates/plan-template.md` for `plan.md`, and the `sdd.plan.*` child commands use their corresponding runtime templates under `.specify/templates/` to generate the stage artifacts.

### **STEP 5:** Execute the planning queue

Run the child commands in queue order:

```text
/sdd.plan.research
/sdd.plan.data-model
/sdd.plan.test-matrix
/sdd.plan.contract
```

`/sdd.plan.contract` is a repeated command. Each run processes one queued unit from `plan.md`, updates that unit's status, and then emits a `Handoff Decision` derived only from the post-update queue state in `plan.md`. The generated contract is the operation-scoped interface artifact, including the authoritative `Full Field Dictionary (Operation-scoped)` used downstream. The `Handoff Decision` should include the next command inferred from the same active feature branch queue state.

Static command frontmatter `handoffs` are advisory metadata only. They may point to one unconditional next command, but they are not the authority for state-dependent routing.

Check the resulting planning artifacts as they are generated. For example, validate `research.md` after `/sdd.plan.research`, then `data-model.md`, `test-matrix.md`, and the queued contract artifacts.

Additionally, you might want to ask Claude Code to research details about the chosen tech stack if it's something that is rapidly changing (e.g., .NET Aspire, JS frameworks), with a prompt like this:

```text
I want you to go through the implementation plan and implementation details, looking for areas that could
benefit from additional research as .NET Aspire is a rapidly changing library. For those areas that you identify that
require further research, I want you to update the research document with additional details about the specific
versions that we are going to be using in this Taskify application and spawn parallel research tasks to clarify
any details using research from the web.
```

During this process, you might find that Claude Code gets stuck researching the wrong thing - you can help nudge it in the right direction with a prompt like this:

```text
I think we need to break this down into a series of steps. First, identify a list of tasks
that you would need to do during implementation that you're not sure of or would benefit
from further research. Write down a list of those tasks. And then for each one of these tasks,
I want you to spin up a separate research task so that the net results is we are researching
all of those very specific tasks in parallel. What I saw you doing was it looks like you were
researching .NET Aspire in general and I don't think that's gonna do much for us in this case.
That's way too untargeted research. The research needs to help you solve a specific targeted question.
```

> [!NOTE]
> Claude Code might be over-eager and add components that you did not ask for. Ask it to clarify the rationale and the source of the change.

### **STEP 6:** Audit model and optional checklist (`/sdd.analyze`, `/sdd.checklist`)

With the plan in place, proceed to `/sdd.tasks` as the main flow. Avoid ad hoc audit prompts here. After `/sdd.tasks`, run `/sdd.analyze` as the default pre-implementation audit pass: it combines lint-backed mechanical checks with cross-artifact semantic findings across `spec.md`, `plan.md`, and `tasks.md` (drift, contradictions, repo-anchor misuse, audit payload leakage, uncovered MUST requirements, and boundary violations).
Each `/sdd.analyze` run appends its report and gate decision to `FEATURE_DIR/audits/analyze-history.md` as an append-only audit history.

If you want checklist-style validation, run `/sdd.checklist` as a separate standalone vertical pass rather than folding checklist burden back into the main-flow artifacts.

You can also ask Claude Code (if you have the [GitHub CLI](https://docs.github.com/en/github-cli/github-cli) installed) to go ahead and create a pull request from your current branch to `main` with a detailed description, to make sure that the effort is properly tracked.

> [!NOTE]
> If you suspect over-engineered decisions or cross-artifact drift before implementation, use `/sdd.analyze` as the dedicated audit step and then adjust the upstream artifacts it flags. Ensure that Claude Code follows the [constitution](.specify/memory/constitution.md) as the foundational piece that it must adhere to when refining the plan. Repo semantic anchors come from source code plus `.specify/memory/constitution.md`; helper docs and prior generated artifacts are not repo anchors.

### **STEP 7:** Generate task breakdown with `/sdd.tasks`

With the implementation plan ready (and any optional vertical checks complete), you can now break down the plan into specific, actionable tasks that can be executed in the correct order. Use the `/sdd.tasks` command to automatically generate a detailed task breakdown from your implementation plan:

```text
/sdd.tasks
```

This step creates a `tasks.md` file in your feature specification directory that contains:

- **Execution scopes** - Shared foundation work is separated from interface delivery units (`GLOBAL` + `IF-###`), where each `IF-###` unit is an IF-scoped execution work package
- **Task DAG dependency model** - `Task DAG` is the execution authority for ordering and safe parallelism
- **File path specifications** - Each task includes the exact file paths where implementation should occur
- **Verification-first delivery loops** - Verify, implement, and completion tasks are grouped around each interface unit
- **Completion anchors** - Tasks carry deterministic pass signals such as contract checks, build/test commands, or case anchors

`/sdd.tasks` consumes approved planning artifacts and turns them into execution orchestration. It does not reopen research, data-model, or contract design, and it does not perform the unified cross-artifact semantic audit.

It should emit single-target work packages only: each task must carry one explicit path or command target plus one primary completion anchor. If required anchors are missing from `plan.md`, `contracts/`, or `test-matrix.md`, or if a selected contract is `blocked`, `/sdd.tasks` should stop and route back to the relevant `/sdd.plan.*` command rather than inferring new semantics or emitting `blocked`/`todo` placeholder tasks. Non-fatal contract hygiene issues (for example missing `Full Field Dictionary (Operation-scoped)` or tuple packet drift) should surface as preflight warnings and be routed as explicit upstream repair actions without hard-blocking task generation.

For faster runs, the prerequisite script may pre-extract a compact `TASKS_BOOTSTRAP` packet from `plan.md` so `/sdd.tasks` can reuse a joined control-plane inventory instead of reparsing the planning tables during the same run.
The same prerequisite payload also emits a `LOCAL_EXECUTION_PROTOCOL` packet as a run-local projection of constitution-defined execution policy. Its packaged SDD core runtime inventory is intentionally narrow: `specify-cli`, `git`, and `rg`. SDD-owned helpers run through explicit `specify-cli` entrypoints such as `specify internal-task-bootstrap`, `specify internal-data-model-bootstrap`, and `specify internal-implement-bootstrap` so execution-phase commands do not spend time guessing equivalent CLIs.

Run `/sdd.analyze` after `/sdd.tasks` as the default pre-implementation audit pass for repo-anchor misuse, audit payload leakage, drift, contradictions, boundary violations, uncovered MUST requirements, and other cross-artifact issues.

The generated tasks.md provides a clear roadmap for the `/sdd.implement` command, ensuring systematic implementation that maintains code quality without turning the task artifact itself into an audit ledger.

### **STEP 8:** Implementation

Once ready, use the `/sdd.implement` command to execute your implementation plan:

```text
/sdd.implement
```

The `/sdd.implement` command is execution plus runtime hard gates. It is not the unified semantic audit step; by default it requires current `/sdd.analyze` evidence with `Gate Decision: PASS` for the current task artifacts.
It should also reuse the emitted `LOCAL_EXECUTION_PROTOCOL` and repo-backed task anchors for local commands instead of trial-and-error across search tools, package managers, or Python runners. SDD-owned helpers should run through packaged `specify-cli` internal commands rather than user-managed interpreters or repo-local `uv run python`.
Current analyze-pass evidence is read from the latest run block in `FEATURE_DIR/audits/analyze-history.md`; missing evidence, stale fingerprint mismatches, or `Gate Decision: FAIL` should block implementation unless the run includes an explicit analyze-gate waiver.

The `/sdd.implement` command will:

- Validate that all prerequisites are in place (constitution, spec, plan, and tasks)
- Parse the execution plan from `tasks.md`
- Execute tasks according to `Task DAG`, `GLOBAL`, and `IF-###` execution work packages
- Follow the TDD approach defined in your task plan
- Provide progress updates, honor strict/adaptive execution mode, and stop for upstream repair when runtime drift exceeds safe local adaptation

> [!IMPORTANT]
> The AI agent will execute local CLI commands (such as `dotnet`, `npm`, etc.) - make sure you have the required tools installed on your machine.

Once the implementation is complete, test the application and resolve any runtime errors that may not be visible in CLI logs (e.g., browser console errors). You can copy and paste such errors back to your AI agent for resolution.

</details>

---

## 🔍 Troubleshooting

### Git Credential Manager on Linux

If you're having issues with Git authentication on Linux, you can install Git Credential Manager:

```bash
#!/usr/bin/env bash
set -e
echo "Downloading Git Credential Manager v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Installing Git Credential Manager..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Configuring Git to use GCM..."
git config --global credential.helper manager
echo "Cleaning up..."
rm gcm-linux_amd64.2.6.1.deb
```

## 💬 Support

For support, please open a [GitHub issue](https://github.com/bigsmartben/sdd/issues/new). We welcome bug reports, feature requests, and questions about using Spec-Driven Development.

## 🙏 Acknowledgements

This project is heavily influenced by and based on the work and research of [John Lam](https://github.com/jflam).

## 📄 License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) file for the full terms.

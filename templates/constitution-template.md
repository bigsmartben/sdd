# Project Constitution

This constitution defines the long-lived normative rules and ownership boundaries for this project.
It exists to ensure consistency across specification, planning, and implementation.

---

## Artifact Quality Signals
- Must: read like durable repository governance.
- Strictly: keep rules normative, long-lived, and the single shortest source of truth.
- **Prohibited**: Process explainers, template tutorials, or patch logs.

---

## Core Principles
**Rules**: MUST be declarative and testable. **Prohibited**: Vague language ("should").

- **Principle 1**: [ succinct name ]
  - **Rule**: [ required/prohibited ]
  - **Scope**: [ where it applies ]
  - **Rationale**: [ non-obvious reason ]

---

## Governance & Terminology
- **"Contract model"** means ... and **MUST NOT** be confused with persistence schema.
- **"Business state"** **MUST NOT** be mixed with workflow status.
- **"URFGP"** (Unified Repository-First Gate Protocol): The shared authority for repository-first gating.
- **"RFEB"** (Repository-First Evidence Bundle): The standard format for emitting decision evidence (`fact -> conclusion`).

---

## Repo-Anchor Evidence Protocol

### Repo-Anchor Evidence Protocol
- **Strategy Priority**: STRICT ORDER — evaluate and apply in strict order: `existing` -> `extended` -> `new`.
- **New-Anchor Rule**: `new` is only valid when both `existing` and `extended` are explicitly rejected with evidence.
- **Evidence Baseline**: Canonical baseline files land in `.specify/memory/repository-first/`:
  - `.specify/memory/repository-first/technical-dependency-matrix.md`
  - `.specify/memory/repository-first/module-invocation-spec.md`
- **Source anchors**: source-code files/symbols
- **Engineering assembly facts**: build/module manifests

---

## Local Execution Protocol Governance
- **Authority**: `constitution.md` is the SSOT for local execution rules.
- **Tooling Isolation**: SDD-owned Python helpers MUST use the `specify-cli` tool runtime.
- **LOCAL_EXECUTION_PROTOCOL**: defined per-run by the prerequisite bootstrap packet.
- **Prohibited**: Installing missing tools, mutating `PATH`, or switching package managers during a run.

---

## Amendment History
- **RATIFICATION_DATE**: [DATE]
- **LAST_AMENDED_DATE**: [DATE]
- **CONSTITUTION_VERSION**: [X.Y.Z]

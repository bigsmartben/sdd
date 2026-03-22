# Prompt Style Baseline (SDD v2.0)

This baseline defines the strict authoring rules for all SDD commands and templates.
Its goal is to minimize token usage, eliminate semantic drift, and focus on non-negotiable behavior.

## 1. Goal & Boundary First (The "Why" Sentence)
- **Rule**: Every command/template must start with one concise description line.
- **Limit**: No "purpose" or "this is for" essays.
- **Example**: `Generate one review-ready ui.html from the resolved spec.md.`

## 2. Rule Selection & Compression
- **Prefer Rules over Prose**: Use `MUST`/`MUST NOT`/`SHOULD` directly.
- **No Teaching**: Do not explain "why this is a good idea" or "how it helps the workflow" unless it's a technical constraint.
- **Merge Synonyms**: If three rules say "do not change upstream", use one `MUST NOT overwrite upstream`.
- **Bullet Lists for Prohibitions**: Replace multiple `Do not...` sentences with one `Prohibited:` list.
- **Table for Enumerations**: Use tables or short lists for field definitions instead of descriptive paragraphs.

## 3. Standard Sections (Mandatory Skeleton)
To keep reading cognitive load low, every command prompt should follow this order:
1. **User Input / Argument Parsing** (The data coming in)
2. **Goal** (The single output intent)
3. **Governance / Authority** (The boundary of the command)
4. **Allowed Inputs** (The strict read scope)
5. **Reasoning Order** (The step-by-step logic)
6. **Output Quality / Contract** (The validation bar)
7. **Writeback Contract** (Where results land)
8. **Handoff Decision** (Where the agent goes next)

## 4. Redundancy Control
- **No Stage Prose**: Do not repeat "This is Stage X of Y" unless required for path resolution.
- **No Restatement**: If a rule is in `AGENTS.md` or a global rule file, reference it; do not clone its full text.
- **Compressed Handoffs**: Use `Next Command`, `Decision Basis`, and `Ready/Blocked` exclusively.
- **Unified Gate Description**: Use **Unified Repository-First Gate Protocol (URFGP)** and **Repository-First Evidence Bundle (RFEB)** instead of expanding gate prose.

## 5. Visual Hierarchy
- **Headers**: Use `##` for main sections, `###` only when required.
- **Emphasis**: Use **bold** for keywords (`MUST`, `PLAN_FILE`, `BindingRowID`).
- **No Filler**: Delete "IMPORTANT:", "Please note:", or "Follow this execution flow" if the rule context is already clear.

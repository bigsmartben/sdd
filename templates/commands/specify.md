---
description: Create or update the feature specification from a natural language feature description.
handoffs:
  - label: Clarify Spec Requirements
    agent: sdd.clarify
    prompt: Clarify specification requirements
    send: true
  - label: Generate Interactive Prototype
    agent: sdd.specify.ui-html
    prompt: Create an interactive prototype by running /sdd.specify.ui-html <path/to/spec.md> with the explicit spec.md path produced in this step.
    send: true
  - label: Build Technical Plan
    agent: sdd.plan
    prompt: Create a plan by running /sdd.plan <path/to/spec.md> with the explicit spec.md path produced in this step. I am building with...
scripts:
  sh: scripts/bash/create-new-feature.sh "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 "{ARGS}"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/sdd.specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `{ARGS}` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

## Backbone-First Guardrails (mandatory)

When generating or updating `spec.md`, enforce backbone-first output and keep content domain-generic unless the user explicitly provides domain details.

- Keep the backbone order stable:
  1. Global business overview
  2. Context/system boundaries
  3. UC set and priorities
  4. User-visible data entities (UDD)
  5. Key interaction/feedback/publish-validation rules
  6. Open questions only when blocking
- Do **not** hardcode analysis-only sample domains, entities, UC names, or project identifiers into the final spec.
- Do **not** spend tokens on side-track verification narratives in the spec body; keep focus on core business flow.
- Preserve template reusability across projects.
- Treat any domain noun not grounded in current user input as suspect until validated.

Given that feature description, do this:

1. **Generate a concise short name** (2-4 words) for the branch:
   - Analyze the feature description and extract the most meaningful keywords
   - Create a 2-4 word short name that captures the essence of the feature
   - Use action-noun format when possible (e.g., "add-user-auth", "fix-payment-bug")
   - Preserve technical terms and acronyms (OAuth2, API, JWT, etc.)
   - Keep it concise but descriptive enough to understand the feature at a glance
   - Examples:
     - "I want to add user authentication" → "user-auth"
     - "Implement OAuth2 integration for the API" → "oauth2-api-integration"
     - "Create a dashboard for analytics" → "analytics-dashboard"
     - "Fix payment processing timeout bug" → "fix-payment-timeout"

2. **Resolve the feature key and spec path** by running the script with `--short-name` (and `--json`), and do NOT pass `--number` (the script auto-detects the next globally available number when fallback naming is needed):

   - Bash example: `{SCRIPT} --json --short-name "user-auth" "Add user authentication"`
   - PowerShell example: `{SCRIPT} -Json -ShortName "user-auth" "Add user authentication"`

   **IMPORTANT**:
   - Do NOT pass `--number` — the script determines the correct next number automatically
   - Always include the JSON flag (`--json` for Bash, `-Json` for PowerShell) so the output can be parsed reliably
   - You must only ever run this script once per feature
   - The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for
   - The JSON output will contain BRANCH_NAME and SPEC_FILE paths
   - The script must not switch branches; it uses the current branch when it already matches `feature-YYYYMMDD-short-name` (or legacy `NNN-short-name`), otherwise it generates fallback naming without checkout
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot")

3. Load `.specify/templates/spec-template.md` to understand required sections. This runtime template path is mandatory; if the file is missing or non-consumable, stop and report the blocker. Do not substitute `templates/spec-template.md` or any other template location.

**Authority and derivation rules**:

- Any extracted actor lists, term sets, requirement drafts, or working summaries used during `/sdd.specify` are derived working views only.
- `spec.md` becomes the authoritative feature-semantics artifact only after the current refinement/validation cycle is written successfully.
- `ui.html` generated later by `/sdd.specify.ui-html` is a derived prototype artifact and MUST NOT override `spec.md`.
- If clarification answers, validation rewrites, or scope edits change feature meaning, discard stale derived notes and re-derive from the current `spec.md` content before handoff.

1. Follow this execution flow:

    1. Parse user description from Input
       If empty: ERROR "No feature description provided"
    2. Extract key concepts from description
       Identify: actors, actions, data, constraints
    3. For unclear aspects:
       - Make informed guesses based on context and industry standards
       - Only mark with [NEEDS CLARIFICATION: specific question] if:
         - The choice significantly impacts feature scope or user experience
         - Multiple reasonable interpretations exist with different implications
         - No reasonable default exists
       - **LIMIT: Maximum 5 [NEEDS CLARIFICATION] markers total**
       - Prioritize clarifications by impact: scope > security/privacy > user experience > technical details
       - Never use example-domain placeholders from prior analysis as if they were user requirements
    4. Build Global Context and boundaries
       - Define actors
       - Define in-scope and out-of-scope boundaries
       - Keep this section business-semantic only (no governance/process-control payload)
    5. Build field-level UDD (mandatory)
       - Define core user-visible entities
       - Define `Entity.field` rows with business calculation, boundaries, display rules, source type, and key path
       - If user-visible data exists but no field-level UDD is provided: ERROR "UDD is required for user-visible data"
    6. Build UC Overview and FR Index
       - Define UC table with priority
       - Define FR Index mapping UC ↔ FR ↔ scenarios
       - Keep UC naming generic and requirement-driven; avoid importing sample UC labels unless provided by user input
    7. Build heavy UX flow sections
       - Create Global UX Flow Overview for cross-UC flows
       - For each interactive UC, provide main flow (Mermaid), path inventory, interaction step table, exception paths, postconditions
       - If interactive UC lacks flow tables: ERROR "Heavy UX flow tables are required for interactive UCs"
    8. Build UI sections (UI subnode)
       - For each user-facing UC, define page/view info, component definitions, state rules, and component-data dependency table
    9. Generate Functional Requirements
       Each requirement must be testable and linked to scenarios and UDD references
    10. Define Success Criteria
       Create measurable, technology-agnostic outcomes
       Include both quantitative metrics (time, performance, volume) and qualitative measures (user satisfaction, task completion)
       Each criterion must be verifiable without implementation details
    11. Add Environment Edge Cases
    12. Add Assumptions/Open Questions only when needed
    13. Return: SUCCESS (spec ready for planning)

2. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.
   - Ensure all concrete names come from user input or reasonable neutral defaults (not from unrelated example projects).

3. **Specification Quality Self-Validation**: After writing the initial spec, validate it in-command against quality criteria (do **not** create checklist artifacts in this command):

   a0. **Run an Anti-Solidification Pass (mandatory before validation)**:
      - Build a term set from current user input (`$ARGUMENTS`) plus neutral template vocabulary.
      - Scan the generated spec for domain/project/entity terms that are not supported by:
        1) user input,
        2) explicit assumptions written in this spec session, or
        3) neutral placeholders.
      - If unsupported terms are found, replace with neutral wording or terms derived from user input.
      - Do not keep legacy/example project terms from prior conversations.

   a. **Run Validation Check**: Review the spec against these criteria:
      - No implementation details (languages, frameworks, APIs)
      - Focused on user value and business needs
      - Written for non-technical stakeholders
      - All mandatory sections completed
      - No unsupported domain terms leaked from prior analysis/examples
      - No [NEEDS CLARIFICATION] markers remain
      - Requirements are testable and unambiguous
      - Success criteria are measurable and technology-agnostic
      - All acceptance scenarios and edge cases are defined
      - Scope is clearly bounded; dependencies and assumptions identified
      - All functional requirements have clear acceptance criteria
      - User scenarios cover primary flows

   b. **Handle Validation Results**:

      - **If all items pass**: proceed to step 7.

      - **If items fail (excluding [NEEDS CLARIFICATION])**:
        1. List the failing items and specific issues
        2. Update the spec to address each issue
        3. Re-run validation until all items pass (max 3 iterations)
        4. If still failing after 3 iterations, document remaining issues in the completion report and warn user

      - **If [NEEDS CLARIFICATION] markers remain**:
        1. Extract all [NEEDS CLARIFICATION: ...] markers from the spec
        2. **LIMIT CHECK**: If more than 5 markers exist, keep only the 5 most critical (by scope/security/UX impact) and make informed guesses for the rest
        3. For each clarification needed (max 5), present options to user in this format:

           ```markdown
           ## Question [N]: [Topic]
           
           **Context**: [Quote relevant spec section]
           
           **What we need to know**: [Specific question from NEEDS CLARIFICATION marker]
           
           **Suggested Answers**:
           
           | Option | Answer | Implications |
           |--------|--------|--------------|
           | A      | [First suggested answer] | [What this means for the feature] |
           | B      | [Second suggested answer] | [What this means for the feature] |
           | C      | [Third suggested answer] | [What this means for the feature] |
           | Custom | Provide your own answer | [Explain how to provide custom input] |
           
           **Your choice**: _[Wait for user response]_
           ```

        4. **CRITICAL - Table Formatting**: Ensure markdown tables are properly formatted:
           - Use consistent spacing with pipes aligned
           - Each cell should have spaces around content: `| Content |` not `|Content|`
           - Header separator must have at least 3 dashes: `|--------|`
           - Test that the table renders correctly in markdown preview
        5. Number questions sequentially (Q1...Q5 - max 5 total)
        6. Present all questions together before waiting for responses
        7. Wait for user to respond with their choices for all questions (e.g., "Q1: A, Q2: Custom - [details], Q3: B")
        8. Update the spec by replacing each [NEEDS CLARIFICATION] marker with the user's selected or provided answer
        9. Re-run validation after all clarifications are resolved

4. Report completion with branch name, spec file path, and readiness for the next phase (run `/sdd.specify.ui-html <path/to/spec.md>` for an interactive prototype if needed, then `/sdd.clarify` first, then `/sdd.plan`; if user explicitly skips clarification, warn about increased downstream rework risk and then proceed). If checklist-style validation output is needed, direct users to run `/sdd.checklist <path/to/plan.md>` as a separate vertical command after `/sdd.plan`.

**NOTE:** The script initializes the `specs/<feature-key>/spec.md` path (`feature-key = YYYYMMDD-short-name` for preferred branch naming) and never performs branch checkout/switch.

## General Guidelines

## Quick Guidelines

- Focus on **WHAT** users need and **WHY**.
- Avoid HOW to implement (no tech stack, APIs, code structure).
- Written for business stakeholders, not developers.
- DO NOT create any checklists that are embedded in the spec. That will be a separate command.
- Do NOT add governance content in spec (no SSOT governance states, stage dispatchers, interface registries, conversion reports, or coverage audit sections).
- Do NOT inject prior analysis examples as project facts (keep template outputs portable and domain-neutral).

### Section Requirements

- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### Required Spec Structure Rules (for this template)

1. **Field-level UDD is mandatory** for core user-visible data.
2. **Heavy UX flow tables are mandatory** for interactive UCs:
   - Preconditions
   - Main Flow (Mermaid)
   - Path Inventory
   - Interaction Step Table
   - Exception Paths
   - Postconditions
3. **UI and UX subnodes are mandatory** for user-facing/interactive UCs.
4. Keep spec focused on business semantics; avoid governance/process-control sections.

### For AI Generation

When creating this spec from a user prompt:

1. **Make informed guesses**: Use context, industry standards, and common patterns to fill gaps
2. **Document assumptions**: Record reasonable defaults in the Assumptions section
3. **Limit clarifications**: Maximum 5 [NEEDS CLARIFICATION] markers - use only for critical decisions that:
   - Significantly impact feature scope or user experience
   - Have multiple reasonable interpretations with different implications
   - Lack any reasonable default
4. **Prioritize clarifications**: scope > security/privacy > user experience > technical details
5. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
6. **Common areas needing clarification** (only if no reasonable default exists):
   - Feature scope and boundaries (include/exclude specific use cases)
   - User types and permissions (if multiple conflicting interpretations possible)
   - Security/compliance requirements (when legally/financially significant)

**Examples of reasonable defaults** (don't ask about these):

- Data retention: Industry-standard practices for the domain
- Performance targets: Standard web/mobile app expectations unless specified
- Error handling: User-friendly messages with appropriate fallbacks
- Authentication method: Standard session-based or OAuth2 for web apps
- Integration patterns: Use project-appropriate patterns (REST/GraphQL for web services, function calls for libraries, CLI args for tools, etc.)

### Success Criteria Guidelines

Success criteria must be:

1. **Measurable**: Include specific metrics (time, percentage, count, rate)
2. **Technology-agnostic**: No mention of frameworks, languages, databases, or tools
3. **User-focused**: Describe outcomes from user/business perspective, not system internals
4. **Verifiable**: Can be tested/validated without knowing implementation details

**Good examples**:

- "Users can complete checkout in under 3 minutes"
- "System supports 10,000 concurrent users"
- "95% of searches return results in under 1 second"
- "Task completion rate improves by 40%"

**Bad examples** (implementation-focused):

- "API response time is under 200ms" (too technical, use "Users see results instantly")
- "Database can handle 1000 TPS" (implementation detail, use user-facing metric)
- "React components render efficiently" (framework-specific)
- "Redis cache hit rate above 80%" (technology-specific)

### Validation Additions for New Structure

When validating the generated spec, also ensure:

- UDD exists and is field-level (`Entity.field`) for core user-visible entities
- Each interactive UC includes the heavy UX flow tables
- Each user-facing UC includes UI definitions and component-data dependency table
- FR sections reference scenarios and relevant UDD fields
- No governance/audit payload is embedded in the spec body
- No carry-over domain identifiers appear unless traceable to current user input or explicit in-spec assumptions

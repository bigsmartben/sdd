# Research: [FEATURE]

**Stage**: Stage 0 Research  
**Inputs**: `spec.md`, user input, targeted source-code reads, `.specify/memory/constitution.md`

Use this artifact to capture planning-blocking research only. Keep it decision-oriented, concise, and grounded in evidence.
For `/sdd.plan.research`, repository reuse evidence comes from source code and `.specify/memory/constitution.md`. Repository-first baseline files are consumed by `/sdd.plan` as shared bootstrap inputs and MAY be referenced here only when a research decision depends on an existing canonical dependency usage row, module-edge rule, or `SIG-*` signal. Do not treat `README.md`, `docs/**`, `specs/**`, demos, or generated artifacts as repo anchors in this file.

## Decisions

| ID | Decision | Rationale | Evidence / Source | Downstream Impact |
|----|----------|-----------|-------------------|-------------------|
| R-001 | [Decision] | [Why this choice was made] | [Repo Source Anchor, Constitution, and/or Spec/User Input] | [What later stages must follow] |

## Repository Reuse Anchors (Source Code Only)

List only source-code modules, symbols, or tests that later stages should reuse. Do not list `README.md`, `docs/**`, `specs/**`, or generated artifacts here.

| Anchor | Source Path / Symbol | Reuse Intent |
|--------|----------------------|--------------|
| [Existing module / pattern] | `[path/to/file.ext::Symbol]` | [How later stages should reuse it] |

## Constraints

- [Constraint that later stages must obey]
- [Version, platform, security, or organizational limitation]

## Blocking Open Questions

- [Only unresolved questions that materially block planning]

## Boundary Notes

- Do not define global models, scenario matrices, contracts, or interface-level detailed design here.
- Do not turn this document into a broad technology survey or implementation log.
- Do not present helper docs or prior generated artifacts as repository reuse anchors.

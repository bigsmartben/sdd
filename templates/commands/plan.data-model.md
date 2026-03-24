---
description: Generate data-model.md and align shared semantics from spec.md and test-matrix.md.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --data-model-preflight
  ps: scripts/powershell/check-prerequisites.ps1 -Json -DataModelPreflight
---

## User Input

```text
$ARGUMENTS
```

Treat all `$ARGUMENTS` as optional direction.
Resolve `PLAN_FILE` using `{SCRIPT}` defaults.

## Goal

Generate one `data-model.md` for the current feature branch.
Use `.specify/templates/data-model-template.md` only.

`/sdd.plan.data-model` owns:
- Shared business semantics (Shared Semantic Elements - SSE).
- Shared owner/source alignment for entities and fields.
- Vocabulary and lifecycle/invariant rules (Shared Field Vocabulary - SFV).

The output MUST define only the shared, stable, reusable semantics — not operation-scoped types or interface-local names.
It MUST close shared semantic ownership, lifecycle vocabulary, invariant refs, and explicit `new` decisions before `/sdd.plan.contract`.

## Stage Packet (Data-Model Unit)

Run `{SCRIPT}` to resolve `FEATURE_DIR`, `PLAN_FILE`, and `DATA_MODEL_BOOTSTRAP`.

If `DATA_MODEL_BOOTSTRAP` is missing, malformed, contradictory, or unavailable, stop immediately and report a hard blocker.

1. Treat `DATA_MODEL_BOOTSTRAP.generation_readiness` as the primary queue/readiness gate.
   - If `generation_readiness.ready_for_generation = false`, stop and report the bootstrap blocker; do not default to `/sdd.plan.contract`.
   - Consume `DATA_MODEL_BOOTSTRAP.recovery_handoff`: if a recovery route is specified, route there and do not default to `/sdd.plan.contract`.
2. Consume `DATA_MODEL_BOOTSTRAP.selected_stage` as the authoritative queue context for this run.
   - runtime selection order is authoritative: first `pending` `data-model` row, then fallback `data-model` row, then synthetic row if absent.
3. Do not recompute stage-row hard gates locally; bootstrap `generation_readiness` + `recovery_handoff` are the authority.
4. Resolve and consume the packet's resolved `plan.md` / `spec.md` / `test-matrix.md` / `data-model.md` paths.
5. Use this packet as the default context for generation.

## Governance / Authority

- **Authority rule**: `data-model.md` is the shared-semantic authority for the feature branch.
- **Stage boundary rule**: No operation-scoped DTOs or collaborator chains.
  - Do not define HTTP routes, controller/service/facade naming, contract-flavored shared names such as `*DTO`, `*Request`, `*Response`, `*Command`, or `*Result`, request/response shapes, operation-scoped command/result models, or repo interface-anchor placement here; those belong to `/sdd.plan.contract`.
- **Shared protocol rule**: Apply **Unified Repository-First Gate Protocol (URFGP)**.

## Allowed Inputs

- `.specify/templates/data-model-template.md` (structure)
- `PLAN_FILE` (queue state and shared snapshot)
- `FEATURE_SPEC` (UDD / interactions authority)
- `test-matrix.md` (binding packets authority)
- Bounded repo evidence (existing entities, persistence models, shared services)
- Use optional `research.md` path only when `spec.md` + `test-matrix.md` wording leaves the shared-semantic boundary ambiguous.

**Prohibited**: `contracts/` or broad symbol scans.

## Semantic Closure Rules

- Shared semantics that are confirmed by `spec.md` + `test-matrix.md` MUST be closed here at owner/source/lifecycle level.
- Shared semantic closure MUST stay explicit in `SSE` / `OSA` / `SFV` / `LC` / `INV` / `DCC`; do not leave owner/source/lifecycle/invariant semantics as narrative-only prose.
- Shared-vs-local classification MUST precede lifecycle/FSM modeling; do not start from state diagrams and backfill shared owners later.
- Mandatory closure order for this stage: shared-vs-local decision -> `SSE` -> `OSA` -> `SFV` -> `LC/INV/FSM`.
- If `existing` and `extended` are both insufficient, `new` is the required outcome for this stage.
- If `existing` and `extended` cannot safely close a confirmed shared semantic, this stage MUST explicitly choose `new` here rather than deferring to contract.
- If a confirmed shared semantic cannot land as `existing` or `extended`, introduce the required `new` class/owner/lifecycle here instead of deferring the decision.
- When `Anchor Status = new`, record repo-first strategy evidence (explain why `existing` and `extended` were rejected).
- Shared semantic names and UML/class labels in this stage MUST avoid contract-flavored suffixes.
- Every shared field, projection, derived value, and lifecycle state MUST close to one explicit owner/source row in `Owner / Source Alignment`.
- Lifecycle guards/invariants MUST reuse shared vocabulary from `SFV`; do not restate interface actions as lifecycle semantics.
- Lifecycle `State Owner` values MUST map to an established `SSE`/`OSA` owner; state machines MUST NOT invent shared owners in reverse.
- Every lifecycle row MUST cite concrete `INV-*` refs; invariant closure belongs here, not in `/sdd.plan.contract`.
- Downstream `/sdd.plan.contract` work MUST reuse shared refs produced here; do not duplicate alignment.
- Shared-semantic authority remains in `data-model.md`; downstream `contract` must consume by `SSE/OSA/SFV/LC/INV/DCC` refs and must not restate shared semantics as local prose authority.

## FSM Policy

- Consume `DATA_MODEL_BOOTSTRAP.state_machine_policy` for lifecycle thresholds, supported model kinds, and required sections/components.
- Use `DATA_MODEL_BOOTSTRAP.state_machine_policy.required_model_kinds` as the allowed `Required Model` vocabulary.
- Use `DATA_MODEL_BOOTSTRAP.state_machine_policy.required_sections_by_model` as the authoritative section contract for `lightweight` vs `fsm`.
- Use `DATA_MODEL_BOOTSTRAP.state_machine_policy.required_components_by_model` as the authoritative lifecycle-closure checklist.
- If `N > 3` or `T >= 2N`, emit `Required Model = fsm` and include transition table, transition pseudocode, invariant catalog rows, and state diagram.
- Otherwise keep the lifecycle `lightweight`, but still include lifecycle summary, invariant catalog, and transition table because they are primary reader views.
- `lightweight` rows MUST still close allowed transitions, forbidden transitions, and key invariants through `Invariant Catalog` + `State Transition Table`.

## Reasoning Order

1. **Semantic Selection**: Distinguish shared business semantics from repeated interface details.
2. **Owner Alignment**: Map each shared semantic to one repo-backed or `new` owner.
3. **Invariant Closure**: Close invariant vocabulary, allowed/forbidden transitions, and state owners before contract design.
4. **Downstream Constraints**: Emit `DCC-*` refs that force `/sdd.plan.contract` to reuse this shared-semantic authority.

## Artifact Quality Contract

- Must: close reusable shared semantics, owner/source alignment, lifecycle, invariants, and downstream reuse constraints before contract design.
- Must: make it obvious why a semantic is shared, who owns it, which `INV-*` refs govern it, and why contract cannot invent an alternative local model.
- Strictly: Shared semantic names and UML/class labels MUST avoid contract-flavored suffixes.

## Writeback Contract

- Create or refresh `data-model.md` using the runtime template.
- Modify only the selected `data-model` row plus blocker fields in `PLAN_FILE` `Stage Queue`.
- `Status = done`, `Output Path`, `Blocker`.
- May batch update only `Blocker` fields for affected `contract` rows in `PLAN_FILE` `Artifact Status` when shared-semantic readiness changes.
- MUST NOT rewrite `Target Path` / `Status` in `Artifact Status`, `Binding Projection Index`, `spec.md`, or `test-matrix.md`.

## Output Contract

- **SSE Table**: MUST map each shared element to one `existing|extended|new|todo` anchor.
- **OSA Table**: MUST close owner/source responsibility for shared fields, projections, and lifecycle state owners.
- **SFV Table**: MUST reuse binding packet refs for meaning and boundary rules.
- **Lifecycle Logic**: MUST include `Lifecycle Summary`, `Invariant Catalog`, `State Transition Table`, `Transition Pseudocode` when `Required Model = fsm`, and `State Diagram` when `Required Model = fsm`.
- **DCC Table**: MUST reference `SSE/OSA/SFV/LC/INV/DCC` refs so `/sdd.plan.contract` reuses shared semantics instead of reinventing them.
- **Determinism Rule**: when a shared semantic is unresolved, keep an explicit blocker row/ref and route downstream as `blocked`; do not emit dual interpretations.
- **Prohibited**: Interface-role names (`*DTO`, `*Request`, `*Response`, `*Controller`).

## Handoff Decision

Emit exactly these fields:
- `Next Command`: `DATA_MODEL_BOOTSTRAP.recovery_handoff.next_command`
- `Decision Basis`: `DATA_MODEL_BOOTSTRAP.recovery_handoff.decision_basis`
- `Selected Stage ID`: `DATA_MODEL_BOOTSTRAP.recovery_handoff.selected_stage_id`
- `Ready/Blocked`: `DATA_MODEL_BOOTSTRAP.recovery_handoff.ready_blocked`

When `Ready/Blocked = Ready`, continue contract generation directly without rerunning `test-matrix`.

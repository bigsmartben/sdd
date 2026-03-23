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
- If `existing` and `extended` are both insufficient, `new` is the required outcome for this stage.
- If `existing` and `extended` cannot safely close a confirmed shared semantic, this stage MUST explicitly choose `new` here rather than deferring to contract.
- If a confirmed shared semantic cannot land as `existing` or `extended`, introduce the required `new` class/owner/lifecycle here instead of deferring the decision.
- When `Anchor Status = new`, record repo-first strategy evidence (explain why `existing` and `extended` were rejected).
- Shared semantic names and UML/class labels in this stage MUST avoid contract-flavored suffixes.
- Downstream `/sdd.plan.contract` work MUST reuse shared refs produced here; do not duplicate alignment.
- Shared-semantic authority remains in `data-model.md`; downstream `contract` must consume by `SSE/OSA/SFV/LC/INV/DCC` refs and must not restate shared semantics as local prose authority.

## FSM Policy

- Consume `DATA_MODEL_BOOTSTRAP.state_machine_policy` for lifecycle thresholds.
- If `N > 3` or `T >= 2N`, emit a full FSM package (state-transition table + Mermaid diagram).
- Otherwise keep the lifecycle lightweight, but still include the transition table because it is a primary reader view.

## Reasoning Order

1. **Semantic Selection**: Distinguish shared business semantics from repeated interface details.
2. **Owner Alignment**: Map each shared semantic to one repo-backed or `new` owner.
3. **Closure**: Complete vocabulary and lifecycle rules for shared fields.

## Artifact Quality Contract

- Must: close reusable shared semantics, owner/source alignment, lifecycle, and invariants before contract design.
- Strictly: Shared semantic names and UML/class labels MUST avoid contract-flavored suffixes.

## Writeback Contract

- Create or refresh `data-model.md` using the runtime template.
- Modify only the selected `data-model` row plus blocker fields in `PLAN_FILE` `Stage Queue`.
- `Status = done`, `Output Path`, `Blocker`.
- May batch update only `Blocker` fields for affected `contract` rows in `PLAN_FILE` `Artifact Status` when shared-semantic readiness changes.
- MUST NOT rewrite `Target Path` / `Status` in `Artifact Status`, `Binding Projection Index`, `spec.md`, or `test-matrix.md`.

## Output Contract

- **SSE Table**: MUST map each shared element to one `existing|extended|new|todo` anchor.
- **SFV Table**: MUST reuse binding packet refs for meaning and boundary rules.
- **Lifecycle Logic**: Capture vocabulary, meaning, and invariants only.
- **Determinism Rule**: when a shared semantic is unresolved, keep an explicit blocker row/ref and route downstream as `blocked`; do not emit dual interpretations.
- **Prohibited**: Interface-role names (`*DTO`, `*Request`, `*Response`, `*Controller`).

## Handoff Decision

Emit exactly these fields:
- `Next Command`: `DATA_MODEL_BOOTSTRAP.recovery_handoff.next_command`
- `Decision Basis`: `DATA_MODEL_BOOTSTRAP.recovery_handoff.decision_basis`
- `Selected Stage ID`: `DATA_MODEL_BOOTSTRAP.recovery_handoff.selected_stage_id`
- `Ready/Blocked`: `DATA_MODEL_BOOTSTRAP.recovery_handoff.ready_blocked`

When `Ready/Blocked = Ready`, continue contract generation directly without rerunning `test-matrix`.

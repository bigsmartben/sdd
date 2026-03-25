from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def read_if_exists(rel_path: str) -> str | None:
    path = REPO_ROOT / rel_path
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def test_plan_command_is_control_plane_only():
    content = read("templates/commands/plan.md")
    assert "does **not** generate downstream planning-stage artifacts directly" in content
    assert "Treat all `$ARGUMENTS` as user planning context." in content
    assert "Planning Sharding Model (Mandatory)" in content
    assert "Stage sharding (fixed): delivery path `research -> test-matrix -> data-model`" in content
    assert "Binding sharding (fixed): `/sdd.plan.contract` consumes one `BindingRowID` row per run" in content
    assert "`contract` is not a `Stage Queue` row" in content
    assert "Unified Repository-First Gate Protocol (`URFGP`)" in content
    assert "explicit handoff order: `sdd.plan.research -> sdd.plan.test-matrix -> sdd.plan.data-model -> sdd.plan.contract`" in content
    assert "## Artifact Quality Contract" in content
    assert "## Reasoning Order" in content
    assert "## Writeback Contract" in content
    assert "## Output Contract" in content
    assert "Must: output one deterministic control plane" in content
    assert "Write `PLAN_FILE` as a control-plane scaffold only." in content
    assert "Seed `Stage Queue` in fixed order" in content
    assert "Keep markdown table headers unchanged" in content


def test_plan_child_commands_are_contract_only():
    assert not (REPO_ROOT / "templates/commands/plan.interface-detail.md").exists()
    assert not (REPO_ROOT / "templates/interface-detail-template.md").exists()

    plan = read("templates/commands/plan.md")
    test_matrix = read("templates/commands/plan.test-matrix.md")
    contract = read("templates/commands/plan.contract.md")

    assert "/sdd.plan.contract" in plan
    assert "/sdd.plan.interface-detail" not in plan
    assert "`Unit Type = contract`" in test_matrix
    assert "If any `contract` rows remain `blocked`, `Next Command = /sdd.plan.contract`" in contract
    assert "Otherwise, if any `contract` rows remain `pending`, `Next Command = /sdd.plan.contract`" in contract
    assert "Otherwise, if all required planning rows (`research`, `test-matrix`, `data-model`, and all queued `contract` rows) are complete, `Next Command = /sdd.tasks`" in contract
    assert "unified northbound interface design artifact" in contract
    assert "minimum northbound interface design artifact" not in contract


def test_plan_template_tracks_only_contract_artifacts():
    content = read("templates/plan-template.md")
    assert "## Artifact Quality Signals" in content
    assert "Must: behave like a trustworthy control plane." in content
    assert "`contract` is tracked as the single per-binding interface design artifact." in content
    assert "| BindingRowID | Packet Source |" in content
    assert "minimal selection and scheduling fields" in content
    assert "regenerate the projection instead of letting downstream commands rewrite it" in content
    assert "<!-- Keep table body empty until /sdd.plan.test-matrix projects stable binding rows. -->" in content
    assert "<!-- Keep table body empty until binding rows exist. -->" in content
    assert "[BindingRowID-001]" not in content
    assert "interface-detail" not in content


def test_plan_and_test_matrix_templates_precompute_contract_bootstrap_inputs():
    plan = read("templates/commands/plan.md")
    test_matrix_command = read("templates/commands/plan.test-matrix.md")
    test_matrix_template = read("templates/test-matrix-template.md")

    assert "- `BindingRowID`" in plan
    assert "- `Packet Source`" in plan
    assert "Do not add `Boundary Anchor`" in plan

    assert "## Binding Packet Requirements" in test_matrix_command
    assert "Do not read `research.md` in this stage." not in test_matrix_command
    assert "Read only:" in test_matrix_command
    assert "- `UIF Path Ref(s)`" in test_matrix_command
    assert "- `UDD Ref(s)`" in test_matrix_command
    assert "stable binding projection for those interface units" in test_matrix_command
    assert "Path Type` is verification coverage metadata only" in test_matrix_command

    assert "## Binding Packets" in test_matrix_template
    assert "Purpose: complete downstream scope-reference packet for the selected interaction unit." in test_matrix_template
    assert "**Inputs**: `spec.md`" in test_matrix_template
    assert "Packets should remove rebinding work without duplicating `spec.md` prose." in test_matrix_template
    assert "Path Type` is verification coverage metadata only" in test_matrix_template
    assert "Create / update / read / authorize / none" in test_matrix_template
    assert "| BindingRowID | IF Scope | User Intent | Trigger Ref(s) | Request Semantics | Visible Result | Side Effect | Boundary Notes | Repo Landing Hint | UIF Path Ref(s) | UDD Ref(s) | Primary TM IDs | TM IDs | TC IDs | Test Scope | Spec Ref(s) | Scenario Ref(s) | Success Ref(s) | Edge Ref(s) |" in test_matrix_template


def test_contract_command_uses_test_matrix_as_default_semantic_source():
    content = read("templates/commands/plan.contract.md")

    assert "Treat the matched `Binding Projection Index` row as a minimal locator ledger only" in content
    assert "Treat the selected packet as demand projection only through" in content
    assert "Treat the selected packet as the semantic authority for binding meaning in this run." in content
    assert "if absent, stop and route back to `/sdd.plan.test-matrix`" in content
    assert "Reconstruct request / response meaning from `UC`, `FR`, `UIF`, `UDD`, and scenario refs before reading repo evidence." in content
    assert "If repo-backed verification finds a binding-projection error or shared-semantic gap" in content
    assert "Use the repo-anchor decision protocol in `.specify/templates/contract-template.md` as the authority for this stage." in content
    assert "Keep repo-backed verification bounded to the selected `BindingRowID` and active blockers" in content
    assert "- `.specify/memory/repository-first/module-invocation-spec.md` (first-party module invocation authority)" in content
    assert "Use `.specify/memory/repository-first/module-invocation-spec.md` to lock first-party module invocation directions before landing sequence/UML anchors." in content
    assert "- required first-party method-level call anchors from module-invocation rules" in content
    assert "- required second-party and third-party call anchors" in content
    assert "- required owner/source symbols" in content
    assert "- middleware anchors only when bounded repo evidence closes them" in content
    assert "Sequence design MUST keep first-party execution hops at method-level call anchors." in content
    assert "Sequence lifeline labels MUST use concrete participant/type names; method-level anchors belong on call labels or notes, not on participant labels." in content
    assert "Sequence design MUST explicitly render mandatory second-party and third-party call anchors on the main path." in content
    assert "Sequence design MUST include middleware traversal only when a concrete middleware call anchor exists in bounded repo evidence." in content
    assert "Sequence design MUST NOT collapse multiple mandatory collaborators/dependencies into one synthetic participant label" in content
    assert "UML class design MUST map first-party sequence participants to concrete method-level anchors." in content
    assert "`opt` blocks are valid only for truly conditional branches" in content
    assert "UML request/response class labels should use anchored symbols or repository boundary naming conventions; do not synthesize placeholder DTO labels." in content
    assert "MAY refine operation-scoped VO/DTO/field mappings" in content
    assert "MUST NOT mint new shared-semantic classes, owners/sources, lifecycle vocabulary, or invariants." in content
    assert "Bounded repo closure MUST end with one explicit boundary/entry decision" in content
    assert "`existing`, `extended`, `new`, or `todo`" in content
    assert "MUST evaluate one concrete `new` anchor set before stopping." in content
    assert "Do not mark the row `blocked` only because no existing repo entry anchor was found" in content
    assert "freeze that naming for this run and finish the contract instead of reopening anchor search loops." in content
    assert "After bounded reads, stop anchor hunting and transition to closure output for this run" in content
    assert "concrete `new` anchors" in content
    assert "Do not route upstream only because no existing repo entry was found" in content
    assert "after evaluating `existing -> extended -> new -> todo` with bounded evidence." in content
    assert "## Concrete Naming Closure (Mandatory)" in content
    assert "Apply the anchor decision order `existing -> extended -> new -> todo`." in content
    assert "Stop local refinement and route upstream when continuing would require a new upstream shared semantic" in content
    assert "new shared semantic owner/source, a new backbone semantic element, a new cross-operation stable owner field, new shared lifecycle/invariant vocabulary" in content
    assert "## Feature-Level Smoke Readiness (Queue-Complete Gate)" in content
    assert "Cross-Interface Smoke Candidate (Required)" in content
    assert "do not rewrite upstream planning artifacts from this command" in content
    assert "## Artifact Quality Contract" in content
    assert "## Reasoning Order" in content
    assert "**Layered Repo Closure**: Use `module-invocation-spec.md` and repo anchors to land method-level Sequence/UML" in content
    assert "## Writeback Contract" in content
    assert "## Output Contract" in content
    assert "Must: close one `BindingRowID` with concrete names, anchors, field semantics, realization, and test projection." in content
    assert "Generate or refresh exactly one contract artifact for the selected `BindingRowID`." in content
    assert "Update only the selected `Artifact Status` row" in content
    assert "Do not modify `Stage Queue`, `Binding Projection Index`, or unrelated `Artifact Status` rows." in content


def test_contract_selection_rules_handle_empty_queue_before_packet_resolution():
    content = read("templates/commands/plan.contract.md")
    no_pending_idx = content.index("If no pending or blocked contract row exists, stop and report that the contract queue is complete")
    resolve_packet_idx = content.index("Attempt to resolve one selected binding packet in `test-matrix.md` by the same `BindingRowID`; if absent, stop and route back to `/sdd.plan.test-matrix`")
    assert no_pending_idx < resolve_packet_idx


def test_research_data_model_and_test_matrix_are_packet_first():
    research = read("templates/commands/plan.research.md")
    data_model = read("templates/commands/plan.data-model.md")
    test_matrix = read("templates/commands/plan.test-matrix.md")
    research_template = read("templates/research-template.md")

    assert "Stage Packet (Research Unit)" in research
    assert "Keep repo-backed reads bounded to the selected unit and active blocker." in research
    assert "Use this packet as the default context for generation." in research
    assert "module-root or directory-only placeholders such as `aidm-api/` are invalid" in research
    assert "Every `Source Path / Symbol` value must be a concrete file path or `path/to/file.ext::Symbol`" in research_template
    assert "Generate `research.md` as a high-signal evidence artifact" in research
    assert "## Writeback Contract" in research
    assert "## Output Contract" in research
    assert "Generate `research.md` as a high-signal evidence artifact" in research
    assert "Modify exactly one `Stage Queue` row where `Stage ID = research`" in research
    assert "Do not change `Binding Projection Index` or `Artifact Status`" in research

    assert "Stage Packet (Data-Model Unit)" in data_model
    assert "Treat `DATA_MODEL_BOOTSTRAP.generation_readiness` as the primary queue/readiness gate" in data_model
    assert "optional `research.md` path only when `spec.md` + `test-matrix.md` wording leaves the shared-semantic boundary ambiguous" in data_model
    assert "The output MUST define only the shared, stable, reusable semantics" in data_model
    assert "Do not define HTTP routes, controller/service/facade naming, contract-flavored shared names such as `*DTO`, `*Request`, `*Response`, `*Command`, or `*Result`, request/response shapes, operation-scoped command/result models, or repo interface-anchor placement here; those belong to `/sdd.plan.contract`." in data_model
    assert "Downstream `/sdd.plan.contract` work MUST reuse shared refs produced here" in data_model
    assert "Shared semantic names and UML/class labels in this stage MUST avoid contract-flavored suffixes" in data_model
    assert "When `Anchor Status = new`, record repo-first strategy evidence" in data_model
    assert "`DATA_MODEL_BOOTSTRAP.state_machine_policy`" in data_model
    assert "Use `DATA_MODEL_BOOTSTRAP.state_machine_policy.required_model_kinds` as the allowed `Required Model` vocabulary." in data_model
    assert "Use `DATA_MODEL_BOOTSTRAP.state_machine_policy.required_sections_by_model` as the authoritative section contract for `lightweight` vs `fsm`." in data_model
    assert "Use `DATA_MODEL_BOOTSTRAP.state_machine_policy.required_components_by_model` as the authoritative lifecycle-closure checklist." in data_model
    assert "If `N > 3` or `T >= 2N`, emit `Required Model = fsm` and include transition table, transition pseudocode, invariant catalog rows, and state diagram." in data_model
    assert "`lightweight` rows MUST still close allowed transitions, forbidden transitions, and key invariants through `Invariant Catalog` + `State Transition Table`." in data_model
    assert "If `existing` and `extended` are both insufficient, `new` is the required outcome for this stage" in data_model
    assert "If `existing` and `extended` cannot safely close a confirmed shared semantic, this stage MUST explicitly choose `new` here" in data_model
    assert "Shared semantics that are confirmed by `spec.md` + `test-matrix.md` MUST be closed here at owner/source/lifecycle level" in data_model
    assert "Every lifecycle row MUST cite concrete `INV-*` refs; invariant closure belongs here, not in `/sdd.plan.contract`." in data_model
    assert "Every shared field, projection, derived value, and lifecycle state MUST close to one explicit owner/source row in `Owner / Source Alignment`." in data_model
    assert "- `Next Command`: `DATA_MODEL_BOOTSTRAP.recovery_handoff.next_command`" in data_model
    assert "- `Decision Basis`: `DATA_MODEL_BOOTSTRAP.recovery_handoff.decision_basis`" in data_model
    assert "- `Selected Stage ID`: `DATA_MODEL_BOOTSTRAP.recovery_handoff.selected_stage_id`" in data_model
    assert "- `Ready/Blocked`: `DATA_MODEL_BOOTSTRAP.recovery_handoff.ready_blocked`" in data_model
    assert "continue contract generation directly without rerunning `test-matrix`" in data_model
    assert "DATA_MODEL_BOOTSTRAP.recovery_handoff" in data_model
    assert "do not default to `/sdd.plan.contract`" in data_model
    assert "runtime selection order is authoritative: first `pending` `data-model` row, then fallback `data-model` row, then synthetic row if absent." in data_model
    assert "Do not recompute stage-row hard gates locally; bootstrap `generation_readiness` + `recovery_handoff` are the authority." in data_model
    assert "## Artifact Quality Contract" in data_model
    assert "## Reasoning Order" in data_model
    assert "## Writeback Contract" in data_model
    assert "## Output Contract" in data_model
    assert "Must: close reusable shared semantics, owner/source alignment, lifecycle, invariants, and downstream reuse constraints before contract design." in data_model
    assert "make it obvious why a semantic is shared, who owns it, which `INV-*` refs govern it, and why contract cannot invent an alternative local model." in data_model
    assert "Modify only the selected `data-model` row plus blocker fields" in data_model
    assert "May batch update only `Blocker` fields for affected `contract` rows in `PLAN_FILE` `Artifact Status`" in data_model
    assert "MUST NOT rewrite `Target Path` / `Status` in `Artifact Status`" in data_model

    assert "Stage Packet (Test-Matrix Unit)" in test_matrix
    assert "Use this packet as the default context for generation and binding projection." in test_matrix
    assert "stable binding projection for those interface units" in test_matrix
    assert "`UIF Full Path Coverage Graph (Mermaid)`" in test_matrix
    assert "`UIF Path Coverage Ledger`" in test_matrix
    assert "prefer section-level rereads over whole-file replay for the selected unit" in test_matrix
    assert "Do not require `research` or `data-model` rows to be `done` before this stage" in test_matrix
    assert "Do not consume `data-model.md` or generated contract artifacts in this stage." in test_matrix
    assert "If the selected packet cannot be closed from `spec.md` and selected plan-row context" in test_matrix
    assert "`UDD Ref(s)`" in test_matrix
    assert "## Artifact Quality Contract" in test_matrix
    assert "## Reasoning Order" in test_matrix
    assert "## Writeback Contract" in test_matrix
    assert "## Output Contract" in test_matrix
    assert "Must: output stable binding cuts, verification semantics, and reusable packets from `spec.md`." in test_matrix
    assert "Refresh `Binding Projection Index` by `BindingRowID`; replace matching rows, do not append duplicates." in test_matrix
    assert "Keep exactly one `contract` row per projected `BindingRowID`" in test_matrix


def test_contract_template_contains_unified_realization_requirements():
    content = read("templates/contract-template.md")
    assert "## Artifact Quality Signals (Normative)" in content
    assert "Must: be strong enough for implementation to start without reopening basics." in content
    assert "# Northbound Interface Design:" in content
    assert "## Interface Definition" in content
    assert "### Contract Summary" in content
    assert "### Full Field Dictionary (Operation-scoped)" in content
    assert "## UML Class Design" in content
    assert "## Sequence Design" in content
    assert "## Closure Check" in content
    assert "| `Test Scope` | [binding-scoped test coverage summary] |" in content
    assert "## Test Projection" in content
    assert "### Cross-Interface Smoke Candidate (Required)" in content
    assert "### Resolved Type Inventory" in content
    assert "Angle-bracket labels in the examples below are template scaffolding only and MUST be replaced before the artifact can be `done`." in content
    assert "| Sequence closure | success/failure paths are contiguous, include mandatory second-party and third-party call anchors, and include middleware only when anchored | [Behavior Paths rows, Sequence Sx refs, repo anchor evidence] | [ok / gap] |" in content
    assert "| UML closure | class diagram and two-party package relations are present, and sequence participants/method anchors are mapped consistently | [Class Diagram refs, Two-Party Package Relations rows, Resolved Type Inventory rows] | [ok / gap] |" in content
    assert "`new` \\| `todo`" in content
    assert "ConcreteBoundary.method" in content
    assert "ConcreteEntry.method" in content
    assert 'participant Boundary as "ConcreteBoundary"' in content
    assert 'participant Entry as "ConcreteEntry"' in content
    assert "- Apply anchor decision order `existing -> extended -> new -> todo`." in content
    assert "- `new` is normative only when selected `spec.md` / `data-model.md` / `test-matrix.md` slices plus bounded repo reads fully close the binding design" in content
    assert "prefer repository-style names such as `*Controller.method`, `*Service.method`, or `*ServiceImpl.method`" in content
    assert "#### Sequence Variant A (Boundary != Entry)" in content
    assert "#### Sequence Variant B (Boundary == Entry)" in content
    assert "##### A1. With Anchored Middleware (Optional)" in content
    assert "##### A2. Without Middleware Anchor" in content
    assert "##### B1. With Anchored Middleware (Optional)" in content
    assert "##### B2. Without Middleware Anchor" in content
    assert "#### UML Variant A (Boundary != Entry)" in content
    assert "#### UML Variant B (Boundary == Entry)" in content
    assert "UML MUST keep first-party executable participants at method-level anchors." in content
    assert "If middleware is present as a concrete first-party call anchor in Sequence, include the same middleware type and call edge in UML." in content
    assert "Sequence MUST NOT merge multiple mandatory collaborators/dependencies into one synthetic participant label." in content
    assert "Sequence MUST NOT merge multiple mandatory collaborators/dependencies into one synthetic participant label" in content
    assert "Middleware traversal MUST appear only when a concrete middleware call anchor exists in bounded repo evidence; do not insert middleware as a default participant." in content
    assert "Sequence lifeline labels MUST use concrete participant/type names; do not embed method-level anchors in participant labels." in content
    assert "render both layers explicitly instead of replacing the design anchor with the nearest existing class." in content
    assert "owner, creator, reader, and writer closure" in content
    assert "the first hop MUST remain the new anchor and the reused repo-backed chain MUST appear as a subsequent explicit handoff." in content
    assert "- If repo evidence is insufficient for `existing` or `extended`, this stage may design concrete `new` operation-scoped boundary/entry/DTO/collaborator/dependency surfaces when they remain bounded to this binding; include middleware only when a concrete middleware anchor is available." in content
    assert "- `new` anchors are planning-final for this binding and MUST stay concrete, uniquely named, and consistent across Interface Definition, UML, Sequence, and Test Projection." in content
    assert "- If `new` anchors reuse `existing` repo-backed implementation, keep the design anchor and reused realization chain distinct instead of collapsing both into one symbol." in content
    assert "- Any `new` operation-scoped holder/state class must close owner, creator, reader, and writer responsibilities before the binding can be treated as design-final." in content
    assert "- repo anchors: [boundary / entry / request-response model / collaborator / dependency symbols / middleware (when anchored)]" in content
    assert "- Sequence and UML MUST stay aligned at method-level anchors for first-party participants." in content
    assert "- `contract` is responsible for first-time production of `Boundary Anchor`, `Implementation Entry Anchor`, request/response surface, UML closure, sequence closure, and test projection for this binding." in content


def test_contract_sequence_variant_without_middleware_keeps_method_level_chain():
    content = read("templates/contract-template.md")

    a2_block = content.split("##### A2. Without Middleware Anchor", 1)[1].split("#### Sequence Variant B", 1)[0]
    assert "participant Middleware" not in a2_block
    assert 'participant Boundary as "ConcreteBoundary"' in a2_block
    assert 'participant Entry as "ConcreteEntry"' in a2_block
    assert "Initiator->>Boundary: ConcreteBoundary.method([operation request])" in a2_block
    assert "Boundary->>Entry: ConcreteEntry.method(...)" in a2_block
    assert "Entry->>SecondParty: <AnchoredSecondPartyCallAnchor>" in a2_block
    assert "SecondParty->>ThirdParty: <AnchoredThirdPartyCallAnchor>" in a2_block


def test_contract_sequence_variant_with_middleware_requires_explicit_anchor():
    content = read("templates/contract-template.md")

    a1_block = content.split("##### A1. With Anchored Middleware (Optional)", 1)[1].split(
        "##### A2. Without Middleware Anchor",
        1,
    )[0]
    assert "participant Middleware as \"<AnchoredMiddlewareType>\"" in a1_block
    assert "Boundary->>Middleware: <AnchoredMiddlewareCallAnchor>" in a1_block
    assert "Middleware->>Entry: ConcreteEntry.method(...)" in a1_block

def test_data_model_template_requires_new_anchor_evidence_and_owner_closure():
    content = read("templates/data-model-template.md")
    assert "## Artifact Quality Signals" in content
    assert "Must: read like a shared business-semantic backbone." in content
    assert "## Shared Semantic Class Model" in content
    assert "classDiagram" in content
    assert "### State Transition Table" in content
    assert "stateDiagram-v2" in content

    assert "**Stage**: Stage 3 Shared Semantic Alignment" in content
    assert "If a semantic is used by only one `BindingRowID`, leave it to `/sdd.plan.contract`" in content
    assert "Leave complete request/response expansion to `/sdd.plan.contract`." in content
    assert "Use stable refs that downstream contracts can cite directly: `SSE-*`, `OSA-*`, `SFV-*`, `LC-*`, `INV-*`, and `DCC-*`." in content
    assert "| SSE ID | Kind | Name | Business Meaning | Primary UDD Ref(s) | Primary Spec Ref(s) | Consumed By BindingRowID(s) | Why Not Contract-Local | Anchor Status | Repo-First Strategy Evidence | Repo Anchor | Anchor Role | Status |" in content
    assert "## Owner / Source Alignment" in content
    assert "| OSA ID | Semantic Ref | Owner Class / Semantic Owner | Source Type | Source Ref(s) | Consumed Field / Concept | Consumed By BindingRowID(s) | Notes |" in content
    assert "Every shared projection, derivation, counter, badge, role label, or lifecycle guard MUST identify the owner class/field/state that sustains it." in content
    assert "- Owner/source for confirmed shared semantics MUST be closed in this stage; use `gap` only when required input/evidence is genuinely missing." in content
    assert "- `Anchor Status` MUST use the repo-anchor decision vocabulary `existing | extended | new | todo`; prefer `existing | extended | new` in this stage and use `todo` only for genuine evidence blockers." in content
    assert "- `Repo-First Strategy Evidence` MUST be explicit whenever `Anchor Status = new`; explain why `existing` and `extended` were rejected, and use `N/A` only for non-`new` rows." in content
    assert "- `Anchor Role` MUST align to the repo-anchor role taxonomy `owner | state-source | projection-source | carrier | partial-lineage`." in content
    assert "- `Why Not Contract-Local` MUST explain why the semantic would become unstable, duplicated, or contradictory if deferred to `/sdd.plan.contract`." in content
    assert "contract-flavored/interface-role names such as `*DTO`, `*Request`, `*Response`, `*Command`, `*Result`, `*Controller`, `*Service`, or `*Facade`" in content
    assert "`contract` MUST reuse these shared refs and MUST NOT redefine shared owner/source alignment, lifecycle vocabulary, invariant vocabulary, or other confirmed shared semantics independently." in content
    assert "| SFV ID | Semantic Owner | Meaning | Primary UDD Ref(s) | Required Semantics | Null / Boundary Rule | Shared By BindingRowID(s) |" in content
    assert "If a confirmed shared semantic cannot land as `existing` or `extended`, introduce the required `new` class/owner/lifecycle here instead of deferring the decision." in content
    assert "- Otherwise keep the lifecycle lightweight, but still include the transition table because it is a primary reader view." in content
    assert "- Apply the constitution lifecycle policy per shared lifecycle." in content
    assert "- Every lifecycle row MUST cite concrete `INV-*` refs and one explicit `State Owner`." in content
    assert "| Lifecycle Ref | State Owner | Stable States | Invariant Ref(s) | Consumed By BindingRowID(s) | Required Model |" in content
    assert "### Invariant Catalog" in content
    assert "| INV ID | Lifecycle Ref | Rule Kind | Invariant / Transition Rule | Owner / Scope | Consumed By BindingRowID(s) |" in content
    assert "Every `lightweight` lifecycle MUST have `Invariant Catalog` rows that cover `allowed-transition`, `forbidden-transition`, and `key-invariant`." in content
    assert "### Transition Pseudocode (when `Required Model = fsm`)" in content
    assert "| Lifecycle Ref | Transition Case | Pseudocode / Decision Steps | Invariant Ref(s) |" in content
    assert "Force `/sdd.plan.contract` to cite `SSE-*`, `OSA-*`, `SFV-*`, `LC-*`, `INV-*`, and `DCC-*` refs instead of restating shared semantics locally." in content
    assert "| DCC ID | BindingRowID | Required Shared Semantic Ref(s) | Constraint Type | Contract Impact |" in content


def test_test_matrix_template_forbids_backfilling_missing_stage_one_model():
    content = read("templates/test-matrix-template.md")
    assert "## Artifact Quality Signals" in content
    assert "Must: make binding identity and verification intent obvious in one pass." in content

    assert "**Inputs**: `spec.md`" in content
    assert "## UIF Full Path Coverage Graph (Mermaid)" in content
    assert "## UIF Path Coverage Ledger" in content
    assert "Every selected-scope `UIF Path Ref` MUST appear exactly once in this ledger." in content
    assert "[Coverage scope: which `UC / FR / UIF / UDD` paths must be verified and why]" in content
    assert "Downstream stages may consume these packets, but they must not rewrite `BindingRowID` or binding meaning." in content
    assert "Do not emit a binding packet for pure internal steps" in content


def test_tasks_command_uses_contract_as_realization_source():
    content = read("templates/commands/tasks.md")
    assert "selected `contracts/` slices" in content
    assert "Treat `TASKS_BOOTSTRAP.execution_readiness` as the primary hard gate." in content
    assert "stop immediately and report the runtime bootstrap blocker" in content
    assert "Keep contract projection authoritative for the current run." in content
    assert "Keep contract method-level `Sequence` / `UML` anchor closure authoritative for execution decomposition" in content
    assert "On projection drift, emit upstream writeback actions only:" in content
    assert "/sdd.specify" in content
    assert "/sdd.plan.test-matrix" in content
    assert "Repository-first explainable evidence" in content
    assert "/sdd.plan.interface-detail" not in content
    assert "interface-details/" not in content
    assert "Terminology note (compatibility, non-normative)" not in content
    assert "detail doc defines a narrower repo-backed internal handoff entry" not in content
    assert "Any selected `contract` row is missing `Full Field Dictionary (Operation-scoped)`" in content
    assert "binding-packet source resolution" in content


def test_tasks_template_is_contract_only():
    content = read("templates/tasks-template.md")
    assert "## Artifact Quality Signals" in content
    assert "Must: feel like an execution plan a senior engineer could run." in content
    assert "contracts/<operationId>.md" in content
    assert "Spec Slice:" in content
    assert "Test Slice:" in content
    assert "selected contract `Binding Context` + `Test Projection Slice`" in content
    assert "contract `Binding Context` `Spec Ref(s)`" in content
    assert "## 2.1) Upstream Alignment Repair (Required On Projection Drift)" in content
    assert "keep contract projection as execution truth for this run and emit explicit upstream writeback repair actions" in content
    assert "`/sdd.specify`" in content
    assert "`/sdd.plan.test-matrix`" in content
    assert "Cross-Interface Smoke Candidate (Required)" in content
    assert "interface detail" not in content.lower()


def test_analyze_routes_contract_projection_drift():
    content = read("templates/commands/analyze.md")
    assert "centralized audit entry and single concentrated audit step before `/sdd.implement`." in content
    assert "contract-projection drift governance" in content
    assert "regenerate `/sdd.plan.contract`" in content
    assert "Projection drift routing:" in content
    assert "upstream binding-projection drift across `plan.md` / `test-matrix.md`" in content
    assert "unresolved placeholder class/type labels in contract artifacts" in content
    assert "Sequence` / `UML` participant and anchor consistency in contract artifacts" in content
    assert "CRITICAL/HIGH findings MUST cite the authoritative source artifact(s) with concise supporting facts." in content
    assert "interface-detail" not in content
    assert "contract/interface DTO drift" not in content
    assert "contract/interface field drift from anchored DTOs/signatures" not in content


def test_docs_describe_contract_only_planning_queue():
    mapping = read_if_exists("docs/command-template-mapping.md")
    readme = read("README.md")
    installation = read_if_exists("docs/installation.md")
    quickstart = read_if_exists("docs/quickstart.md")
    spec_driven = read("spec-driven.md")

    if mapping is not None:
        assert "repeated `/sdd.plan.contract`" in mapping
        assert "/sdd.plan.interface-detail" not in mapping
        assert "interface-details/" not in mapping

    assert "/sdd.plan.contract" in readme
    assert "/sdd.plan.interface-detail" not in readme
    assert "interface-details/" not in readme

    if installation is not None:
        assert "/sdd.plan.contract" in installation
        assert "/sdd.plan.interface-detail" not in installation

    if quickstart is not None:
        assert "/sdd.plan.contract" in quickstart
        assert "/sdd.plan.interface-detail" not in quickstart

    assert "/sdd.plan.contract" in spec_driven
    assert "/sdd.plan.interface-detail" not in spec_driven


def test_docs_follow_canonical_planning_queue_order():
    readme = read("README.md")
    spec_driven = read("spec-driven.md")
    spec_template = read("templates/spec-template.md")

    assert readme.index("/sdd.plan.research") < readme.index("/sdd.plan.test-matrix") < readme.index("/sdd.plan.data-model")
    assert spec_driven.index("/sdd.plan.research") < spec_driven.index("/sdd.plan.test-matrix") < spec_driven.index("/sdd.plan.data-model")
    assert spec_template.index("`research.md` via `/sdd.plan.research`") < spec_template.index("`test-matrix.md` via `/sdd.plan.test-matrix`") < spec_template.index("`data-model.md` via `/sdd.plan.data-model`")


def test_readme_positions_analyze_as_main_flow_default():
    readme = read("README.md")
    assert "| `/sdd.analyze`   | Default pre-implementation unified audit entrypoint" in readme
    optional_section = readme.split("#### Optional Commands", 1)[1].split("### Environment Variables", 1)[0]
    assert "/sdd.analyze" not in optional_section


def test_readme_walkthrough_orders_tasks_before_analyze():
    readme = read("README.md")
    assert readme.index("### **STEP 6:** Generate task breakdown with `/sdd.tasks`") < readme.index("### **STEP 7:** Audit model and optional checklist (`/sdd.analyze`, `/sdd.checklist`)")


def test_cli_skill_descriptions_and_next_steps_drop_interface_detail():
    content = read("src/specify_cli/__init__.py")
    assert '"plan.contract": "Generate one queued full-field contract artifact' in content
    assert "plan.interface-detail" not in content
    assert "repeated [cyan]/{COMMAND_NAMESPACE}.plan.contract[/]" in content


def test_generation_commands_reference_runtime_templates_only():
    expected = {
        "templates/commands/constitution.md": ".specify/templates/constitution-template.md",
        "templates/commands/specify.md": ".specify/templates/spec-template.md",
        "templates/commands/specify.ui-html.md": ".specify/templates/ui-html-template.html",
        "templates/commands/plan.md": ".specify/templates/plan-template.md",
        "templates/commands/plan.research.md": ".specify/templates/research-template.md",
        "templates/commands/plan.data-model.md": ".specify/templates/data-model-template.md",
        "templates/commands/plan.test-matrix.md": ".specify/templates/test-matrix-template.md",
        "templates/commands/plan.contract.md": ".specify/templates/contract-template.md",
        "templates/commands/tasks.md": ".specify/templates/tasks-template.md",
        "templates/commands/checklist.md": ".specify/templates/checklist-template.md",
    }
    for rel_path, marker in expected.items():
        assert marker in read(rel_path)


def test_lint_rules_for_unified_contract_runtime_rows():
    content = read("rules/planning-lint-rules.tsv")
    assert "PLN-BP-002" in content
    assert "PLN-ID-007" in content
    assert "PLN-ID-008" in content
    assert "PLN-ID-009" in content
    assert "PLN-ID-012" in content
    assert "PLN-ID-013" in content
    assert "PLN-ID-014" in content
    assert "PLN-ID-015" in content
    assert "PLN-RA-011" in content
    assert "PLN-RA-012" in content
    assert "PLN-DM-006" in content
    assert "PLN-DM-007" in content
    assert "PLN-DM-008" in content
    assert "PLN-DM-009" in content
    assert "PLN-RA-013" in content
    assert "PLN-RA-014" in content
    assert "trigger_file=.specify/memory/repository-first/module-invocation-spec.md" in content
    assert "\tcontracts\tcontracts/*\t" in content
    assert "Interface details are missing" not in content


def test_plan_required_sections_are_consistent_across_lint_and_preflights():
    rules = read("rules/planning-lint-rules.tsv")
    task_runtime = read("src/specify_cli/runtime_task_bootstrap.py")
    data_model_runtime = read("src/specify_cli/runtime_data_model_bootstrap.py")
    task_preflight = read("scripts/task_preflight.py")
    data_model_preflight = read("scripts/data_model_preflight.py")
    required_sections = [
        "Summary",
        "Shared Context Snapshot",
        "Stage Queue",
        "Binding Projection Index",
        "Artifact Status",
        "Handoff Protocol",
    ]
    for section in required_sections:
        assert section in rules
        assert section in task_runtime
        assert section in data_model_runtime
    assert "from specify_cli.runtime_task_bootstrap import build_task_bootstrap_payload" in task_preflight
    assert "from specify_cli.runtime_data_model_bootstrap import build_data_model_bootstrap_payload" in data_model_preflight


def test_checklist_command_uses_branch_inferred_plan_input_with_hard_gate():
    content = read("templates/commands/checklist.md")
    assert "Treat all `$ARGUMENTS` as checklist context input." in content
    assert "## Artifact Quality Contract" in content
    assert "generate a checklist a strong reviewer would actually use" in content
    assert "Resolve `PLAN_FILE` from the current feature branch using `{SCRIPT}` defaults." in content
    assert "Run `{SCRIPT}` from repo root; parse `FEATURE_DIR` and `AVAILABLE_DOCS`." in content
    assert "plan.md` (required; must match resolved `PLAN_FILE`)" in content
    assert "If present, the first positional token is `PLAN_FILE`" not in content
    assert "`/sdd.checklist <path/to/plan.md> [checklist-context...]`" not in content
    assert "--plan-file <PLAN_FILE>" not in content


def test_checklist_docs_and_templates_use_branch_inferred_invocation():
    readme = read("README.md")
    spec_template = read("templates/spec-template.md")
    specify_command = read("templates/commands/specify.md")
    checklist_template = read("templates/checklist-template.md")
    cli_init = read("src/specify_cli/__init__.py")

    assert "/sdd.checklist" in readme
    assert "/sdd.checklist <plan.md>" not in readme
    assert "/sdd.checklist specs/001-create-taskify/plan.md" not in readme
    assert "/sdd.checklist" in spec_template
    assert "/sdd.checklist <path/to/plan.md>" not in spec_template
    assert "/sdd.checklist" in specify_command
    assert "/sdd.checklist <path/to/plan.md>" not in specify_command
    assert "/sdd.checklist" in checklist_template
    assert "/sdd.checklist <path/to/plan.md>" not in checklist_template
    assert '/{COMMAND_NAMESPACE}.checklist[/]' in cli_init
    assert '/{COMMAND_NAMESPACE}.checklist <plan.md>' not in cli_init

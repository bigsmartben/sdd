from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_tasks_command_hard_fails_on_missing_execution_anchors():
    content = read("templates/commands/tasks.md")

    assert "`/sdd.tasks <path/to/plan.md> [context...]`" in content
    assert "Preflight Fast Path (Performance + Consistency)" in content
    assert "Treat `TASKS_BOOTSTRAP.execution_readiness` as the primary preflight hard-gate source when present and parseable." in content
    assert "If `TASKS_BOOTSTRAP.execution_readiness.ready_for_task_generation = false`, stop immediately and report blocker codes/details from `execution_readiness.errors`; do not continue into broad artifact reads." in content
    assert "If `TASKS_BOOTSTRAP.execution_readiness.ready_for_task_generation = true`, do not recompute full control-plane hard gates by replaying whole `plan.md` tables" in content
    assert "Run `{SCRIPT} --plan-file <PLAN_FILE>`" in content
    assert "execution decomposition step for completed `plan`-stage detailed design" in content
    assert "MUST NOT supplement design details, verification semantics, target paths, completion anchors, or dependency meaning" in content
    assert "fail fast and route back to the relevant `/sdd.plan.*` command; do not emit placeholder execution tasks" in content
    assert "Do not create `blocked`, `todo`, placeholder, or compensating execution rows" in content
    assert "Stop and route to `/sdd.plan.test-matrix` if `test-matrix.md` is missing, non-consumable, or lacks the tuple keys needed for executable verification mapping." in content
    assert "Stop and route to `/sdd.plan.contract` if a required contract artifact/path is missing, non-consumable, cannot be aligned to the selected binding tuple, is `blocked`, or lacks `Full Field Dictionary (Operation-scoped)`." in content
    assert "treat contract `Downstream Projection Input (Required)` (`Spec Projection Slice`, `Test Projection Slice`) as the authoritative downstream execution projection" in content
    assert "Treat contract `Full Field Dictionary (Operation-scoped)` as the authoritative upstream field-semantics source" in content
    assert "keep contract projection as execution truth for this run and emit explicit upstream writeback repair actions" in content
    assert "/sdd.plan.interface-detail" not in content


def test_tasks_command_uses_mechanical_single_target_decomposition_rules():
    content = read("templates/commands/tasks.md")

    assert "unique run-local `tuple-index`" in content
    assert "sole execution inventory for task generation" in content
    assert "Output execution mapping conclusions only; do not emit design explanations" in content
    assert "Use deterministic mechanical mapping rules during `Generate`:" in content
    assert "one work package maps to exactly one `operationId` or one shared prerequisite objective" in content
    assert "one work package maps to exactly one target path cluster or one command target" in content
    assert "one work package maps to exactly one primary completion anchor" in content
    assert "do not merge multiple operations, unrelated file clusters, or distinct validation objectives into one task" in content
    assert "If multiple operations share one `IF Scope`, keep them as separate work packages rather than one composite task." in content
    assert "Use `contracts/` as the authoritative realization design source for execution targeting" in content
    assert "projection drift is detected (`Spec Projection Slice` or `Test Projection Slice` vs `spec.md` / `test-matrix.md`), keep contract projection semantics for this execution run" in content
    assert "emit `Upstream Alignment Repair` actions mapped to owner commands (`/sdd.specify` for spec drift, `/sdd.plan.test-matrix` for test-matrix drift)." in content
    assert "When `Boundary Anchor` and `Implementation Entry Anchor` differ, keep `Boundary Anchor` for verification/binding refs but anchor implementation tasks to the internal entry/collaborator path defined in `contracts/`." in content
    assert "Do not supplement owner/default/validation/persisted semantics in `/sdd.tasks`" in content
    assert "Do not infer new business ordering, responsibility boundaries, or implementation strategy." in content
    assert "`GLOBAL` is limited to prerequisites shared by multiple IF units. Using `GLOBAL` as overflow for one-scope work is a hard error." in content
    assert "Do not emit `blocked`, `todo`, placeholder, or compensating tasks to represent missing upstream design anchors." in content


def test_tasks_template_requires_explicit_single_target_tasks():
    content = read("templates/tasks-template.md")

    assert "projects completed `plan`-stage detailed design into execution decomposition only" in content
    assert "MUST NOT supplement missing design, verification semantics, target paths, completion anchors, or dependency meaning." in content
    assert "Description with explicit file path or command target (Completion Anchor: [single primary pass signal])" in content
    assert "Each task MUST map to exactly one execution target: one `operationId` or one shared prerequisite objective." in content
    assert "Each task MUST declare exactly one explicit target path cluster or one command target." in content
    assert "Each task MUST declare exactly one primary completion anchor; if no primary completion anchor can be projected, do not generate the task." in content
    assert "A task MUST NOT combine multiple operations, multiple unrelated file clusters, or multiple distinct validation objectives." in content
    assert "Only place prerequisites here when they are consumed by multiple IF units." in content
    assert "Treat use of `GLOBAL` as overflow for one-scope work as invalid task generation." in content
    assert "## 2.1) Upstream Alignment Repair (Required On Projection Drift)" in content
    assert "Do not dual-write conflicting semantics into `tasks.md`; keep one active projection source per IF unit." in content
    assert "- Implementation Entry: [single repo-backed entry anchor from contract realization section, or same as contract boundary]" in content
    assert "Use `Contract` as the client-facing binding reference and `Implementation Entry` as the internal execution-target reference when they differ." in content
    assert "Keep `Goal`, `Contract`, `Implementation Entry`, and `Primary Refs` as short execution references only." in content
    assert "If multiple operations share an `IF Scope`, keep them as separate work packages inside the same IF unit; do not merge them into a composite task." in content
    assert "`tasks.manifest.json` task IDs and dependencies must stay aligned with the `tasks.md` lines rendered from the same execution graph." in content
    assert "`tasks.manifest.json` top-level keys MUST include `schema_version`, `generated_at`, `generated_from`, and `tasks`." in content
    assert "`generated_from` MUST include `plan_path`, `plan_source_fingerprint`, and `contract_source_fingerprints`." in content


def test_manifest_schema_contract_between_tasks_and_implement():
    tasks_command = read("templates/commands/tasks.md")
    implement_command = read("templates/commands/implement.md")

    assert "Manifest top-level MUST include: `schema_version`, `generated_at`, `generated_from`, `tasks`." in tasks_command
    assert "`generated_from` MUST include at least: `plan_path`, `plan_source_fingerprint`, `contract_source_fingerprints`." in tasks_command
    assert "**Manifest fast path**: when manifest validation passes, treat manifest as the runtime source of truth for scheduling metadata and skip full `tasks.md` structural parsing in pre-execution gates." in implement_command
    assert "required task keys: `task_id`, `dependencies`, `if_scope`, `refs`, `target_paths`, `completion_anchors`, `conflict_hints`, `topo_layer`, `status`" in implement_command


def test_docs_describe_tasks_as_execution_decomposition_only():
    mapping_doc_path = REPO_ROOT / "docs" / "command-template-mapping.md"
    mapping_doc = mapping_doc_path.read_text(encoding="utf-8") if mapping_doc_path.exists() else None
    readme = read("README.md")
    spec_driven = read("spec-driven.md")

    if mapping_doc is not None:
        assert "project completed `plan`-stage detailed design into execution decomposition only; it does not supplement missing design." in mapping_doc
        assert "must use one unique tuple inventory derived from `Binding Projection Index` plus completed `Artifact Status` rows as the sole task-generation inventory." in mapping_doc
        assert "must hard-fail and route to the relevant `/sdd.plan.*` command when required execution anchors are missing or non-traceable" in mapping_doc
        assert "must treat contract `Spec Projection Slice` and `Test Projection Slice` as authoritative downstream projection input per IF unit." in mapping_doc
        assert "must keep contract projection for current task output and emit explicit upstream writeback repair actions (`/sdd.specify` for spec drift, `/sdd.plan.test-matrix` for test drift)." in mapping_doc
        assert "must keep the contract boundary for verification/binding refs and use the implementation entry/collaborator path for implementation target mapping." in mapping_doc
        assert "must not supplement verification semantics, target paths, completion anchors, dependency meaning, or execution rationale" in mapping_doc
        assert "each generated work package/task must map to exactly one `operationId` or one shared prerequisite objective, one explicit target path cluster or command target, and one primary completion anchor." in mapping_doc
        assert "must not emit placeholder/blocked/todo execution rows or infer new business ordering, responsibility boundaries, or implementation strategy." in mapping_doc

    assert "This is an execution decomposition step only" in readme
    assert "hard-fails on missing execution anchors instead of supplementing design or writing placeholder tasks" in readme
    assert "each task must carry one explicit path or command target plus one primary completion anchor" in readme
    assert "should stop and route back to the relevant `/sdd.plan.*` command rather than inferring new semantics or emitting `blocked`/`todo` placeholder tasks" in readme

    assert "projects the completed planning-stage design set into an executable task list" in spec_driven
    assert "does not supplement missing design or audit the feature end-to-end" in spec_driven
    assert "stop and route back to the relevant planning command instead of emitting placeholder tasks" in spec_driven

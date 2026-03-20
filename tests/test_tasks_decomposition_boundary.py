from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_tasks_command_enforces_preflight_and_hard_stop():
    content = read("templates/commands/tasks.md")

    assert "Resolve `PLAN_FILE` from current feature branch using `{SCRIPT}` defaults." in content
    assert "scripts/bash/check-prerequisites.sh --json --task-preflight" in content
    assert "scripts/powershell/check-prerequisites.ps1 -Json -TaskPreflight" in content
    assert "Run `{SCRIPT}` once from repo root." in content
    assert "Treat `TASKS_BOOTSTRAP.execution_readiness` as the primary hard gate." in content
    assert "stop immediately and report the runtime bootstrap blocker" in content
    assert "Stop immediately when any condition holds:" in content
    assert "`TASKS_BOOTSTRAP.execution_readiness.errors` contains blockers" in content
    assert "LOCAL_EXECUTION_PROTOCOL.repo_search.list_files_cmd" in content
    assert "Active executable tuples select `new` repo anchors but lack explicit rejection evidence for `existing` and `extended`" in content
    assert "Unified Repository-First Gate Protocol (`URFGP`)" in content
    assert "/sdd.plan.interface-detail" not in content


def test_tasks_command_keeps_execution_only_boundary():
    content = read("templates/commands/tasks.md")

    assert "`/sdd.tasks` owns execution decomposition only." in content
    assert "do not redesign in this command." in content
    assert "does **not** own comprehensive audit concerns" in content
    assert "Route those to `/sdd.analyze`." in content


def test_tasks_command_deterministic_mapping_and_manifest_schema():
    content = read("templates/commands/tasks.md")

    assert "Enforce deterministic mapping rules during task generation:" in content
    assert "one work package maps to exactly one `operationId` or one shared prerequisite objective" in content
    assert "one work package maps to exactly one target path cluster or one command target" in content
    assert "one work package maps to exactly one primary completion anchor" in content
    assert "Top-level keys: `schema_version`, `generated_at`, `generated_from`, `tasks`" in content
    assert "`generated_from` keys: `plan_path`, `plan_source_fingerprint`, `contract_source_fingerprints`" in content
    assert "Repository-First Evidence Bundle (`RFEB`)" in content
    assert "`source_refs`" in content
    assert "`signal_ids` (`SIG-*` rows" in content
    assert "`module_edge_ids`" in content


def test_tasks_template_requires_single_target_and_projection_repair():
    content = read("templates/tasks-template.md")

    assert "projects completed `plan`-stage detailed design into execution decomposition only" in content
    assert "MUST NOT supplement missing design, verification semantics, target paths, completion anchors, or dependency meaning." in content
    assert "Each task MUST map to exactly one execution target" in content
    assert "Each task MUST declare exactly one explicit target path cluster or one command target." in content
    assert "Each task MUST declare exactly one primary completion anchor" in content
    assert "## 2.1) Upstream Alignment Repair (Required On Projection Drift)" in content
    assert "If executable tuples depend on `Anchor Status = new` / `Implementation Entry Anchor Status = new`, include explicit strategy evidence refs showing `existing` and `extended` were evaluated and rejected" in content
    assert "keep contract projection as execution truth for this run and emit explicit upstream writeback repair actions" in content
    assert "`/sdd.specify`" in content
    assert "`/sdd.plan.test-matrix`" in content


def test_manifest_schema_contract_between_tasks_and_implement():
    tasks_command = read("templates/commands/tasks.md")
    implement_command = read("templates/commands/implement.md")

    assert "Top-level keys: `schema_version`, `generated_at`, `generated_from`, `tasks`" in tasks_command
    assert "`generated_from` keys: `plan_path`, `plan_source_fingerprint`, `contract_source_fingerprints`" in tasks_command
    assert "use `tasks.manifest.json` when schema validation passes" in implement_command
    assert "fallback to `tasks.md` parsing when manifest is missing or invalid" in implement_command
    assert "task keys: `task_id`, `dependencies`, `if_scope`, `refs`, `target_paths`, `completion_anchors`, `conflict_hints`, `topo_layer`, `status`" in implement_command
    assert "Active execution targets rely on `new` repo anchors without explicit rejection evidence for `existing` and `extended`." in implement_command
    assert "LOCAL_EXECUTION_PROTOCOL" in implement_command
    assert "no bypass of repo-anchor strategy priority (`existing -> extended -> new`)" in implement_command
    assert "Unified Repository-First Gate Protocol (`URFGP`)" in implement_command
    assert "Repository-First Evidence Bundle (`RFEB`)" in implement_command


def test_docs_describe_tasks_as_execution_decomposition_only():
    readme = read("README.md")
    spec_driven = read("spec-driven.md")

    assert "This is an execution decomposition step only" in readme
    assert "hard-fails on missing execution anchors instead of supplementing design or writing placeholder tasks" in readme
    assert "projects the completed planning-stage design set into an executable task list" in spec_driven
    assert "does not supplement missing design or audit the feature end-to-end" in spec_driven

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from specify_cli.extensions import CommandRegistrar


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TOOLS = ("bash", "zip", "find", "sed", "awk")
PACKAGED_COMMAND_DIR_OVERRIDES = {
    "cursor-agent": ".cursor/commands",
    "kilocode": ".kilocode/rules",
    "auggie": ".augment/rules",
    "agy": ".agent/workflows",
    "vibe": ".vibe/prompts",
    "generic": ".sdd/commands",
}
EXPECTED_MARKERS = [
    "`spec.md` becomes the authoritative feature-semantics artifact",
    "derived views only; they MUST NOT override upstream artifacts or downstream stage artifacts",
    "authoritative for planning queue state, binding-projection rows, and source/output fingerprints only",
    "matrix dependency facts plus `SIG-*` governance signals including divergence, version-source-mix, and `unresolved`",
    "using concrete module-to-module rows as the primary representation",
    "Repository-first explainable evidence",
    "Repository-first Validation Trace",
    "CRITICAL/HIGH findings MUST cite the authoritative source artifact(s)",
    "## UIF + UDD Coverage Protocol (MUST)",
    "## Deterministic Prototype Selection Protocol (MUST)",
    "Every demonstrated user interaction MUST trace back to an explicit `UIF` node.",
    "The prototype should visibly dedicate a primary review surface to the selected `UIF` path/node progression",
    "Only surface the subset of completed `Entity.field` rows needed to make the selected interaction understandable from the user's point of view.",
    "Every business-significant datum that appears inside the demonstrated interaction MUST trace back to explicit completed `Entity.field` rows.",
    "The prototype should visibly dedicate a peer review surface to step-level `UDD` feedback",
    "Otherwise, choose exactly one primary walkthrough by this priority order:",
    "`UIF Interaction View` MUST enumerate the selected `UIF` nodes in execution order",
    "`UDD-backed View State` MUST map each selected `UIF` node to the user-visible feedback or state change",
    "Do not make IDs, coverage ledgers, or audit-style badges the dominant visible content of the prototype.",
    "`ui.html` should deliver a tool, not a document page.",
    "Organize the experience around a closed interaction loop: context -> action -> system feedback -> completion/result -> next action",
    "`ui.html` MUST make the core expression of `spec.md` easier to perceive through interaction",
    "Start by extracting one plain-language expression sentence from `spec.md`",
    "`UIF Coverage Summary`",
    "`UDD Coverage Summary`",
]


requires_packaging_tools = pytest.mark.skipif(
    any(shutil.which(tool) is None for tool in REQUIRED_TOOLS),
    reason="release packaging tools are unavailable",
)
requires_pwsh = pytest.mark.skipif(
    shutil.which("pwsh") is None,
    reason="pwsh is unavailable",
)


def _copy_tree(rel_path: str, dest_root: Path) -> None:
    src = REPO_ROOT / rel_path
    if not src.exists():
        return
    dst = dest_root / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)


def _release_agents(script_text: str) -> list[str]:
    match = re.search(r"ALL_AGENTS=\(([^)]*)\)", script_text)
    assert match is not None
    return match.group(1).split()


def _read_text_files(root: Path) -> str:
    chunks: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in {".md", ".toml"} and path.name != "SKILL.md":
            continue
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _packaged_command_dir(package_root: Path, agent: str) -> Path:
    if agent in PACKAGED_COMMAND_DIR_OVERRIDES:
        return package_root / PACKAGED_COMMAND_DIR_OVERRIDES[agent]
    registrar_key = "cursor" if agent == "cursor-agent" else agent
    return package_root / CommandRegistrar.AGENT_CONFIGS[registrar_key]["dir"]


def _prepare_packaging_fixture(tmp_path: Path) -> None:
    for rel in [
        ".github/workflows/scripts",
        "agent_templates",
        "memory",
        "scripts",
        "src",
        "templates",
    ]:
        _copy_tree(rel, tmp_path)

def _assert_packaged_authority_markers(tmp_path: Path, agents: list[str], suffix: str) -> None:
    for agent in agents:
        package_root = tmp_path / ".genreleases" / f"sdd-{agent}-package-{suffix}"
        command_dir = _packaged_command_dir(package_root, agent)
        assert command_dir.exists(), f"missing command directory for {agent}: {command_dir}"
        combined_text = _read_text_files(command_dir)
        for marker in EXPECTED_MARKERS:
            assert marker in combined_text, f"missing authority marker for {agent}: {marker}"


@requires_packaging_tools
def test_bash_release_packaging_carries_authority_protocol_into_all_agent_outputs(tmp_path: Path):
    _prepare_packaging_fixture(tmp_path)

    script_path = tmp_path / ".github" / "workflows" / "scripts" / "create-release-packages.sh"
    script_text = script_path.read_text(encoding="utf-8")
    agents = _release_agents(script_text)

    env = os.environ.copy()
    env["AGENTS"] = " ".join(agents)
    env["SCRIPTS"] = "sh"

    subprocess.run(
        ["bash", str(script_path), "v0.0.9"],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    _assert_packaged_authority_markers(tmp_path, agents, "sh")


@requires_packaging_tools
@requires_pwsh
def test_powershell_release_packaging_carries_authority_protocol_into_all_agent_outputs(tmp_path: Path):
    _prepare_packaging_fixture(tmp_path)

    script_path = tmp_path / ".github" / "workflows" / "scripts" / "create-release-packages.ps1"
    script_text = script_path.read_text(encoding="utf-8")
    match = re.search(r"\$AllAgents\s*=\s*@\(([^)]*)\)", script_text)
    if match is not None:
        agents = re.findall(r"'([^']+)'", match.group(1))
    else:
        assert "$AllAgents = Get-AllAgents" in script_text
        helper_script = script_path.parent / "list-agent-config-keys.py"
        python_exe = shutil.which("python3") or shutil.which("python")
        assert python_exe is not None
        helper_result = subprocess.run(
            [python_exe, str(helper_script)],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        )
        agents = [line.strip() for line in helper_result.stdout.splitlines() if line.strip()]

    assert agents

    subprocess.run(
        [
            "pwsh",
            "-File",
            str(script_path),
            "v0.0.9",
            "-Agents",
            " ".join(agents),
            "-Scripts",
            "sh",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    _assert_packaged_authority_markers(tmp_path, agents, "sh")

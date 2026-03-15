"""Consistency checks for agent configuration across runtime and packaging scripts."""

import re
import subprocess
import sys
from pathlib import Path

from specify_cli import AGENT_CONFIG, AI_ASSISTANT_ALIASES, AI_ASSISTANT_HELP
from specify_cli.extensions import CommandRegistrar


REPO_ROOT = Path(__file__).resolve().parent.parent
HELPER_SCRIPT = REPO_ROOT / ".github" / "workflows" / "scripts" / "list-agent-config-keys.py"


def _agent_keys_from_helper() -> list[str]:
    result = subprocess.run(
        [sys.executable, str(HELPER_SCRIPT)],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


class TestAgentConfigConsistency:
    """Ensure kiro-cli migration stays synchronized across key surfaces."""

    def test_runtime_config_uses_kiro_cli_and_removes_q(self):
        """AGENT_CONFIG should include kiro-cli and exclude legacy q."""
        assert "kiro-cli" in AGENT_CONFIG
        assert AGENT_CONFIG["kiro-cli"]["folder"] == ".kiro/"
        assert AGENT_CONFIG["kiro-cli"]["commands_subdir"] == "prompts"
        assert "q" not in AGENT_CONFIG

    def test_extension_registrar_uses_kiro_cli_and_removes_q(self):
        """Extension command registrar should target .kiro/prompts."""
        cfg = CommandRegistrar.AGENT_CONFIGS

        assert "kiro-cli" in cfg
        assert cfg["kiro-cli"]["dir"] == ".kiro/prompts"
        assert "q" not in cfg

    def test_extension_registrar_includes_codex(self):
        """Extension command registrar should include codex targeting .codex/prompts."""
        cfg = CommandRegistrar.AGENT_CONFIGS

        assert "codex" in cfg
        assert cfg["codex"]["dir"] == ".codex/prompts"

    def test_release_agent_lists_include_kiro_cli_and_exclude_q(self):
        """Release packaging should source agent keys from AGENT_CONFIG helper output."""
        sh_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.sh").read_text(encoding="utf-8")
        ps_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.ps1").read_text(encoding="utf-8")
        helper_agents = _agent_keys_from_helper()

        assert "list-agent-config-keys.py" in sh_text
        assert "list-agent-config-keys.py" in ps_text
        assert helper_agents == list(AGENT_CONFIG.keys())

        assert "kiro-cli" in helper_agents
        assert "shai" in helper_agents
        assert "agy" in helper_agents
        assert "q" not in helper_agents

    def test_release_ps_switch_has_shai_and_agy_generation(self):
        """PowerShell release builder must generate files for shai and agy agents."""
        ps_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.ps1").read_text(encoding="utf-8")

        assert re.search(r"'shai'\s*\{.*?\.shai/commands", ps_text, re.S) is not None
        assert re.search(r"'agy'\s*\{.*?\.agent/workflows", ps_text, re.S) is not None

    def test_init_ai_help_includes_roo_and_kiro_alias(self):
        """CLI help text for --ai should stay in sync with agent config and alias guidance."""
        assert "roo" in AI_ASSISTANT_HELP
        for alias, target in AI_ASSISTANT_ALIASES.items():
            assert alias in AI_ASSISTANT_HELP
            assert target in AI_ASSISTANT_HELP

    def test_devcontainer_kiro_installer_uses_pinned_checksum(self):
        """Devcontainer installer should always verify Kiro installer via pinned SHA256."""
        post_create_text = (REPO_ROOT / ".devcontainer" / "post-create.sh").read_text(encoding="utf-8")

        assert 'KIRO_INSTALLER_SHA256="7487a65cf310b7fb59b357c4b5e6e3f3259d383f4394ecedb39acf70f307cffb"' in post_create_text
        assert "sha256sum -c -" in post_create_text
        assert "KIRO_SKIP_KIRO_INSTALLER_VERIFY" not in post_create_text

    def test_release_output_targets_kiro_prompt_dir(self):
        """Packaging scripts should target Kiro prompt dir and GitHub release should collect template archives by glob."""
        sh_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.sh").read_text(encoding="utf-8")
        ps_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.ps1").read_text(encoding="utf-8")
        gh_release_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-github-release.sh").read_text(encoding="utf-8")

        assert ".kiro/prompts" in sh_text
        assert ".kiro/prompts" in ps_text
        assert ".amazonq/prompts" not in sh_text
        assert ".amazonq/prompts" not in ps_text

        assert "spec-kit-template-*-${VERSION}.zip" in gh_release_text
        assert "spec-kit-template-q-" not in gh_release_text

    def test_agent_context_scripts_use_kiro_cli(self):
        """Agent context scripts should advertise kiro-cli and not legacy q agent key."""
        bash_text = (REPO_ROOT / "scripts" / "bash" / "update-agent-context.sh").read_text(encoding="utf-8")
        pwsh_text = (REPO_ROOT / "scripts" / "powershell" / "update-agent-context.ps1").read_text(encoding="utf-8")

        assert "kiro-cli" in bash_text
        assert "kiro-cli" in pwsh_text
        assert "Amazon Q Developer CLI" not in bash_text
        assert "Amazon Q Developer CLI" not in pwsh_text

    # --- Tabnine CLI consistency checks ---

    def test_runtime_config_includes_tabnine(self):
        """AGENT_CONFIG should include tabnine with correct folder and subdir."""
        assert "tabnine" in AGENT_CONFIG
        assert AGENT_CONFIG["tabnine"]["folder"] == ".tabnine/agent/"
        assert AGENT_CONFIG["tabnine"]["commands_subdir"] == "commands"
        assert AGENT_CONFIG["tabnine"]["requires_cli"] is True
        assert AGENT_CONFIG["tabnine"]["install_url"] is not None

    def test_extension_registrar_includes_tabnine(self):
        """CommandRegistrar.AGENT_CONFIGS should include tabnine with correct TOML config."""
        from specify_cli.extensions import CommandRegistrar

        assert "tabnine" in CommandRegistrar.AGENT_CONFIGS
        cfg = CommandRegistrar.AGENT_CONFIGS["tabnine"]
        assert cfg["dir"] == ".tabnine/agent/commands"
        assert cfg["format"] == "toml"
        assert cfg["args"] == "{{args}}"
        assert cfg["extension"] == ".toml"

    def test_release_agent_lists_include_tabnine(self):
        """Release packaging should include tabnine via AGENT_CONFIG helper keys."""
        helper_agents = _agent_keys_from_helper()
        assert "tabnine" in helper_agents

    def test_release_scripts_generate_tabnine_toml_commands(self):
        """Release scripts should generate TOML commands for tabnine in .tabnine/agent/commands."""
        sh_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.sh").read_text(encoding="utf-8")
        ps_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.ps1").read_text(encoding="utf-8")

        assert ".tabnine/agent/commands" in sh_text
        assert ".tabnine/agent/commands" in ps_text
        assert re.search(r"'tabnine'\s*\{.*?\.tabnine/agent/commands", ps_text, re.S) is not None

    def test_github_release_includes_tabnine_packages(self):
        """GitHub release script should upload all template packages using glob expansion."""
        gh_release_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-github-release.sh").read_text(encoding="utf-8")

        assert "spec-kit-template-*-${VERSION}.zip" in gh_release_text

    def test_agent_context_scripts_include_tabnine(self):
        """Agent context scripts should support tabnine agent type."""
        bash_text = (REPO_ROOT / "scripts" / "bash" / "update-agent-context.sh").read_text(encoding="utf-8")
        pwsh_text = (REPO_ROOT / "scripts" / "powershell" / "update-agent-context.ps1").read_text(encoding="utf-8")

        assert "tabnine" in bash_text
        assert "TABNINE_FILE" in bash_text
        assert "tabnine" in pwsh_text
        assert "TABNINE_FILE" in pwsh_text

    def test_ai_help_includes_tabnine(self):
        """CLI help text for --ai should include tabnine."""
        assert "tabnine" in AI_ASSISTANT_HELP

    # --- Cline consistency checks ---

    def test_runtime_config_includes_cline(self):
        """AGENT_CONFIG should include cline with .clinerules/workflows."""
        assert "cline" in AGENT_CONFIG
        assert AGENT_CONFIG["cline"]["folder"] == ".clinerules/"
        assert AGENT_CONFIG["cline"]["commands_subdir"] == "workflows"
        assert AGENT_CONFIG["cline"]["requires_cli"] is False

    def test_extension_registrar_includes_cline(self):
        """CommandRegistrar.AGENT_CONFIGS should include cline workflow directory."""
        cfg = CommandRegistrar.AGENT_CONFIGS
        assert "cline" in cfg
        assert cfg["cline"]["dir"] == ".clinerules/workflows"

    def test_release_scripts_include_cline(self):
        """Release scripts should include cline in packaging outputs and template glob upload."""
        sh_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.sh").read_text(encoding="utf-8")
        ps_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.ps1").read_text(encoding="utf-8")
        gh_release_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-github-release.sh").read_text(encoding="utf-8")

        assert "cline" in sh_text
        assert "cline" in ps_text
        assert ".clinerules/workflows" in sh_text
        assert ".clinerules/workflows" in ps_text
        assert "spec-kit-template-*-${VERSION}.zip" in gh_release_text

    def test_agent_context_scripts_include_cline(self):
        """Agent context scripts should support cline agent type."""
        bash_text = (REPO_ROOT / "scripts" / "bash" / "update-agent-context.sh").read_text(encoding="utf-8")
        pwsh_text = (REPO_ROOT / "scripts" / "powershell" / "update-agent-context.ps1").read_text(encoding="utf-8")

        assert "cline" in bash_text
        assert "CLINE_FILE" in bash_text
        assert "cline" in pwsh_text
        assert "CLINE_FILE" in pwsh_text

    def test_ai_help_includes_cline(self):
        """CLI help text for --ai should include cline."""
        assert "cline" in AI_ASSISTANT_HELP

    # --- Kimi Code CLI consistency checks ---

    def test_kimi_in_agent_config(self):
        """AGENT_CONFIG should include kimi with correct folder and commands_subdir."""
        assert "kimi" in AGENT_CONFIG
        assert AGENT_CONFIG["kimi"]["folder"] == ".kimi/"
        assert AGENT_CONFIG["kimi"]["commands_subdir"] == "skills"
        assert AGENT_CONFIG["kimi"]["requires_cli"] is True

    def test_kimi_in_extension_registrar(self):
        """Extension command registrar should include kimi using .kimi/skills and SKILL.md."""
        cfg = CommandRegistrar.AGENT_CONFIGS

        assert "kimi" in cfg
        kimi_cfg = cfg["kimi"]
        assert kimi_cfg["dir"] == ".kimi/skills"
        assert kimi_cfg["extension"] == "/SKILL.md"

    def test_kimi_in_release_agent_lists(self):
        """Release packaging should include kimi via AGENT_CONFIG helper keys."""
        helper_agents = _agent_keys_from_helper()

        assert "kimi" in helper_agents

    def test_kimi_in_powershell_validate_set(self):
        """PowerShell update-agent-context script should include 'kimi' in ValidateSet."""
        ps_text = (REPO_ROOT / "scripts" / "powershell" / "update-agent-context.ps1").read_text(encoding="utf-8")

        validate_set_match = re.search(r"\[ValidateSet\(([^)]*)\)\]", ps_text)
        assert validate_set_match is not None
        validate_set_values = re.findall(r"'([^']+)'", validate_set_match.group(1))

        assert "kimi" in validate_set_values

    def test_kimi_in_github_release_output(self):
        """GitHub release script should upload template packages via template glob."""
        gh_release_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-github-release.sh").read_text(encoding="utf-8")

        assert "spec-kit-template-*-${VERSION}.zip" in gh_release_text

    def test_ai_help_includes_kimi(self):
        """CLI help text for --ai should include kimi."""
        assert "kimi" in AI_ASSISTANT_HELP

    def test_generate_release_notes_warns_about_commit_subject_quality(self):
        """Release notes generator should document commit-subject quality dependency."""
        notes_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "generate-release-notes.sh").read_text(encoding="utf-8")

        assert "Output quality depends on commit subject quality" in notes_text
        assert "Conventional Commits" in notes_text
        assert "Changelog lines are generated from commit subjects" in notes_text

    def test_simulate_release_documents_mutating_behavior(self):
        """simulate-release should clearly warn that it mutates local files and is not read-only."""
        simulate_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "simulate-release.sh").read_text(encoding="utf-8")

        assert "intentionally modifies local files" in simulate_text
        assert "Do not include it in read-only preflight checks" in simulate_text
        assert "LOCAL FILES WERE MODIFIED AS PART OF THIS SIMULATION" in simulate_text

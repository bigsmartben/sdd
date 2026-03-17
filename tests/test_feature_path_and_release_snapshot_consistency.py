from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_bash_and_powershell_share_prefix_based_feature_dir_resolution():
    bash = read("scripts/bash/common.sh")
    pwsh = read("scripts/powershell/common.ps1")

    # Both sides should use prefix-based resolver from get_feature_paths / Get-FeaturePathsEnv
    assert "find_feature_dir_by_prefix" in bash
    assert "local feature_dir=$(find_feature_dir_by_prefix \"$repo_root\" \"$current_branch\")" in bash

    assert "Find-FeatureDirByPrefix" in pwsh
    assert "$featureDir = Find-FeatureDirByPrefix -RepoRoot $repoRoot -BranchName $currentBranch" in pwsh

    # Both sides should implement the same 3-digit prefix rule
    assert "^([0-9]{3})-" in bash
    assert "^(\\d{3})-" in pwsh


def test_release_packaging_templates_snapshot_and_path_rewrite_rules_are_consistent():
    bash_release = read(".github/workflows/scripts/create-release-packages.sh")
    pwsh_release = read(".github/workflows/scripts/create-release-packages.ps1")

    # Snapshot copy: templates -> .specify/templates and exclude commands + vscode settings
    assert "if [[ -d templates ]]; then" in bash_release
    assert "mkdir -p \"$spec_dir/templates\"" in bash_release
    assert "-not -path \"templates/commands/*\"" in bash_release
    assert "-not -name \"vscode-settings.json\"" in bash_release

    assert "if (Test-Path \"templates\")" in pwsh_release
    assert "$templatesDestDir = Join-Path $specDir \"templates\"" in pwsh_release
    assert "-notmatch 'templates[/\\\\]commands[/\\\\]'" in pwsh_release
    assert "$_.Name -ne 'vscode-settings.json'" in pwsh_release

    # Command rewrite paths include templates -> .specify/templates on both platforms
    assert "s@(/?)templates/@.specify/templates/@g" in bash_release
    assert "-replace '(/?)\\btemplates/', '.specify/templates/'" in pwsh_release


def test_release_packaging_rewrites_memory_and_scripts_paths_on_both_platforms():
    bash_release = read(".github/workflows/scripts/create-release-packages.sh")
    pwsh_release = read(".github/workflows/scripts/create-release-packages.ps1")

    assert "s@(/?)memory/@.specify/memory/@g" in bash_release
    assert "s@(/?)scripts/@.specify/scripts/@g" in bash_release

    assert "-replace '(/?)\\bmemory/', '.specify/memory/'" in pwsh_release
    assert "-replace '(/?)\\bscripts/', '.specify/scripts/'" in pwsh_release

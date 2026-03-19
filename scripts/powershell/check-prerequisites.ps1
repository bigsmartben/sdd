#!/usr/bin/env pwsh

# Consolidated prerequisite checking script (PowerShell)
#
# This script provides unified prerequisite checking for Spec-Driven Development workflow.
# It replaces the functionality previously spread across multiple scripts.
#
# Usage: ./check-prerequisites.ps1 [OPTIONS]
#
# OPTIONS:
#   -Json               Output in JSON format
#   -RequireTasks       Require tasks.md to exist (for implementation phase)
#   -IncludeTasks       Include tasks.md in AVAILABLE_DOCS list
#   -DataModelPreflight Include compact data-model bootstrap packet extracted from plan.md (primary /sdd.plan.data-model readiness gate, JSON mode only)
#   -TaskPreflight      Include compact tasks bootstrap packet extracted from plan.md (primary /sdd.tasks readiness gate, JSON mode only)
#   -ImplementPreflight Include compact implement bootstrap packet extracted from analyze-history.md (primary /sdd.implement analyze gate, JSON mode only)
#   -PathsOnly          Only output path variables (no validation)
#   -Help, -h           Show help message

[CmdletBinding(PositionalBinding = $false)]
param(
    [switch]$Json,
    [switch]$RequireTasks,
    [switch]$IncludeTasks,
    [switch]$DataModelPreflight,
    [switch]$TaskPreflight,
    [switch]$ImplementPreflight,
    [switch]$PathsOnly,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

function Resolve-SpecifyCommand {
    $override = $env:SDD_SPECIFY_CMD
    if (-not [string]::IsNullOrWhiteSpace($override)) {
        if (Test-Path $override -PathType Leaf) {
            return (Resolve-Path $override).Path
        }

        $overrideCommand = Get-Command $override -ErrorAction SilentlyContinue
        if ($overrideCommand) {
            return $overrideCommand.Source
        }

        return $null
    }

    $specifyCommand = Get-Command specify -ErrorAction SilentlyContinue
    if ($specifyCommand) {
        return $specifyCommand.Source
    }

    return $null
}

function Get-LocalExecutionProtocol {
    param(
        [Parameter(Mandatory = $true)]
        [bool]$HasGit
    )

    $hasRipgrep = [bool](Get-Command rg -ErrorAction SilentlyContinue)
    $hasGitCli = [bool](Get-Command git -ErrorAction SilentlyContinue)
    $specifyCmd = Resolve-SpecifyCommand
    $hasSpecify = -not [string]::IsNullOrWhiteSpace($specifyCmd)

    $repoSearch = [ordered]@{
        available = $false
        tool = 'unavailable'
        list_files_cmd = ''
        search_text_cmd = ''
    }

    if ($hasRipgrep) {
        $repoSearch.available = $true
        $repoSearch.tool = 'rg'
        $repoSearch.list_files_cmd = 'rg --files'
        $repoSearch.search_text_cmd = "rg -n --hidden --glob '!.git/*' -- <pattern>"
    } elseif ($HasGit -and $hasGitCli) {
        $repoSearch.available = $true
        $repoSearch.tool = 'git'
        $repoSearch.list_files_cmd = 'git ls-files'
        $repoSearch.search_text_cmd = 'git grep -n -- <pattern>'
    }

    $repoInspection = [ordered]@{
        available = $false
        status_cmd = ''
        diff_cmd = ''
        history_cmd = ''
    }
    if ($HasGit -and $hasGitCli) {
        $repoInspection.available = $true
        $repoInspection.status_cmd = 'git status --short'
        $repoInspection.diff_cmd = 'git diff -- <path>'
        $repoInspection.history_cmd = 'git log --oneline -- <path>'
    }

    $python = [ordered]@{
        available = $false
        tool = 'unavailable'
        runner_cmd = ''
    }
    $runtimeTools = $null
    if ($hasSpecify) {
        if (-not [string]::IsNullOrWhiteSpace($specifyCmd)) {
            try {
                $runtimeToolsJson = & $specifyCmd internal-runtime-tools
                if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($runtimeToolsJson)) {
                    $runtimeTools = $runtimeToolsJson | ConvertFrom-Json
                    $python.available = $true
                    $python.tool = 'specify-cli'
                    $python.runner_cmd = 'specify internal-run-python --script <helper-script> -- <helper-args>'
                }
            } catch {
                $runtimeTools = $null
            }
        }
    }

    return [ordered]@{
        schema_version = '1.0'
        rules = @(
            'Reuse the emitted commands before trying alternates.',
            'Do not install missing tools or mutate PATH during /sdd runs.',
            'Use project-specific build/test commands only when they are task anchors or repo-backed scripts/configs.'
        )
        repo_search = $repoSearch
        repo_inspection = $repoInspection
        python = $python
        runtime_tools = $runtimeTools
    }
}

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: check-prerequisites.ps1 [OPTIONS]

Consolidated prerequisite checking for Spec-Driven Development workflow.

OPTIONS:
  -Json               Output in JSON format
  -RequireTasks       Require tasks.md to exist (for implementation phase)
  -IncludeTasks       Include tasks.md in AVAILABLE_DOCS list
  -DataModelPreflight Include compact data-model bootstrap packet extracted from plan.md (primary /sdd.plan.data-model readiness gate, JSON mode only)
  -TaskPreflight      Include compact tasks bootstrap packet extracted from plan.md (primary /sdd.tasks readiness gate, JSON mode only)
  -ImplementPreflight Include compact implement bootstrap packet extracted from analyze-history.md (primary /sdd.implement analyze gate, JSON mode only)
  -PathsOnly          Only output path variables (no prerequisite validation)
  -Help, -h           Show this help message

EXAMPLES:
  # Check task prerequisites (plan.md required)
  .\check-prerequisites.ps1 -Json
  
  # Check implementation prerequisites (plan.md + tasks.md required)
  .\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks

  # Extract compact data-model bootstrap packet for /sdd.plan.data-model
  .\check-prerequisites.ps1 -Json -DataModelPreflight

  # Extract compact tasks bootstrap packet for /sdd.tasks
  .\check-prerequisites.ps1 -Json -TaskPreflight

  # Extract compact implementation bootstrap packet for /sdd.implement
  .\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks -ImplementPreflight
  
  # Get feature paths only (no validation)
  .\check-prerequisites.ps1 -PathsOnly

"@
    exit 0
}

if ($DataModelPreflight -and -not $Json) {
    Write-Output "ERROR: -DataModelPreflight requires -Json output mode."
    exit 1
}

if ($TaskPreflight -and -not $Json) {
    Write-Output "ERROR: -TaskPreflight requires -Json output mode."
    exit 1
}

if ($ImplementPreflight -and -not $Json) {
    Write-Output "ERROR: -ImplementPreflight requires -Json output mode."
    exit 1
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get feature paths and validate branch.
$paths = Get-FeaturePathsEnv
if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -HasGit:$paths.HAS_GIT)) {
    exit 1
}

# If paths-only mode, output paths and exit (support combined -Json -PathsOnly)
if ($PathsOnly) {
    if ($Json) {
        [PSCustomObject]@{
            REPO_ROOT    = $paths.REPO_ROOT
            BRANCH       = $paths.CURRENT_BRANCH
            FEATURE_DIR  = $paths.FEATURE_DIR
            FEATURE_SPEC = $paths.FEATURE_SPEC
            IMPL_PLAN    = $paths.IMPL_PLAN
            TASKS        = $paths.TASKS
        } | ConvertTo-Json -Compress
    } else {
        Write-Output "REPO_ROOT: $($paths.REPO_ROOT)"
        Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
        Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"
        Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
        Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
        Write-Output "TASKS: $($paths.TASKS)"
    }
    exit 0
}

# Validate required directories and files
if (-not (Test-Path $paths.FEATURE_DIR -PathType Container)) {
    Write-Output "ERROR: Feature directory not found: $($paths.FEATURE_DIR)"
    Write-Output "Run /sdd.specify first to create the feature structure."
    exit 1
}

if (-not (Test-Path $paths.IMPL_PLAN -PathType Leaf)) {
    Write-Output "ERROR: plan.md not found in $($paths.FEATURE_DIR)"
    Write-Output "Run /sdd.plan first to create the implementation plan."
    exit 1
}

# Check for tasks.md if required
if ($RequireTasks -and -not (Test-Path $paths.TASKS -PathType Leaf)) {
    Write-Output "ERROR: tasks.md not found in $($paths.FEATURE_DIR)"
    Write-Output "Run /sdd.tasks first to create the task list."
    exit 1
}

# Build list of available documents
$docs = @()

# Check planning support docs when present
if (Test-Path $paths.RESEARCH) { $docs += 'research.md' }
if (Test-Path $paths.DATA_MODEL) { $docs += 'data-model.md' }

# Check contracts directory (only if it exists and has files)
if ((Test-Path $paths.CONTRACTS_DIR) -and (Get-ChildItem -Path $paths.CONTRACTS_DIR -ErrorAction SilentlyContinue | Select-Object -First 1)) { 
    $docs += 'contracts/' 
}

if (Test-Path $paths.TEST_MATRIX) { $docs += 'test-matrix.md' }

# Include tasks.md if requested and it exists
if ($IncludeTasks -and (Test-Path $paths.TASKS)) { 
    $docs += 'tasks.md' 
}

# Output results
if ($Json) {
    # JSON output
    $payload = [ordered]@{
        FEATURE_DIR = $paths.FEATURE_DIR
        AVAILABLE_DOCS = $docs
        LOCAL_EXECUTION_PROTOCOL = Get-LocalExecutionProtocol -HasGit:$paths.HAS_GIT
    }

    if ($DataModelPreflight) {
        $payload.DATA_MODEL_BOOTSTRAP = $null
        $specifyCmd = Resolve-SpecifyCommand
        if (-not [string]::IsNullOrWhiteSpace($specifyCmd)) {
            try {
                $dataModelBootstrapJson = & $specifyCmd internal-data-model-bootstrap `
                    --feature-dir $paths.FEATURE_DIR `
                    --plan $paths.IMPL_PLAN `
                    --spec $paths.FEATURE_SPEC `
                    --research $paths.RESEARCH `
                    --data-model $paths.DATA_MODEL

                if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($dataModelBootstrapJson)) {
                    $payload.DATA_MODEL_BOOTSTRAP = $dataModelBootstrapJson | ConvertFrom-Json
                }
            } catch {
                $payload.DATA_MODEL_BOOTSTRAP = $null
            }
        }
    }

    if ($TaskPreflight) {
        $payload.TASKS_BOOTSTRAP = $null
        $specifyCmd = Resolve-SpecifyCommand
        if (-not [string]::IsNullOrWhiteSpace($specifyCmd)) {
            try {
                $taskBootstrapJson = & $specifyCmd internal-task-bootstrap `
                    --feature-dir $paths.FEATURE_DIR `
                    --plan $paths.IMPL_PLAN `
                    --spec $paths.FEATURE_SPEC `
                    --data-model $paths.DATA_MODEL `
                    --test-matrix $paths.TEST_MATRIX `
                    --contracts-dir $paths.CONTRACTS_DIR

                if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($taskBootstrapJson)) {
                    $payload.TASKS_BOOTSTRAP = $taskBootstrapJson | ConvertFrom-Json
                }
            } catch {
                $payload.TASKS_BOOTSTRAP = $null
            }
        }
    }

    if ($ImplementPreflight) {
        $payload.IMPLEMENT_BOOTSTRAP = $null
        $specifyCmd = Resolve-SpecifyCommand
        if (-not [string]::IsNullOrWhiteSpace($specifyCmd)) {
            try {
                $implementBootstrapJson = & $specifyCmd internal-implement-bootstrap `
                    --feature-dir $paths.FEATURE_DIR `
                    --spec $paths.FEATURE_SPEC `
                    --plan $paths.IMPL_PLAN `
                    --tasks $paths.TASKS `
                    --analyze-history (Join-Path $paths.FEATURE_DIR 'audits/analyze-history.md')

                if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($implementBootstrapJson)) {
                    $payload.IMPLEMENT_BOOTSTRAP = $implementBootstrapJson | ConvertFrom-Json
                }
            } catch {
                $payload.IMPLEMENT_BOOTSTRAP = $null
            }
        }
    }

    [PSCustomObject]$payload | ConvertTo-Json -Compress -Depth 8
} else {
    # Text output
    Write-Output "FEATURE_DIR:$($paths.FEATURE_DIR)"
    Write-Output "AVAILABLE_DOCS:"
    
    # Show status of each potential document
    Test-FileExists -Path $paths.RESEARCH -Description 'research.md' | Out-Null
    Test-FileExists -Path $paths.DATA_MODEL -Description 'data-model.md' | Out-Null
    Test-DirHasFiles -Path $paths.CONTRACTS_DIR -Description 'contracts/' | Out-Null
    Test-FileExists -Path $paths.TEST_MATRIX -Description 'test-matrix.md' | Out-Null
    
    if ($IncludeTasks) {
        Test-FileExists -Path $paths.TASKS -Description 'tasks.md' | Out-Null
    }
}

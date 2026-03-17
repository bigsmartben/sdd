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
#   -TaskPreflight      Include compact tasks bootstrap packet extracted from plan.md (JSON mode only)
#   -PathsOnly          Only output path variables (no validation)
#   -Help, -h           Show help message

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$RequireTasks,
    [switch]$IncludeTasks,
    [switch]$TaskPreflight,
    [string]$PlanFile,
    [switch]$PathsOnly,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: check-prerequisites.ps1 [OPTIONS]

Consolidated prerequisite checking for Spec-Driven Development workflow.

OPTIONS:
  -Json               Output in JSON format
  -RequireTasks       Require tasks.md to exist (for implementation phase)
  -IncludeTasks       Include tasks.md in AVAILABLE_DOCS list
  -TaskPreflight      Include compact tasks bootstrap packet extracted from plan.md (JSON mode only)
  -PlanFile <path>    Explicit path to plan.md under repo/specs/** for planning commands
  -PathsOnly          Only output path variables (no prerequisite validation)
  -Help, -h           Show this help message

EXAMPLES:
  # Check task prerequisites (plan.md required)
  .\check-prerequisites.ps1 -Json
  
  # Check implementation prerequisites (plan.md + tasks.md required)
  .\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks

  # Resolve planning inputs from an explicit plan.md path
  .\check-prerequisites.ps1 -Json -PlanFile specs/001-demo/plan.md

  # Extract compact tasks bootstrap packet for /sdd.tasks
  .\check-prerequisites.ps1 -Json -TaskPreflight
  
  # Get feature paths only (no validation)
  .\check-prerequisites.ps1 -PathsOnly

"@
    exit 0
}

if ($TaskPreflight -and -not $Json) {
    Write-Output "ERROR: -TaskPreflight requires -Json output mode."
    exit 1
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get feature paths and validate branch only when using active-feature discovery.
if ($PlanFile) {
    $paths = Get-FeaturePathsFromPlanFile -PlanFile $PlanFile
} else {
    $paths = Get-FeaturePathsEnv
    if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -HasGit:$paths.HAS_GIT)) {
        exit 1
    }
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
    }

    if ($TaskPreflight) {
        $payload.TASKS_BOOTSTRAP = $null
        $helper = Join-Path (Split-Path $PSScriptRoot -Parent) 'task_preflight.py'
        if (Test-Path $helper -PathType Leaf) {
            $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
            if (-not $pythonCmd) {
                $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
            }

            if ($pythonCmd) {
                try {
                    $taskBootstrapJson = & $pythonCmd.Source $helper `
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

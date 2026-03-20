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

function Stop-Script {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Lines,
        [string]$Reason = 'Prerequisite validation failed.'
    )

    foreach ($line in $Lines) {
        Write-Output $line
    }

    throw $Reason
}

function Resolve-SpecifyCommand {
    $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $repoShimDir = Join-Path $repoRoot '.test-bin'
    $repoShimCandidates = @(
        (Join-Path $repoShimDir 'specify'),
        (Join-Path $repoShimDir 'specify.cmd'),
        (Join-Path $repoShimDir 'specify.exe')
    )
    foreach ($candidate in $repoShimCandidates) {
        if (Test-Path $candidate -PathType Leaf) {
            return (Resolve-Path $candidate).Path
        }
    }

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

function Get-RequiredBootstrapPayload {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string]$InternalCommand,
        [string[]]$Arguments = @()
    )

    $specifyCmd = Resolve-SpecifyCommand
    if ([string]::IsNullOrWhiteSpace($specifyCmd)) {
        Stop-Script -Lines @("ERROR: $Label requested but specify runtime could not be resolved.")
    }

    try {
        $rawOutput = (& $specifyCmd $InternalCommand @Arguments 2>&1 | Out-String).Trim()
    } catch {
        Stop-Script -Lines @(
            "ERROR: $Label failed.",
            $_.Exception.Message
        )
    }

    if ($LASTEXITCODE -ne 0) {
        Stop-Script -Lines @(
            "ERROR: $Label failed.",
            $rawOutput
        )
    }

    if ([string]::IsNullOrWhiteSpace($rawOutput)) {
        Stop-Script -Lines @("ERROR: $Label produced empty output.")
    }

    try {
        return ($rawOutput | ConvertFrom-Json)
    } catch {
        Stop-Script -Lines @(
            "ERROR: $Label produced non-JSON output.",
            $rawOutput
        )
    }
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
        $runtimeToolCandidates = @()
        if (-not [string]::IsNullOrWhiteSpace($specifyCmd)) {
            $runtimeToolCandidates += $specifyCmd
        }

        $pathSpecify = Get-Command specify -ErrorAction SilentlyContinue
        if ($pathSpecify -and ($runtimeToolCandidates -notcontains $pathSpecify.Source)) {
            $runtimeToolCandidates += $pathSpecify.Source
        }

        foreach ($runtimeToolCandidate in $runtimeToolCandidates) {
            try {
                $runtimeToolsJson = & $runtimeToolCandidate internal-runtime-tools
                if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($runtimeToolsJson)) {
                    $runtimeTools = $runtimeToolsJson | ConvertFrom-Json
                    $python.available = $true
                    $python.tool = 'specify-cli'
                    $python.runner_cmd = 'specify internal-run-python --script <helper-script> -- <helper-args>'
                    break
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
    return
}

if ($DataModelPreflight -and -not $Json) {
    Write-Error "ERROR: -DataModelPreflight requires -Json output mode."
}

if ($TaskPreflight -and -not $Json) {
    Write-Error "ERROR: -TaskPreflight requires -Json output mode."
}

if ($ImplementPreflight -and -not $Json) {
    Write-Error "ERROR: -ImplementPreflight requires -Json output mode."
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get feature paths and validate branch.
$paths = Get-FeaturePathsEnv
if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -HasGit:$paths.HAS_GIT)) {
    throw "Feature branch validation failed."
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
            TASKS_MANIFEST = $paths.TASKS_MANIFEST
        } | ConvertTo-Json -Compress
    } else {
        Write-Output "REPO_ROOT: $($paths.REPO_ROOT)"
        Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
        Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"
        Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
        Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
        Write-Output "TASKS: $($paths.TASKS)"
        Write-Output "TASKS_MANIFEST: $($paths.TASKS_MANIFEST)"
    }
    return
}

# Validate required directories and files
if (-not (Test-Path $paths.FEATURE_DIR -PathType Container)) {
    Stop-Script -Lines @(
        "ERROR: Feature directory not found: $($paths.FEATURE_DIR)",
        "Run /sdd.specify first to create the feature structure."
    )
}

if (-not (Test-Path $paths.IMPL_PLAN -PathType Leaf)) {
    Stop-Script -Lines @(
        "ERROR: plan.md not found in $($paths.FEATURE_DIR)",
        "Run /sdd.plan first to create the implementation plan."
    )
}

# Check for tasks.md if required
if ($RequireTasks -and -not (Test-Path $paths.TASKS -PathType Leaf)) {
    Stop-Script -Lines @(
        "ERROR: tasks.md not found in $($paths.FEATURE_DIR)",
        "Run /sdd.tasks first to create the task list."
    )
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
        $payload.DATA_MODEL_BOOTSTRAP = Get-RequiredBootstrapPayload `
            -Label 'DATA_MODEL_BOOTSTRAP' `
            -InternalCommand 'internal-data-model-bootstrap' `
            -Arguments @(
                '--feature-dir', $paths.FEATURE_DIR,
                '--plan', $paths.IMPL_PLAN,
                '--spec', $paths.FEATURE_SPEC,
                '--research', $paths.RESEARCH,
                '--data-model', $paths.DATA_MODEL
            )
    }

    if ($TaskPreflight) {
        $payload.TASKS_BOOTSTRAP = Get-RequiredBootstrapPayload `
            -Label 'TASKS_BOOTSTRAP' `
            -InternalCommand 'internal-task-bootstrap' `
            -Arguments @(
                '--feature-dir', $paths.FEATURE_DIR,
                '--plan', $paths.IMPL_PLAN,
                '--spec', $paths.FEATURE_SPEC,
                '--data-model', $paths.DATA_MODEL,
                '--test-matrix', $paths.TEST_MATRIX,
                '--contracts-dir', $paths.CONTRACTS_DIR
            )
    }

    if ($ImplementPreflight) {
        $payload.IMPLEMENT_BOOTSTRAP = Get-RequiredBootstrapPayload `
            -Label 'IMPLEMENT_BOOTSTRAP' `
            -InternalCommand 'internal-implement-bootstrap' `
            -Arguments @(
                '--feature-dir', $paths.FEATURE_DIR,
                '--spec', $paths.FEATURE_SPEC,
                '--plan', $paths.IMPL_PLAN,
                '--tasks', $paths.TASKS,
                '--analyze-history', (Join-Path $paths.FEATURE_DIR 'audits/analyze-history.md')
            )
        $payload.TASKS_MANIFEST_BOOTSTRAP = Get-RequiredBootstrapPayload `
            -Label 'TASKS_MANIFEST_BOOTSTRAP' `
            -InternalCommand 'internal-tasks-manifest-bootstrap' `
            -Arguments @(
                '--feature-dir', $paths.FEATURE_DIR,
                '--plan', $paths.IMPL_PLAN,
                '--tasks', $paths.TASKS,
                '--tasks-manifest', $paths.TASKS_MANIFEST
            )
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

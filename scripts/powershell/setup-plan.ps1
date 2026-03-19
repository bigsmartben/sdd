#!/usr/bin/env pwsh
# Setup implementation plan for a feature

[CmdletBinding(PositionalBinding = $false)]
param(
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output "Usage: ./setup-plan.ps1 [-Json] [-Help]"
    Write-Output "  Uses current feature branch to resolve specs/<feature-key>/spec.md"
    Write-Output "  -Json             Output results in JSON format"
    Write-Output "  -Help             Show this help message"
    exit 0
}

# Load common functions
. "$PSScriptRoot/common.ps1"

$paths = Get-FeaturePathsEnv
$isFeatureBranch = [bool](Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -HasGit:$paths.HAS_GIT | Select-Object -Last 1)
if (-not $isFeatureBranch) {
    exit 1
}

$template = Join-Path $paths.REPO_ROOT '.specify/templates/plan-template.md'
if (-not (Test-Path $template -PathType Leaf)) {
    Write-Error "Required runtime template not found or not readable at $template"
    exit 1
}

# Validate spec file before creating plan.md beside it.
if (-not (Test-Path $paths.FEATURE_SPEC -PathType Leaf)) {
    Write-Error "spec.md not found at $($paths.FEATURE_SPEC)"
    exit 1 
}

$constitution = Join-Path $paths.REPO_ROOT '.specify/memory/constitution.md'
$dependencyMatrix = Join-Path $paths.REPO_ROOT '.specify/memory/repository-first/technical-dependency-matrix.md'
$moduleInvocation = Join-Path $paths.REPO_ROOT '.specify/memory/repository-first/module-invocation-spec.md'

foreach ($requiredPath in @($constitution, $dependencyMatrix, $moduleInvocation)) {
    if (-not (Test-Path $requiredPath -PathType Leaf)) {
        Write-Error "Required constitution or repository-first baseline not found or not readable at $requiredPath. Run /sdd.constitution first."
        exit 1
    }

    $item = Get-Item $requiredPath
    if ($item.Length -le 0) {
        Write-Error "Required constitution or repository-first baseline is empty at $requiredPath. Run /sdd.constitution first."
        exit 1
    }
}

# Ensure the feature directory exists
New-Item -ItemType Directory -Path $paths.FEATURE_DIR -Force | Out-Null

# Copy plan template
Copy-Item $template $paths.IMPL_PLAN -Force
if (-not $Json) {
    Write-Output "Copied plan template to $($paths.IMPL_PLAN)"
}

# Output results
if ($Json) {
    $result = [PSCustomObject]@{ 
        FEATURE_SPEC = $paths.FEATURE_SPEC
        IMPL_PLAN = $paths.IMPL_PLAN
        SPECS_DIR = $paths.FEATURE_DIR
        BRANCH = $paths.CURRENT_BRANCH
        HAS_GIT = $paths.HAS_GIT
    }
    $result | ConvertTo-Json -Compress
} else {
    Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
    Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
    Write-Output "SPECS_DIR: $($paths.FEATURE_DIR)"
    Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
    Write-Output "HAS_GIT: $($paths.HAS_GIT)"
}

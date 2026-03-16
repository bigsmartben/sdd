#!/usr/bin/env pwsh
# Setup implementation plan for a feature

[CmdletBinding()]
param(
    [switch]$Json,
    [string]$SpecFile,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output "Usage: ./setup-plan.ps1 -SpecFile <path/to/spec.md> [-Json] [-Help]"
    Write-Output "  -SpecFile <path>  Explicit path to spec.md under repo/specs/**"
    Write-Output "  -Json             Output results in JSON format"
    Write-Output "  -Help             Show this help message"
    exit 0
}

# Load common functions
. "$PSScriptRoot/common.ps1"

if (-not $SpecFile) {
    Write-Error "-SpecFile is required and must point to spec.md under repo/specs/**"
    exit 1
}

# Get all paths and variables from explicit spec file
$paths = Get-FeaturePathsFromSpecFile -SpecFile $SpecFile

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

# Ensure the feature directory exists
New-Item -ItemType Directory -Path $paths.FEATURE_DIR -Force | Out-Null

# Copy plan template
Copy-Item $template $paths.IMPL_PLAN -Force
Write-Output "Copied plan template to $($paths.IMPL_PLAN)"

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

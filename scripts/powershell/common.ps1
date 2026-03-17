#!/usr/bin/env pwsh
# Common PowerShell functions analogous to common.sh

function Get-RepoRoot {
    try {
        $result = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # Git command failed
    }
    
    # Fall back to script location for non-git repos
    return (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
}

function Get-CurrentBranch {
    # First check if SPECIFY_FEATURE environment variable is set
    if ($env:SPECIFY_FEATURE) {
        return $env:SPECIFY_FEATURE
    }
    
    # Then check git if available
    try {
        $result = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # Git command failed
    }
    
    # For non-git repos, try to find the latest feature directory
    $repoRoot = Get-RepoRoot
    $specsDir = Join-Path $repoRoot "specs"
    
    if (Test-Path $specsDir) {
        $latestFeature = ""
        $highest = 0
        
        Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d{3})-') {
                $num = [int]$matches[1]
                if ($num -gt $highest) {
                    $highest = $num
                    $latestFeature = $_.Name
                }
            }
        }
        
        if ($latestFeature) {
            return $latestFeature
        }
    }
    
    # Final fallback
    return "main"
}

function Test-HasGit {
    try {
        git rev-parse --show-toplevel 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Test-FeatureBranch {
    param(
        [string]$Branch,
        [bool]$HasGit = $true
    )
    
    # For non-git repos, we can't enforce branch naming but still provide output
    if (-not $HasGit) {
        Write-Warning "[specify] Warning: Git repository not detected; skipped branch validation"
        return $true
    }
    
    if ($Branch -notmatch '^[0-9]{3}-') {
        Write-Output "ERROR: Not on a feature branch. Current branch: $Branch"
        Write-Output "Feature branches should be named like: 001-feature-name"
        return $false
    }
    return $true
}

function Get-FeatureDir {
    param([string]$RepoRoot, [string]$Branch)
    Join-Path $RepoRoot "specs/$Branch"
}

function Test-PathWithinRoot {
    param(
        [string]$Path,
        [string]$Root
    )

    $normalizedPath = [System.IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
    $normalizedRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $prefix = $normalizedRoot + [System.IO.Path]::DirectorySeparatorChar

    return $normalizedPath -eq $normalizedRoot -or $normalizedPath.StartsWith($prefix, [System.StringComparison]::Ordinal)
}

function Resolve-RepoRelativePath {
    param(
        [string]$RepoRoot,
        [string]$InputPath
    )

    if (-not $InputPath) {
        throw "Path is required."
    }

    $candidate = if ([System.IO.Path]::IsPathRooted($InputPath)) {
        $InputPath
    } else {
        Join-Path $RepoRoot $InputPath
    }

    $parent = Split-Path -Parent $candidate
    if (-not (Test-Path $parent -PathType Container)) {
        throw "Unable to resolve path: $InputPath"
    }

    Join-Path (Resolve-Path $parent).Path (Split-Path -Leaf $candidate)
}

function Resolve-FeatureFilePath {
    param(
        [string]$RepoRoot,
        [string]$InputPath,
        [string]$ExpectedFileName,
        [string]$Label
    )

    $specsRoot = Join-Path $RepoRoot 'specs'
    if (-not (Test-Path $specsRoot -PathType Container)) {
        throw "specs directory not found: $specsRoot"
    }

    try {
        $resolvedPath = Resolve-RepoRelativePath -RepoRoot $RepoRoot -InputPath $InputPath
    } catch {
        throw "Unable to resolve $Label path: $InputPath"
    }

    $resolvedSpecsRoot = (Resolve-Path $specsRoot).Path
    if (-not (Test-PathWithinRoot -Path $resolvedPath -Root $resolvedSpecsRoot)) {
        throw "$Label must be located under $resolvedSpecsRoot"
    }

    if ((Split-Path -Leaf $resolvedPath) -ne $ExpectedFileName) {
        throw "$Label must point to a file named ${ExpectedFileName}: $resolvedPath"
    }

    if (-not (Test-Path $resolvedPath -PathType Leaf)) {
        throw "$Label not found: $resolvedPath"
    }

    $resolvedPath
}

function New-FeaturePathsObject {
    param(
        [string]$RepoRoot,
        [string]$CurrentBranch,
        [bool]$HasGit,
        [string]$FeatureDir,
        [string]$FeatureSpec,
        [string]$ImplPlan
    )

    [PSCustomObject]@{
        REPO_ROOT             = $RepoRoot
        CURRENT_BRANCH        = $CurrentBranch
        HAS_GIT               = $HasGit
        FEATURE_DIR           = $FeatureDir
        FEATURE_SPEC          = $FeatureSpec
        IMPL_PLAN             = $ImplPlan
        TASKS                 = Join-Path $FeatureDir 'tasks.md'
        RESEARCH              = Join-Path $FeatureDir 'research.md'
        DATA_MODEL            = Join-Path $FeatureDir 'data-model.md'
        TEST_MATRIX           = Join-Path $FeatureDir 'test-matrix.md'
        CONTRACTS_DIR         = Join-Path $FeatureDir 'contracts'
    }
}

function Get-FeaturePathsFromSpecFile {
    param([string]$SpecFile)

    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGit = Test-HasGit
    $resolvedSpec = Resolve-FeatureFilePath -RepoRoot $repoRoot -InputPath $SpecFile -ExpectedFileName 'spec.md' -Label 'spec file'
    $featureDir = Split-Path -Parent $resolvedSpec

    New-FeaturePathsObject -RepoRoot $repoRoot -CurrentBranch $currentBranch -HasGit:$hasGit -FeatureDir $featureDir -FeatureSpec $resolvedSpec -ImplPlan (Join-Path $featureDir 'plan.md')
}

function Get-FeaturePathsFromPlanFile {
    param([string]$PlanFile)

    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGit = Test-HasGit
    $resolvedPlan = Resolve-FeatureFilePath -RepoRoot $repoRoot -InputPath $PlanFile -ExpectedFileName 'plan.md' -Label 'plan file'
    $featureDir = Split-Path -Parent $resolvedPlan

    New-FeaturePathsObject -RepoRoot $repoRoot -CurrentBranch $currentBranch -HasGit:$hasGit -FeatureDir $featureDir -FeatureSpec (Join-Path $featureDir 'spec.md') -ImplPlan $resolvedPlan
}

function Find-FeatureDirByPrefix {
    param(
        [string]$RepoRoot,
        [string]$BranchName
    )

    $specsDir = Join-Path $RepoRoot 'specs'

    if ($BranchName -notmatch '^(\d{3})-') {
        return (Join-Path $specsDir $BranchName)
    }

    $prefix = $matches[1]
    $matchingDirs = @()

    if (Test-Path $specsDir) {
        $matchingDirs = @(
            Get-ChildItem -Path $specsDir -Directory -Filter "$prefix-*" |
                ForEach-Object { $_.Name }
        )
    }

    if ($matchingDirs.Count -eq 0) {
        return (Join-Path $specsDir $BranchName)
    }

    if ($matchingDirs.Count -eq 1) {
        return (Join-Path $specsDir $matchingDirs[0])
    }

    [Console]::Error.WriteLine("ERROR: Multiple spec directories found with prefix '$prefix': $($matchingDirs -join ' ')")
    [Console]::Error.WriteLine('Please ensure only one spec directory exists per numeric prefix.')
    return (Join-Path $specsDir $BranchName)
}

function Get-FeaturePathsEnv {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGit = Test-HasGit
    $featureDir = Find-FeatureDirByPrefix -RepoRoot $repoRoot -BranchName $currentBranch

    New-FeaturePathsObject -RepoRoot $repoRoot -CurrentBranch $currentBranch -HasGit:$hasGit -FeatureDir $featureDir -FeatureSpec (Join-Path $featureDir 'spec.md') -ImplPlan (Join-Path $featureDir 'plan.md')
}

function Test-FileExists {
    param([string]$Path, [string]$Description)
    if (Test-Path -Path $Path -PathType Leaf) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}

function Test-DirHasFiles {
    param([string]$Path, [string]$Description)
    if ((Test-Path -Path $Path -PathType Container) -and (Get-ChildItem -Path $Path -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer } | Select-Object -First 1)) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}

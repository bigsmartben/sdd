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
    
    # For non-git repos, try to find the latest feature directory.
    # Prefer date-based naming (YYYYMMDD-slug), then fallback to legacy NNN-slug.
    $repoRoot = Get-RepoRoot
    $specsDir = Join-Path $repoRoot "specs"
    
    if (Test-Path $specsDir) {
        $latestFeature = ""
        $highestDate = 0
        $highestLegacy = 0
        
        Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d{8})-') {
                $dateKey = [int64]$matches[1]
                if ($dateKey -gt $highestDate) {
                    $highestDate = $dateKey
                    $latestFeature = $_.Name
                }
            } elseif ($_.Name -match '^(\d{3})-') {
                $num = [int]$matches[1]
                if ($highestDate -eq 0 -and $num -gt $highestLegacy) {
                    $highestLegacy = $num
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
    
    $branchLeaf = Split-Path -Leaf $Branch

    if ($branchLeaf -match '^feature-[0-9]{8}-[a-z0-9][a-z0-9-]*$') {
        return $true
    }

    # Backward-compatible acceptance for existing projects.
    if ($branchLeaf -match '^[0-9]{3}-[a-z0-9][a-z0-9-]*$') {
        Write-Warning "[specify] Legacy branch naming detected: $branchLeaf. Prefer feature-YYYYMMDD-short-name."
        return $true
    }

    if ($branchLeaf -notmatch '^[0-9]{8}-[a-z0-9][a-z0-9-]*$') {
        [Console]::Error.WriteLine("ERROR: Not on a feature branch. Current branch: $Branch")
        [Console]::Error.WriteLine("Feature branches should be named like: feature-20250708-parent-hanxue-channel")
        return $false
    }
    return $true
}

function Get-FeatureDir {
    param([string]$RepoRoot, [string]$Branch)
    Join-Path $RepoRoot "specs/$Branch"
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

function Find-FeatureDirByPrefix {
    param(
        [string]$RepoRoot,
        [string]$BranchName
    )

    $specsDir = Join-Path $RepoRoot 'specs'
    $branchLeaf = Split-Path -Leaf $BranchName

    # Preferred naming: feature-YYYYMMDD-slug -> specs/YYYYMMDD-slug
    if ($branchLeaf -match '^feature-([0-9]{8}-[a-z0-9][a-z0-9-]*)$') {
        return (Join-Path $specsDir $matches[1])
    }

    # Accept already normalized feature key as branch leaf.
    if ($branchLeaf -match '^([0-9]{8}-[a-z0-9][a-z0-9-]*)$') {
        return (Join-Path $specsDir $matches[1])
    }

    if ($branchLeaf -notmatch '^(\d{3})-') {
        return (Join-Path $specsDir $branchLeaf)
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
        return (Join-Path $specsDir $branchLeaf)
    }

    if ($matchingDirs.Count -eq 1) {
        return (Join-Path $specsDir $matchingDirs[0])
    }

    [Console]::Error.WriteLine("ERROR: Multiple spec directories found with prefix '$prefix': $($matchingDirs -join ' ')")
    [Console]::Error.WriteLine('Please ensure only one spec directory exists per numeric prefix.')
    return (Join-Path $specsDir $branchLeaf)
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

#!/usr/bin/env pwsh
# Create a new feature
[CmdletBinding(PositionalBinding = $false)]
param(
    [switch]$Json,
    [string]$ShortName,
    [int]$Number = 0,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$FeatureDescription
)
$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Host "Usage: ./create-new-feature.ps1 [-Json] [-ShortName <name>] [-Number N] <feature description>"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json               Output in JSON format"
    Write-Host "  -ShortName <name>   Provide a custom short name (2-4 words) for fallback naming"
    Write-Host "  -Number N           Specify feature number manually for fallback naming"
    Write-Host "  -Help               Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  ./create-new-feature.ps1 'Add user authentication system' -ShortName 'user-auth'"
    Write-Host "  ./create-new-feature.ps1 'Implement OAuth2 integration for API'"
    exit 0
}

# Check if feature description provided
if (-not $FeatureDescription -or $FeatureDescription.Count -eq 0) {
    Write-Error "Usage: ./create-new-feature.ps1 [-Json] [-ShortName <name>] <feature description>"
    exit 1
}

$featureDesc = ($FeatureDescription -join ' ').Trim()

# Validate description is not empty after trimming (e.g., user passed only whitespace)
if ([string]::IsNullOrWhiteSpace($featureDesc)) {
    Write-Error "Error: Feature description cannot be empty or contain only whitespace"
    exit 1
}

# Resolve repository root. Prefer git information when available, but fall back
# to searching for repository markers so the workflow still functions in repositories that
# were initialized with --no-git.
function Find-RepositoryRoot {
    param(
        [string]$StartDir,
        [string[]]$Markers = @('.git', '.specify')
    )
    $current = Resolve-Path $StartDir
    while ($true) {
        foreach ($marker in $Markers) {
            if (Test-Path (Join-Path $current $marker)) {
                return $current
            }
        }
        $parent = Split-Path $current -Parent
        if ($parent -eq $current) {
            # Reached filesystem root without finding markers
            return $null
        }
        $current = $parent
    }
}

function Get-HighestNumberFromSpecs {
    param([string]$SpecsDir)
    
    $highest = 0
    if (Test-Path $SpecsDir) {
        Get-ChildItem -Path $SpecsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d+)') {
                $num = [int]$matches[1]
                if ($num -gt $highest) { $highest = $num }
            }
        }
    }
    return $highest
}

function Get-HighestNumberFromBranches {
    param()
    
    $highest = 0
    try {
        $branches = git branch -a 2>$null
        if ($LASTEXITCODE -eq 0) {
            foreach ($branch in $branches) {
                # Clean branch name: remove leading markers and remote prefixes
                $cleanBranch = $branch.Trim() -replace '^\*?\s+', '' -replace '^remotes/[^/]+/', ''
                
                # Extract feature number if branch matches pattern ###-*
                if ($cleanBranch -match '^(\d+)-') {
                    $num = [int]$matches[1]
                    if ($num -gt $highest) { $highest = $num }
                }
            }
        }
    } catch {
        # If git command fails, return 0
        Write-Verbose "Could not check Git branches: $_"
    }
    return $highest
}

function Get-NextBranchNumber {
    param(
        [string]$SpecsDir
    )

    # Best-effort remote sync that avoids interactive/network hangs.
    # Behavior controls:
    # - SPECIFY_SKIP_FETCH=1        -> skip remote fetch entirely
    # - SPECIFY_FETCH_TIMEOUT=<s>   -> timeout seconds (default: 8)
    # - SPECIFY_FETCH_MODE=<mode>   -> preferred (default), all, none
    $skipFetch = $env:SPECIFY_SKIP_FETCH
    $fetchMode = if ([string]::IsNullOrWhiteSpace($env:SPECIFY_FETCH_MODE)) { 'preferred' } else { $env:SPECIFY_FETCH_MODE }
    if ($skipFetch -eq '1' -or $fetchMode -eq 'none') {
        Write-Warning "[specify] Skipping remote fetch (SPECIFY_SKIP_FETCH=1 or SPECIFY_FETCH_MODE=none)"
    } else {
        $fetchTimeout = 8
        if ($env:SPECIFY_FETCH_TIMEOUT -and ($env:SPECIFY_FETCH_TIMEOUT -as [int])) {
            $fetchTimeout = [int]$env:SPECIFY_FETCH_TIMEOUT
        }

        # Prefer a non-interactive SSH command unless user already set one.
        if (-not $env:GIT_SSH_COMMAND) {
            $env:GIT_SSH_COMMAND = 'ssh -o BatchMode=yes -o ConnectTimeout=5'
        }

        try {
            # Make fetch non-interactive and bounded by timeout.
            $fetchTarget = '--all'
            if ($fetchMode -ne 'all') {
                $remotes = @(git remote 2>$null)
                if ($remotes.Count -gt 0) {
                    if ($remotes -contains 'origin') {
                        $fetchTarget = 'origin'
                    } else {
                        $fetchTarget = $remotes[0]
                    }
                }
            }

            $fetchArgs = @('-c', 'credential.interactive=never', 'fetch', $fetchTarget, '--prune', '--no-tags', '--quiet')
            $proc = Start-Process -FilePath 'git' -ArgumentList $fetchArgs -NoNewWindow -PassThru
            if (-not $proc.WaitForExit($fetchTimeout * 1000)) {
                try { $proc.Kill() } catch {}
                Write-Warning "[specify] git fetch timed out; using local branch/spec data"
            } elseif ($proc.ExitCode -ne 0) {
                Write-Warning "[specify] git fetch failed; using local branch/spec data"
            }
        } catch {
            Write-Warning "[specify] git fetch skipped/failed; using local branch/spec data"
        }
    }

    # Get highest number from ALL branches (not just matching short name)
    $highestBranch = Get-HighestNumberFromBranches

    # Get highest number from ALL specs (not just matching short name)
    $highestSpec = Get-HighestNumberFromSpecs -SpecsDir $SpecsDir

    # Take the maximum of both
    $maxNum = [Math]::Max($highestBranch, $highestSpec)

    # Return next number
    return $maxNum + 1
}

function ConvertTo-CleanBranchName {
    param([string]$Name)
    
    return $Name.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', ''
}
$fallbackRoot = (Find-RepositoryRoot -StartDir $PSScriptRoot)
if (-not $fallbackRoot) {
    Write-Error "Error: Could not determine repository root. Please run this script from within the repository."
    exit 1
}

try {
    $repoRoot = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0) {
        $hasGit = $true
    } else {
        throw "Git not available"
    }
} catch {
    $repoRoot = $fallbackRoot
    $hasGit = $false
}

Set-Location $repoRoot

$template = Join-Path $repoRoot '.specify/templates/spec-template.md'
if (-not (Test-Path $template -PathType Leaf)) {
    Write-Error "Required runtime template not found or not readable at $template"
    exit 1
}

$specsDir = Join-Path $repoRoot 'specs'
New-Item -ItemType Directory -Path $specsDir -Force | Out-Null

# Function to generate branch name with stop word filtering and length filtering
function Get-BranchName {
    param([string]$Description)
    
    # Common stop words to filter out
    $stopWords = @(
        'i', 'a', 'an', 'the', 'to', 'for', 'of', 'in', 'on', 'at', 'by', 'with', 'from',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall',
        'this', 'that', 'these', 'those', 'my', 'your', 'our', 'their',
        'want', 'need', 'add', 'get', 'set'
    )
    
    # Convert to lowercase and extract words (alphanumeric only)
    $cleanName = $Description.ToLower() -replace '[^a-z0-9\s]', ' '
    $words = $cleanName -split '\s+' | Where-Object { $_ }
    
    # Filter words: remove stop words and words shorter than 3 chars (unless they're uppercase acronyms in original)
    $meaningfulWords = @()
    foreach ($word in $words) {
        # Skip stop words
        if ($stopWords -contains $word) { continue }
        
        # Keep words that are length >= 3 OR appear as uppercase in original (likely acronyms)
        if ($word.Length -ge 3) {
            $meaningfulWords += $word
        } elseif ($Description -match "\b$($word.ToUpper())\b") {
            # Keep short words if they appear as uppercase in original (likely acronyms)
            $meaningfulWords += $word
        }
    }
    
    # If we have meaningful words, use first 3-4 of them
    if ($meaningfulWords.Count -gt 0) {
        $maxWords = if ($meaningfulWords.Count -eq 4) { 4 } else { 3 }
        $result = ($meaningfulWords | Select-Object -First $maxWords) -join '-'
        return $result
    } else {
        # Fallback to original logic if no meaningful words found
        $result = ConvertTo-CleanBranchName -Name $Description
        $fallbackWords = ($result -split '-') | Where-Object { $_ } | Select-Object -First 3
        return [string]::Join('-', $fallbackWords)
    }
}

# Generate fallback branch suffix
if ($ShortName) {
    $branchSuffix = ConvertTo-CleanBranchName -Name $ShortName
} else {
    $branchSuffix = Get-BranchName -Description $featureDesc
}

$branchName = $null
$currentBranchLeaf = $null

if ($hasGit) {
    try {
        $currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($currentBranch) -and $currentBranch -ne 'HEAD') {
            $currentBranchLeaf = ($currentBranch -replace '^.*/', '')
            if ($currentBranchLeaf -match '^feature-[0-9]{8}-[a-z0-9][a-z0-9-]*$|^\d+-[a-z0-9][a-z0-9-]*$') {
                $branchName = $currentBranchLeaf
            } else {
                Write-Warning "[specify] Current branch '$currentBranch' does not match 'feature-YYYYMMDD-short-name'; using fallback generated feature key"
            }
        }
    } catch {
        Write-Verbose "Could not read current git branch: $_"
    }
}

if (-not $branchName) {
    if ($Number -eq 0) {
        if ($hasGit) {
            $Number = Get-NextBranchNumber -SpecsDir $specsDir
        } else {
            $Number = (Get-HighestNumberFromSpecs -SpecsDir $specsDir) + 1
        }
    }

    $featureNum = ('{0:000}' -f $Number)
    $branchName = "$featureNum-$branchSuffix"

    # GitHub enforces a 244-byte limit on branch names
    $maxBranchLength = 244
    if ($branchName.Length -gt $maxBranchLength) {
        $maxSuffixLength = $maxBranchLength - 4
        $truncatedSuffix = $branchSuffix.Substring(0, [Math]::Min($branchSuffix.Length, $maxSuffixLength))
        $truncatedSuffix = $truncatedSuffix -replace '-$', ''

        $originalBranchName = $branchName
        $branchName = "$featureNum-$truncatedSuffix"

        Write-Warning "[specify] Branch name exceeded GitHub's 244-byte limit"
        Write-Warning "[specify] Original: $originalBranchName ($($originalBranchName.Length) bytes)"
        Write-Warning "[specify] Truncated to: $branchName ($($branchName.Length) bytes)"
    }

}

$featurePrefix = ($branchName -split '-', 2)[0]
if ($branchName -match '^feature-([0-9]{8})-') {
    $featureNum = $matches[1]
} elseif ($featurePrefix -match '^\d+$') {
    if ($featurePrefix.Length -lt 3) {
        $featureNum = ('{0:000}' -f [int]$featurePrefix)
    } else {
        $featureNum = $featurePrefix
    }
} else {
    $featureNum = '000'
}

$featureKey = $branchName
if ($branchName -match '^feature-([0-9]{8}-[a-z0-9][a-z0-9-]*)$') {
    $featureKey = $matches[1]
}

$featureDir = Join-Path $specsDir $featureKey
New-Item -ItemType Directory -Path $featureDir -Force | Out-Null

$specFile = Join-Path $featureDir 'spec.md'
Copy-Item $template $specFile -Force

if ($hasGit) {
    try {
        $currentHead = git rev-parse --abbrev-ref HEAD 2>$null
    } catch {
        $currentHead = ''
    }

    if ($currentHead -ne $branchName) {
        try {
            git show-ref --verify --quiet "refs/heads/$branchName" 2>$null | Out-Null
            $branchExists = ($LASTEXITCODE -eq 0)
        } catch {
            $branchExists = $false
        }

        if ($branchExists) {
            try {
                git checkout $branchName 2>$null | Out-Null
                if ($LASTEXITCODE -ne 0) {
                    Write-Error "Error: Failed to switch to git branch '$branchName'. Please check your git configuration and try again."
                    exit 1
                }
            } catch {
                Write-Error "Error: Failed to switch to git branch '$branchName'. Please check your git configuration and try again."
                exit 1
            }
        } else {
            try {
                git checkout -b $branchName 2>$null | Out-Null
                if ($LASTEXITCODE -ne 0) {
                    Write-Error "Error: Failed to create and switch to git branch '$branchName'. Please check your git configuration and try again."
                    exit 1
                }
            } catch {
                Write-Error "Error: Failed to create and switch to git branch '$branchName'. Please check your git configuration and try again."
                exit 1
            }
        }
    }
}

# Set the SPECIFY_FEATURE environment variable for the current session
$env:SPECIFY_FEATURE = $branchName

if ($Json) {
    $obj = [PSCustomObject]@{ 
        BRANCH_NAME = $branchName
        SPEC_FILE = $specFile
        FEATURE_NUM = $featureNum
        HAS_GIT = $hasGit
    }
    $obj | ConvertTo-Json -Compress
} else {
    Write-Output "BRANCH_NAME: $branchName"
    Write-Output "SPEC_FILE: $specFile"
    Write-Output "FEATURE_NUM: $featureNum"
    Write-Output "HAS_GIT: $hasGit"
    Write-Output "SPECIFY_FEATURE environment variable set to: $branchName"
}

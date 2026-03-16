#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [string]$FeatureDir,
    [string]$Rules,
    [switch]$Json,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Show-Help {
    Write-Output @"
Usage: run-planning-lint.ps1 -FeatureDir <abs-path> -Rules <abs-path> [-Json] [-Help]

Run planning mechanical lint checks from a TSV rules catalog.

Options:
  -FeatureDir <abs-path>    Absolute path to feature directory (e.g. /repo/specs/001-feature)
  -Rules <abs-path>         Absolute path to rules TSV catalog
  -Json                     Output machine-readable JSON
  -Help                     Show this help message

Supported rule kinds:
  - file_regex_forbidden
  - file_regex_required_any
  - component_symbols_exist
  - anchor_status_allowed_values
"@
}

function Write-ErrorAndExit {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [int]$Code = 1
    )

    Write-Output "ERROR: $Message"
    exit $Code
}

function Test-AbsolutePath {
    param([string]$PathValue)

    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return $false
    }

    if (-not [System.IO.Path]::IsPathRooted($PathValue)) {
        return $false
    }

    return ($PathValue.StartsWith('/') -or $PathValue -match '^[A-Za-z]:[\\/]')
}

function Parse-Params {
    param([string]$ParamsText)

    $result = @{}
    if ([string]::IsNullOrWhiteSpace($ParamsText)) {
        return $result
    }

    foreach ($pair in $ParamsText -split ';') {
        if ([string]::IsNullOrWhiteSpace($pair)) {
            continue
        }

        $eq = $pair.IndexOf('=')
        if ($eq -lt 1) {
            continue
        }

        $key = $pair.Substring(0, $eq).Trim()
        $value = $pair.Substring($eq + 1).Trim()
        if (-not [string]::IsNullOrWhiteSpace($key)) {
            $result[$key] = $value
        }
    }

    return $result
}

function Get-RelPath {
    param(
        [string]$FullPath,
        [string]$BasePath
    )

    $baseNorm = $BasePath.TrimEnd('/', '\')
    $fullNorm = $FullPath

    if ($fullNorm.StartsWith("$baseNorm/")) {
        return $fullNorm.Substring($baseNorm.Length + 1)
    }

    if ($fullNorm.StartsWith("$baseNorm\")) {
        return $fullNorm.Substring($baseNorm.Length + 1) -replace '\\', '/'
    }

    return (Split-Path -Path $fullNorm -Leaf)
}

function Get-AllowedStatusSet {
    param([string]$AllowedCsv)

    $set = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($raw in ($AllowedCsv -split ',')) {
        $token = $raw.Trim().ToLowerInvariant()
        if (-not [string]::IsNullOrWhiteSpace($token)) {
            [void]$set.Add($token)
        }
    }
    return $set
}

function Get-StatusTokens {
    param([string]$Text)

    $tokens = @()
    $backticks = [regex]::Matches($Text, '`([^`]+)`')
    if ($backticks.Count -gt 0) {
        foreach ($m in $backticks) {
            $value = $m.Groups[1].Value.Trim().ToLowerInvariant()
            if (-not [string]::IsNullOrWhiteSpace($value)) {
                $tokens += $value
            }
        }
        return $tokens
    }

    $wordMatches = [regex]::Matches($Text, '[A-Za-z][A-Za-z_-]*')
    foreach ($m in $wordMatches) {
        $value = $m.Value.Trim().ToLowerInvariant()
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            $tokens += $value
        }
    }

    return $tokens
}

function Test-AnchorStatusFragment {
    param(
        [Parameter(Mandatory = $true)][string]$Fragment,
        [Parameter(Mandatory = $true)][System.Collections.Generic.HashSet[string]]$AllowedSet
    )

    $ignored = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($token in @('anchor', 'status', 'repo', 'boundary', 'implementation', 'entry', 'required', 'legacy', 'or', 'and')) {
        [void]$ignored.Add($token)
    }

    $tokens = Get-StatusTokens -Text $Fragment
    $candidates = @()
    foreach ($token in $tokens) {
        if (-not $ignored.Contains($token)) {
            $candidates += $token
        }
    }

    if ($candidates.Count -eq 0) {
        return [PSCustomObject]@{
            Ok      = $false
            Details = 'Anchor Status field is present but no status token was detected.'
        }
    }

    $invalid = @()
    $hasAllowed = $false
    $allowedText = (($AllowedSet | ForEach-Object { $_ }) -join ',')
    foreach ($token in $candidates) {
        if ($AllowedSet.Contains($token)) {
            $hasAllowed = $true
        } else {
            $invalid += $token
        }
    }

    if ($invalid.Count -gt 0) {
        return [PSCustomObject]@{
            Ok      = $false
            Details = "Invalid status token(s): $($invalid -join ','). Allowed: $allowedText"
        }
    }

    if ($candidates.Count -ne 1) {
        return [PSCustomObject]@{
            Ok      = $false
            Details = "Anchor Status must contain exactly one status token. Found: $($candidates -join ',')."
        }
    }

    if (-not $hasAllowed) {
        return [PSCustomObject]@{
            Ok      = $false
            Details = "No allowed status token found. Allowed: $allowedText"
        }
    }

    return [PSCustomObject]@{
        Ok      = $true
        Details = ''
    }
}

function Get-MarkdownCells {
    param([string]$Line)

    if ($Line -notmatch '^\s*\|.*\|\s*$') {
        return @()
    }

    $trimmed = $Line.Trim()
    $content = $trimmed.Trim('|')
    $cells = @()
    foreach ($raw in ($content -split '\|')) {
        $cells += $raw.Trim()
    }
    return $cells
}

function Test-MarkdownSeparatorRow {
    param([string[]]$Cells)

    if ($Cells.Count -eq 0) {
        return $false
    }

    foreach ($cell in $Cells) {
        if ($cell -notmatch '^:?-{3,}:?$') {
            return $false
        }
    }
    return $true
}

if ($Help) {
    Show-Help
    exit 0
}

if ([string]::IsNullOrWhiteSpace($FeatureDir) -or [string]::IsNullOrWhiteSpace($Rules)) {
    Show-Help
    Write-ErrorAndExit -Message 'Both -FeatureDir and -Rules are required.'
}

if (-not (Test-AbsolutePath -PathValue $FeatureDir)) {
    Write-ErrorAndExit -Message '-FeatureDir must be an absolute path.'
}

if (-not (Test-AbsolutePath -PathValue $Rules)) {
    Write-ErrorAndExit -Message '-Rules must be an absolute path.'
}

if (-not (Test-Path -Path $FeatureDir -PathType Container)) {
    Write-ErrorAndExit -Message "Feature directory not found: $FeatureDir"
}

if (-not (Test-Path -Path $Rules -PathType Leaf)) {
    Write-ErrorAndExit -Message "Rules catalog not found: $Rules"
}

$featureRoot = (Resolve-Path -Path $FeatureDir).Path.TrimEnd('/', '\')
$rulesPath = (Resolve-Path -Path $Rules).Path

$allFiles = @(
    Get-ChildItem -Path $featureRoot -Recurse -File -ErrorAction SilentlyContinue |
        ForEach-Object {
            [PSCustomObject]@{
                FullPath = $_.FullName
                RelPath  = (Get-RelPath -FullPath $_.FullName -BasePath $featureRoot)
            }
        }
)

$findings = New-Object System.Collections.Generic.List[object]
$rulesTotal = 0
$rulesEvaluated = 0
$severityCounts = [ordered]@{
    CRITICAL = 0
    HIGH     = 0
    MEDIUM   = 0
    LOW      = 0
    INFO     = 0
}

function Add-Finding {
    param(
        [string]$RuleId,
        [string]$Severity,
        [string]$File,
        [int]$Line,
        [string]$Message,
        [string]$Remediation
    )

    $findings.Add([PSCustomObject]@{
        rule_id     = $RuleId
        severity    = $Severity
        source      = 'lint'
        file        = $File
        line        = $Line
        message     = $Message
        remediation = $Remediation
    }) | Out-Null

    $sev = ($Severity ?? '').ToString().ToUpperInvariant()
    if ([string]::IsNullOrWhiteSpace($sev)) {
        $sev = 'INFO'
    }
    if ($severityCounts.Contains($sev)) {
        $severityCounts[$sev] = [int]$severityCounts[$sev] + 1
    }
}

$rows = Import-Csv -Path $rulesPath -Delimiter "`t"

foreach ($row in $rows) {
    if ([string]::IsNullOrWhiteSpace($row.id)) {
        continue
    }

    $rulesTotal++

    $enabled = ($row.enabled ?? '').ToString().ToLowerInvariant()
    if ($enabled -ne 'true') {
        continue
    }

    $rulesEvaluated++
    $matched = @($allFiles | Where-Object { $_.RelPath -like $row.glob })
    $params = Parse-Params -ParamsText $row.params

    switch ($row.kind) {
        'file_regex_forbidden' {
            $regex = $params['regex']
            if ([string]::IsNullOrWhiteSpace($regex)) {
                Add-Finding -RuleId $row.id -Severity $row.severity -File $row.glob -Line 0 -Message 'Rule params missing required key: regex' -Remediation 'Fix rules TSV params for this rule.'
                continue
            }

            foreach ($file in $matched) {
                try {
                    $hits = Select-String -Path $file.FullPath -Pattern $regex -AllMatches -ErrorAction Stop
                    foreach ($hit in $hits) {
                        Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $hit.LineNumber -Message $row.message -Remediation $row.remediation
                    }
                } catch {
                    # If regex is invalid for a file, emit one finding for visibility.
                    Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line 0 -Message "Regex evaluation failed: $($_.Exception.Message)" -Remediation 'Adjust regex in rules TSV to a valid .NET-compatible pattern.'
                }
            }
        }

        'file_regex_required_any' {
            $regex = $params['regex']
            if ([string]::IsNullOrWhiteSpace($regex)) {
                Add-Finding -RuleId $row.id -Severity $row.severity -File $row.glob -Line 0 -Message 'Rule params missing required key: regex' -Remediation 'Fix rules TSV params for this rule.'
                continue
            }

            $foundAny = $false
            foreach ($file in $matched) {
                try {
                    if (Select-String -Path $file.FullPath -Pattern $regex -Quiet -ErrorAction Stop) {
                        $foundAny = $true
                        break
                    }
                } catch {
                    Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line 0 -Message "Regex evaluation failed: $($_.Exception.Message)" -Remediation 'Adjust regex in rules TSV to a valid .NET-compatible pattern.'
                }
            }

            if (-not $foundAny) {
                $target = if ($matched.Count -gt 0) { $matched[0].RelPath } else { $row.glob }
                Add-Finding -RuleId $row.id -Severity $row.severity -File $target -Line 0 -Message $row.message -Remediation $row.remediation
            }
        }

        'component_symbols_exist' {
            $targetRel = $params['file']
            $symbolsCsv = $params['symbols']

            if ([string]::IsNullOrWhiteSpace($targetRel) -or [string]::IsNullOrWhiteSpace($symbolsCsv)) {
                Add-Finding -RuleId $row.id -Severity $row.severity -File $row.glob -Line 0 -Message 'Rule params missing required key: file and/or symbols' -Remediation 'Fix rules TSV params for this rule.'
                continue
            }

            $targetPath = Join-Path $featureRoot ($targetRel -replace '/', [System.IO.Path]::DirectorySeparatorChar)
            if (-not (Test-Path -Path $targetPath -PathType Leaf)) {
                Add-Finding -RuleId $row.id -Severity $row.severity -File $targetRel -Line 0 -Message $row.message -Remediation $row.remediation
                continue
            }

            $missing = @()
            foreach ($symbol in ($symbolsCsv -split ',')) {
                $token = $symbol.Trim()
                if ([string]::IsNullOrWhiteSpace($token)) {
                    continue
                }

                if (-not (Select-String -Path $targetPath -Pattern ([regex]::Escape($token)) -Quiet)) {
                    $missing += $token
                }
            }

            if ($missing.Count -gt 0) {
                $missingText = ($missing -join ',')
                Add-Finding -RuleId $row.id -Severity $row.severity -File $targetRel -Line 0 -Message "$($row.message) Missing symbols: $missingText" -Remediation $row.remediation
            }
        }

        'anchor_status_allowed_values' {
            $allowedCsv = $params['allowed']
            if ([string]::IsNullOrWhiteSpace($allowedCsv)) {
                Add-Finding -RuleId $row.id -Severity $row.severity -File $row.glob -Line 0 -Message 'Rule params missing required key: allowed' -Remediation 'Fix rules TSV params for this rule.'
                continue
            }

            $allowedSet = Get-AllowedStatusSet -AllowedCsv $allowedCsv
            $labelPattern = '(?i)^\s*(?:[-*]\s*)?(?:\*\*)?(?:Repo[ _-]*Anchor[ _-]*Status|Boundary[ _-]*Anchor[ _-]*Status|Implementation[ _-]*Entry[ _-]*Anchor[ _-]*Status|Anchor[ _-]*Status)(?:\s*\([^)]*\))?(?:\*\*)?\s*:\s*(.+)$'
            $headerPattern = '(?i)(Repo[ _-]*Anchor[ _-]*Status|Boundary[ _-]*Anchor[ _-]*Status|Implementation[ _-]*Entry[ _-]*Anchor[ _-]*Status|Anchor[ _-]*Status)'

            foreach ($file in $matched) {
                $lines = Get-Content -Path $file.FullPath -ErrorAction Stop
                $statusColumnIndex = -1
                $inTable = $false

                for ($i = 0; $i -lt $lines.Count; $i++) {
                    $lineNumber = $i + 1
                    $line = $lines[$i]

                    $labelMatch = [regex]::Match($line, $labelPattern)
                    if ($labelMatch.Success) {
                        $result = Test-AnchorStatusFragment -Fragment $labelMatch.Groups[1].Value -AllowedSet $allowedSet
                        if (-not $result.Ok) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lineNumber -Message "$($row.message) $($result.Details)" -Remediation $row.remediation
                        }
                    }

                    $cells = Get-MarkdownCells -Line $line
                    if ($cells.Count -eq 0) {
                        $statusColumnIndex = -1
                        $inTable = $false
                        continue
                    }

                    if (-not $inTable) {
                        $statusColumnIndex = -1
                        for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                            if ([regex]::IsMatch($cells[$idx], $headerPattern)) {
                                $statusColumnIndex = $idx
                                break
                            }
                        }
                        if ($statusColumnIndex -ge 0) {
                            $inTable = $true
                        }
                        continue
                    }

                    if ($statusColumnIndex -lt 0) {
                        continue
                    }

                    if (Test-MarkdownSeparatorRow -Cells $cells) {
                        continue
                    }

                    if ($statusColumnIndex -ge $cells.Count) {
                        Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lineNumber -Message "$($row.message) Anchor Status column is missing in this table row." -Remediation $row.remediation
                        continue
                    }

                    $result = Test-AnchorStatusFragment -Fragment $cells[$statusColumnIndex] -AllowedSet $allowedSet
                    if (-not $result.Ok) {
                        Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lineNumber -Message "$($row.message) $($result.Details)" -Remediation $row.remediation
                    }
                }
            }
        }

        default {
            Add-Finding -RuleId $row.id -Severity $row.severity -File $row.glob -Line 0 -Message "Unsupported rule kind: $($row.kind)" -Remediation 'Use one of: file_regex_forbidden, file_regex_required_any, component_symbols_exist, anchor_status_allowed_values.'
        }
    }
}

$payload = [ordered]@{
    feature_dir     = $featureRoot
    rules_total     = $rulesTotal
    rules_evaluated = $rulesEvaluated
    findings_total  = $findings.Count
    findings_by_severity = $severityCounts
    findings        = @($findings)
}

if ($Json) {
    $payload | ConvertTo-Json -Depth 8 -Compress
} else {
    Write-Output "feature_dir: $($payload.feature_dir)"
    Write-Output "rules_total: $($payload.rules_total)"
    Write-Output "rules_evaluated: $($payload.rules_evaluated)"
    Write-Output "findings_total: $($payload.findings_total)"
    Write-Output ("findings_by_severity: {0}" -f (($payload.findings_by_severity | ConvertTo-Json -Compress)))
    if ($payload.findings_total -eq 0) {
        Write-Output 'findings: []'
    } else {
        Write-Output 'findings:'
        foreach ($f in $findings) {
            Write-Output ("  {0}" -f (($f | ConvertTo-Json -Compress)))
        }
    }
}

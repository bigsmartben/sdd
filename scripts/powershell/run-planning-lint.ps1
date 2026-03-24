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
  -FeatureDir <abs-path>    Absolute path to feature directory (e.g. /repo/specs/20250708-feature)
  -Rules <abs-path>         Absolute path to rules TSV catalog
  -Json                     Output machine-readable JSON
  -Help                     Show this help message

Supported rule kinds:
  - file_regex_forbidden
  - file_regex_required_any
  - component_symbols_exist
  - anchor_status_allowed_values
  - northbound_controller_required
  - repo_anchor_paths_exist
    - plan_status_consistency
    - binding_projection_stable_only
  - binding_tuple_projection_sync
  - shared_semantic_reuse_enum
  - anchor_strategy_evidence_required
  - data_model_semantic_closure
  - data_model_single_binding_shared_warning
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

function Get-FeatureRepoRoot {
    param([string]$FeaturePath)

    $featureItem = Get-Item -LiteralPath $FeaturePath
    $parent = $featureItem.Parent
    if ($null -ne $parent -and $parent.Name -eq 'specs' -and $null -ne $parent.Parent) {
        return $parent.Parent.FullName
    }

    if ($null -ne $parent) {
        return $parent.FullName
    }

    return $FeaturePath
}

function Resolve-RepoAnchorPath {
    param(
        [string]$RepoRoot,
        [string]$AnchorPath
    )

    $normalized = ($AnchorPath ?? '') -replace '\\', '/'
    if ([System.IO.Path]::IsPathRooted($normalized)) {
        return $normalized
    }

    return Join-Path $RepoRoot ($normalized -replace '/', [System.IO.Path]::DirectorySeparatorChar)
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
    $cells = New-Object System.Collections.Generic.List[string]
    $cellBuilder = New-Object System.Text.StringBuilder
    $escaping = $false

    for ($idx = 0; $idx -lt $content.Length; $idx++) {
        $ch = $content[$idx]

        if ($escaping) {
            if ($ch -eq '|' -or $ch -eq '\') {
                [void]$cellBuilder.Append($ch)
            } else {
                [void]$cellBuilder.Append('\')
                [void]$cellBuilder.Append($ch)
            }
            $escaping = $false
            continue
        }

        if ($ch -eq '\') {
            $escaping = $true
            continue
        }

        if ($ch -eq '|') {
            $cells.Add($cellBuilder.ToString().Trim()) | Out-Null
            [void]$cellBuilder.Clear()
            continue
        }

        [void]$cellBuilder.Append($ch)
    }

    if ($escaping) {
        [void]$cellBuilder.Append('\')
    }
    $cells.Add($cellBuilder.ToString().Trim()) | Out-Null

    return @($cells)
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

function Normalize-MarkdownScalar {
    param([string]$Value)

    if ($null -eq $Value) {
        return ''
    }

    return (($Value.Trim()) -replace '`', '').Trim()
}

function Normalize-MarkdownListCell {
    param([string]$Value)

    $normalized = Normalize-MarkdownScalar -Value $Value
    if ($normalized.StartsWith('[') -and $normalized.EndsWith(']')) {
        $normalized = $normalized.Substring(1, $normalized.Length - 2)
    }

    if ([string]::IsNullOrWhiteSpace($normalized)) {
        return ''
    }

    $parts = @()
    foreach ($item in ($normalized -split ',')) {
        $trimmed = $item.Trim()
        if (-not [string]::IsNullOrWhiteSpace($trimmed)) {
            $parts += $trimmed
        }
    }
    return ($parts -join ',')
}

function Get-CanonicalPacketSource {
    param([string]$BindingRowId)

    $normalized = Normalize-MarkdownScalar -Value $BindingRowId
    if ([string]::IsNullOrWhiteSpace($normalized)) {
        return ''
    }

    return "test-matrix.md#Binding Packets:$normalized"
}

function Normalize-PacketSourceRef {
    param([string]$Value)

    $normalized = Normalize-MarkdownScalar -Value $Value
    if ([string]::IsNullOrWhiteSpace($normalized)) {
        return ''
    }

    $match = [regex]::Match($normalized, '(?i)^test-matrix\.md\s*#\s*binding(?:\s|-)?packets\s*:\s*([A-Za-z0-9_.-]+)\s*$')
    if ($match.Success) {
        return Get-CanonicalPacketSource -BindingRowId $match.Groups[1].Value
    }

    return $normalized
}

function Get-PacketSourceBindingRowId {
    param([string]$Value)

    $normalized = Normalize-PacketSourceRef -Value $Value
    $match = [regex]::Match($normalized, '^test-matrix\.md#Binding Packets:([A-Za-z0-9_.-]+)$')
    if ($match.Success) {
        return $match.Groups[1].Value
    }

    return ''
}

function Get-AnchorStatusToken {
    param([string]$Value)

    $normalized = (Normalize-MarkdownScalar -Value $Value).ToLowerInvariant()
    foreach ($token in @('existing', 'extended', 'new', 'todo')) {
        if ($normalized -match "(^|[^a-z])$token([^a-z]|$)") {
            return $token
        }
    }

    return ''
}

function Normalize-RuleToken {
    param([string]$Value)

    $normalized = (Normalize-MarkdownScalar -Value $Value).ToLowerInvariant()
    $normalized = $normalized -replace '[_\s]+', '-'
    $normalized = $normalized -replace '-+', '-'
    return $normalized.Trim('-')
}

function Get-SemanticRefTokens {
    param(
        [string]$Value,
        [string]$Pattern = '(SSE|OSA|SFV|LC|INV|DCC)-[A-Za-z0-9_.-]+'
    )

    $normalized = Normalize-MarkdownScalar -Value $Value
    if ([string]::IsNullOrWhiteSpace($normalized)) {
        return @()
    }

    $matches = [regex]::Matches($normalized, $Pattern)
    if ($matches.Count -eq 0) {
        return @()
    }

    $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $tokens = New-Object System.Collections.Generic.List[string]
    foreach ($match in $matches) {
        $token = $match.Value
        if (-not [string]::IsNullOrWhiteSpace($token) -and $seen.Add($token)) {
            $tokens.Add($token) | Out-Null
        }
    }
    return @($tokens.ToArray())
}

function Test-SingleBindingReasonWeak {
    param([string]$Reason)

    $normalized = (Normalize-MarkdownScalar -Value $Reason).ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($normalized)) {
        return $true
    }

    if ($normalized -in @('n/a', 'na', 'none', '[none]', 'todo', 'tbd')) {
        return $true
    }

    if ($normalized.Length -lt 24) {
        return $true
    }

    if ($normalized -notmatch '(shared|reuse|reused|reusable|lifecycle|invariant|owner|source|stable|consisten|cross[- ]binding|duplicate|contradict)') {
        return $true
    }

    return $false
}

function Get-PlanBindingTupleData {
    param([string]$Path)

    $rows = @{}
    $lines = @(Get-Content -Path $Path -ErrorAction Stop)
    $currentSection = ''
    $inTable = $false
    $bindingRowIndex = -1
    $operationIndex = -1
    $ifScopeIndex = -1
    $tmIndex = -1
    $tcIndex = -1
    $uifPathIndex = -1
    $uddRefIndex = -1
    $testScopeIndex = -1
    $packetSourceIndex = -1
    $hasPacketSourceColumn = $false

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        $lineNumber = $i + 1
        $trimmed = $line.Trim()
        $headingMatch = [regex]::Match($trimmed, '^##\s+(.+)$')
        if ($headingMatch.Success) {
            $currentSection = $headingMatch.Groups[1].Value.Trim()
            $inTable = $false
            $bindingRowIndex = -1
            $operationIndex = -1
            $ifScopeIndex = -1
            $tmIndex = -1
            $tcIndex = -1
            $uifPathIndex = -1
            $uddRefIndex = -1
            $testScopeIndex = -1
            $packetSourceIndex = -1
            continue
        }

        if ($currentSection -ne 'Binding Projection Index') {
            continue
        }

        $cells = @(Get-MarkdownCells -Line $line)
        if ($cells.Count -eq 0) {
            $inTable = $false
            $bindingRowIndex = -1
            $operationIndex = -1
            $ifScopeIndex = -1
            $tmIndex = -1
            $tcIndex = -1
            $uifPathIndex = -1
            $uddRefIndex = -1
            $testScopeIndex = -1
            $packetSourceIndex = -1
            continue
        }

        if (-not $inTable) {
            $bindingRowIndex = -1
            $operationIndex = -1
            $ifScopeIndex = -1
            $tmIndex = -1
            $tcIndex = -1
            $uifPathIndex = -1
            $uddRefIndex = -1
            $testScopeIndex = -1
            $packetSourceIndex = -1

            for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                switch ($cells[$idx]) {
                    'BindingRowID' { $bindingRowIndex = $idx }
                    'Packet Source' {
                        $packetSourceIndex = $idx
                        $hasPacketSourceColumn = $true
                    }
                    'Trigger Ref(s)' { $operationIndex = $idx }
                    'IF ID / IF Scope' { $ifScopeIndex = $idx }
                    'Primary TM IDs' { $tmIndex = $idx }
                    'TC IDs' { $tcIndex = $idx }
                    'UIF Path Ref(s)' { $uifPathIndex = $idx }
                    'UDD Ref(s)' { $uddRefIndex = $idx }
                    'Test Scope' { $testScopeIndex = $idx }
                }
            }

            if ($bindingRowIndex -ge 0) {
                $inTable = $true
            }
            continue
        }

        if (Test-MarkdownSeparatorRow -Cells $cells) {
            continue
        }

        if ($bindingRowIndex -lt 0 -or $bindingRowIndex -ge $cells.Count) {
            continue
        }

        $bindingId = Normalize-MarkdownScalar -Value $cells[$bindingRowIndex]
        if ([string]::IsNullOrWhiteSpace($bindingId)) {
            continue
        }

        $rows[$bindingId] = [PSCustomObject]@{
            Line       = $lineNumber
            PacketSource = if ($packetSourceIndex -ge 0 -and $packetSourceIndex -lt $cells.Count) { Normalize-PacketSourceRef -Value $cells[$packetSourceIndex] } else { '' }
            ExpectedPacketSource = Get-CanonicalPacketSource -BindingRowId $bindingId
            SourceBindingRowId = if ($packetSourceIndex -ge 0 -and $packetSourceIndex -lt $cells.Count) { Get-PacketSourceBindingRowId -Value $cells[$packetSourceIndex] } else { '' }
            Operation  = if ($operationIndex -ge 0 -and $operationIndex -lt $cells.Count) { Normalize-MarkdownListCell -Value $cells[$operationIndex] } else { '' }
            IfScope    = if ($ifScopeIndex -ge 0 -and $ifScopeIndex -lt $cells.Count) { Normalize-MarkdownScalar -Value $cells[$ifScopeIndex] } else { '' }
            TmId       = if ($tmIndex -ge 0 -and $tmIndex -lt $cells.Count) { Normalize-MarkdownListCell -Value $cells[$tmIndex] } else { '' }
            TcIds      = if ($tcIndex -ge 0 -and $tcIndex -lt $cells.Count) { Normalize-MarkdownListCell -Value $cells[$tcIndex] } else { '' }
            UifPathRefs = if ($uifPathIndex -ge 0 -and $uifPathIndex -lt $cells.Count) { Normalize-MarkdownListCell -Value $cells[$uifPathIndex] } else { '' }
            UddRefs    = if ($uddRefIndex -ge 0 -and $uddRefIndex -lt $cells.Count) { Normalize-MarkdownListCell -Value $cells[$uddRefIndex] } else { '' }
            TestScope  = if ($testScopeIndex -ge 0 -and $testScopeIndex -lt $cells.Count) { Normalize-MarkdownScalar -Value $cells[$testScopeIndex] } else { '' }
        }
    }

    return [PSCustomObject]@{
        Rows = $rows
        HasPacketSourceColumn = $hasPacketSourceColumn
    }
}

function Get-TestMatrixBindingPackets {
    param([string]$Path)

    $rows = @{}
    $lines = @(Get-Content -Path $Path -ErrorAction Stop)
    $currentSection = ''
    $inTable = $false
    $bindingRowIndex = -1
    $operationIndex = -1
    $ifScopeIndex = -1
    $tmIndex = -1
    $tcIndex = -1
    $uifPathIndex = -1
    $uddRefIndex = -1
    $testScopeIndex = -1

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        $lineNumber = $i + 1
        $trimmed = $line.Trim()
        $headingMatch = [regex]::Match($trimmed, '^##\s+(.+)$')
        if ($headingMatch.Success) {
            $currentSection = $headingMatch.Groups[1].Value.Trim()
            $inTable = $false
            $bindingRowIndex = -1
            $operationIndex = -1
            $ifScopeIndex = -1
            $tmIndex = -1
            $tcIndex = -1
            $uifPathIndex = -1
            $uddRefIndex = -1
            $testScopeIndex = -1
            continue
        }

        if ($currentSection -ne 'Binding Packets') {
            continue
        }

        $cells = @(Get-MarkdownCells -Line $line)
        if ($cells.Count -eq 0) {
            $inTable = $false
            $bindingRowIndex = -1
            $operationIndex = -1
            $ifScopeIndex = -1
            $tmIndex = -1
            $tcIndex = -1
            $uifPathIndex = -1
            $uddRefIndex = -1
            $testScopeIndex = -1
            continue
        }

        if (-not $inTable) {
            $bindingRowIndex = -1
            $operationIndex = -1
            $ifScopeIndex = -1
            $tmIndex = -1
            $tcIndex = -1
            $uifPathIndex = -1
            $uddRefIndex = -1
            $testScopeIndex = -1

            for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                switch ($cells[$idx]) {
                    'BindingRowID' { $bindingRowIndex = $idx }
                    'Trigger Ref(s)' { $operationIndex = $idx }
                    'IF Scope' { $ifScopeIndex = $idx }
                    'Primary TM IDs' { $tmIndex = $idx }
                    'TC IDs' { $tcIndex = $idx }
                    'UIF Path Ref(s)' { $uifPathIndex = $idx }
                    'UDD Ref(s)' { $uddRefIndex = $idx }
                    'Test Scope' { $testScopeIndex = $idx }
                }
            }

            if ($bindingRowIndex -ge 0) {
                $inTable = $true
            }
            continue
        }

        if (Test-MarkdownSeparatorRow -Cells $cells) {
            continue
        }

        if ($bindingRowIndex -lt 0 -or $bindingRowIndex -ge $cells.Count) {
            continue
        }

        $bindingId = Normalize-MarkdownScalar -Value $cells[$bindingRowIndex]
        if ([string]::IsNullOrWhiteSpace($bindingId)) {
            continue
        }

        $rows[$bindingId] = [PSCustomObject]@{
            Line        = $lineNumber
            Operation   = if ($operationIndex -ge 0 -and $operationIndex -lt $cells.Count) { Normalize-MarkdownListCell -Value $cells[$operationIndex] } else { '' }
            IfScope     = if ($ifScopeIndex -ge 0 -and $ifScopeIndex -lt $cells.Count) { Normalize-MarkdownScalar -Value $cells[$ifScopeIndex] } else { '' }
            TmId        = if ($tmIndex -ge 0 -and $tmIndex -lt $cells.Count) { Normalize-MarkdownListCell -Value $cells[$tmIndex] } else { '' }
            TcIds       = if ($tcIndex -ge 0 -and $tcIndex -lt $cells.Count) { Normalize-MarkdownListCell -Value $cells[$tcIndex] } else { '' }
            UifPathRefs = if ($uifPathIndex -ge 0 -and $uifPathIndex -lt $cells.Count) { Normalize-MarkdownListCell -Value $cells[$uifPathIndex] } else { '' }
            UddRefs     = if ($uddRefIndex -ge 0 -and $uddRefIndex -lt $cells.Count) { Normalize-MarkdownListCell -Value $cells[$uddRefIndex] } else { '' }
            TestScope   = if ($testScopeIndex -ge 0 -and $testScopeIndex -lt $cells.Count) { Normalize-MarkdownScalar -Value $cells[$testScopeIndex] } else { '' }
        }
    }

    return $rows
}

function Get-ContractHeaderTuple {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }

    $boundaryPattern = '(?i)^\s*(?:\*\*)?Boundary[ _-]*Anchor(?:\s*\([^)]*\))?(?:\*\*)?\s*:\s*(.+)$'
    $anchorStatusPattern = '(?i)^\s*(?:\*\*)?Anchor[ _-]*Status(?:\s*\([^)]*\))?(?:\*\*)?\s*:\s*(.+)$'
    $entryStatusPattern = '(?i)^\s*(?:\*\*)?Implementation[ _-]*Entry[ _-]*Anchor[ _-]*Status(?:\s*\([^)]*\))?(?:\*\*)?\s*:\s*(.+)$'
    $entryPattern = '(?i)^\s*(?:\*\*)?Implementation[ _-]*Entry[ _-]*Anchor(?:\s*\([^)]*\))?(?:\*\*)?\s*:\s*(.+)$'

    $tuple = [ordered]@{
        Line           = 0
        Boundary       = ''
        BoundaryStatus = ''
        Entry          = ''
        EntryStatus    = ''
    }

    $lines = @(Get-Content -Path $Path -ErrorAction Stop)
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        $lineNumber = $i + 1

        $match = [regex]::Match($line, $boundaryPattern)
        if ($match.Success -and [string]::IsNullOrWhiteSpace($tuple.Boundary)) {
            $tuple.Boundary = Normalize-MarkdownScalar -Value $match.Groups[1].Value
            if ($tuple.Line -eq 0) {
                $tuple.Line = $lineNumber
            }
            continue
        }

        $match = [regex]::Match($line, $anchorStatusPattern)
        if ($match.Success -and [string]::IsNullOrWhiteSpace($tuple.BoundaryStatus)) {
            $tuple.BoundaryStatus = Get-AnchorStatusToken -Value $match.Groups[1].Value
            if ($tuple.Line -eq 0) {
                $tuple.Line = $lineNumber
            }
            continue
        }

        $match = [regex]::Match($line, $entryStatusPattern)
        if ($match.Success -and [string]::IsNullOrWhiteSpace($tuple.EntryStatus)) {
            $tuple.EntryStatus = Get-AnchorStatusToken -Value $match.Groups[1].Value
            if ($tuple.Line -eq 0) {
                $tuple.Line = $lineNumber
            }
            continue
        }

        $match = [regex]::Match($line, $entryPattern)
        if ($match.Success -and [string]::IsNullOrWhiteSpace($tuple.Entry)) {
            $tuple.Entry = Normalize-MarkdownScalar -Value $match.Groups[1].Value
            if ($tuple.Line -eq 0) {
                $tuple.Line = $lineNumber
            }
        }
    }

    return [PSCustomObject]$tuple
}

function Test-NorthboundAnchorPair {
    param(
        [string]$BoundaryValue,
        [string]$EntryValue,
        [string]$BoundaryHttpRegex,
        [string]$BoundaryForbiddenRegex,
        [string]$EntryControllerRegex,
        [string]$EntryForbiddenRegex
    )

    $boundary = ($BoundaryValue ?? '').Trim()
    $entry = ($EntryValue ?? '').Trim()

    if ([string]::IsNullOrWhiteSpace($boundary)) {
        return $null
    }

    if ($boundary -match $BoundaryForbiddenRegex) {
        return 'Boundary Anchor resolves to facade/service-style symbol while controller-first HTTP entry is required by feature layering.'
    }

    if ($boundary -match $BoundaryHttpRegex) {
        if ([string]::IsNullOrWhiteSpace($entry)) {
            return 'HTTP Boundary Anchor requires an Implementation Entry Anchor that resolves to the owning controller method.'
        }

        if ($entry -notmatch $EntryControllerRegex) {
            return 'HTTP Boundary Anchor is paired with a non-controller Implementation Entry Anchor.'
        }

        if (($entry -match $EntryForbiddenRegex) -and ($entry -notmatch $EntryControllerRegex)) {
            return 'HTTP Boundary Anchor is paired with service/facade-style Implementation Entry Anchor instead of the owning controller method.'
        }
    }

    return $null
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
$repoRootForFeature = Get-FeatureRepoRoot -FeaturePath $featureRoot

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
                $lines = @(Get-Content -Path $file.FullPath -ErrorAction Stop)
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

                    $cells = @(Get-MarkdownCells -Line $line)
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

        'northbound_controller_required' {
            $triggerRel = $params['trigger_file']
            if ([string]::IsNullOrWhiteSpace($triggerRel)) {
                $triggerRel = 'research.md'
            }

            $triggerRegex = $params['trigger_regex']
            $boundaryHttpRegex = $params['boundary_http_regex']
            $boundaryForbiddenRegex = $params['boundary_forbidden_regex']
            $entryControllerRegex = $params['entry_controller_regex']
            $entryForbiddenRegex = $params['entry_forbidden_regex']
            $sequenceVariantBRegex = $params['sequence_variant_b_regex']

            if ([string]::IsNullOrWhiteSpace($triggerRegex) -or
                [string]::IsNullOrWhiteSpace($boundaryHttpRegex) -or
                [string]::IsNullOrWhiteSpace($boundaryForbiddenRegex) -or
                [string]::IsNullOrWhiteSpace($entryControllerRegex) -or
                [string]::IsNullOrWhiteSpace($entryForbiddenRegex) -or
                [string]::IsNullOrWhiteSpace($sequenceVariantBRegex)) {
                Add-Finding -RuleId $row.id -Severity $row.severity -File $row.glob -Line 0 -Message 'Rule params missing required northbound-controller keys.' -Remediation 'Fix rules TSV params for this rule.'
                continue
            }

            $triggerPath = Join-Path $featureRoot ($triggerRel -replace '/', [System.IO.Path]::DirectorySeparatorChar)
            if (-not (Test-Path -Path $triggerPath -PathType Leaf)) {
                continue
            }

            if (-not (Select-String -Path $triggerPath -Pattern $triggerRegex -Quiet -ErrorAction Stop)) {
                continue
            }

            $boundaryLabelPattern = '(?i)^\s*(?:[-*]\s*)?(?:\*\*)?Boundary[ _-]*Anchor(?:\s*\([^)]*\))?(?:\*\*)?\s*:\s*(.+)$'
            $entryLabelPattern = '(?i)^\s*(?:[-*]\s*)?(?:\*\*)?Implementation[ _-]*Entry[ _-]*Anchor(?:\s*\([^)]*\))?(?:\*\*)?\s*:\s*(.+)$'
            $boundaryHeaderPattern = '(?i)^Boundary[ _-]*Anchor$'
            $entryHeaderPattern = '(?i)^Implementation[ _-]*Entry[ _-]*Anchor$'

            foreach ($file in $matched) {
                $lines = @(Get-Content -Path $file.FullPath -ErrorAction Stop)
                $pendingBoundaryValue = $null
                $pendingBoundaryLine = 0
                $boundaryColumnIndex = -1
                $entryColumnIndex = -1
                $inTable = $false
                $hasHttpBoundary = $false

                for ($i = 0; $i -lt $lines.Count; $i++) {
                    $lineNumber = $i + 1
                    $line = $lines[$i]

                    $boundaryMatch = [regex]::Match($line, $boundaryLabelPattern)
                    if ($boundaryMatch.Success) {
                        if ($null -ne $pendingBoundaryValue) {
                            $detail = Test-NorthboundAnchorPair `
                                -BoundaryValue $pendingBoundaryValue `
                                -EntryValue '' `
                                -BoundaryHttpRegex $boundaryHttpRegex `
                                -BoundaryForbiddenRegex $boundaryForbiddenRegex `
                                -EntryControllerRegex $entryControllerRegex `
                                -EntryForbiddenRegex $entryForbiddenRegex
                            if ($detail -and ($pendingBoundaryValue -notmatch $boundaryForbiddenRegex)) {
                                Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $pendingBoundaryLine -Message "$($row.message) $detail" -Remediation $row.remediation
                            }
                        }

                        $pendingBoundaryValue = $boundaryMatch.Groups[1].Value.Trim()
                        $pendingBoundaryLine = $lineNumber
                        if ($pendingBoundaryValue -match $boundaryHttpRegex) {
                            $hasHttpBoundary = $true
                        }

                        $detail = Test-NorthboundAnchorPair `
                            -BoundaryValue $pendingBoundaryValue `
                            -EntryValue '' `
                            -BoundaryHttpRegex $boundaryHttpRegex `
                            -BoundaryForbiddenRegex $boundaryForbiddenRegex `
                            -EntryControllerRegex $entryControllerRegex `
                            -EntryForbiddenRegex $entryForbiddenRegex
                        if ($detail -and ($pendingBoundaryValue -match $boundaryForbiddenRegex)) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lineNumber -Message "$($row.message) $detail" -Remediation $row.remediation
                        }
                        continue
                    }

                    $entryMatch = [regex]::Match($line, $entryLabelPattern)
                    if ($entryMatch.Success -and $null -ne $pendingBoundaryValue) {
                        $detail = Test-NorthboundAnchorPair `
                            -BoundaryValue $pendingBoundaryValue `
                            -EntryValue $entryMatch.Groups[1].Value.Trim() `
                            -BoundaryHttpRegex $boundaryHttpRegex `
                            -BoundaryForbiddenRegex $boundaryForbiddenRegex `
                            -EntryControllerRegex $entryControllerRegex `
                            -EntryForbiddenRegex $entryForbiddenRegex
                        if ($detail) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $pendingBoundaryLine -Message "$($row.message) $detail" -Remediation $row.remediation
                        }
                        $pendingBoundaryValue = $null
                        $pendingBoundaryLine = 0
                        continue
                    }

                    $cells = @(Get-MarkdownCells -Line $line)
                    if ($cells.Count -eq 0) {
                        $boundaryColumnIndex = -1
                        $entryColumnIndex = -1
                        $inTable = $false
                        continue
                    }

                    if (-not $inTable) {
                        $boundaryColumnIndex = -1
                        $entryColumnIndex = -1
                        for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                            if ($cells[$idx] -match $boundaryHeaderPattern) {
                                $boundaryColumnIndex = $idx
                            }
                            if ($cells[$idx] -match $entryHeaderPattern) {
                                $entryColumnIndex = $idx
                            }
                        }
                        if ($boundaryColumnIndex -ge 0 -and $entryColumnIndex -ge 0) {
                            $inTable = $true
                        }
                        continue
                    }

                    if (Test-MarkdownSeparatorRow -Cells $cells) {
                        continue
                    }

                    if ($boundaryColumnIndex -ge 0 -and $boundaryColumnIndex -lt $cells.Count) {
                        $boundaryValue = $cells[$boundaryColumnIndex]
                        if ($boundaryValue -match $boundaryHttpRegex) {
                            $hasHttpBoundary = $true
                        }
                        $entryValue = ''
                        if ($entryColumnIndex -ge 0 -and $entryColumnIndex -lt $cells.Count) {
                            $entryValue = $cells[$entryColumnIndex]
                        }

                        $detail = Test-NorthboundAnchorPair `
                            -BoundaryValue $boundaryValue `
                            -EntryValue $entryValue `
                            -BoundaryHttpRegex $boundaryHttpRegex `
                            -BoundaryForbiddenRegex $boundaryForbiddenRegex `
                            -EntryControllerRegex $entryControllerRegex `
                            -EntryForbiddenRegex $entryForbiddenRegex
                        if ($detail) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lineNumber -Message "$($row.message) $detail" -Remediation $row.remediation
                        }
                    }
                }

                if ($null -ne $pendingBoundaryValue) {
                    $detail = Test-NorthboundAnchorPair `
                        -BoundaryValue $pendingBoundaryValue `
                        -EntryValue '' `
                        -BoundaryHttpRegex $boundaryHttpRegex `
                        -BoundaryForbiddenRegex $boundaryForbiddenRegex `
                        -EntryControllerRegex $entryControllerRegex `
                        -EntryForbiddenRegex $entryForbiddenRegex
                    if ($detail -and ($pendingBoundaryValue -notmatch $boundaryForbiddenRegex)) {
                        Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $pendingBoundaryLine -Message "$($row.message) $detail" -Remediation $row.remediation
                    }
                }

                if ($file.RelPath -like 'contracts/*' -and $hasHttpBoundary) {
                    $hasVariantA = Select-String -Path $file.FullPath -Pattern '(?i)Sequence\s+Variant\s+A' -ErrorAction SilentlyContinue
                    if (-not $hasVariantA) {
                        $variantHits = Select-String -Path $file.FullPath -Pattern $sequenceVariantBRegex -ErrorAction SilentlyContinue
                        foreach ($hit in $variantHits) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $hit.LineNumber -Message "$($row.message) HTTP boundary contracts must not render Sequence Variant B (Boundary == Entry)." -Remediation $row.remediation
                        }
                    }
                }
            }
        }

        'repo_anchor_paths_exist' {
            $anchorPattern = '[A-Za-z0-9_./\\-]+\.[A-Za-z0-9_-]+::[A-Za-z_$][A-Za-z0-9_.$-]*'

            foreach ($file in $matched) {
                $lines = @(Get-Content -Path $file.FullPath -ErrorAction Stop)
                for ($i = 0; $i -lt $lines.Count; $i++) {
                    $lineNumber = $i + 1
                    $matchesOnLine = [regex]::Matches($lines[$i], $anchorPattern)
                    foreach ($m in $matchesOnLine) {
                        $anchorToken = $m.Value
                        if ([string]::IsNullOrWhiteSpace($anchorToken)) {
                            continue
                        }

                        $anchorPath = ($anchorToken -split '::', 2)[0]
                        $resolved = Resolve-RepoAnchorPath -RepoRoot $repoRootForFeature -AnchorPath $anchorPath
                        if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lineNumber -Message "$($row.message) Missing file: $anchorPath" -Remediation $row.remediation
                        }
                    }
                }
            }
        }

        'plan_status_consistency' {
            foreach ($file in $matched) {
                $lines = @(Get-Content -Path $file.FullPath -ErrorAction Stop)
                $planStatus = $null
                $statusLine = 0
                $currentSection = ''
                $inTable = $false
                $statusColumnIndex = -1
                $stageStatuses = New-Object System.Collections.Generic.List[string]
                $artifactStatuses = New-Object System.Collections.Generic.List[string]

                for ($i = 0; $i -lt $lines.Count; $i++) {
                    $lineNumber = $i + 1
                    $line = $lines[$i]
                    $trimmed = $line.Trim()

                    $statusMatch = [regex]::Match($trimmed, '^-+\s*Status:\s*(planning-not-started|planning-in-progress|planning-complete)\s*$')
                    if ($statusMatch.Success) {
                        $planStatus = $statusMatch.Groups[1].Value
                        $statusLine = $lineNumber
                    }

                    $headingMatch = [regex]::Match($trimmed, '^##\s+(.+)$')
                    if ($headingMatch.Success) {
                        $currentSection = $headingMatch.Groups[1].Value.Trim()
                        $inTable = $false
                        $statusColumnIndex = -1
                        continue
                    }

                    if ($currentSection -notin @('Stage Queue', 'Artifact Status')) {
                        continue
                    }

                    $cells = @(Get-MarkdownCells -Line $line)
                    if ($cells.Count -eq 0) {
                        $inTable = $false
                        $statusColumnIndex = -1
                        continue
                    }

                    if (-not $inTable) {
                        $statusColumnIndex = -1
                        for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                            if ($cells[$idx] -eq 'Status') {
                                $statusColumnIndex = $idx
                                break
                            }
                        }
                        if ($statusColumnIndex -ge 0) {
                            $inTable = $true
                        }
                        continue
                    }

                    if (Test-MarkdownSeparatorRow -Cells $cells) {
                        continue
                    }

                    if ($statusColumnIndex -ge 0 -and $statusColumnIndex -lt $cells.Count) {
                        $token = $cells[$statusColumnIndex].Trim().ToLowerInvariant()
                        if ($currentSection -eq 'Stage Queue') {
                            $stageStatuses.Add($token) | Out-Null
                        } else {
                            $artifactStatuses.Add($token) | Out-Null
                        }
                    }
                }

                if ([string]::IsNullOrWhiteSpace($planStatus)) {
                    Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line 0 -Message "$($row.message) Missing ``Feature Identity -> Status`` value." -Remediation $row.remediation
                    continue
                }

                $stageCount = $stageStatuses.Count
                $artifactCount = $artifactStatuses.Count
                $allStagePending = ($stageCount -gt 0)
                $allStageDone = ($stageCount -gt 0)
                foreach ($token in $stageStatuses) {
                    if ($token -ne 'pending') {
                        $allStagePending = $false
                    }
                    if ($token -ne 'done') {
                        $allStageDone = $false
                    }
                }

                $allArtifactDone = $true
                foreach ($token in $artifactStatuses) {
                    if ($token -ne 'done') {
                        $allArtifactDone = $false
                    }
                }

                $nothingStarted = $allStagePending -and ($artifactCount -eq 0)
                $everythingDone = $allStageDone -and $allArtifactDone

                switch ($planStatus) {
                    'planning-not-started' {
                        if (-not $nothingStarted) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $statusLine -Message "$($row.message) ``planning-not-started`` requires all stage rows to remain ``pending`` and ``Artifact Status`` to stay empty." -Remediation $row.remediation
                        }
                    }
                    'planning-complete' {
                        if (-not $everythingDone) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $statusLine -Message "$($row.message) ``planning-complete`` requires all stage rows and artifact rows to be ``done``." -Remediation $row.remediation
                        }
                    }
                    'planning-in-progress' {
                        if ($nothingStarted) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $statusLine -Message "$($row.message) ``planning-in-progress`` is too advanced for an untouched queue; use ``planning-not-started`` instead." -Remediation $row.remediation
                        } elseif ($everythingDone) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $statusLine -Message "$($row.message) ``planning-in-progress`` is stale after all stage/artifact rows are complete; use ``planning-complete`` instead." -Remediation $row.remediation
                        }
                    }
                }
            }
        }

        'binding_projection_stable_only' {
            foreach ($file in $matched) {
                $lines = @(Get-Content -Path $file.FullPath -ErrorAction Stop)
                $currentSection = ''
                $inTable = $false

                for ($i = 0; $i -lt $lines.Count; $i++) {
                    $lineNumber = $i + 1
                    $line = $lines[$i]
                    $trimmed = $line.Trim()

                    $headingMatch = [regex]::Match($trimmed, '^##\s+(.+)$')
                    if ($headingMatch.Success) {
                        $currentSection = $headingMatch.Groups[1].Value.Trim()
                        $inTable = $false
                        continue
                    }

                    if ($currentSection -ne 'Binding Projection Index') {
                        continue
                    }

                    $cells = @(Get-MarkdownCells -Line $line)
                    if ($cells.Count -eq 0) {
                        $inTable = $false
                        continue
                    }

                    if (-not $inTable) {
                        $inTable = $true
                        foreach ($cell in $cells) {
                            if ($cell -in @(
                                'Boundary Anchor',
                                'Implementation Entry Anchor',
                                'Boundary Anchor Status',
                                'Implementation Entry Anchor Status',
                                'Request DTO Anchor',
                                'Response DTO Anchor',
                                'Primary Collaborator Anchor',
                                'State Owner Anchor(s)',
                                'Repo Anchor',
                                'Repo Anchor Role',
                                'Boundary Anchor Strategy Evidence',
                                'Implementation Entry Anchor Strategy Evidence',
                                'Lifecycle Ref(s)',
                                'Invariant Ref(s)',
                                'Main Pass Anchor',
                                'Branch/Failure Anchor(s)'
                            )) {
                                Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lineNumber -Message $row.message -Remediation $row.remediation
                                break
                            }
                        }
                        continue
                    }
                }
            }
        }

        'binding_tuple_projection_sync' {
            foreach ($file in $matched) {
                $testMatrixPath = Join-Path $featureRoot 'test-matrix.md'
                if (-not (Test-Path -LiteralPath $testMatrixPath -PathType Leaf)) {
                    Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line 0 -Message "$($row.message) Missing file: test-matrix.md" -Remediation $row.remediation
                    continue
                }

                $planData = Get-PlanBindingTupleData -Path $file.FullPath
                $packetRows = Get-TestMatrixBindingPackets -Path $testMatrixPath

                foreach ($bindingId in $planData.Rows.Keys) {
                    $planRow = $planData.Rows[$bindingId]
                    if (-not $packetRows.ContainsKey($bindingId)) {
                        Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $planRow.Line -Message "$($row.message) BindingRowID $bindingId is present in `Binding Projection Index` but missing from `test-matrix.md` `Binding Packets`." -Remediation $row.remediation
                        continue
                    }

                    if ($planData.HasPacketSourceColumn) {
                        if ([string]::IsNullOrWhiteSpace($planRow.PacketSource) -or
                            [string]::IsNullOrWhiteSpace($planRow.SourceBindingRowId) -or
                            $planRow.SourceBindingRowId -ne $bindingId -or
                            $planRow.PacketSource -ne $planRow.ExpectedPacketSource) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $planRow.Line -Message "$($row.message) BindingRowID $bindingId differs from `test-matrix.md` `Binding Packets` for minimal projection fields." -Remediation $row.remediation
                        }
                        continue
                    }

                    $packetRow = $packetRows[$bindingId]
                    if ($planRow.Operation -ne $packetRow.Operation -or $planRow.IfScope -ne $packetRow.IfScope -or $planRow.TmId -ne $packetRow.TmId -or $planRow.TcIds -ne $packetRow.TcIds -or $planRow.UifPathRefs -ne $packetRow.UifPathRefs -or $planRow.UddRefs -ne $packetRow.UddRefs -or $planRow.TestScope -ne $packetRow.TestScope) {
                        Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $planRow.Line -Message "$($row.message) BindingRowID $bindingId differs from `test-matrix.md` `Binding Packets` for minimal projection fields." -Remediation $row.remediation
                    }

                }
            }
        }

        'shared_semantic_reuse_enum' {
            $allowedCsv = $params['allowed']
            if ([string]::IsNullOrWhiteSpace($allowedCsv)) {
                Add-Finding -RuleId $row.id -Severity $row.severity -File $row.glob -Line 0 -Message 'Rule params missing required key: allowed' -Remediation 'Fix rules TSV params for this rule.'
                continue
            }

            $allowedSet = Get-AllowedStatusSet -AllowedCsv $allowedCsv
            $typeHeaderPattern = '(?i)^Constraint[ _-]*Type(?:\s*\([^)]*\))?$'

            foreach ($file in $matched) {
                $lines = @(Get-Content -Path $file.FullPath -ErrorAction Stop)
                $typeColumnIndex = -1
                $inTable = $false

                for ($i = 0; $i -lt $lines.Count; $i++) {
                    $lineNumber = $i + 1
                    $line = $lines[$i]

                    $cells = @(Get-MarkdownCells -Line $line)
                    if ($cells.Count -eq 0) {
                        $typeColumnIndex = -1
                        $inTable = $false
                        continue
                    }

                    if (-not $inTable) {
                        $typeColumnIndex = -1
                        for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                            if ($cells[$idx] -match $typeHeaderPattern) {
                                $typeColumnIndex = $idx
                                break
                            }
                        }
                        if ($typeColumnIndex -ge 0) {
                            $inTable = $true
                        }
                        continue
                    }

                    if (Test-MarkdownSeparatorRow -Cells $cells) {
                        continue
                    }

                    if ($typeColumnIndex -ge $cells.Count) {
                        continue
                    }

                    $typeValue = $cells[$typeColumnIndex].Trim()
                    if ($typeValue -eq 'N/A') {
                        continue
                    }

                    if (-not $allowedSet.Contains($typeValue)) {
                        $allowedText = (($allowedSet | ForEach-Object { $_ }) -join ',')
                        Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lineNumber -Message "$($row.message) Invalid type: $typeValue. Allowed: $allowedText" -Remediation $row.remediation
                    }
                }
            }
        }

        'anchor_strategy_evidence_required' {
            $statusLabelPattern = '(?i)^\s*(?:[-*]\s*)?(?:\*\*)?(Boundary[ _-]*Anchor[ _-]*Status|Implementation[ _-]*Entry[ _-]*Anchor[ _-]*Status|Anchor[ _-]*Status)(?:\s*\([^)]*\))?(?:\*\*)?\s*:\s*(.+)$'
            $strategyLabelPattern = '(?i)^\s*(?:[-*]\s*)?(?:\*\*)?(Boundary[ _-]*Anchor[ _-]*Strategy[ _-]*Evidence|Implementation[ _-]*Entry[ _-]*Anchor[ _-]*Strategy[ _-]*Evidence|Anchor[ _-]*Strategy[ _-]*Evidence)(?:\s*\([^)]*\))?(?:\*\*)?\s*:\s*(.+)$'

            foreach ($file in $matched) {
                $lines = @(Get-Content -Path $file.FullPath -ErrorAction Stop)
                $pendingStatus = $null
                $pendingType = $null
                $pendingLine = 0

                for ($i = 0; $i -lt $lines.Count; $i++) {
                    $lineNumber = $i + 1
                    $line = $lines[$i]

                    $statusMatch = [regex]::Match($line, $statusLabelPattern)
                    if ($statusMatch.Success) {
                        $pType = $statusMatch.Groups[1].Value
                        $pStatus = Get-AnchorStatusToken -Value $statusMatch.Groups[2].Value
                        if ($pStatus -eq 'new') {
                            $pendingType = $pType
                            $pendingStatus = $pStatus
                            $pendingLine = $lineNumber
                        } else {
                            $pendingStatus = 'DONE'
                            $pendingType = $pType
                            $pendingLine = $lineNumber
                        }
                        continue
                    }

                    $strategyMatch = [regex]::Match($line, $strategyLabelPattern)
                    if ($strategyMatch.Success -and $null -ne $pendingStatus) {
                        $strategyType = $strategyMatch.Groups[1].Value
                        $evidenceValue = Normalize-MarkdownScalar -Value $strategyMatch.Groups[2].Value

                        $isMatch = $false
                        if ($pendingType -like 'Boundary*' -and $strategyType -like 'Boundary*') {
                            $isMatch = $true
                        } elseif ($pendingType -like 'Implementation*' -and $strategyType -like 'Implementation*') {
                            $isMatch = $true
                        } elseif ($pendingType -like 'Anchor*' -and $strategyType -like 'Anchor*') {
                            $isMatch = $true
                        }

                        if ($isMatch) {
                            if ($pendingStatus -eq 'new') {
                                if ($evidenceValue -notmatch 'existing[ _-]+rejected' -or $evidenceValue -notmatch 'extended[ _-]+rejected') {
                                    Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lineNumber -Message "$($row.message) Anchor status is 'new' but evidence is missing 'existing rejected' or 'extended rejected'. Evidence: $evidenceValue" -Remediation $row.remediation
                                }
                            }
                            $pendingStatus = $null
                            $pendingType = $null
                            $pendingLine = 0
                        }
                    }
                }

                if ($pendingStatus -eq 'new') {
                    Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $pendingLine -Message "$($row.message) Anchor status is 'new' but strategy evidence label is missing for $pendingType." -Remediation $row.remediation
                }
            }
        }

        'data_model_semantic_closure' {
            foreach ($file in $matched) {
                $lines = @(Get-Content -Path $file.FullPath -ErrorAction Stop)
                $currentSection = ''
                $currentSubsection = ''
                $currentTable = ''
                $lifecycleSummaryLine = 0
                $invariantCatalogLine = 0
                $transitionTableLine = 0
                $transitionPseudocodeLine = 0
                $stateDiagramLine = 0
                $hasStateDiagram = $false
                $summaryHeaderSeen = $false
                $invariantHeaderSeen = $false
                $transitionHeaderSeen = $false
                $pseudocodeHeaderSeen = $false
                $summaryLifecycleIndex = -1
                $summaryOwnerIndex = -1
                $summaryInvariantIndex = -1
                $summaryModelIndex = -1
                $invariantIdIndex = -1
                $invariantLifecycleIndex = -1
                $invariantKindIndex = -1
                $transitionLifecycleIndex = -1
                $pseudocodeLifecycleIndex = -1
                $sseIdIndex = -1
                $osaIdIndex = -1
                $osaOwnerIndex = -1
                $sfvIdIndex = -1
                $dccIdIndex = -1
                $dccRequiredRefsIndex = -1
                $lifecycleRows = @{}
                $invariantAllowed = @{}
                $invariantForbidden = @{}
                $invariantKey = @{}
                $transitionRows = @{}
                $pseudocodeRows = @{}
                $sseIds = @{}
                $osaIds = @{}
                $osaOwnerValues = @{}
                $sfvIds = @{}
                $lcIds = @{}
                $invIds = @{}
                $dccIds = @{}
                $dccRequiredRefsById = @{}
                $dccLines = @{}

                for ($i = 0; $i -lt $lines.Count; $i++) {
                    $lineNumber = $i + 1
                    $line = $lines[$i]
                    $trimmed = $line.Trim()

                    $h2Match = [regex]::Match($trimmed, '^##\s+(.+)$')
                    if ($h2Match.Success) {
                        $currentSection = $h2Match.Groups[1].Value.Trim()
                        $currentSubsection = ''
                        $currentTable = ''
                        continue
                    }

                    $h3Match = [regex]::Match($trimmed, '^###\s+(.+)$')
                    if ($h3Match.Success) {
                        $currentSubsection = $h3Match.Groups[1].Value.Trim()
                        $currentTable = ''
                        switch ($currentSubsection) {
                            'Lifecycle Summary' { $lifecycleSummaryLine = $lineNumber }
                            'Invariant Catalog' { $invariantCatalogLine = $lineNumber }
                            'State Transition Table' { $transitionTableLine = $lineNumber }
                            'Transition Pseudocode (when `Required Model = fsm`)' { $transitionPseudocodeLine = $lineNumber }
                        }
                        continue
                    }

                    if ($currentSection -eq 'Business Invariants & Lifecycle Rules' -and $line -match 'stateDiagram-v2') {
                        $hasStateDiagram = $true
                        if ($stateDiagramLine -eq 0) {
                            $stateDiagramLine = $lineNumber
                        }
                    }

                    switch ($currentSection) {
                        'Shared Semantic Elements (SSE)' { $currentTable = 'sse' }
                        'Shared Semantic Elements' { $currentTable = 'sse' }
                        'Owner / Source Alignment' { $currentTable = 'osa' }
                        'Shared Field Vocabulary (SFV)' { $currentTable = 'sfv' }
                        'Shared Field Vocabulary' { $currentTable = 'sfv' }
                        'Downstream Contract Constraints' { $currentTable = 'dcc' }
                        default {
                            switch ($currentSubsection) {
                                'Lifecycle Summary' { $currentTable = 'lifecycle_summary' }
                                'Invariant Catalog' { $currentTable = 'invariant_catalog' }
                                'State Transition Table' { $currentTable = 'state_transition_table' }
                                'Transition Pseudocode (when `Required Model = fsm`)' { $currentTable = 'transition_pseudocode' }
                                default { $currentTable = '' }
                            }
                        }
                    }

                    if ([string]::IsNullOrWhiteSpace($currentTable)) {
                        continue
                    }

                    $cells = @(Get-MarkdownCells -Line $line)
                    if ($cells.Count -eq 0) {
                        switch ($currentTable) {
                            'sse' { $sseIdIndex = -1 }
                            'osa' {
                                $osaIdIndex = -1
                                $osaOwnerIndex = -1
                            }
                            'sfv' { $sfvIdIndex = -1 }
                            'dcc' {
                                $dccIdIndex = -1
                                $dccRequiredRefsIndex = -1
                            }
                            'lifecycle_summary' {
                                $summaryLifecycleIndex = -1
                                $summaryOwnerIndex = -1
                                $summaryInvariantIndex = -1
                                $summaryModelIndex = -1
                            }
                            'invariant_catalog' {
                                $invariantIdIndex = -1
                                $invariantLifecycleIndex = -1
                                $invariantKindIndex = -1
                            }
                            'state_transition_table' { $transitionLifecycleIndex = -1 }
                            'transition_pseudocode' { $pseudocodeLifecycleIndex = -1 }
                        }
                        continue
                    }

                    if ($currentTable -eq 'sse') {
                        if ($sseIdIndex -lt 0) {
                            for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                                if ($cells[$idx] -eq 'SSE ID') {
                                    $sseIdIndex = $idx
                                    break
                                }
                            }
                            continue
                        }
                        if (Test-MarkdownSeparatorRow -Cells $cells) {
                            continue
                        }
                        if ($sseIdIndex -ge $cells.Count) {
                            continue
                        }
                        $sseId = Normalize-MarkdownScalar -Value $cells[$sseIdIndex]
                        if (-not [string]::IsNullOrWhiteSpace($sseId)) {
                            $sseIds[$sseId] = $lineNumber
                        }
                        continue
                    }

                    if ($currentTable -eq 'osa') {
                        if ($osaIdIndex -lt 0) {
                            for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                                switch ($cells[$idx]) {
                                    'OSA ID' { $osaIdIndex = $idx }
                                    'Owner Class / Semantic Owner' { $osaOwnerIndex = $idx }
                                }
                            }
                            continue
                        }
                        if (Test-MarkdownSeparatorRow -Cells $cells) {
                            continue
                        }
                        if ($osaIdIndex -ge $cells.Count) {
                            continue
                        }
                        $osaId = Normalize-MarkdownScalar -Value $cells[$osaIdIndex]
                        if (-not [string]::IsNullOrWhiteSpace($osaId)) {
                            $osaIds[$osaId] = $lineNumber
                        }
                        if ($osaOwnerIndex -ge 0 -and $osaOwnerIndex -lt $cells.Count) {
                            $ownerKey = (Normalize-MarkdownScalar -Value $cells[$osaOwnerIndex]).ToLowerInvariant()
                            if (-not [string]::IsNullOrWhiteSpace($ownerKey)) {
                                $osaOwnerValues[$ownerKey] = $lineNumber
                            }
                        }
                        continue
                    }

                    if ($currentTable -eq 'sfv') {
                        if ($sfvIdIndex -lt 0) {
                            for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                                if ($cells[$idx] -eq 'SFV ID') {
                                    $sfvIdIndex = $idx
                                    break
                                }
                            }
                            continue
                        }
                        if (Test-MarkdownSeparatorRow -Cells $cells) {
                            continue
                        }
                        if ($sfvIdIndex -ge $cells.Count) {
                            continue
                        }
                        $sfvId = Normalize-MarkdownScalar -Value $cells[$sfvIdIndex]
                        if (-not [string]::IsNullOrWhiteSpace($sfvId)) {
                            $sfvIds[$sfvId] = $lineNumber
                        }
                        continue
                    }

                    if ($currentTable -eq 'dcc') {
                        if ($dccIdIndex -lt 0) {
                            for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                                switch ($cells[$idx]) {
                                    'DCC ID' { $dccIdIndex = $idx }
                                    'Required Shared Semantic Ref(s)' { $dccRequiredRefsIndex = $idx }
                                }
                            }
                            continue
                        }
                        if (Test-MarkdownSeparatorRow -Cells $cells) {
                            continue
                        }
                        if ($dccIdIndex -ge $cells.Count) {
                            continue
                        }
                        $dccId = Normalize-MarkdownScalar -Value $cells[$dccIdIndex]
                        if ([string]::IsNullOrWhiteSpace($dccId)) {
                            continue
                        }
                        $dccIds[$dccId] = $lineNumber
                        $dccLines[$dccId] = $lineNumber
                        $dccRequiredRefsById[$dccId] = if ($dccRequiredRefsIndex -ge 0 -and $dccRequiredRefsIndex -lt $cells.Count) {
                            Normalize-MarkdownListCell -Value $cells[$dccRequiredRefsIndex]
                        } else {
                            ''
                        }
                        continue
                    }

                    if ($currentTable -eq 'lifecycle_summary') {
                        if ($summaryLifecycleIndex -lt 0) {
                            for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                                switch ($cells[$idx]) {
                                    'Lifecycle Ref' { $summaryLifecycleIndex = $idx }
                                    'State Owner' { $summaryOwnerIndex = $idx }
                                    'Invariant Ref(s)' { $summaryInvariantIndex = $idx }
                                    'Required Model' { $summaryModelIndex = $idx }
                                }
                            }
                            if ($summaryLifecycleIndex -ge 0) {
                                $summaryHeaderSeen = $true
                            }
                            continue
                        }
                        if (Test-MarkdownSeparatorRow -Cells $cells) {
                            continue
                        }
                        if ($summaryLifecycleIndex -ge $cells.Count) {
                            continue
                        }
                        $lifecycleRef = Normalize-MarkdownScalar -Value $cells[$summaryLifecycleIndex]
                        if ([string]::IsNullOrWhiteSpace($lifecycleRef)) {
                            continue
                        }
                        $lifecycleRows[$lifecycleRef] = [PSCustomObject]@{
                            Line       = $lineNumber
                            StateOwner = if ($summaryOwnerIndex -ge 0 -and $summaryOwnerIndex -lt $cells.Count) { Normalize-MarkdownScalar -Value $cells[$summaryOwnerIndex] } else { '' }
                            Invariants = if ($summaryInvariantIndex -ge 0 -and $summaryInvariantIndex -lt $cells.Count) { Normalize-MarkdownListCell -Value $cells[$summaryInvariantIndex] } else { '' }
                            Model      = if ($summaryModelIndex -ge 0 -and $summaryModelIndex -lt $cells.Count) { Normalize-RuleToken -Value $cells[$summaryModelIndex] } else { '' }
                        }
                        $lcIds[$lifecycleRef] = $lineNumber
                        continue
                    }

                    if ($currentTable -eq 'invariant_catalog') {
                        if ($invariantIdIndex -lt 0 -or $invariantLifecycleIndex -lt 0 -or $invariantKindIndex -lt 0) {
                            for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                                switch ($cells[$idx]) {
                                    'INV ID' { $invariantIdIndex = $idx }
                                    'Lifecycle Ref' { $invariantLifecycleIndex = $idx }
                                    'Rule Kind' { $invariantKindIndex = $idx }
                                }
                            }
                            if ($invariantLifecycleIndex -ge 0 -and $invariantKindIndex -ge 0) {
                                $invariantHeaderSeen = $true
                            }
                            continue
                        }
                        if (Test-MarkdownSeparatorRow -Cells $cells) {
                            continue
                        }
                        if ($invariantLifecycleIndex -ge $cells.Count -or $invariantKindIndex -ge $cells.Count) {
                            continue
                        }
                        $lifecycleRef = Normalize-MarkdownScalar -Value $cells[$invariantLifecycleIndex]
                        $ruleKind = Normalize-RuleToken -Value $cells[$invariantKindIndex]
                        if ([string]::IsNullOrWhiteSpace($lifecycleRef) -or [string]::IsNullOrWhiteSpace($ruleKind)) {
                            continue
                        }
                        if ($invariantIdIndex -ge 0 -and $invariantIdIndex -lt $cells.Count) {
                            $invId = Normalize-MarkdownScalar -Value $cells[$invariantIdIndex]
                            if (-not [string]::IsNullOrWhiteSpace($invId)) {
                                $invIds[$invId] = $lineNumber
                            }
                        }
                        switch ($ruleKind) {
                            'allowed-transition' { $invariantAllowed[$lifecycleRef] = 1 + [int]($invariantAllowed[$lifecycleRef] ?? 0) }
                            'forbidden-transition' { $invariantForbidden[$lifecycleRef] = 1 + [int]($invariantForbidden[$lifecycleRef] ?? 0) }
                            'key-invariant' { $invariantKey[$lifecycleRef] = 1 + [int]($invariantKey[$lifecycleRef] ?? 0) }
                        }
                        continue
                    }

                    if ($currentTable -eq 'state_transition_table') {
                        if ($transitionLifecycleIndex -lt 0) {
                            for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                                if ($cells[$idx] -eq 'Lifecycle Ref') {
                                    $transitionLifecycleIndex = $idx
                                    break
                                }
                            }
                            if ($transitionLifecycleIndex -ge 0) {
                                $transitionHeaderSeen = $true
                            }
                            continue
                        }
                        if (Test-MarkdownSeparatorRow -Cells $cells) {
                            continue
                        }
                        if ($transitionLifecycleIndex -ge $cells.Count) {
                            continue
                        }
                        $lifecycleRef = Normalize-MarkdownScalar -Value $cells[$transitionLifecycleIndex]
                        if ([string]::IsNullOrWhiteSpace($lifecycleRef)) {
                            continue
                        }
                        $transitionRows[$lifecycleRef] = 1 + [int]($transitionRows[$lifecycleRef] ?? 0)
                        continue
                    }

                    if ($currentTable -eq 'transition_pseudocode') {
                        if ($pseudocodeLifecycleIndex -lt 0) {
                            for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                                if ($cells[$idx] -eq 'Lifecycle Ref') {
                                    $pseudocodeLifecycleIndex = $idx
                                    break
                                }
                            }
                            if ($pseudocodeLifecycleIndex -ge 0) {
                                $pseudocodeHeaderSeen = $true
                            }
                            continue
                        }
                        if (Test-MarkdownSeparatorRow -Cells $cells) {
                            continue
                        }
                        if ($pseudocodeLifecycleIndex -ge $cells.Count) {
                            continue
                        }
                        $lifecycleRef = Normalize-MarkdownScalar -Value $cells[$pseudocodeLifecycleIndex]
                        if ([string]::IsNullOrWhiteSpace($lifecycleRef)) {
                            continue
                        }
                        $pseudocodeRows[$lifecycleRef] = 1 + [int]($pseudocodeRows[$lifecycleRef] ?? 0)
                    }
                }

                if ($lifecycleSummaryLine -eq 0 -or -not $summaryHeaderSeen) {
                    Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycleSummaryLine -Message "$($row.message) Missing ``### Lifecycle Summary`` table." -Remediation $row.remediation
                    continue
                }
                if ($invariantCatalogLine -eq 0 -or -not $invariantHeaderSeen) {
                    Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $invariantCatalogLine -Message "$($row.message) Missing ``### Invariant Catalog`` table." -Remediation $row.remediation
                }
                if ($transitionTableLine -eq 0 -or -not $transitionHeaderSeen) {
                    Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $transitionTableLine -Message "$($row.message) Missing ``### State Transition Table`` table." -Remediation $row.remediation
                }
                if ($lifecycleRows.Count -eq 0) {
                    Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycleSummaryLine -Message "$($row.message) ``Lifecycle Summary`` has no lifecycle rows." -Remediation $row.remediation
                    continue
                }

                foreach ($lifecycleRef in $lifecycleRows.Keys) {
                    $lifecycle = $lifecycleRows[$lifecycleRef]
                    if ([string]::IsNullOrWhiteSpace($lifecycle.StateOwner) -or $lifecycle.StateOwner -eq 'N/A' -or $lifecycle.StateOwner -eq '[none]') {
                        Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycle.Line -Message "$($row.message) Lifecycle Ref $lifecycleRef is missing ``State Owner`` closure in ``Lifecycle Summary``." -Remediation $row.remediation
                    } else {
                        $ownerRefs = @(Get-SemanticRefTokens -Value $lifecycle.StateOwner -Pattern '(SSE|OSA)-[A-Za-z0-9_.-]+')
                        if ($ownerRefs.Count -gt 0) {
                            $resolvedOwnerRefCount = 0
                            $unresolvedOwnerRefs = New-Object System.Collections.Generic.List[string]
                            foreach ($ownerRef in $ownerRefs) {
                                if ($ownerRef -like 'OSA-*') {
                                    if ($osaIds.ContainsKey($ownerRef)) {
                                        $resolvedOwnerRefCount++
                                    } else {
                                        $unresolvedOwnerRefs.Add($ownerRef) | Out-Null
                                    }
                                } elseif ($ownerRef -like 'SSE-*') {
                                    if ($sseIds.ContainsKey($ownerRef)) {
                                        $resolvedOwnerRefCount++
                                    } else {
                                        $unresolvedOwnerRefs.Add($ownerRef) | Out-Null
                                    }
                                }
                            }
                            if ($resolvedOwnerRefCount -eq 0) {
                                Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycle.Line -Message "$($row.message) Lifecycle Ref $lifecycleRef ``State Owner`` does not resolve to existing ``SSE/OSA`` refs: $($unresolvedOwnerRefs -join ',')." -Remediation $row.remediation
                            }
                        } else {
                            $ownerKey = (Normalize-MarkdownScalar -Value $lifecycle.StateOwner).ToLowerInvariant()
                            if (-not [string]::IsNullOrWhiteSpace($ownerKey) -and -not $osaOwnerValues.ContainsKey($ownerKey)) {
                                Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycle.Line -Message "$($row.message) Lifecycle Ref $lifecycleRef ``State Owner`` must map to an existing ``SSE/OSA`` owner row; no matching ``Owner / Source Alignment`` owner was found." -Remediation $row.remediation
                            }
                        }
                    }

                    if ([string]::IsNullOrWhiteSpace($lifecycle.Invariants) -or $lifecycle.Invariants -notmatch 'INV-') {
                        Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycle.Line -Message "$($row.message) Lifecycle Ref $lifecycleRef is missing concrete ``Invariant Ref(s)`` in ``Lifecycle Summary``." -Remediation $row.remediation
                    }

                    if ($lifecycle.Model -notin @('lightweight', 'fsm')) {
                        Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycle.Line -Message "$($row.message) Lifecycle Ref $lifecycleRef uses invalid ``Required Model`` value '$($lifecycle.Model)'; expected ``lightweight`` or ``fsm``." -Remediation $row.remediation
                        continue
                    }

                    if ($lifecycle.Model -eq 'lightweight') {
                        if ([int]($transitionRows[$lifecycleRef] ?? 0) -eq 0) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycle.Line -Message "$($row.message) Lifecycle Ref $lifecycleRef is ``lightweight`` but ``State Transition Table`` has no rows for it." -Remediation $row.remediation
                        }
                        if ([int]($invariantAllowed[$lifecycleRef] ?? 0) -eq 0) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycle.Line -Message "$($row.message) Lifecycle Ref $lifecycleRef is ``lightweight`` but ``Invariant Catalog`` is missing an ``allowed-transition`` row." -Remediation $row.remediation
                        }
                        if ([int]($invariantForbidden[$lifecycleRef] ?? 0) -eq 0) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycle.Line -Message "$($row.message) Lifecycle Ref $lifecycleRef is ``lightweight`` but ``Invariant Catalog`` is missing a ``forbidden-transition`` row." -Remediation $row.remediation
                        }
                        if ([int]($invariantKey[$lifecycleRef] ?? 0) -eq 0) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycle.Line -Message "$($row.message) Lifecycle Ref $lifecycleRef is ``lightweight`` but ``Invariant Catalog`` is missing a ``key-invariant`` row." -Remediation $row.remediation
                        }
                    }

                    if ($lifecycle.Model -eq 'fsm') {
                        if ([int]($transitionRows[$lifecycleRef] ?? 0) -eq 0) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycle.Line -Message "$($row.message) Lifecycle Ref $lifecycleRef is ``fsm`` but ``State Transition Table`` has no rows for it." -Remediation $row.remediation
                        }
                        if ($transitionPseudocodeLine -eq 0 -or -not $pseudocodeHeaderSeen -or [int]($pseudocodeRows[$lifecycleRef] ?? 0) -eq 0) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycle.Line -Message "$($row.message) Lifecycle Ref $lifecycleRef is ``fsm`` but ``Transition Pseudocode`` is missing required rows." -Remediation $row.remediation
                        }
                        if (-not $hasStateDiagram) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line ($(if ($stateDiagramLine -gt 0) { $stateDiagramLine } else { $lifecycle.Line })) -Message "$($row.message) Lifecycle Ref $lifecycleRef is ``fsm`` but no ``stateDiagram-v2`` was found." -Remediation $row.remediation
                        }
                        if ([int]($invariantKey[$lifecycleRef] ?? 0) -eq 0) {
                            Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lifecycle.Line -Message "$($row.message) Lifecycle Ref $lifecycleRef is ``fsm`` but ``Invariant Catalog`` is missing a ``key-invariant`` row." -Remediation $row.remediation
                        }
                    }
                }

                foreach ($dccId in $dccIds.Keys) {
                    $refsValue = $dccRequiredRefsById[$dccId]
                    $lineNumber = [int]($dccLines[$dccId] ?? 0)
                    $dccRefs = @(Get-SemanticRefTokens -Value $refsValue -Pattern '(SSE|OSA|SFV|LC|INV|DCC)-[A-Za-z0-9_.-]+')
                    if ($dccRefs.Count -eq 0) {
                        Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lineNumber -Message "$($row.message) DCC row $dccId is missing resolvable ``Required Shared Semantic Ref(s)`` tokens (``SSE/OSA/SFV/LC/INV/DCC-*``)." -Remediation $row.remediation
                        continue
                    }
                    $unresolved = New-Object System.Collections.Generic.List[string]
                    foreach ($requiredRef in $dccRefs) {
                        switch -Regex ($requiredRef) {
                            '^SSE-' { if (-not $sseIds.ContainsKey($requiredRef)) { $unresolved.Add($requiredRef) | Out-Null } }
                            '^OSA-' { if (-not $osaIds.ContainsKey($requiredRef)) { $unresolved.Add($requiredRef) | Out-Null } }
                            '^SFV-' { if (-not $sfvIds.ContainsKey($requiredRef)) { $unresolved.Add($requiredRef) | Out-Null } }
                            '^LC-' { if (-not $lcIds.ContainsKey($requiredRef)) { $unresolved.Add($requiredRef) | Out-Null } }
                            '^INV-' { if (-not $invIds.ContainsKey($requiredRef)) { $unresolved.Add($requiredRef) | Out-Null } }
                            '^DCC-' { if (-not $dccIds.ContainsKey($requiredRef)) { $unresolved.Add($requiredRef) | Out-Null } }
                        }
                    }
                    if ($unresolved.Count -gt 0) {
                        Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lineNumber -Message "$($row.message) DCC row $dccId references unknown shared-semantic refs: $($unresolved -join ',')." -Remediation $row.remediation
                    }
                }
            }
        }

        'data_model_single_binding_shared_warning' {
            foreach ($file in $matched) {
                $lines = @(Get-Content -Path $file.FullPath -ErrorAction Stop)
                $currentSection = ''
                $inSseTable = $false
                $sseIdIndex = -1
                $consumedIndex = -1
                $whyIndex = -1

                for ($i = 0; $i -lt $lines.Count; $i++) {
                    $lineNumber = $i + 1
                    $line = $lines[$i]
                    $trimmed = $line.Trim()

                    $h2Match = [regex]::Match($trimmed, '^##\s+(.+)$')
                    if ($h2Match.Success) {
                        $currentSection = $h2Match.Groups[1].Value.Trim()
                        $inSseTable = $false
                        $sseIdIndex = -1
                        $consumedIndex = -1
                        $whyIndex = -1
                        continue
                    }

                    if ($currentSection -ne 'Shared Semantic Elements (SSE)' -and $currentSection -ne 'Shared Semantic Elements') {
                        continue
                    }

                    $cells = @(Get-MarkdownCells -Line $line)
                    if ($cells.Count -eq 0) {
                        $inSseTable = $false
                        $sseIdIndex = -1
                        $consumedIndex = -1
                        $whyIndex = -1
                        continue
                    }

                    if (-not $inSseTable) {
                        for ($idx = 0; $idx -lt $cells.Count; $idx++) {
                            switch ($cells[$idx]) {
                                'SSE ID' { $sseIdIndex = $idx }
                                'Consumed By BindingRowID(s)' { $consumedIndex = $idx }
                                'Why Not Contract-Local' { $whyIndex = $idx }
                            }
                        }
                        if ($sseIdIndex -ge 0 -and $consumedIndex -ge 0 -and $whyIndex -ge 0) {
                            $inSseTable = $true
                        }
                        continue
                    }

                    if (Test-MarkdownSeparatorRow -Cells $cells) {
                        continue
                    }

                    if ($sseIdIndex -ge $cells.Count -or $consumedIndex -ge $cells.Count -or $whyIndex -ge $cells.Count) {
                        continue
                    }

                    $sseId = Normalize-MarkdownScalar -Value $cells[$sseIdIndex]
                    if ([string]::IsNullOrWhiteSpace($sseId)) {
                        continue
                    }
                    $consumedCell = Normalize-MarkdownListCell -Value $cells[$consumedIndex]
                    $whyNotLocal = Normalize-MarkdownScalar -Value $cells[$whyIndex]
                    $bindingSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
                    foreach ($item in ($consumedCell -split ',')) {
                        $bindingId = Normalize-MarkdownScalar -Value $item
                        if (-not [string]::IsNullOrWhiteSpace($bindingId)) {
                            [void]$bindingSet.Add($bindingId)
                        }
                    }

                    if ($bindingSet.Count -eq 1 -and (Test-SingleBindingReasonWeak -Reason $whyNotLocal)) {
                        Add-Finding -RuleId $row.id -Severity $row.severity -File $file.RelPath -Line $lineNumber -Message "$($row.message) SSE row $sseId is consumed by a single binding but ``Why Not Contract-Local`` rationale is weak (``$whyNotLocal``)." -Remediation $row.remediation
                    }
                }
            }
        }

        default {
            Add-Finding -RuleId $row.id -Severity $row.severity -File $row.glob -Line 0 -Message "Unsupported rule kind: $($row.kind)" -Remediation 'Use one of: file_regex_forbidden, file_regex_required_any, component_symbols_exist, anchor_status_allowed_values, northbound_controller_required, repo_anchor_paths_exist, plan_status_consistency, binding_projection_stable_only, binding_tuple_projection_sync, shared_semantic_reuse_enum, anchor_strategy_evidence_required, data_model_semantic_closure, data_model_single_binding_shared_warning.'
        }
    }
}

$payload = [PSCustomObject][ordered]@{
    feature_dir          = $featureRoot
    rules_total          = $rulesTotal
    rules_evaluated      = $rulesEvaluated
    findings_total       = [int]$findings.Count
    findings_by_severity = $severityCounts
    findings             = @($findings.ToArray())
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

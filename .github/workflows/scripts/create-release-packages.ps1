#!/usr/bin/env pwsh
#requires -Version 7.0

<#
.SYNOPSIS
    Build Spec Kit template release archives for each supported AI assistant and script type.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Version,

    [Parameter(Mandatory = $false)]
    [string]$Agents = "",

    [Parameter(Mandatory = $false)]
    [string]$Scripts = ""
)

$ErrorActionPreference = "Stop"

if ($Version -notmatch '^v\d+\.\d+\.\d+$') {
    Write-Error "Version must look like v0.0.0"
    exit 1
}

Write-Host "Building release packages for $Version"

$ScriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$AgentKeysScript = Join-Path $ScriptRoot "list-agent-config-keys.py"

$GenReleasesDir = ".genreleases"
if (Test-Path $GenReleasesDir) {
    Remove-Item -Path $GenReleasesDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $GenReleasesDir -Force | Out-Null

$TemplateCommandCount = @(Get-ChildItem -Path "templates/commands/*.md" -File -ErrorAction SilentlyContinue).Count
if ($TemplateCommandCount -eq 0) {
    Write-Error "No command templates found under templates/commands"
    exit 1
}

function Rewrite-Paths {
    param([string]$Content)

    $Content = $Content -replace '(/?)\bmemory/', '.specify/memory/'
    $Content = $Content -replace '(/?)\bscripts/', '.specify/scripts/'
    $Content = $Content -replace '(/?)\btemplates/', '.specify/templates/'
    return $Content -replace '\.specify\.specify/', '.specify/'
}

function Validate-GeneratedCommandFiles {
    param(
        [string]$OutputDir,
        [string]$Extension,
        [string]$Agent
    )

    $pattern = "sdd.*.$Extension"
    $generatedCount = @(Get-ChildItem -Path $OutputDir -Filter $pattern -File -ErrorAction SilentlyContinue).Count
    if ($generatedCount -ne $TemplateCommandCount) {
        throw "Generated command count mismatch for $Agent ($Extension). expected=$TemplateCommandCount actual=$generatedCount dir=$OutputDir"
    }
}

function Validate-CopilotPromptFiles {
    param(
        [string]$AgentsDir,
        [string]$PromptsDir
    )

    $agentCount = @(Get-ChildItem -Path $AgentsDir -Filter "sdd.*.agent.md" -File -ErrorAction SilentlyContinue).Count
    $promptCount = @(Get-ChildItem -Path $PromptsDir -Filter "sdd.*.prompt.md" -File -ErrorAction SilentlyContinue).Count
    if ($agentCount -ne $promptCount) {
        throw "Generated Copilot prompt count mismatch. expected=$agentCount actual=$promptCount prompts_dir=$PromptsDir"
    }
}

function Validate-GeneratedKimiSkills {
    param(
        [string]$SkillsDir
    )

    $skillCount = @(
        Get-ChildItem -Path $SkillsDir -Recurse -File -Filter "SKILL.md" -ErrorAction SilentlyContinue |
            Where-Object { $_.DirectoryName -match [regex]::Escape($SkillsDir) + '[\\/]sdd\.[^\\/]+' }
    ).Count

    if ($skillCount -ne $TemplateCommandCount) {
        throw "Generated Kimi skill count mismatch. expected=$TemplateCommandCount actual=$skillCount dir=$SkillsDir"
    }
}

function Generate-Commands {
    param(
        [string]$Agent,
        [string]$Extension,
        [string]$ArgFormat,
        [string]$OutputDir,
        [string]$ScriptVariant
    )

    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    $templates = Get-ChildItem -Path "templates/commands/*.md" -File -ErrorAction SilentlyContinue

    foreach ($template in $templates) {
        $name = [System.IO.Path]::GetFileNameWithoutExtension($template.Name)
        $fileContent = (Get-Content -Path $template.FullName -Raw) -replace "`r`n", "`n"

        $description = ""
        if ($fileContent -match '(?m)^description:\s*(.+)$') {
            $description = $matches[1]
        }

        $scriptCommand = ""
        if ($fileContent -match "(?m)^\s*${ScriptVariant}:\s*(.+)$") {
            $scriptCommand = $matches[1]
        }
        if ([string]::IsNullOrEmpty($scriptCommand)) {
            if ($fileContent.Contains('{SCRIPT}')) {
                Write-Warning "No script command found for $ScriptVariant in $($template.Name)"
            }
            $scriptCommand = "(Missing script command for $ScriptVariant)"
        }

        $agentScriptCommand = ""
        if ($fileContent -match "(?ms)^agent_scripts:`n.*?^\s*${ScriptVariant}:\s*(.+?)$") {
            $agentScriptCommand = $matches[1].Trim()
        }

        $body = $fileContent.Replace('{SCRIPT}', $scriptCommand)
        if (-not [string]::IsNullOrEmpty($agentScriptCommand)) {
            $body = $body.Replace('{AGENT_SCRIPT}', $agentScriptCommand)
        }

        $lines = $body -split "`n"
        $outputLines = @()
        $inFrontmatter = $false
        $skipScripts = $false
        $dashCount = 0

        foreach ($line in $lines) {
            if ($line -match '^---$') {
                $outputLines += $line
                $dashCount++
                $inFrontmatter = ($dashCount -eq 1)
                continue
            }

            if ($inFrontmatter) {
                if ($line -match '^(scripts|agent_scripts):$') {
                    $skipScripts = $true
                    continue
                }
                if ($line -match '^[a-zA-Z].*:' -and $skipScripts) {
                    $skipScripts = $false
                }
                if ($skipScripts -and $line -match '^\s+') {
                    continue
                }
            }

            $outputLines += $line
        }

        $body = $outputLines -join "`n"
        $body = $body.Replace('{ARGS}', $ArgFormat)
        $body = $body.Replace('__AGENT__', $Agent)
        $body = Rewrite-Paths -Content $body

        $outputFile = Join-Path $OutputDir "sdd.$name.$Extension"
        switch ($Extension) {
            'toml' {
                $output = "description = `"$description`"`n`nprompt = `"`"`"`n$body`n`"`"`""
                Set-Content -Path $outputFile -Value $output -NoNewline
            }
            'md' { Set-Content -Path $outputFile -Value $body -NoNewline }
            'agent.md' { Set-Content -Path $outputFile -Value $body -NoNewline }
            default { throw "Unsupported extension '$Extension'." }
        }
    }

    Validate-GeneratedCommandFiles -OutputDir $OutputDir -Extension $Extension -Agent $Agent
}

function Generate-CopilotPrompts {
    param(
        [string]$AgentsDir,
        [string]$PromptsDir
    )

    New-Item -ItemType Directory -Path $PromptsDir -Force | Out-Null
    $agentFiles = Get-ChildItem -Path "$AgentsDir/sdd.*.agent.md" -File -ErrorAction SilentlyContinue

    foreach ($agentFile in $agentFiles) {
        $basename = $agentFile.Name -replace '\.agent\.md$', ''
        $promptFile = Join-Path $PromptsDir "$basename.prompt.md"
        $content = @"
---
agent: $basename
---
"@
        Set-Content -Path $promptFile -Value $content -NoNewline
    }

    Validate-CopilotPromptFiles -AgentsDir $AgentsDir -PromptsDir $PromptsDir
}

function New-KimiSkills {
    param(
        [string]$SkillsDir,
        [string]$ScriptVariant
    )

    $templates = Get-ChildItem -Path "templates/commands/*.md" -File -ErrorAction SilentlyContinue

    foreach ($template in $templates) {
        $name = [System.IO.Path]::GetFileNameWithoutExtension($template.Name)
        $skillName = "sdd.$name"
        $skillDir = Join-Path $SkillsDir $skillName
        New-Item -ItemType Directory -Path $skillDir -Force | Out-Null

        $fileContent = (Get-Content -Path $template.FullName -Raw) -replace "`r`n", "`n"

        $description = "Spec Kit: $name workflow"
        if ($fileContent -match '(?m)^description:\s*(.+)$') {
            $description = $matches[1]
        }

        $scriptCommand = "(Missing script command for $ScriptVariant)"
        if ($fileContent -match "(?m)^\s*${ScriptVariant}:\s*(.+)$") {
            $scriptCommand = $matches[1]
        } elseif ($fileContent.Contains('{SCRIPT}')) {
            Write-Warning "No script command found for $ScriptVariant in $($template.Name)"
        }

        $agentScriptCommand = ""
        if ($fileContent -match "(?ms)^agent_scripts:`n.*?^\s*${ScriptVariant}:\s*(.+?)$") {
            $agentScriptCommand = $matches[1].Trim()
        }

        $body = $fileContent.Replace('{SCRIPT}', $scriptCommand)
        if (-not [string]::IsNullOrEmpty($agentScriptCommand)) {
            $body = $body.Replace('{AGENT_SCRIPT}', $agentScriptCommand)
        }

        $lines = $body -split "`n"
        $outputLines = @()
        $inFrontmatter = $false
        $skipScripts = $false
        $dashCount = 0

        foreach ($line in $lines) {
            if ($line -match '^---$') {
                $outputLines += $line
                $dashCount++
                $inFrontmatter = ($dashCount -eq 1)
                continue
            }
            if ($inFrontmatter) {
                if ($line -match '^(scripts|agent_scripts):$') { $skipScripts = $true; continue }
                if ($line -match '^[a-zA-Z].*:' -and $skipScripts) { $skipScripts = $false }
                if ($skipScripts -and $line -match '^\s+') { continue }
            }
            $outputLines += $line
        }

        $body = $outputLines -join "`n"
        $body = $body.Replace('{ARGS}', '$ARGUMENTS')
        $body = $body.Replace('__AGENT__', 'kimi')
        $body = Rewrite-Paths -Content $body

        $templateBody = ""
        $fmCount = 0
        $inBody = $false
        foreach ($line in ($body -split "`n")) {
            if ($line -match '^---$') {
                $fmCount++
                if ($fmCount -eq 2) { $inBody = $true }
                continue
            }
            if ($inBody) { $templateBody += "$line`n" }
        }

        $skillContent = "---`nname: `"$skillName`"`ndescription: `"$description`"`n---`n`n$templateBody"
        Set-Content -Path (Join-Path $skillDir "SKILL.md") -Value $skillContent -NoNewline
    }

    Validate-GeneratedKimiSkills -SkillsDir $SkillsDir
}

function Build-Variant {
    param(
        [string]$Agent,
        [string]$Script
    )

    $baseDir = Join-Path $GenReleasesDir "sdd-${Agent}-package-${Script}"
    Write-Host "Building $Agent ($Script) package..."
    New-Item -ItemType Directory -Path $baseDir -Force | Out-Null

    $specDir = Join-Path $baseDir ".specify"
    New-Item -ItemType Directory -Path $specDir -Force | Out-Null

    if (Test-Path "memory") {
        Copy-Item -Path "memory" -Destination $specDir -Recurse -Force
    }

    if (Test-Path "scripts") {
        $scriptsDestDir = Join-Path $specDir "scripts"
        New-Item -ItemType Directory -Path $scriptsDestDir -Force | Out-Null

        switch ($Script) {
            'sh' {
                if (Test-Path "scripts/bash") {
                    Copy-Item -Path "scripts/bash" -Destination $scriptsDestDir -Recurse -Force
                }
            }
            'ps' {
                if (Test-Path "scripts/powershell") {
                    Copy-Item -Path "scripts/powershell" -Destination $scriptsDestDir -Recurse -Force
                }
            }
        }

        Get-ChildItem -Path "scripts" -File -ErrorAction SilentlyContinue | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination $scriptsDestDir -Force
        }
    }

    if (Test-Path "templates") {
        $templatesDestDir = Join-Path $specDir "templates"
        New-Item -ItemType Directory -Path $templatesDestDir -Force | Out-Null

        Get-ChildItem -Path "templates" -Recurse -File | Where-Object {
            $_.FullName -notmatch 'templates[/\\]commands[/\\]' -and $_.Name -ne 'vscode-settings.json'
        } | ForEach-Object {
            $relativePath = $_.FullName.Substring((Resolve-Path "templates").Path.Length + 1)
            $destFile = Join-Path $templatesDestDir $relativePath
            $destDir = Split-Path $destFile -Parent
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            Copy-Item -Path $_.FullName -Destination $destFile -Force
        }
    }

    switch ($Agent) {
        'claude' {
            $cmdDir = Join-Path $baseDir ".claude/commands"
            Generate-Commands -Agent 'claude' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'gemini' {
            $cmdDir = Join-Path $baseDir ".gemini/commands"
            Generate-Commands -Agent 'gemini' -Extension 'toml' -ArgFormat '{{args}}' -OutputDir $cmdDir -ScriptVariant $Script
            if (Test-Path "agent_templates/gemini/GEMINI.md") {
                Copy-Item -Path "agent_templates/gemini/GEMINI.md" -Destination (Join-Path $baseDir "GEMINI.md")
            }
        }
        'copilot' {
            $agentsDir = Join-Path $baseDir ".github/agents"
            Generate-Commands -Agent 'copilot' -Extension 'agent.md' -ArgFormat '$ARGUMENTS' -OutputDir $agentsDir -ScriptVariant $Script
            Generate-CopilotPrompts -AgentsDir $agentsDir -PromptsDir (Join-Path $baseDir ".github/prompts")
            $vscodeDir = Join-Path $baseDir ".vscode"
            New-Item -ItemType Directory -Path $vscodeDir -Force | Out-Null
            if (Test-Path "templates/vscode-settings.json") {
                Copy-Item -Path "templates/vscode-settings.json" -Destination (Join-Path $vscodeDir "settings.json")
            }
        }
        'cursor-agent' {
            $cmdDir = Join-Path $baseDir ".cursor/commands"
            Generate-Commands -Agent 'cursor-agent' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'cline' {
            $cmdDir = Join-Path $baseDir ".clinerules/workflows"
            Generate-Commands -Agent 'cline' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'qwen' {
            $cmdDir = Join-Path $baseDir ".qwen/commands"
            Generate-Commands -Agent 'qwen' -Extension 'toml' -ArgFormat '{{args}}' -OutputDir $cmdDir -ScriptVariant $Script
            if (Test-Path "agent_templates/qwen/QWEN.md") {
                Copy-Item -Path "agent_templates/qwen/QWEN.md" -Destination (Join-Path $baseDir "QWEN.md")
            }
        }
        'opencode' {
            $cmdDir = Join-Path $baseDir ".opencode/command"
            Generate-Commands -Agent 'opencode' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'windsurf' {
            $cmdDir = Join-Path $baseDir ".windsurf/workflows"
            Generate-Commands -Agent 'windsurf' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'codex' {
            $cmdDir = Join-Path $baseDir ".codex/prompts"
            Generate-Commands -Agent 'codex' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'kilocode' {
            $cmdDir = Join-Path $baseDir ".kilocode/rules"
            Generate-Commands -Agent 'kilocode' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'auggie' {
            $cmdDir = Join-Path $baseDir ".augment/rules"
            Generate-Commands -Agent 'auggie' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'roo' {
            $cmdDir = Join-Path $baseDir ".roo/commands"
            Generate-Commands -Agent 'roo' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'codebuddy' {
            $cmdDir = Join-Path $baseDir ".codebuddy/commands"
            Generate-Commands -Agent 'codebuddy' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'amp' {
            $cmdDir = Join-Path $baseDir ".agents/commands"
            Generate-Commands -Agent 'amp' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'kiro-cli' {
            $cmdDir = Join-Path $baseDir ".kiro/prompts"
            Generate-Commands -Agent 'kiro-cli' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'bob' {
            $cmdDir = Join-Path $baseDir ".bob/commands"
            Generate-Commands -Agent 'bob' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'qodercli' {
            $cmdDir = Join-Path $baseDir ".qoder/commands"
            Generate-Commands -Agent 'qodercli' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'shai' {
            $cmdDir = Join-Path $baseDir ".shai/commands"
            Generate-Commands -Agent 'shai' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'tabnine' {
            $cmdDir = Join-Path $baseDir ".tabnine/agent/commands"
            Generate-Commands -Agent 'tabnine' -Extension 'toml' -ArgFormat '{{args}}' -OutputDir $cmdDir -ScriptVariant $Script
            $tabnineTemplate = Join-Path 'agent_templates' 'tabnine/TABNINE.md'
            if (Test-Path $tabnineTemplate) {
                Copy-Item -Path $tabnineTemplate -Destination (Join-Path $baseDir "TABNINE.md")
            }
        }
        'agy' {
            $cmdDir = Join-Path $baseDir ".agent/workflows"
            Generate-Commands -Agent 'agy' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'vibe' {
            $cmdDir = Join-Path $baseDir ".vibe/prompts"
            Generate-Commands -Agent 'vibe' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'kimi' {
            $skillsDir = Join-Path $baseDir ".kimi/skills"
            New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null
            New-KimiSkills -SkillsDir $skillsDir -ScriptVariant $Script
        }
        'generic' {
            $cmdDir = Join-Path $baseDir ".sdd/commands"
            Generate-Commands -Agent 'generic' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        default {
            throw "Unsupported agent '$Agent'."
        }
    }

    $zipFile = Join-Path $GenReleasesDir "spec-kit-template-${Agent}-${Script}-${Version}.zip"
    $archiveItems = @(
        Get-ChildItem -Path $baseDir -Force -ErrorAction SilentlyContinue | ForEach-Object {
            $_.FullName
        }
    )
    if ($archiveItems.Count -eq 0) {
        throw "No files generated under $baseDir for agent '$Agent' ($Script)"
    }
    Compress-Archive -Path $archiveItems -DestinationPath $zipFile -Force
    Write-Host "Created $zipFile"
}

function Get-AllAgents {
    if (-not (Test-Path $AgentKeysScript)) {
        throw "Agent key helper not found: $AgentKeysScript"
    }

    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    }
    if (-not $pythonCmd) {
        throw "python3 or python is required to load AGENT_CONFIG keys"
    }

    $agentKeys = & $pythonCmd.Source $AgentKeysScript
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to load AGENT_CONFIG keys from $AgentKeysScript"
    }

    $agentKeys = @($agentKeys | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($agentKeys.Count -eq 0) {
        throw "No agents discovered from AGENT_CONFIG"
    }

    return $agentKeys
}

$AllAgents = Get-AllAgents
$AllScripts = @('sh', 'ps')

function Normalize-List {
    param([string]$Input)

    if ([string]::IsNullOrEmpty($Input)) {
        return @()
    }

    return ($Input -split '[,\s]+' | Where-Object { $_ } | Select-Object -Unique)
}

function Validate-Subset {
    param(
        [string]$Type,
        [string[]]$Allowed,
        [string[]]$Items
    )

    $ok = $true
    foreach ($item in $Items) {
        if ($item -notin $Allowed) {
            Write-Error "Unknown $Type '$item' (allowed: $($Allowed -join ', '))"
            $ok = $false
        }
    }
    return $ok
}

if (-not [string]::IsNullOrEmpty($Agents)) {
    $AgentList = Normalize-List -Input $Agents
    if (-not (Validate-Subset -Type 'agent' -Allowed $AllAgents -Items $AgentList)) {
        exit 1
    }
} else {
    $AgentList = $AllAgents
}

if (-not [string]::IsNullOrEmpty($Scripts)) {
    $ScriptList = Normalize-List -Input $Scripts
    if (-not (Validate-Subset -Type 'script' -Allowed $AllScripts -Items $ScriptList)) {
        exit 1
    }
} else {
    $ScriptList = $AllScripts
}

Write-Host "Agents: $($AgentList -join ', ')"
Write-Host "Scripts: $($ScriptList -join ', ')"

foreach ($agent in $AgentList) {
    foreach ($script in $ScriptList) {
        Build-Variant -Agent $agent -Script $script
    }
}

Write-Host "`nArchives in ${GenReleasesDir}:"
Get-ChildItem -Path $GenReleasesDir -Filter "spec-kit-template-*-${Version}.zip" | ForEach-Object {
    Write-Host "  $($_.Name)"
}

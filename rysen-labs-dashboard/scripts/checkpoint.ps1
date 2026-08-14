param(
    [Parameter(Mandatory = $true)]
    [string]$Project,

    [Parameter(Mandatory = $true)]
    [string]$Task,

    [string]$Checkpoint,

    [ValidateSet("todo", "in_progress", "blocked", "done", "complete")]
    [string]$Status = "done",

    [string]$Result = "passed",

    [string]$Notes,

    [string]$Sprint = "",

    [string]$CommitSha,

    [string]$RepositoryPath = ".",

    [string]$DashboardRoot = "",

    [string]$ValidationCommand,

    [string]$PythonExe = "",

    [switch]$SkipValidation,

    [switch]$AllowDirty,

    [switch]$Apply,

    [string]$UpdateId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RootPath {
    param([string]$PathValue)
    return (Resolve-Path -LiteralPath $PathValue).Path
}

function Invoke-Git {
    param(
        [string]$RepoPath,
        [string[]]$Arguments
    )
    $output = & git -C $RepoPath @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed: $output"
    }
    return ($output | Out-String).Trim()
}

function Get-SafeSlug {
    param([string]$Value)
    $slug = $Value.Trim().ToLowerInvariant() -replace "[^a-z0-9_-]+", "-"
    $slug = $slug.Trim("-")
    if ([string]::IsNullOrWhiteSpace($slug)) {
        throw "Value '$Value' cannot be converted to a safe slug."
    }
    return $slug
}

function Get-CheckpointConfig {
    param([string]$Root)
    $configPath = Join-Path $Root "config/checkpoints.json"
    if (-not (Test-Path -LiteralPath $configPath)) {
        return $null
    }
    return Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
}

function Get-ConfiguredValidationCommand {
    param(
        [object]$Config,
        [string]$ProjectId
    )
    if ($null -eq $Config -or $null -eq $Config.projects) {
        return ""
    }
    $projectConfig = $Config.projects.PSObject.Properties[$ProjectId]
    if ($null -eq $projectConfig) {
        return ""
    }
    return [string]$projectConfig.Value.validation_command
}

function Invoke-ValidationCommand {
    param(
        [string]$RepoPath,
        [string]$Command
    )
    if ([string]::IsNullOrWhiteSpace($Command)) {
        return "No validation command configured."
    }
    Push-Location -LiteralPath $RepoPath
    try {
        $output = & powershell.exe -NoProfile -Command $Command 2>&1
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) {
            throw "Validation command failed with exit code $exitCode. $output"
        }
    }
    finally {
        Pop-Location
    }
    return $Command
}

function Write-SprintUpdateFile {
    param(
        [string]$Path,
        [hashtable]$Payload
    )
    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    $json = $Payload | ConvertTo-Json -Depth 10
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $json, $utf8NoBom)
}

function Get-PythonExecutable {
    param([string]$Root, [string]$RequestedPython)
    if (-not [string]::IsNullOrWhiteSpace($RequestedPython)) {
        return $RequestedPython
    }
    $venvPython = Join-Path $Root ".venv/Scripts/python.exe"
    if (Test-Path -LiteralPath $venvPython) {
        return $venvPython
    }
    return "python"
}

try {
    if ([string]::IsNullOrWhiteSpace($DashboardRoot)) {
        $DashboardRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
    }
    else {
        $DashboardRoot = Resolve-RootPath $DashboardRoot
    }
    $RepositoryPath = Resolve-RootPath $RepositoryPath

    $projectId = Get-SafeSlug $Project
    $taskId = Get-SafeSlug $Task
    $checkpointId = if ([string]::IsNullOrWhiteSpace($Checkpoint)) { "" } else { Get-SafeSlug $Checkpoint }
    $normalizedStatus = if ($Status -eq "complete") { "done" } else { $Status }

    $config = Get-CheckpointConfig -Root $DashboardRoot
    $configuredValidation = Get-ConfiguredValidationCommand -Config $config -ProjectId $projectId
    if ([string]::IsNullOrWhiteSpace($ValidationCommand)) {
        $ValidationCommand = $configuredValidation
    }

    $gitRoot = Invoke-Git -RepoPath $RepositoryPath -Arguments @("rev-parse", "--show-toplevel")
    $branch = Invoke-Git -RepoPath $RepositoryPath -Arguments @("branch", "--show-current")
    if ([string]::IsNullOrWhiteSpace($CommitSha)) {
        $CommitSha = Invoke-Git -RepoPath $RepositoryPath -Arguments @("rev-parse", "HEAD")
    }
    $commitMessage = Invoke-Git -RepoPath $RepositoryPath -Arguments @("log", "-1", "--pretty=%s", $CommitSha)
    $dirtyStatus = Invoke-Git -RepoPath $RepositoryPath -Arguments @("status", "--porcelain")
    $isDirty = -not [string]::IsNullOrWhiteSpace($dirtyStatus)
    if ($isDirty -and -not $AllowDirty) {
        throw "Working tree is dirty. Commit or clean changes first, or rerun with -AllowDirty for an evidence-only checkpoint."
    }

    $validationSummary = "Skipped by -SkipValidation."
    if (-not $SkipValidation) {
        $validationSummary = Invoke-ValidationCommand -RepoPath $RepositoryPath -Command $ValidationCommand
    }

    $timestamp = (Get-Date).ToUniversalTime().ToString("o")
    $repoName = Split-Path -Leaf $gitRoot
    if ([string]::IsNullOrWhiteSpace($UpdateId)) {
        $shortCommit = if ($CommitSha.Length -ge 12) { $CommitSha.Substring(0, 12) } else { $CommitSha }
        $target = if ([string]::IsNullOrWhiteSpace($checkpointId)) { $taskId } else { $checkpointId }
        $UpdateId = "$projectId-$target-$normalizedStatus-$shortCommit"
    }

    $evidence = @{
        validation = $validationSummary
        commit = $CommitSha
        branch = $branch
        repository = $repoName
        commit_message = $commitMessage
        timestamp = $timestamp
        working_tree = if ($isDirty) { "dirty" } else { "clean" }
    }
    if (-not [string]::IsNullOrWhiteSpace($Notes)) {
        $evidence.notes = $Notes
    }
    if (-not [string]::IsNullOrWhiteSpace($Sprint)) {
        $evidence.sprint = $Sprint
    }

    $sprintUpdate = @{
        update_id = $UpdateId
        sprint_update = @{
            project = $projectId
            task = $taskId
            checkpoint = if ([string]::IsNullOrWhiteSpace($checkpointId)) { $null } else { $checkpointId }
            result = $Result
            evidence = $evidence
            recommendation = @{
                status = $normalizedStatus
            }
        }
    }

    $updatesRoot = if ([string]::IsNullOrWhiteSpace($env:SPRINT_UPDATES_DIR)) {
        Join-Path $DashboardRoot "roadmap/updates"
    }
    else {
        $env:SPRINT_UPDATES_DIR
    }
    $pendingName = "$UpdateId.json"
    $pendingPath = Join-Path $updatesRoot (Join-Path "pending" $pendingName)
    Write-SprintUpdateFile -Path $pendingPath -Payload $sprintUpdate

    Write-Host "Created sprint update: $pendingPath"
    Write-Host "Project: $projectId"
    Write-Host "Task: $taskId"
    if (-not [string]::IsNullOrWhiteSpace($checkpointId)) {
        Write-Host "Checkpoint: $checkpointId"
    }
    Write-Host "Recommended status: $normalizedStatus"
    Write-Host "Commit: $CommitSha"

    Push-Location -LiteralPath $DashboardRoot
    try {
        $processorMode = if ($Apply) { "--apply" } else { "--dry-run" }
        $python = Get-PythonExecutable -Root $DashboardRoot -RequestedPython $PythonExe
        & $python scripts/process_sprint_updates.py $processorMode --file $pendingPath
        if ($LASTEXITCODE -ne 0) {
            throw "Sprint update processor failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }

    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}

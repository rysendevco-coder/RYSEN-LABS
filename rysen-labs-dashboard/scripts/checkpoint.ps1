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

    [switch]$CommitSprintState,

    [switch]$PushSprintState,

    [string]$SprintStateBranch = "develop",

    [string]$ExpectedRemote = "origin",

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

function Invoke-GitAllowFailure {
    param(
        [string]$RepoPath,
        [string[]]$Arguments
    )
    $output = & git -C $RepoPath @Arguments 2>&1
    return @{
        ExitCode = $LASTEXITCODE
        Output = ($output | Out-String).Trim()
    }
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

function Assert-GitDiffCheck {
    param([string]$RepoPath)
    $output = & git -C $RepoPath diff --check 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git diff --check failed: $output"
    }
}

function Assert-CommitExists {
    param(
        [string]$RepoPath,
        [string]$Sha
    )
    $result = Invoke-GitAllowFailure -RepoPath $RepoPath -Arguments @("cat-file", "-e", "$Sha^{commit}")
    if ($result.ExitCode -ne 0) {
        throw "Project commit '$Sha' does not exist."
    }
}

function Assert-BranchSynchronized {
    param(
        [string]$RepoPath,
        [string]$RemoteName
    )
    $remote = Invoke-GitAllowFailure -RepoPath $RepoPath -Arguments @("remote", "get-url", $RemoteName)
    if ($remote.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($remote.Output)) {
        throw "Expected remote '$RemoteName' is not configured."
    }
    $upstream = Invoke-GitAllowFailure -RepoPath $RepoPath -Arguments @("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if ($upstream.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($upstream.Output)) {
        throw "Project branch is not tracking an upstream branch."
    }
    $fetch = Invoke-GitAllowFailure -RepoPath $RepoPath -Arguments @("fetch", "--quiet", $RemoteName)
    if ($fetch.ExitCode -ne 0) {
        throw "Could not fetch expected remote '$RemoteName': $($fetch.Output)"
    }
    $counts = Invoke-Git -RepoPath $RepoPath -Arguments @("rev-list", "--left-right", "--count", "HEAD...@{u}")
    $parts = $counts -split "\s+"
    if ($parts.Count -lt 2 -or $parts[0] -ne "0" -or $parts[1] -ne "0") {
        throw "Project branch is not synchronized with upstream; ahead=$($parts[0]) behind=$($parts[1])."
    }
}

function Assert-DashboardCleanBeforeMutation {
    param([string]$Root)
    $status = Invoke-Git -RepoPath $Root -Arguments @("status", "--porcelain", "--", ".")
    if (-not [string]::IsNullOrWhiteSpace($status)) {
        throw "RYSEN-LABS dashboard working tree contains unexpected changes before sprint mutation: $status"
    }
}

function Assert-DashboardBranch {
    param(
        [string]$Root,
        [string]$ExpectedBranch
    )
    $branch = Invoke-Git -RepoPath $Root -Arguments @("branch", "--show-current")
    if ($branch -ne $ExpectedBranch) {
        throw "RYSEN-LABS dashboard branch '$branch' is not approved branch '$ExpectedBranch'."
    }
}

function Assert-DashboardChangesExpected {
    param([string]$Root)
    $status = Invoke-Git -RepoPath $Root -Arguments @("status", "--porcelain", "--", ".")
    if ([string]::IsNullOrWhiteSpace($status)) {
        throw "No RYSEN-LABS sprint-state changes found to commit."
    }
    foreach ($line in ($status -split "`r?`n")) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        $path = $line.Substring(3).Replace("\", "/")
        $allowed = (
            $path -eq "roadmap/current_sprint.yaml" -or
            $path.StartsWith("roadmap/updates/processed/") -or
            $path.StartsWith("roadmap/updates/rejected/")
        )
        if (-not $allowed) {
            throw "Unexpected RYSEN-LABS change in checkpoint transaction: $line"
        }
    }

    $diff = Invoke-Git -RepoPath $Root -Arguments @("diff", "--unified=0", "--", "roadmap/current_sprint.yaml")
    foreach ($line in ($diff -split "`r?`n")) {
        if ($line.StartsWith("+++") -or $line.StartsWith("---") -or -not ($line.StartsWith("+") -or $line.StartsWith("-"))) {
            continue
        }
        if ($line -notmatch "^[+-]\s+status:\s+(todo|in_progress|blocked|done)\s*$") {
            throw "Sprint-state change contains non-status edit: $line"
        }
    }
}

function Invoke-DashboardValidation {
    param(
        [string]$Root,
        [string]$Python
    )
    & $Python -m pytest tests/test_sprint_sync_service.py tests/test_sprint_service.py tests/test_routes.py
    if ($LASTEXITCODE -ne 0) {
        throw "RYSEN-LABS sprint tests failed."
    }
    & $Python -m pytest
    if ($LASTEXITCODE -ne 0) {
        throw "RYSEN-LABS full test suite failed."
    }
    & $Python -m compileall app tests scripts
    if ($LASTEXITCODE -ne 0) {
        throw "RYSEN-LABS compileall failed."
    }
    Assert-GitDiffCheck -RepoPath $Root
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
    $target = if ([string]::IsNullOrWhiteSpace($checkpointId)) { $taskId } else { $checkpointId }
    $isAutomaticCompletion = $Apply -and $normalizedStatus -eq "done"

    if ($isAutomaticCompletion -and $AllowDirty) {
        throw "Automatic completion to done cannot use -AllowDirty."
    }
    if ($isAutomaticCompletion -and $SkipValidation) {
        throw "Automatic completion to done requires a real validation command; -SkipValidation is not allowed."
    }
    if ($CommitSprintState -or $PushSprintState) {
        if (-not $Apply) {
            throw "-CommitSprintState and -PushSprintState require -Apply."
        }
        if ($PushSprintState -and -not $CommitSprintState) {
            throw "-PushSprintState requires -CommitSprintState."
        }
        Assert-DashboardBranch -Root $DashboardRoot -ExpectedBranch $SprintStateBranch
        Assert-DashboardCleanBeforeMutation -Root $DashboardRoot
    }

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
    Assert-CommitExists -RepoPath $RepositoryPath -Sha $CommitSha
    $commitMessage = Invoke-Git -RepoPath $RepositoryPath -Arguments @("log", "-1", "--pretty=%s", $CommitSha)
    $dirtyStatus = Invoke-Git -RepoPath $RepositoryPath -Arguments @("status", "--porcelain")
    $isDirty = -not [string]::IsNullOrWhiteSpace($dirtyStatus)
    if ($isDirty -and -not $AllowDirty) {
        throw "Working tree is dirty. Commit or clean changes first, or rerun with -AllowDirty for an evidence-only checkpoint."
    }
    if ($isAutomaticCompletion) {
        Assert-GitDiffCheck -RepoPath $RepositoryPath
        Assert-BranchSynchronized -RepoPath $RepositoryPath -RemoteName $ExpectedRemote
    }

    $validationSummary = "Skipped by -SkipValidation."
    if (-not $SkipValidation) {
        if ($isAutomaticCompletion -and [string]::IsNullOrWhiteSpace($ValidationCommand)) {
            throw "Automatic completion to done requires a configured or supplied validation command."
        }
        $validationSummary = Invoke-ValidationCommand -RepoPath $RepositoryPath -Command $ValidationCommand
        if ($isAutomaticCompletion -and $validationSummary -eq "No validation command configured.") {
            throw "Automatic completion to done requires a real validation command."
        }
    }

    $timestamp = (Get-Date).ToUniversalTime().ToString("o")
    $repoName = Split-Path -Leaf $gitRoot
    if ([string]::IsNullOrWhiteSpace($UpdateId)) {
        $shortCommit = if ($CommitSha.Length -ge 12) { $CommitSha.Substring(0, 12) } else { $CommitSha }
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

        if ($CommitSprintState -or $PushSprintState) {
            Assert-DashboardChangesExpected -Root $DashboardRoot
            Invoke-DashboardValidation -Root $DashboardRoot -Python $python
            & git add roadmap/current_sprint.yaml roadmap/updates/processed roadmap/updates/rejected
            if ($LASTEXITCODE -ne 0) {
                throw "git add failed for RYSEN-LABS sprint-state files."
            }
            $commitMessage = "Update sprint checkpoint $target"
            if ($CommitSprintState) {
                & git commit -m $commitMessage
                if ($LASTEXITCODE -ne 0) {
                    throw "git commit failed for RYSEN-LABS sprint-state update."
                }
                $dashboardCommit = Invoke-Git -RepoPath $DashboardRoot -Arguments @("rev-parse", "HEAD")
                Write-Host "RYSEN-LABS sprint-state commit: $dashboardCommit"
            }
            if ($PushSprintState) {
                & git push $ExpectedRemote $SprintStateBranch
                if ($LASTEXITCODE -ne 0) {
                    throw "git push failed for RYSEN-LABS sprint-state update."
                }
            }
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

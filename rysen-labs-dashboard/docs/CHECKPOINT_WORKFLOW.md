# Checkpoint Workflow

`scripts/checkpoint.ps1` creates a verified sprint update from a development checkpoint.

The script does not edit dashboard UI files and does not calculate percentages. It writes a `sprint_update` JSON file into the Sprint Update Inbox, then runs the existing inbox processor in dry-run or apply mode. The sprint engine remains responsible for calculating progress from task/checkpoint points.

## Command

```powershell
.\scripts\checkpoint.ps1 `
  -Project rip-or-vault `
  -Task rov-002 `
  -Checkpoint rov-002-e `
  -Status done `
  -RepositoryPath ..\rip-or-vault `
  -SkipValidation
```

Apply the recommended status change when explicitly authorized:

```powershell
.\scripts\checkpoint.ps1 `
  -Project rip-or-vault `
  -Task rov-002 `
  -Checkpoint rov-002-e `
  -Status done `
  -RepositoryPath ..\rip-or-vault `
  -Apply
```

## Parameters

- `Project`: roadmap project ID, such as `rip-or-vault`.
- `Task`: sprint task ID, such as `rov-002`.
- `Checkpoint`: optional checkpoint ID, such as `rov-002-e`.
- `Status`: recommended status: `todo`, `in_progress`, `blocked`, `done`, or `complete` as an alias for `done`.
- `RepositoryPath`: Git repository that produced the checkpoint evidence.
- `ValidationCommand`: optional command run from `RepositoryPath`.
- `SkipValidation`: skips validation and records that fact.
- `Apply`: applies the update through `scripts/process_sprint_updates.py`.
- `AllowDirty`: permits evidence capture from a dirty working tree.
- `CommitSha`: records a specific commit instead of current `HEAD`.
- `UpdateId`: explicit idempotency key.

## Configuration

Project defaults live in `config/checkpoints.json`.

Each project can define a `validation_command`. The script uses that command unless `-ValidationCommand` is supplied. Empty validation commands are allowed for projects that do not yet have a standardized validation hook.

## Git Behavior

The checkpoint script records an existing commit. It does not create commits, push, reset, clean, checkout, merge, rebase, or force any Git state.

By default, the working tree must be clean before a checkpoint can be marked successful. Use `-AllowDirty` only for evidence-only updates where dirty state is intentional.

Captured metadata includes:

- repository name
- branch
- commit SHA
- commit message
- timestamp
- working-tree state
- optional notes

## Progress Calculation

Progress is recalculated by the sprint engine:

```text
completed checkpoint/task points / total sprint points * 100
```

The checkpoint script never writes percentages and never changes points, sprint dates, objectives, or task definitions.

## Duplicate Handling

If `-UpdateId` is not supplied, the script derives one from:

- project
- task or checkpoint
- recommended status
- commit SHA

The Sprint Update Inbox treats an already processed update ID as idempotent and does not apply it again.

## Failure Behavior

The script exits non-zero when:

- validation fails
- Git metadata cannot be read
- the working tree is dirty without `-AllowDirty`
- the inbox processor rejects the update
- the project, task, checkpoint, or status is invalid

Failed validation does not write a pending update file. Rejected apply attempts are archived under `roadmap/updates/rejected/`.

## Codex Checkpoint Workflow

1. Complete implementation work.
2. Run repository validation.
3. Commit the project checkpoint when authorized.
4. Run `scripts/checkpoint.ps1` with the matching sprint task/checkpoint IDs.
5. Use dry-run first unless the prompt explicitly authorizes sprint-state mutation.
6. Use `-Apply` only when the checkpoint is authorized to update sprint state.
7. Refresh the dashboard; progress recalculates from the roadmap.

## Adding Another Project

1. Add the project to `roadmap/projects.yaml`.
2. Add sprint tasks/checkpoints to `roadmap/current_sprint.yaml`.
3. Add optional defaults to `config/checkpoints.json`.
4. Have the project use `scripts/checkpoint.ps1` or emit compatible `sprint_update` files.

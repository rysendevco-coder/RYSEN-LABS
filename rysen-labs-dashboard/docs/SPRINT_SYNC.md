# Sprint Sync

Sprint Sync keeps progress reporting factual and checkpoint based.

## Standard Completion Report

```yaml
sprint_update:
  project:
  task:
  checkpoint:
  result:
  evidence:
  recommendation:
```

## Principles

- Project agents report verified facts and objective evidence.
- Agents do not invent arbitrary completion percentages.
- The sprint engine calculates progress from task and checkpoint points.
- Agents may recommend a status change.
- Sprint state is only modified when explicitly authorized.
- Commits, pushes, and deploys require explicit authorization.
- Project repositories emit `sprint_update` evidence files; this dashboard repository owns `roadmap/current_sprint.yaml`.
- No update may add sprint scope, alter point totals, or change sprint metadata automatically.

## Sprint Update Inbox

Project repositories can produce YAML or JSON files using the standard shape:

```yaml
update_id: rov-002-e-regression-20260811
sprint_update:
  project: rip-or-vault
  task: rov-002
  checkpoint: rov-002-e
  result: passed
  evidence:
    tests: "34 passed"
    validation: "result/error-state regression complete"
    commit: "abc1234"
  recommendation:
    status: done
```

Place pending updates in:

```text
roadmap/updates/pending/
```

The processor validates project, task, checkpoint, and status references against the current roadmap. Valid applied updates are archived to `roadmap/updates/processed/`. Invalid updates are archived to `roadmap/updates/rejected/`. The original update file is preserved in the archive for auditability.

Completion updates to `done` require objective evidence. `"No validation command configured."` and skipped validation do not qualify as completion evidence.

Evidence-only project activity can be recorded without changing sprint math by adding `activity_only: true` inside `sprint_update`. Activity-only updates are useful for verified work outside the active sprint, such as a project checkpoint that has no Sprint 01 task yet. They must reference a registered project, are archived for auditability, and are shown as latest project activity, but they never alter `roadmap/current_sprint.yaml`.

Dry-run validates and reports without modifying sprint state or moving files:

```powershell
python scripts/process_sprint_updates.py --dry-run --all
```

Apply mode is authorized input. It may change only the requested task/checkpoint `status`:

```powershell
python scripts/process_sprint_updates.py --apply --file roadmap/updates/pending/rov-update-001.yaml
```

Duplicate updates are detected by `update_id` when present, or by a stable hash of the `sprint_update` payload. Already processed updates are reported and not applied again.

For a Git-aware developer checkpoint workflow, use `scripts/checkpoint.ps1`. It records branch, commit SHA, commit message, validation status, and optional notes before handing the generated update to the same inbox processor. See `docs/CHECKPOINT_WORKFLOW.md`.

## Sprint Auto-Sync V1.2

`scripts/checkpoint.ps1` can run an explicitly authorized checkpoint transaction:

```powershell
.\scripts\checkpoint.ps1 `
  -Project rip-or-vault `
  -Task rov-002 `
  -Checkpoint rov-002-e `
  -Status done `
  -RepositoryPath C:\path\to\project `
  -ValidationCommand ".\run-validation.ps1" `
  -Apply `
  -CommitSprintState `
  -PushSprintState
```

For automatic completion to `done`, the workflow refuses to continue when validation is missing or skipped, validation fails, the source repository is dirty, `git diff --check` fails, the checkpoint commit is missing, or the source branch is not synchronized with its upstream. Sprint-state commits are allowed only on the approved dashboard branch and only when the dashboard diff is limited to the requested `status` change plus processed/rejected audit files.

Project agents should complete validation, commit, and push their project checkpoint first. The central Rysen Labs dashboard repository remains the only owner of active sprint state and calculated progress.

## Daily Snapshots

Write or refresh the current day's sprint progress snapshot with:

```powershell
python scripts/snapshot_sprint.py
```

Snapshots are stored in `roadmap/history/YYYY-MM-DD.yaml` and include sprint totals, schedule health, and per-project progress. Running the command repeatedly on the same day safely refreshes that day's snapshot.

## Morning Brief Data

`GET /api/sprint/brief` returns structured factual data for a future morning founder brief:

- sprint name
- days remaining
- actual, expected, variance, and schedule status
- per-project progress
- recent processed updates
- blockers
- next incomplete checkpoints

The backend does not generate AI prose.

## Adding A New Project

1. Add the project to `roadmap/projects.yaml`.
2. Add sprint tasks/checkpoints to `roadmap/current_sprint.yaml`.
3. Have the project repo emit `sprint_update` files with the same standard shape.
4. Process updates through this dashboard repo; do not write directly to `current_sprint.yaml` from project repos.

Project registration and active sprint membership are separate. A registered project ID is valid for evidence intake, but an update is applied only when the referenced task/checkpoint exists in `roadmap/current_sprint.yaml`.

Lunch Roulette is registered as `lunch-roulette` on canonical branch `main`. Checkpoint 8, "Real Google Places Restaurant Provider", completed outside Sprint 01 at commit `4b882661e9f9d652c7b9852865a433011108e59a` and should be treated as historical evidence, not retroactive Sprint 01 scope. Recommended future sprint candidate: "Lunch Roulette - Checkpoint 9 - Final Recommendation UX + Live Places Smoke Test."

## ZimaBoard Roadmap Sync

Repository-managed sync artifacts live in:

```text
scripts/zima_sync.sh
deploy/systemd/rysen-labs-dashboard-sync.service
deploy/systemd/rysen-labs-dashboard-sync.timer
```

They are prepared for later manual installation on the ZimaBoard. The script fetches `origin`, fast-forwards only a clean approved branch, refuses dirty or non-fast-forward states, logs clearly, and never restarts Docker or rebuilds containers. Roadmap updates become visible through the existing read-only `./roadmap:/app/roadmap:ro` volume mount.

## Safe Update Utility

Use `scripts/update_sprint.py` only when sprint-state modification is explicitly authorized.

Task update:

```powershell
python scripts/update_sprint.py --task rov-002 --status done
```

Checkpoint update:

```powershell
python scripts/update_sprint.py --task rov-002 --checkpoint rov-002-a --status done
```

Allowed statuses:

- `todo`
- `in_progress`
- `blocked`
- `done`

The utility validates task IDs, checkpoint IDs, allowed statuses, and checkpoint point totals before writing.

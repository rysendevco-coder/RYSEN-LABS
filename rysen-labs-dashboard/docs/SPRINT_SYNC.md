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

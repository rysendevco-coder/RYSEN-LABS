# Sprint System

The Rysen Labs Project/Sprint Command Center is backed by version-controlled YAML files.

## Files

```text
roadmap/
  projects.yaml
  current_sprint.yaml
  history/
```

- `projects.yaml` defines the tracked projects and display order.
- `current_sprint.yaml` defines the active sprint, objective, revenue goal, and tasks.
- `history/` is where completed sprint files should be archived.

## Task Statuses

Supported task statuses:

- `todo`
- `in_progress`
- `blocked`
- `done`

Blocked tasks may include a `blocker` field. Notes are optional.

## Progress Calculation

Progress is calculated by the backend from task points:

```text
completed_points / total_points * 100
```

Only tasks with `status: done` count as completed. Blocked work is not counted as completed.

## Example Workflow For Charles

1. Edit `roadmap/current_sprint.yaml`.
2. Change a task status from `todo` to `in_progress` to `done`.
3. Refresh the dashboard.
4. Progress recalculates automatically.

## Starting A New Sprint

1. Copy `roadmap/current_sprint.yaml` to `roadmap/history/`.
2. Rename the archived file with the sprint number or date range.
3. Edit `roadmap/current_sprint.yaml` with the new sprint name, dates, objective, and task list.
4. Refresh the dashboard and check `/api/sprint`.

## Future Architecture Notes

These are intentionally not implemented yet:

- GitHub issue and pull request synchronization.
- Automatic Git repository activity summaries.
- Scheduled daily status snapshots.
- AI-generated morning founder brief.
- Historical sprint metrics.
- Revenue and MRR tracking.

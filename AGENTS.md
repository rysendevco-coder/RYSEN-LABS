# Repository Operating Instructions

This repository contains the RYSEN Labs AI Development Framework. Treat it as a reusable, project-agnostic operating system for AI-assisted software development.

## Required Reading

Before making changes, the primary Codex session must read:

- [README.md](README.md)
- [docs/FRAMEWORK_OVERVIEW.md](docs/FRAMEWORK_OVERVIEW.md)
- Any relevant project context, such as files created from [templates/PROJECT_CONTEXT.template.md](templates/PROJECT_CONTEXT.template.md)

## Working Rules

- Plan before editing.
- Keep work inside the assigned role.
- Avoid modifying unrelated files.
- Keep changes small, reviewable, and documented.
- Use specialized subagents only when work can be cleanly divided.
- Prefer read-only agents for exploration and review.
- Avoid parallel write-heavy tasks that touch overlapping files.
- Wait for all requested subagents before consolidating results.
- Never expose or commit secrets.
- Update documentation and [CHANGELOG.md](CHANGELOG.md) when behavior or framework structure changes.

## Rysen Labs Sprint Standard

- Follow AGENTS.md and the Rysen Labs sprint-reporting standards.
- Sprint progress is determined from task/checkpoint points.
- Agents must not invent arbitrary project-completion percentages.
- Meaningful completed work should produce a machine-readable `sprint_update` report.
- `sprint_update` should identify: `project`, `task`, optional `checkpoint`, `result`, `evidence`, and `recommendation`.
- Include objective evidence when relevant: tests, validation, coverage measurements, commits, build results, or other measurable outcomes.
- Agents may recommend a task/checkpoint status change, but the sprint engine remains the source of truth for calculated progress.
- Do not modify sprint state unless explicitly authorized.
- Do not commit, push, or deploy unless explicitly authorized.
- Read `docs/SPRINT_SYNC.md` and `docs/SPRINT_SYSTEM.md` when performing sprint-related work.
- Preserve repository-specific instructions and safety rules.

## Human Approval Boundaries

All gated actions require explicit human approval in the current task. See [docs/HUMAN_APPROVAL_POLICY.md](docs/HUMAN_APPROVAL_POLICY.md) for the authoritative list.

## Final Response

The final response must list:

- Files changed.
- Validation performed.
- Known risks.
- Recommended next action.

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

## Human Approval Boundaries

All gated actions require explicit human approval in the current task. See [docs/HUMAN_APPROVAL_POLICY.md](docs/HUMAN_APPROVAL_POLICY.md) for the authoritative list.

## Final Response

The final response must list:

- Files changed.
- Validation performed.
- Known risks.
- Recommended next action.

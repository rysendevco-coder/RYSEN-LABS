# Agent Handoff Protocol

A handoff transfers responsibility between roles without losing context.

Use [HANDOFF.template.md](../templates/HANDOFF.template.md) for reusable handoff records.

## Required Fields

- Source role.
- Destination role.
- Task summary.
- Decisions already made.
- Files changed.
- Files allowed to change.
- Files not to change.
- Contracts or interfaces.
- Validation completed.
- Human approval status.
- Human approval boundaries.
- Known risks.
- Open questions.
- Acceptance criteria.
- Recommended next action.

## Rules

- State ownership clearly.
- Identify files the destination role may change.
- Identify files the destination role must not change.
- State whether explicit human approval has been granted for any gated action.
- Preserve approval boundaries even when work is passed between agents.
- Preserve contract details instead of relying on memory.
- Escalate unclear, risky, or production-impacting decisions to the human developer.

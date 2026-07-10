# New Feature Prompt

## Objective

Implement `[feature summary]` for `[project name]` according to the active project context.

## Context To Inspect

- `AGENTS.md`
- Project context
- Requirements or feature request
- Relevant architecture decisions
- Existing tests and validation commands

## Agent Or Agents To Use

Use the Orchestrator if scope is unclear. Use the Backend Engineer for backend changes. Use the Flutter Engineer for Flutter changes. Use the Reviewer after implementation.

## Sequencing

Plan first. Backend and Flutter work may run in parallel only if files and contracts do not overlap. Review must run after implementation.

## Files Allowed To Change

- Files listed in the approved feature request
- Tests for the changed behavior
- Documentation directly related to the feature
- Changelog when behavior changes

## Files Prohibited From Changing

- Secrets
- Credentials
- Unrelated modules
- Release or deployment files unless explicitly approved

## Required Validation

- Run the project validation commands relevant to changed files.
- Confirm tests cover changed behavior or explain why not.
- Confirm documentation and changelog are updated when behavior changes.

## Expected Final Report

Report files changed, behavior added, validation performed, reviewer findings, risks, and recommended next action.

## Human Approval Boundaries

Follow [../docs/HUMAN_APPROVAL_POLICY.md](../docs/HUMAN_APPROVAL_POLICY.md). Do not execute any gated action during this prompt unless the user explicitly approves that exact action in the current task. Prior approval from another prompt or conversation does not carry forward.

# Bug Fix Prompt

## Objective

Fix `[bug summary]` while minimizing scope and preserving existing behavior.

## Context To Inspect

- Bug report or reproduction steps
- Project context
- Relevant code and tests
- Recent changes touching the affected area

## Agent Or Agents To Use

Use the specialist that owns the affected area. Use the Reviewer after the fix. Use the Orchestrator only if ownership or scope is unclear.

## Sequencing

Run discovery before editing. Implementation and review should be sequential.

## Files Allowed To Change

- Minimal files required to fix the bug
- Tests proving the fix
- Documentation if the bug affected documented behavior
- Changelog if user-visible behavior changes

## Files Prohibited From Changing

- Unrelated modules
- Secrets
- Credentials
- Deployment files unless the bug is specifically in release preparation

## Required Validation

- Reproduce or explain the bug.
- Add or update a regression test when practical.
- Run relevant tests or validation commands.

## Expected Final Report

Report root cause, files changed, validation performed, remaining risks, and recommended next action.

## Human Approval Boundaries

Follow [../docs/HUMAN_APPROVAL_POLICY.md](../docs/HUMAN_APPROVAL_POLICY.md). Do not execute any gated action during this prompt unless the user explicitly approves that exact action in the current task. Prior approval from another prompt or conversation does not carry forward.

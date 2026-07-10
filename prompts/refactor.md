# Refactor Prompt

## Objective

Refactor `[area]` to improve `[maintainability, clarity, performance, or architecture goal]` without changing intended behavior.

## Context To Inspect

- Project context
- Architecture decisions
- Existing tests
- Files in the target area
- Known risks or technical debt notes

## Agent Or Agents To Use

Use the specialist that owns the target area. Use the Reviewer after the refactor. Use the Orchestrator if the refactor crosses role boundaries.

## Sequencing

Plan first. Run implementation sequentially unless the Orchestrator identifies non-overlapping file ownership.

## Files Allowed To Change

- Files in the approved refactor scope
- Tests for the affected area
- Documentation explaining changed structure

## Files Prohibited From Changing

- Unrelated behavior
- Public contracts unless explicitly approved
- Secrets
- Credentials
- Production deployment configuration

## Required Validation

- Run tests for the affected area.
- Confirm intended behavior is unchanged.
- Document any public contract changes, or state that none were made.

## Expected Final Report

Report files changed, structure improved, validation performed, behavior-change assessment, risks, and recommended next action.

## Human Approval Boundaries

Follow [../docs/HUMAN_APPROVAL_POLICY.md](../docs/HUMAN_APPROVAL_POLICY.md). Do not execute any gated action during this prompt unless the user explicitly approves that exact action in the current task. Prior approval from another prompt or conversation does not carry forward.

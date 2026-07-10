# Project Kickoff Prompt

## Objective

Establish initial project context and a disciplined starting plan for `[project name]`.

## Context To Inspect

- `README.md`
- `AGENTS.md`
- Existing project documentation
- Existing source tree in read-only mode unless explicitly approved

## Agent Or Agents To Use

Use the Orchestrator. Use the Reviewer only for read-only risk inspection if the existing project already has code or production assets.

## Sequencing

Run sequentially. Complete context discovery before planning.

## Files Allowed To Change

- `PROJECT_CONTEXT.md`
- `REQUIREMENTS.md`
- `ROADMAP.md`
- Documentation files explicitly named by the human developer

## Files Prohibited From Changing

- Application source code
- Secrets
- Credentials
- Deployment configuration
- Files outside the assigned project repository

## Required Validation

- Confirm required context files exist.
- Confirm no application source code was changed.
- Confirm approval boundaries are documented.

## Expected Final Report

Report the project purpose, known constraints, proposed milestones, agent roles needed, validation performed, risks, open questions, and recommended next action.

## Human Approval Boundaries

Follow [../docs/HUMAN_APPROVAL_POLICY.md](../docs/HUMAN_APPROVAL_POLICY.md). Do not execute any gated action during this prompt unless the user explicitly approves that exact action in the current task. Prior approval from another prompt or conversation does not carry forward.

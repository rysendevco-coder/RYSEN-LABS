# Code Review Prompt

## Objective

Review `[branch, pull request, or diff]` for correctness, regressions, security, maintainability, architecture compliance, and missing tests.

## Context To Inspect

- Diff under review
- Project context
- Requirements or acceptance criteria
- Relevant tests and validation output
- Architecture decisions

## Agent Or Agents To Use

Use the Reviewer. Do not use the original implementation agent as the primary reviewer.

## Sequencing

Run review after implementation. Keep review read-only unless the human developer explicitly asks for fixes.

## Files Allowed To Change

- None by default
- Review notes only if requested

## Files Prohibited From Changing

- Implementation files during review
- Secrets
- Credentials
- Release or deployment files unless they are the subject of review

## Required Validation

- Inspect the diff.
- Check whether relevant tests were run.
- Identify missing tests or documentation.

## Expected Final Report

Lead with findings ordered by severity. Include file and symbol references, blockers, recommendations, test gaps, residual risk, and a brief summary.

## Human Approval Boundaries

Follow [../docs/HUMAN_APPROVAL_POLICY.md](../docs/HUMAN_APPROVAL_POLICY.md). Do not execute any gated action during this prompt unless the user explicitly approves that exact action in the current task. Prior approval from another prompt or conversation does not carry forward.

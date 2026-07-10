# Architecture Review Prompt

## Objective

Review the architecture of `[area or project]` for maintainability, modularity, risk, and alignment with project goals.

## Context To Inspect

- Project context
- Architecture decision records
- Requirements and roadmap
- Relevant code or documentation in read-only mode
- Known constraints

## Agent Or Agents To Use

Use the Reviewer for independent assessment. Use the Orchestrator afterward only if recommendations need to become a task plan.

## Sequencing

Run review before planning implementation. Keep inspection read-only unless the human developer explicitly asks for document updates.

## Files Allowed To Change

- Architecture review notes if requested
- ADR drafts if requested
- Planning documents if requested

## Files Prohibited From Changing

- Application source code
- Deployment configuration
- Secrets
- Credentials

## Required Validation

- Confirm reviewed files and assumptions.
- Distinguish evidence from inference.
- Identify decisions that need human approval.

## Expected Final Report

Report findings ordered by severity, architecture risks, recommendations, open questions, and suggested next actions.

## Human Approval Boundaries

Follow [../docs/HUMAN_APPROVAL_POLICY.md](../docs/HUMAN_APPROVAL_POLICY.md). Do not execute any gated action during this prompt unless the user explicitly approves that exact action in the current task. Prior approval from another prompt or conversation does not carry forward.

# Release Preparation Prompt

## Objective

Prepare release `[version]` for `[project name]` without performing production deployment or publication.

## Context To Inspect

- Project context
- Changelog
- Release notes
- Versioning policy
- Validation results
- Deployment or store-submission documentation

## Agent Or Agents To Use

Use the Deployment Engineer. Use the Reviewer for independent release-readiness review if the release has meaningful risk.

## Sequencing

Prepare release materials first. Review readiness second. Do not execute production deployment or publication.

## Files Allowed To Change

- Changelog
- Release notes
- Release checklist
- Version documentation
- Deployment documentation

## Files Prohibited From Changing

- Secrets
- Private keys
- Production credential stores
- Protected branch configuration
- Store submissions

## Required Validation

- Confirm version and changelog consistency.
- Confirm no secrets are present.
- Confirm required tests or manual validation are documented.
- Confirm deployment remains preparation-only unless explicit approval is granted.

## Expected Final Report

Report release scope, files changed, validation performed, unresolved risks, approval status, and recommended next action.

## Human Approval Boundaries

Follow [../docs/HUMAN_APPROVAL_POLICY.md](../docs/HUMAN_APPROVAL_POLICY.md). Do not execute any gated action during this prompt unless the user explicitly approves that exact action in the current task. Prior approval from another prompt or conversation does not carry forward. Preparing release notes, manifests, commands, and checklists is allowed when within scope.

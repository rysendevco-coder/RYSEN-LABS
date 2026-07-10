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

Do not push, merge, publish, deploy, delete remote resources, rotate credentials, upload signing keys, or submit to an app store without explicit human approval in the current task.

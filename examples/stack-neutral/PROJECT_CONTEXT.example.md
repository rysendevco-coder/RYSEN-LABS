# Stack-Neutral Project Context Example

This example shows how to adopt the RYSEN Labs AI Development Framework without selecting a specific programming language, UI toolkit, backend framework, or database.

## Problem Statement

The project helps a defined user group complete a recurring workflow with less manual coordination and clearer status tracking.

## Project Boundaries

- Allowed paths: `docs/`, `templates/`, project planning files, and explicitly assigned implementation areas after stack selection.
- Prohibited paths: secrets, credentials, signing material, deployment settings, generated files, vendor-managed files, and unrelated repositories.
- External services: out of scope until documented in project context and approved by the human developer.

## Roles Selected

- Orchestrator for requirements, milestones, risks, and handoffs.
- Reviewer for read-only quality and safety review.
- Deployment Engineer for release preparation documentation only.

## Roles Replaced Or Omitted

- Flutter Engineer may be replaced by the frontend specialist selected by the project.
- Backend Engineer is used only after the project chooses a backend architecture.
- Stack-specific overlays are provisional until architecture decisions are recorded.

## Approval Status

All gated actions are `Not approved` by default. See [../../docs/HUMAN_APPROVAL_POLICY.md](../../docs/HUMAN_APPROVAL_POLICY.md). Any task-specific approval must be recorded with the exact approved action and current-task boundary.

## Allowed And Prohibited Paths

- Allowed for discovery: documentation, project context, requirements, roadmap, and ADR drafts.
- Allowed for implementation: TBD after architecture approval.
- Prohibited: secrets, credentials, signing keys, production data, unrelated repositories, and generated or vendor-managed files.

## Provisional Architecture

Architecture is intentionally undecided. The project should define user workflows, domain boundaries, data ownership, integration needs, and validation expectations before selecting technologies.

## Validation Expectations

- Documentation links remain valid.
- Project context records approved scope and gated-action status.
- Any future implementation defines stack-specific tests before code changes are considered done.

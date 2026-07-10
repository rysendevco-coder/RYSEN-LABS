# Git Workflow

## Branch Model

- `main`: stable framework releases.
- `develop`: integration branch.
- `feature/<short-description>`: isolated framework changes.
- `fix/<short-description>`: corrections.
- `docs/<short-description>`: documentation-only changes.

## Rules

- Work should normally enter through `develop`.
- `main` should not receive unfinished work.
- Never force-push.
- Use small, descriptive commits.
- Human approval is required before merging into `main`.
- Framework releases use semantic versioning.

## Release Flow

1. Integrate completed work into `develop`.
2. Validate documentation, links, configuration, and templates.
3. Prepare release notes and changelog updates.
4. Request human approval before merging to `main`.
5. Tag releases only after approval.

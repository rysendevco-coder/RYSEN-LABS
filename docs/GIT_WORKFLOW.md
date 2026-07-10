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
- All gated actions require explicit human approval in the current task. See [HUMAN_APPROVAL_POLICY.md](HUMAN_APPROVAL_POLICY.md).
- Framework releases use semantic versioning.

## Release Flow

1. Integrate completed work into `develop`.
2. Validate documentation, links, configuration, and templates.
3. Prepare release notes and changelog updates.
4. Request human approval before merging to `main`.
5. Tag releases only after approval.

## Establishing main for the First Stable Release

Creating `main`, changing the GitHub default branch, and tagging a release are separate gated actions under the [Human Approval Policy](HUMAN_APPROVAL_POLICY.md).

1. Confirm `develop` is clean and synchronized with `origin/develop`.
2. Run the formal read-only framework review.
3. Resolve all Blocker and High findings.
4. Re-run required validation.
5. Obtain explicit human approval in the current task to create and push `main`.
6. Create `main` from the exact approved `develop` commit.
7. Push `main` without force.
8. Verify local and remote commit parity.
9. Set or confirm the GitHub default branch separately, only with explicit approval.
10. Create and push a version tag only with separate explicit approval.
11. Never delete `develop` as part of first-time `main` establishment.

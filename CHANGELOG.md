# Changelog

This changelog follows a Keep a Changelog-inspired structure.

## [Unreleased]

### Added

- Added the `rysen-labs-dashboard` FastAPI project for a read-only ZimaBoard operations dashboard.
- Prepared `rysen-labs-dashboard` v0.2 with service-oriented backend modules, typed models, SSE live updates, per-app health checks, environment feature flags, hardened Docker defaults, expanded tests, and project status documentation.
- Prepared `rysen-labs-dashboard` v0.3 with optional read-only Git repository inspection, a repository registry, repository status cards, Docker image Git support, cached Git scans, a repositories API, safe repository mount guidance, and expanded validation coverage.
- Added the first Rysen Labs Project/Sprint Command Center with YAML roadmap files, point-weighted sprint progress, `/api/sprint`, `/api/projects`, dashboard sprint cards, needs-attention tracking, and sprint system documentation.
- Added Sprint Sync V1.1 support for optional task checkpoints, backend schedule health, schedule status UI, read-only roadmap Compose mounting, a safe sprint update CLI, sprint sync documentation, and expanded tests.
- Added automated sprint update pipeline support with a validated update inbox, processed/rejected archives, daily sprint snapshots, a structured morning brief endpoint, compact dashboard update activity, and expanded tests.
- Added a PowerShell checkpoint workflow that captures validation and Git metadata, emits sprint update inbox files, supports idempotent apply/dry-run processing, and documents Codex checkpoint usage.
- Registered Lunch Roulette as a managed dashboard project for Sprint Update / Auto-Sync evidence intake without altering Sprint 01 scope or progress.
- Added Sprint Auto-Sync V1.2 transaction safeguards, evidence-only activity records, ZimaBoard safe sync artifacts, and dashboard latest-activity visibility.
- Corrected ZimaBoard sync service paths to the confirmed `/home/charles/projects/RYSEN-LABS` checkout.
- Reconciled the living dashboard with current verified project state, registered Organize Me for activity intake, and recorded activity-only baselines without adding Sprint 01 scope.

## [0.1.0] - 2026-07-10 - Foundation

### Added

- Initial framework documentation.
- Reusable project templates.
- Reusable Codex prompt library.
- Human-readable handbooks for five specialist roles.
- Project-scoped Codex custom-agent definitions.
- Conservative Codex subagent configuration.
- Architecture decision record process.
- Initial ADR for specialized agents.
- Human approval policy and agent handoff protocol.

### Changed

- Tightened approval language across contribution guidance and Codex agent definitions.
- Added approval status and allowed-file fields to handoff guidance.
- Reduced default agent concurrency to lower the risk of overlapping write-heavy work.
- Clarified Codex adoption files in the README.
- Established the Human Approval Policy as the canonical gated-action source.
- Added required-reading rules to all custom-agent TOML definitions.
- Expanded project-context and feature-request templates with boundaries and approval status.
- Documented first-time `main` establishment.
- Added a stack-neutral project-context example.

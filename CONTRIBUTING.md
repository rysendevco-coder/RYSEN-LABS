# Contributing

Contributions to the RYSEN Labs AI Development Framework should preserve its project-agnostic purpose.

## Process

1. Work from `develop` or a short-lived branch based on `develop`.
2. Keep changes small and focused.
3. Update documentation, templates, prompts, and handbooks together when behavior changes.
4. Update [CHANGELOG.md](CHANGELOG.md).
5. Validate Markdown links and TOML syntax before committing.
6. Follow the canonical [Human Approval Policy](docs/HUMAN_APPROVAL_POLICY.md). All gated actions require explicit human approval in the current task.

## Boundaries

Do not introduce application code, runtime stack implementations, databases, Docker, or CI/CD implementations into the framework foundation unless a future approved milestone explicitly adds them.

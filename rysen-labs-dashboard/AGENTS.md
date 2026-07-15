# Rysen Labs Dashboard Instructions

This project is the Rysen Labs Dashboard, a local FastAPI command-center dashboard for the future Rysen Labs ZimaBoard.

- Preserve the service-oriented FastAPI architecture under `app/routes`, `app/services`, `app/models`, and `app/realtime`.
- Preserve safe-mode and read-only defaults.
- Never deploy without explicit user instruction for that task.
- Never add arbitrary shell execution.
- Never add Git mutation endpoints without authentication and explicit human approval.
- Never mount the Docker socket by default.
- Never expose the dashboard directly to the public internet.
- Use repository-relative paths in examples and configuration.
- Run tests before reporting completion.
- Update `README.md`, `docs/PROJECT_STATUS.md`, and the root `CHANGELOG.md` when behavior changes.
- Report commands and validation results honestly, including skipped or failed checks.

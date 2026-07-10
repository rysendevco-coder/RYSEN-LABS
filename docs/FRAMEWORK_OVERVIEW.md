# Framework Overview

The RYSEN Labs AI Development Framework is a reusable operating model for AI-assisted software projects.

It defines how to start projects, divide work across specialist agents, document architecture decisions, transfer context between roles, validate changes, and preserve human control over high-risk actions.

## Scope

The framework provides:

- Shared engineering principles.
- Project startup and handoff workflows.
- Five specialist roles.
- Codex custom-agent configuration.
- Reusable task prompts.
- Reusable project templates.
- Architecture decision records.
- Human approval boundaries.
- A framework improvement loop.

It does not provide application code, runtime stacks, databases, Docker configuration, or CI/CD implementations in version 0.1.0.

## Roles

- Orchestrator plans and coordinates.
- Backend Engineer owns backend implementation once a project selects a backend.
- Flutter Engineer owns Flutter client implementation once a project includes Flutter.
- Reviewer inspects independently.
- Deployment Engineer prepares release procedures and documentation.

## Workflow

1. Establish project context.
2. Identify requirements and constraints.
3. Record architecture decisions.
4. Assign bounded work to the appropriate role.
5. Validate changes.
6. Review independently.
7. Update documentation and changelog.
8. Capture lessons learned.

## Improvement Loop

When repeated patterns appear across projects, promote them into templates, prompts, handbooks, or engineering guidance. Framework changes should be documented and released with semantic versioning.

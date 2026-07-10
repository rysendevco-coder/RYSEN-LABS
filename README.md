# RYSEN Labs AI Development Framework

RYSEN Labs helps one human developer use specialized AI agents with the discipline and quality controls of a small software engineering team.

This repository contains the reusable operating framework for that work. It defines shared engineering principles, agent roles, Codex configuration, task prompts, project templates, handoff rules, approval boundaries, and a continuous improvement loop.

Current maturity: **Version 0.1.0 - Foundation**.

Production deployment always requires explicit human approval.

## What It Solves

AI-assisted development can move quickly, but speed without structure creates drift. The RYSEN Labs AI Development Framework gives each project a repeatable way to:

- Start from clear project context before implementation.
- Separate architecture, backend, frontend, review, and release responsibilities.
- Keep changes small, reviewable, and documented.
- Preserve human control over production actions.
- Capture lessons once and reuse them across future projects.

The framework is project-agnostic. It can be adopted by projects such as Pokemon Sniper, Lunch Roulette, future Flutter applications, Python or Java backend systems, and other software products.

## Initial Agent Roles

- **Orchestrator**: converts goals into requirements, milestones, tasks, ownership, dependencies, risks, and acceptance criteria.
- **Backend Engineer**: owns backend application logic, APIs, validation, integrations, persistence boundaries, and backend tests.
- **Flutter Engineer**: owns Flutter and Dart UI, navigation, state management, accessibility, responsive layouts, and frontend tests.
- **Reviewer**: independently reviews correctness, regressions, security, maintainability, architecture compliance, and missing tests.
- **Deployment Engineer**: owns release preparation, versioning, changelogs, release checklists, environment documentation, and deployment procedure design.

## Repository Structure

```text
.codex/                  Codex framework configuration and project-scoped custom agents
agents/                  Human-readable role handbooks
docs/                    Framework guides, policies, workflows, and ADRs
prompts/                 Reusable paste-ready Codex task prompts
templates/               Project and workflow document templates
examples/                Project-context examples only
AGENTS.md                Repository-level Codex operating instructions
CHANGELOG.md             Version history
CONTRIBUTING.md          Contribution workflow
LICENSE                  MIT License
README.md                Framework introduction
```

## Adopting The Framework

1. Copy the relevant documents into a project repository.
2. Create a project-specific context file from [PROJECT_CONTEXT.template.md](templates/PROJECT_CONTEXT.template.md).
3. Review [FRAMEWORK_OVERVIEW.md](docs/FRAMEWORK_OVERVIEW.md) and [ENGINEERING_GUIDE.md](docs/ENGINEERING_GUIDE.md).
4. Customize agent scope only where the project context requires it.
5. Use the prompt library in [prompts/](prompts/) to start work with clear boundaries.
6. Capture project decisions as ADRs and keep the changelog current.

## Codex Discovery

Codex discovers repository-level operating instructions from [AGENTS.md](AGENTS.md). The primary Codex session should read that file, this README, [FRAMEWORK_OVERVIEW.md](docs/FRAMEWORK_OVERVIEW.md), and relevant project context before making changes.

Project-scoped Codex custom agents are stored in [.codex/agents/](.codex/agents/). These TOML files describe the available specialist roles and their sandbox boundaries.

## Invoking Agents

Invoke agents through a Codex task by naming the required role and providing:

- The objective.
- Context files to inspect.
- Files allowed to change.
- Files prohibited from changing.
- Required validation.
- Human approval boundaries.
- Expected final report.

Example: ask the Orchestrator to split a feature request into backend and Flutter tasks, then ask the Backend Engineer and Flutter Engineer to work only on their non-overlapping files. Ask the Reviewer to inspect the result after implementation.

## Simple Workflow

1. Use [project-kickoff.md](prompts/project-kickoff.md) to establish context.
2. Ask the Orchestrator to produce a scoped plan and handoff.
3. Assign implementation to the appropriate specialist.
4. Run validation required by the project.
5. Ask the Reviewer for an independent review.
6. Update docs, changelog, and lessons learned.
7. Request explicit human approval before any push, merge, publish, deploy, or store submission.

## Improvement Loop

When the framework itself changes, update the affected docs, templates, prompts, handbooks, and [CHANGELOG.md](CHANGELOG.md). Promote reusable lessons into templates or guides so future projects start with better defaults.

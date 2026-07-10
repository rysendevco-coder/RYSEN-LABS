# RYSEN Labs AI Development Framework

RYSEN Labs helps one human developer use specialized AI agents with the discipline and quality controls of a small software engineering team.

This repository contains the reusable operating framework for that work. It defines shared engineering principles, agent roles, Codex configuration, task prompts, project templates, handoff rules, approval boundaries, and a continuous improvement loop.

Current maturity: **Version 0.1.0 - Foundation**.

All gated actions require explicit human approval in the current task. See the [Human Approval Policy](docs/HUMAN_APPROVAL_POLICY.md) for the authoritative list.

## What It Solves

AI-assisted development can move quickly, but speed without structure creates drift. The RYSEN Labs AI Development Framework gives each project a repeatable way to:

- Start from clear project context before implementation.
- Separate architecture, backend, frontend, review, and release responsibilities.
- Keep changes small, reviewable, and documented.
- Preserve human control over production actions.
- Capture lessons once and reuse them across future projects.

The framework is project-agnostic. It can be adopted by projects such as Pokemon Sniper, Lunch Roulette, future Flutter applications, Python or Java backend systems, and other software products. Example projects are illustrative, not mandatory architecture defaults.

## Initial Agent Roles

- **Orchestrator**: converts goals into requirements, milestones, tasks, ownership, dependencies, risks, and acceptance criteria.
- **Backend Engineer**: owns backend application logic, APIs, validation, integrations, persistence boundaries, and backend tests.
- **Flutter Engineer**: owns Flutter and Dart UI, navigation, state management, accessibility, responsive layouts, and frontend tests.
- **Reviewer**: independently reviews correctness, regressions, security, maintainability, architecture compliance, and missing tests.
- **Deployment Engineer**: owns release preparation, versioning, changelogs, release checklists, environment documentation, and deployment procedure design.

The initial included frontend specialist is Flutter-focused, but the framework itself is stack-neutral. Projects may replace that role with a web, desktop, Android, iOS, JavaFX, React, Vue, or other project-specific frontend role. Backend roles must follow the selected project context rather than assume Python, FastAPI, Java, Spring, or any other stack.

## Repository Structure

```text
.codex/                  Codex framework configuration and project-scoped custom agents
agents/                  Human-readable role handbooks
docs/                    Framework guides, policies, workflows, and ADRs
prompts/                 Reusable paste-ready Codex task prompts
templates/               Project and workflow document templates
examples/                Project-context examples only
examples/stack-neutral/  Stack-neutral project-context example
AGENTS.md                Repository-level Codex operating instructions
CHANGELOG.md             Version history
CONTRIBUTING.md          Contribution workflow
LICENSE                  MIT License
README.md                Framework introduction
```

## Adopting The Framework

1. Copy the relevant documents into a project repository.
2. Copy [AGENTS.md](AGENTS.md), [.codex/config.toml](.codex/config.toml), and the needed project-scoped agent definitions from [.codex/agents/](.codex/agents/).
3. Create a project-specific context file from [PROJECT_CONTEXT.template.md](templates/PROJECT_CONTEXT.template.md).
4. Review [FRAMEWORK_OVERVIEW.md](docs/FRAMEWORK_OVERVIEW.md) and [ENGINEERING_GUIDE.md](docs/ENGINEERING_GUIDE.md).
5. Customize agent scope only where the project context requires it.
6. Use the prompt library in [prompts/](prompts/) to start work with clear boundaries.
7. Capture project decisions as ADRs and keep the changelog current.

See [examples/stack-neutral/PROJECT_CONTEXT.example.md](examples/stack-neutral/PROJECT_CONTEXT.example.md) for a project-context example that does not select a specific stack.

## Codex Discovery

Codex discovers repository-level operating instructions from [AGENTS.md](AGENTS.md). The primary Codex session should read that file, this README, [FRAMEWORK_OVERVIEW.md](docs/FRAMEWORK_OVERVIEW.md), and relevant project context before making changes.

Project-scoped Codex custom agents are stored in [.codex/agents/](.codex/agents/). These TOML files describe the available specialist roles and their sandbox boundaries.

The default Codex configuration limits agent depth and keeps concurrency conservative. Parallel work should be limited to read-only tasks or clearly non-overlapping write scopes.

## Invoking Agents

Invoke agents through a Codex task by naming the required role and providing:

- The objective.
- Context files to inspect.
- Files allowed to change.
- Files prohibited from changing.
- Required validation.
- Human approval boundaries from the [Human Approval Policy](docs/HUMAN_APPROVAL_POLICY.md).
- Expected final report.

Example: ask the Orchestrator to split a feature request into backend and Flutter tasks, then ask the Backend Engineer and Flutter Engineer to work only on their non-overlapping files. Ask the Reviewer to inspect the result after implementation.

## Simple Workflow

1. Use [project-kickoff.md](prompts/project-kickoff.md) to establish context.
2. Ask the Orchestrator to produce a scoped plan and handoff.
3. Assign implementation to the appropriate specialist.
4. Run validation required by the project.
5. Ask the Reviewer for an independent review.
6. Update docs, changelog, and lessons learned.
7. Follow the [Human Approval Policy](docs/HUMAN_APPROVAL_POLICY.md) before any gated action.

## Improvement Loop

When the framework itself changes, update the affected docs, templates, prompts, handbooks, and [CHANGELOG.md](CHANGELOG.md). Promote reusable lessons into templates or guides so future projects start with better defaults.

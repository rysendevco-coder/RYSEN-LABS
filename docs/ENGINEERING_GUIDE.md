# Engineering Guide

RYSEN Labs projects should optimize for maintainability, clarity, and deliberate change.

## Core Practices

- Define the problem before choosing technology.
- Write down important decisions before implementation hardens them.
- Keep modules focused and boundaries explicit.
- Prefer simple designs that can evolve.
- Make behavior observable through tests, logs, or documentation.
- Keep documentation close to the change it explains.

## Project Startup

Every project should begin with a project context document. Use [PROJECT_CONTEXT.template.md](../templates/PROJECT_CONTEXT.template.md) to capture goals, users, constraints, architecture, risks, validation commands, and approval boundaries.

## Handoffs

Use [AGENT_HANDOFF_PROTOCOL.md](AGENT_HANDOFF_PROTOCOL.md) whenever work moves between roles. A handoff should preserve decisions, risks, contracts, and acceptance criteria.

A handoff does not grant approval for gated actions. Use [HUMAN_APPROVAL_POLICY.md](HUMAN_APPROVAL_POLICY.md) as the canonical approval policy.

## Review

Review should focus on correctness, architecture, regressions, security, maintainability, tests, and documentation. Style-only feedback should be reserved for cases that affect comprehension or long-term maintainability.

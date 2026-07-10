# ADR-0001: Use Specialized Agents

Status: Accepted

## Context

AI-assisted development can blur ownership when one assistant plans, implements, reviews, and releases without clear separation. RYSEN Labs needs a reusable operating model that lets one human developer benefit from multiple perspectives while preserving control.

## Decision

The framework will use five initial specialist roles:

- Orchestrator.
- Backend Engineer.
- Flutter Engineer.
- Reviewer.
- Deployment Engineer.

Each role has a bounded mission, responsibilities, non-responsibilities, expected outputs, and approval boundaries. Codex custom-agent definitions live under `.codex/agents/`, and human-readable handbooks live under `agents/`.

## Consequences

This improves clarity, review quality, and handoff discipline. It also adds coordination overhead, so tasks should use only the roles that are actually needed.

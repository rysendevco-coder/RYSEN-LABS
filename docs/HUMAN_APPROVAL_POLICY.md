# Human Approval Policy

The human developer owns production authority and high-risk decisions.

## Approval Required

This document is the canonical source of truth for gated actions in the RYSEN Labs AI Development Framework.

Explicit human approval in the current task is required before any of these actions:

- Push to a remote repository.
- Merge any branch or pull request.
- Publish any package, artifact, image, or application.
- Create or publish a release.
- Deploy to any shared, staging, or production environment.
- Upload, replace, expose, or rotate signing keys or credentials.
- Delete remote branches, tags, repositories, cloud resources, or production data.
- Submit an application or update to any app store.
- Change repository security settings, branch protections, access controls, secrets, or deployment protections.

## Approval Not Implied

Approval is not implied by a prior conversation, a checklist item, or an agent recommendation. The current task must include clear permission.

Prior approval from another task or conversation does not carry forward. A handoff does not itself grant approval. Authentication availability does not grant approval.

Preparing commands, manifests, release notes, or checklists is allowed when within scope. Executing a gated action requires explicit approval in the current task.

## Secrets

Secrets must never be committed. Agents should stop and escalate if credentials, private keys, tokens, or signing material appear in a proposed change.

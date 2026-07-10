# Human Approval Policy

The human developer owns production authority and high-risk decisions.

## Approval Required

Explicit human approval in the current task is required before:

- Pushing to a remote.
- Merging branches.
- Publishing packages.
- Creating releases.
- Deploying to production.
- Deleting remote resources.
- Rotating credentials.
- Uploading signing keys.
- Submitting to an app store.
- Changing repository security settings.

## Approval Not Implied

Approval is not implied by a prior conversation, a checklist item, or an agent recommendation. The current task must include clear permission.

## Secrets

Secrets must never be committed. Agents should stop and escalate if credentials, private keys, tokens, or signing material appear in a proposed change.

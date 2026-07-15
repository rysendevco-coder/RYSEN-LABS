# Security

Rysen Labs Dashboard v0.3 is intended for LAN or Tailscale access only.

Do not expose this dashboard directly to the internet with router port forwarding. If remote access is needed, use Tailscale or another private network overlay.

## Current Boundaries

- Read-only dashboard behavior.
- No shell execution.
- No container restart, stop, delete, pull, update, or console controls.
- No authentication or user accounts yet.
- No secrets rendered into the frontend.
- `SAFE_MODE=true` by default.
- Docker integration disabled by default.
- Git repository inspection disabled by default.
- Git repository inspection uses a short cache to avoid repeated subprocess scans on every live-update request.

## Docker Socket Warning

The Docker socket is powerful. Even read-only inspection requires careful handling because Docker socket access can expose sensitive host and container details.

The default Compose file does not mount `/var/run/docker.sock`. Use `docker-compose.docker.yml` only on trusted hosts and trusted networks.

## Git Repository Inspection Warning

Git integration is read-only and disabled by default. When enabled, it allows the dashboard process to read configured source trees and run a limited allowlist of Git status commands with argument arrays and timeouts.

Do not configure paths that contain secrets unless the dashboard process is allowed to read them. Remote URLs are sanitized before display, and repository-changing Git commands are not implemented. Ahead/behind status is based on locally known upstream refs; the dashboard does not fetch from remotes.

## Network Guidance

Use one of these access patterns initially:

- Local LAN access from trusted devices.
- Tailscale access from trusted devices.

Avoid:

- Direct router port forwarding.
- Public internet exposure.
- Cloud tunnel exposure before authentication, authorization, and rate limiting are designed.

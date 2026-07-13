# Security

Version 0.1 is intended for LAN or Tailscale access only.

Do not expose this dashboard directly to the internet with router port forwarding. If remote access is needed, use Tailscale or another private network overlay first.

## Boundaries

- The dashboard is read-only.
- It does not provide shell execution.
- It does not provide Docker restart, stop, delete, pull, or exec controls.
- It does not render secrets or environment values in the frontend.
- Application cards are loaded from local YAML configuration.

## Docker Socket Warning

The Docker socket is powerful. Even though this application only reads container status and the Compose file mounts the socket as read-only, access to `/var/run/docker.sock` should still be treated as privileged.

Run this dashboard only on trusted hosts and trusted networks.

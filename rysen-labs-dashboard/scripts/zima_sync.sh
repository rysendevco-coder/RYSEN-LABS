#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${RYSEN_DASHBOARD_DIR:-/opt/rysen-labs-dashboard}"
REMOTE="${RYSEN_DASHBOARD_REMOTE:-origin}"
BRANCH="${RYSEN_DASHBOARD_BRANCH:-develop}"

log() {
  printf '%s %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"
}

run_git() {
  git -C "$APP_DIR" "$@"
}

if [ ! -d "$APP_DIR/.git" ]; then
  log "refusing sync: $APP_DIR is not a Git checkout"
  exit 1
fi

current_branch="$(run_git branch --show-current)"
if [ "$current_branch" != "$BRANCH" ]; then
  log "refusing sync: current branch is $current_branch, expected $BRANCH"
  exit 1
fi

if [ -n "$(run_git status --porcelain)" ]; then
  log "refusing sync: working tree is dirty"
  exit 1
fi

run_git fetch --quiet "$REMOTE"

local_sha="$(run_git rev-parse HEAD)"
remote_sha="$(run_git rev-parse "$REMOTE/$BRANCH")"
merge_base="$(run_git merge-base HEAD "$REMOTE/$BRANCH")"

if [ "$local_sha" = "$remote_sha" ]; then
  log "sync skipped: already at $local_sha"
  exit 0
fi

if [ "$merge_base" != "$local_sha" ]; then
  log "refusing sync: $BRANCH cannot fast-forward to $REMOTE/$BRANCH"
  exit 1
fi

run_git merge --ff-only "$REMOTE/$BRANCH"
log "sync complete: fast-forwarded $BRANCH to $remote_sha"

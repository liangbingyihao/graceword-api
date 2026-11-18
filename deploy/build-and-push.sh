#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

SHA="$(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || echo nogit)"
DIRTY=""
if [[ -n "$(git -C "$ROOT_DIR" status --porcelain 2>/dev/null || true)" ]]; then
  DIRTY="-dirty"
fi

TAG="${IMAGE_TAG:-$(date +%Y%m%d-%H%M%S)-${SHA}${DIRTY}}"
IMAGE="${IMAGE_REPO}:${TAG}"

ssh "$REMOTE_HOST" "mkdir -p '$REMOTE_BUILD_DIR'"
rsync -a --delete \
  --exclude .git \
  --exclude app/data/bibleart \
  --exclude tests \
  --exclude deploy/env \
  "$ROOT_DIR/" \
  "$REMOTE_HOST:$REMOTE_BUILD_DIR/"

ssh "$REMOTE_HOST" "cd '$REMOTE_BUILD_DIR' && docker build -t '$IMAGE' ."

if ! ssh "$REMOTE_HOST" "test -f '$DOCKER_CONFIG_DIR/config.json'"; then
  echo "Missing remote Docker config: $DOCKER_CONFIG_DIR/config.json" >&2
  echo "Run once on $REMOTE_HOST:" >&2
  echo "  mkdir -p '$DOCKER_CONFIG_DIR' && chmod 700 '$DOCKER_CONFIG_DIR'" >&2
  echo "  DOCKER_CONFIG='$DOCKER_CONFIG_DIR' docker login -u <username>" >&2
  exit 1
fi

ssh "$REMOTE_HOST" "DOCKER_CONFIG='$DOCKER_CONFIG_DIR' docker push '$IMAGE'"
ssh "$REMOTE_HOST" "DOCKER_CONFIG='$DOCKER_CONFIG_DIR' docker image inspect '$IMAGE' --format '{{index .RepoDigests 0}}'"

printf 'IMAGE=%s\n' "$IMAGE"

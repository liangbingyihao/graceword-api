#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

: "${1:?Usage: deploy-image.sh <image-tag>}"
TAG="$1"
IMAGE="${IMAGE_REPO}:${TAG}"
STAMP="$(date +%Y%m%d-%H%M%S)"

ssh "$REMOTE_HOST" "cd '$REMOTE_COMPOSE_DIR' && grep -q 'GRACEWORD_PY_IMAGE_TAG' docker-compose.yml"
ssh "$REMOTE_HOST" "cp '$REMOTE_COMPOSE_DIR/docker-compose.yml' '/tmp/graceword-compose-$STAMP.yml'"

ssh "$REMOTE_HOST" "cd '$REMOTE_COMPOSE_DIR' && \
  GRACEWORD_PY_IMAGE_TAG='$TAG' docker compose pull graceword-py && \
  GRACEWORD_PY_IMAGE_TAG='$TAG' docker compose up -d graceword-py"

RUNNING_IMAGE="$(ssh "$REMOTE_HOST" "docker inspect graceword-py --format '{{.Config.Image}}'")"
if [[ "$RUNNING_IMAGE" != "$IMAGE" ]]; then
  echo "Unexpected running image: $RUNNING_IMAGE (expected $IMAGE)" >&2
  exit 1
fi

printf 'DEPLOYED image=%s composeBackup=/tmp/graceword-compose-%s.yml\n' "$IMAGE" "$STAMP"

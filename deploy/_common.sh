#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -f "$SCRIPT_DIR/env" ]]; then
  set -a
  source "$SCRIPT_DIR/env"
  set +a
fi

: "${REMOTE_HOST:?Set REMOTE_HOST before running this script}"
: "${IMAGE_REPO:?Set IMAGE_REPO in deploy/env}"

REMOTE_HOST="${REMOTE_HOST#ssh://}"
REMOTE_BUILD_DIR="${REMOTE_BUILD_DIR:-/tmp/graceword-api-build}"
REMOTE_CONTENT_DIR="${REMOTE_CONTENT_DIR:-/opt/graceword/graceword-py/bibleart}"
REMOTE_COMPOSE_DIR="${REMOTE_COMPOSE_DIR:-/opt/graceword}"
DOCKER_CONFIG_DIR="${DOCKER_CONFIG_DIR:-/root/.docker-bliang}"
SMOKE_PORT="${SMOKE_PORT:-18080}"

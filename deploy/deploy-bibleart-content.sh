#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

: "${1:?Usage: deploy-bibleart-content.sh <catalog-dir>}"
SOURCE_DIR="$(cd "$1" && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
CONTENT_PARENT="$(dirname "$REMOTE_CONTENT_DIR")"
CONTENT_NAME="$(basename "$REMOTE_CONTENT_DIR")"
NEXT_DIR="${REMOTE_CONTENT_DIR}.next"
PREV_DIR="${REMOTE_CONTENT_DIR}.prev"
BACKUP="/tmp/graceword-bibleart-content-${STAMP}.tgz"

python3 - "$SOURCE_DIR" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text())
version = manifest.get("contentVersion")
if not version:
    raise SystemExit("manifest missing contentVersion")
stories = sorted((root / "stories").glob("*.json"))
if not stories:
    raise SystemExit("no story files")
for path in stories:
    data = json.loads(path.read_text())
    if data.get("contentVersion") != version:
        raise SystemExit(f"version mismatch: {path}")
print(f"validated {len(stories)} stories version={version}")
PY

ssh "$REMOTE_HOST" "mkdir -p '$CONTENT_PARENT'"
ssh "$REMOTE_HOST" "if [ -d '$REMOTE_CONTENT_DIR' ]; then tar czf '$BACKUP' -C '$CONTENT_PARENT' '$CONTENT_NAME'; fi"
ssh "$REMOTE_HOST" "rm -rf '$NEXT_DIR' && mkdir -p '$NEXT_DIR'"
rsync -a --delete "$SOURCE_DIR/" "$REMOTE_HOST:$NEXT_DIR/"

ssh "$REMOTE_HOST" "python3 - '$NEXT_DIR'" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text())
version = manifest.get("contentVersion")
if not version:
    raise SystemExit("manifest missing contentVersion")
stories = sorted((root / "stories").glob("*.json"))
if not stories:
    raise SystemExit("no story files")
for path in stories:
    data = json.loads(path.read_text())
    if data.get("contentVersion") != version:
        raise SystemExit(f"version mismatch: {path}")
print(f"remote validated {len(stories)} stories version={version}")
PY

ssh "$REMOTE_HOST" "set -e; \
  if [ -d '$REMOTE_CONTENT_DIR' ]; then rm -rf '$PREV_DIR'; mv '$REMOTE_CONTENT_DIR' '$PREV_DIR'; fi; \
  mv '$NEXT_DIR' '$REMOTE_CONTENT_DIR'"

if ! ssh "$REMOTE_HOST" "cd '$REMOTE_COMPOSE_DIR' && docker compose restart graceword-py"; then
  ssh "$REMOTE_HOST" "set -e; \
    if [ -d '$PREV_DIR' ]; then rm -rf '$REMOTE_CONTENT_DIR'; mv '$PREV_DIR' '$REMOTE_CONTENT_DIR'; fi" || true
  echo "Restart failed; previous content restored if available" >&2
  exit 1
fi

if [[ "$(ssh "$REMOTE_HOST" "docker inspect graceword-py --format '{{.State.Running}}'")" != "true" ]]; then
  echo "graceword-py is not running after content update" >&2
  exit 1
fi

ssh "$REMOTE_HOST" "rm -rf '$PREV_DIR'"
printf 'CONTENT_DEPLOYED dir=%s backup=%s\n' "$REMOTE_CONTENT_DIR" "$BACKUP"

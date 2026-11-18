#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

: "${1:?Usage: smoke-test.sh <image>}"
IMAGE="$1"
NAME="graceword-bibleart-smoke-$(date +%s)"
CID=""

cleanup() {
  if [[ -n "$CID" ]]; then
    ssh "$REMOTE_HOST" "docker rm -f '$CID' >/dev/null 2>&1 || true" || true
  fi
}
trap cleanup EXIT

if ! ssh "$REMOTE_HOST" "test -f '$REMOTE_CONTENT_DIR/manifest.json'"; then
  echo "Missing remote catalog: $REMOTE_CONTENT_DIR/manifest.json" >&2
  exit 1
fi

CID="$(ssh "$REMOTE_HOST" "docker run -d --name '$NAME' -p '${SMOKE_PORT}:8080' \
  -e SECRET_KEY=test-secret \
  -e JWT_SECRET_KEY=test-jwt-secret \
  -e DATABASE_URL=sqlite:////tmp/app.db \
  -e COZE_API_TOKEN=test-token \
  -e COZE_MAIN_BOT_ID=test-bot \
  -e BIBLEART_CATALOG_ROOT=/app/app/data/bibleart \
  -v '$REMOTE_CONTENT_DIR:/app/app/data/bibleart:ro' \
  '$IMAGE'")"

PORT="$(ssh "$REMOTE_HOST" "printf '%s' '${SMOKE_PORT}'")"
if [[ -z "$PORT" ]]; then
  echo "Could not determine smoke-test port" >&2
  exit 1
fi

STATUS=""
for _ in $(seq 1 30); do
  STATUS="$(ssh "$REMOTE_HOST" "curl -s -o /dev/null -w '%{http_code}' 'http://localhost:$PORT/api/bibleart/stories' || true")"
  if [[ "$STATUS" == "401" ]]; then
    break
  fi
  sleep 1
done

if [[ "$STATUS" != "401" ]]; then
  echo "Expected 401 without JWT, got $STATUS" >&2
  ssh "$REMOTE_HOST" "docker logs --tail 80 '$CID'" >&2 || true
  exit 1
fi

ROUTES="$(ssh "$REMOTE_HOST" "docker exec '$CID' python -c \"from app.main import gw_app; print('\\n'.join(sorted(str(r) for r in gw_app.url_map.iter_rules())))\"")"
for required in /api/session/message /api/session/\<int:session_id\> /api/message/\<string:msg_id\>/retry /api/message/\<string:msg_id\>/stop /api/bibleart/stories; do
  if ! grep -Fqx "$required" <<< "$ROUTES"; then
    echo "Missing route: $required" >&2
    exit 1
  fi
done

TOKEN="$(ssh "$REMOTE_HOST" "docker exec '$CID' python -c \"from flask import Flask; from flask_jwt_extended import JWTManager, create_access_token; app=Flask(__name__); app.config['JWT_SECRET_KEY']='test-jwt-secret'; JWTManager(app); ctx=app.app_context(); ctx.push(); print(create_access_token(identity=1))\"")"

TOTAL="$(ssh "$REMOTE_HOST" "curl -s -H 'Authorization: Bearer $TOKEN' 'http://localhost:$PORT/api/bibleart/stories?lang=zh-Hant' | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"data\"][\"total\"])'")"
QUESTIONS="$(ssh "$REMOTE_HOST" "curl -s -H 'Authorization: Bearer $TOKEN' 'http://localhost:$PORT/api/bibleart/stories/birth?lang=zh-Hant' | python3 -c 'import json,sys; print(len(json.load(sys.stdin)[\"data\"][\"questions\"]))'")"

if [[ "$TOTAL" -lt 1 || "$QUESTIONS" -ne 3 ]]; then
  echo "Smoke test failed: total=$TOTAL birthQuestions=$QUESTIONS" >&2
  exit 1
fi

printf 'SMOKE_OK total=%s birthQuestions=%s image=%s\n' "$TOTAL" "$QUESTIONS" "$IMAGE"

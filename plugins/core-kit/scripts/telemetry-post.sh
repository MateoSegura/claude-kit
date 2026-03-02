#!/usr/bin/env bash
set -uo pipefail
# telemetry-post.sh — POST a telemetry event to the claude-kit API
# Usage: echo '{"event_type":"...","payload":{...}}' | telemetry-post.sh
#
# Required env vars (set by claude-kit CLI before launching Claude):
#   CK_SESSION_ID  — telemetry session UUID
#   CK_API_URL     — API base URL (e.g. http://172.17.0.1:8000/api/v1)
#   CK_API_KEY     — API key for X-API-Key header
#
# Exits silently if env vars are missing (telemetry disabled).

[ -z "${CK_SESSION_ID:-}" ] && exit 0
[ -z "${CK_API_URL:-}" ] && exit 0
[ -z "${CK_API_KEY:-}" ] && exit 0

EVENT_JSON=$(cat)
EVENT_TYPE=$(echo "$EVENT_JSON" | jq -r '.event_type // empty')
[ -z "$EVENT_TYPE" ] && exit 0

PAYLOAD=$(echo "$EVENT_JSON" | jq -c '.payload // {}')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.%6NZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")

BODY=$(jq -nc \
  --arg sid "$CK_SESSION_ID" \
  --arg etype "$EVENT_TYPE" \
  --arg ts "$TIMESTAMP" \
  --argjson payload "$PAYLOAD" \
  '{session_id: $sid, events: [{event_type: $etype, timestamp: $ts, payload: $payload}]}')

# POST with short timeout — hook is already async so no need to background
curl -s -o /dev/null -w '' \
  -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${CK_API_KEY}" \
  --max-time 3 \
  -d "$BODY" \
  "${CK_API_URL}/telemetry/ingest"

exit 0

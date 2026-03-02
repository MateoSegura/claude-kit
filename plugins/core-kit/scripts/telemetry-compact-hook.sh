#!/usr/bin/env bash
set -uo pipefail
# telemetry-compact-hook.sh — PreCompact hook that emits session.compact events
# Fires when context compaction occurs (auto or manual).

[ -z "${CK_SESSION_ID:-}" ] && exit 0
[ -z "${CK_API_URL:-}" ] && exit 0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cat | jq -c '{
  event_type: "session.compact",
  payload: {
    trigger: (.source // "auto")
  }
}' 2>/dev/null | "${SCRIPT_DIR}/telemetry-post.sh"

exit 0

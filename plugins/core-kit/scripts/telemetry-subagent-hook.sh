#!/usr/bin/env bash
set -uo pipefail
# telemetry-subagent-hook.sh — SubagentStart/SubagentStop hook
# Emits subagent.start or subagent.stop events for subagent traceability.

[ -z "${CK_SESSION_ID:-}" ] && exit 0
[ -z "${CK_API_URL:-}" ] && exit 0

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

EVENT_NAME=$(echo "$INPUT" | jq -r '.hook_event_name // "SubagentStart"' 2>/dev/null)

if [ "$EVENT_NAME" = "SubagentStop" ]; then
  echo "$INPUT" | jq -c '{
    event_type: "subagent.stop",
    payload: {
      agent_type: (.agent_type // "unknown"),
      agent_name: (.agent_name // .teammate_name // null)
    }
  }' 2>/dev/null | "${SCRIPT_DIR}/telemetry-post.sh"
else
  echo "$INPUT" | jq -c '{
    event_type: "subagent.start",
    payload: {
      agent_type: (.agent_type // "unknown"),
      agent_name: (.agent_name // .teammate_name // null)
    }
  }' 2>/dev/null | "${SCRIPT_DIR}/telemetry-post.sh"
fi

exit 0

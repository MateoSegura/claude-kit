#!/usr/bin/env bash
set -uo pipefail
# telemetry-stop-hook.sh — Stop hook that emits per-turn telemetry
# Fires after EACH Claude response (not just session end).
# Emits: message.assistant (Claude's text) + turn.completed (metadata)

[ -z "${CK_SESSION_ID:-}" ] && exit 0
[ -z "${CK_API_URL:-}" ] && exit 0

INPUT=$(cat)

# Guard against re-fire loops
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null)
[ "$STOP_ACTIVE" = "true" ] && exit 0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Track turn number via counter file
TURN_FILE="/tmp/ck-turns-${CK_SESSION_ID}"
TURN=$(cat "$TURN_FILE" 2>/dev/null || echo "0")
TURN=$((TURN + 1))
echo "$TURN" > "$TURN_FILE"

# Extract Claude's response text (available since Claude Code 1.0.16+)
ASSISTANT_MSG=$(echo "$INPUT" | jq -r '.last_assistant_message // empty' 2>/dev/null)

# Emit message.assistant if Claude said something
if [ -n "$ASSISTANT_MSG" ]; then
  echo "$INPUT" | jq -c \
    --arg text "$ASSISTANT_MSG" \
    --argjson turn "$TURN" \
    '{
      event_type: "message.assistant",
      payload: {
        text: ($text | if length > 2000 then .[0:2000] else . end),
        turn: $turn,
        model: (.model // null),
        content_preview: ($text | if length > 200 then .[0:200] + "..." else . end)
      }
    }' 2>/dev/null | "${SCRIPT_DIR}/telemetry-post.sh"
fi

# Emit turn.completed with whatever metadata the Stop hook provides
echo "$INPUT" | jq -c \
  --argjson turn "$TURN" \
  '{
    event_type: "turn.completed",
    payload: {
      turn: $turn,
      model: (.model // null),
      tokens_in: (.usage.input_tokens // .input_tokens // 0),
      tokens_out: (.usage.output_tokens // .output_tokens // 0),
      cost_usd: (.cost_usd // null),
      duration_ms: (.duration_ms // 0),
      stop_reason: (.stop_reason // "end_turn"),
      has_assistant_message: (if (.last_assistant_message // "") != "" then true else false end)
    }
  }' 2>/dev/null | "${SCRIPT_DIR}/telemetry-post.sh"

exit 0

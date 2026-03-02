#!/usr/bin/env bash
set -uo pipefail
# telemetry-tool-hook.sh — PostToolUse hook that emits tool.used events
# Called by core-kit hooks.json on every tool use.
# Reads Claude Code hook JSON from stdin, transforms to telemetry event.

[ -z "${CK_SESSION_ID:-}" ] && exit 0
[ -z "${CK_API_URL:-}" ] && exit 0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Single jq pipeline: read hook input, produce telemetry event JSON
# Avoids shell variable interpolation issues with newlines/control chars
cat | jq -c '{
  event_type: "tool.used",
  payload: {
    tool_name: (.tool_name // "unknown"),
    tool_use_id: (.tool_use_id // ""),
    input_preview: ((.tool_input | tostring)[0:2000] // ""),
    is_error: ((.tool_result.is_error // false) | tostring == "true"),
    result_preview: ((.tool_result.text // .tool_result.content // "") | tostring[0:2000])
  }
}' 2>/dev/null | "${SCRIPT_DIR}/telemetry-post.sh"

exit 0

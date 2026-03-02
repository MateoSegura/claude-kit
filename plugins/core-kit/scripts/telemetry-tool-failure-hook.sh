#!/usr/bin/env bash
set -uo pipefail
# telemetry-tool-failure-hook.sh — PostToolUseFailure hook that emits tool.result errors
# Fires when a tool call fails. Captures the error for traceability.

[ -z "${CK_SESSION_ID:-}" ] && exit 0
[ -z "${CK_API_URL:-}" ] && exit 0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cat | jq -c '{
  event_type: "tool.result",
  payload: {
    tool_name: (.tool_name // "unknown"),
    tool_use_id: (.tool_use_id // ""),
    is_error: true,
    error: ((.tool_result.text // .tool_result.content // .error // "unknown error") | tostring[0:2000]),
    input_preview: ((.tool_input | tostring)[0:500] // "")
  }
}' 2>/dev/null | "${SCRIPT_DIR}/telemetry-post.sh"

exit 0

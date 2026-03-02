#!/usr/bin/env bash
set -uo pipefail
# telemetry-prompt-hook.sh — UserPromptSubmit hook that emits prompt.submitted events
# Called by core-kit hooks.json on every user prompt submission.
# Reads Claude Code hook JSON from stdin, transforms to telemetry event.

[ -z "${CK_SESSION_ID:-}" ] && exit 0
[ -z "${CK_API_URL:-}" ] && exit 0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cat | jq -c '{
  event_type: "prompt.submitted",
  payload: {
    prompt_text: ((.prompt // .user_message // "") | tostring[0:2000])
  }
}' 2>/dev/null | "${SCRIPT_DIR}/telemetry-post.sh"

exit 0

#!/usr/bin/env bash
set -uo pipefail
# telemetry-session-end-hook.sh — SessionEnd hook that emits session.end
# Fires once when the session terminates. Collects final aggregate stats.

[ -z "${CK_SESSION_ID:-}" ] && exit 0
[ -z "${CK_API_URL:-}" ] && exit 0

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Read turn counter for total turns
TURN_FILE="/tmp/ck-turns-${CK_SESSION_ID}"
TOTAL_TURNS=$(cat "$TURN_FILE" 2>/dev/null || echo "0")

# Clean up turn counter file
rm -f "$TURN_FILE"

# Extract reason from SessionEnd matcher (clear, logout, prompt_input_exit, etc.)
END_REASON=$(echo "$INPUT" | jq -r '.end_reason // .source // "unknown"' 2>/dev/null)

# Emit session.end with aggregate data
# Token/cost totals come from the Stop hooks per-turn — the API aggregates them.
# Here we just record the session termination event with what metadata we have.
jq -nc \
  --argjson turns "${TOTAL_TURNS:-0}" \
  --arg reason "$END_REASON" \
  '{event_type: "session.end", payload: {
    total_turns: $turns,
    stop_reason: $reason,
    plugins_loaded: 0,
    skills_invoked: {},
    hooks_fired: {},
    autorouter_matches: 0,
    autorouter_misses: 0,
    tool_uses: {},
    mcp_calls: {},
    compact_count: 0,
    total_tokens_in: 0,
    total_tokens_out: 0,
    cost_usd: null,
    model: null,
    duration_s: 0
  }}' \
  | "${SCRIPT_DIR}/telemetry-post.sh"

exit 0

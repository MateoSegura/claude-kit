#!/usr/bin/env bash
set -euo pipefail
# pre-compact-snapshot.sh — PreCompact hook
# Appends a COMPACTION_SNAPSHOT marker to active plan's status.log before context compaction.
# This marker helps the context-recovery agent identify the boundary between
# pre-compaction and post-compaction work.

# Source the shared helper to resolve active plan directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/resolve-active-plan.sh"

# Only write if active plan directory exists
if [ -z "$ACTIVE_PLAN_DIR" ]; then
  exit 0
fi

# Ensure status.log exists
touch "$ACTIVE_PLAN_DIR/status.log"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Append compaction boundary marker
cat >> "$ACTIVE_PLAN_DIR/status.log" << EOF
--- COMPACTION_SNAPSHOT [${TIMESTAMP}] ---
Context compaction triggered. State above this line was in context before compaction.
The context-recovery agent will read this file to restore orientation.
---
EOF

# Write structured state.json for context-recovery agent
# Derive active_plan relative path (ACTIVE_PLAN_DIR is already relative like "docs/plans/auth-refactor-2026-02-16")
ACTIVE_PLAN_REL="${ACTIVE_PLAN_DIR#./}"

# Parse the last COMPLETED entry from status.log
# Format: [TIMESTAMP] COMPLETED (task #ID): Phase NN: Title
LAST_COMPLETED_LINE=$(grep "COMPLETED (task #" "$ACTIVE_PLAN_DIR/status.log" | tail -1)

# Extract last_completed_task_id from "(task #ID)"
LAST_COMPLETED_TASK_ID=$(echo "$LAST_COMPLETED_LINE" | sed -n 's/.*COMPLETED (task #\([^)]*\)).*/\1/p')

# Extract last_completed_phase from "Phase NN" in the subject
LAST_COMPLETED_PHASE=$(echo "$LAST_COMPLETED_LINE" | sed -n 's/.*): Phase \([0-9]*\):.*/\1/p')

# Determine current_phase: prefer .current-phase file, else derive from last completed
if [ -f "$ACTIVE_PLAN_DIR/.current-phase" ]; then
  CURRENT_PHASE=$(cat "$ACTIVE_PLAN_DIR/.current-phase")
elif [ -n "$LAST_COMPLETED_PHASE" ]; then
  CURRENT_PHASE=$((LAST_COMPLETED_PHASE + 1))
else
  CURRENT_PHASE=""
fi

# Determine current_task_id: last completed task + 1
if [ -n "$LAST_COMPLETED_TASK_ID" ]; then
  CURRENT_TASK_ID=$((LAST_COMPLETED_TASK_ID + 1))
else
  CURRENT_TASK_ID=""
fi

# Write state.json using jq if available, fall back to printf
if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg active_plan "$ACTIVE_PLAN_REL" \
    --argjson current_phase "${CURRENT_PHASE:-null}" \
    --arg current_task_id "${CURRENT_TASK_ID:-}" \
    --arg last_completed_task_id "${LAST_COMPLETED_TASK_ID:-}" \
    --argjson last_completed_phase "${LAST_COMPLETED_PHASE:-null}" \
    --arg timestamp "$TIMESTAMP" \
    '{
      active_plan: $active_plan,
      current_phase: $current_phase,
      current_task_id: (if $current_task_id == "" then null else $current_task_id end),
      last_completed_task_id: (if $last_completed_task_id == "" then null else $last_completed_task_id end),
      last_completed_phase: $last_completed_phase,
      timestamp: $timestamp
    }' > "$ACTIVE_PLAN_DIR/state.json"
else
  # Fallback: printf-based JSON generation
  _ap_val="\"${ACTIVE_PLAN_REL}\""
  _cp_val="${CURRENT_PHASE:-null}"
  _ctid_val=$([ -n "$CURRENT_TASK_ID" ] && echo "\"${CURRENT_TASK_ID}\"" || echo "null")
  _lctid_val=$([ -n "$LAST_COMPLETED_TASK_ID" ] && echo "\"${LAST_COMPLETED_TASK_ID}\"" || echo "null")
  _lcp_val="${LAST_COMPLETED_PHASE:-null}"
  _ts_val="\"${TIMESTAMP}\""
  printf '{\n  "active_plan": %s,\n  "current_phase": %s,\n  "current_task_id": %s,\n  "last_completed_task_id": %s,\n  "last_completed_phase": %s,\n  "timestamp": %s\n}\n' \
    "$_ap_val" "$_cp_val" "$_ctid_val" "$_lctid_val" "$_lcp_val" "$_ts_val" \
    > "$ACTIVE_PLAN_DIR/state.json"
fi

exit 0

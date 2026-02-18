#!/usr/bin/env bash
set -euo pipefail
# update-status.sh — TaskCompleted hook
# Appends a timestamped entry to active spec's status.log when a TaskList item completes.
# Only writes if an active spec exists.

# Source the shared helper to resolve active spec directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/resolve-active-spec.sh"

# Read hook input from stdin
INPUT=$(cat)
TASK_SUBJECT=$(echo "$INPUT" | jq -r '.task.subject // "unknown task"')
TASK_ID=$(echo "$INPUT" | jq -r '.task.id // "?"')

# Only write if active spec directory exists
if [ -z "$ACTIVE_PLAN_DIR" ]; then
  exit 0
fi

# Ensure status.log exists
touch "$ACTIVE_PLAN_DIR/status.log"

# Append timestamped completion entry
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "[${TIMESTAMP}] COMPLETED (task #${TASK_ID}): ${TASK_SUBJECT}" >> "$ACTIVE_PLAN_DIR/status.log"

# Extract phase number from TASK_SUBJECT (format: "Phase NN: Title")
EXTRACTED_PHASE=$(echo "$TASK_SUBJECT" | sed -n 's/^Phase \([0-9]*\):.*/\1/p')

if [ -n "$EXTRACTED_PHASE" ]; then
  NEXT_PHASE=$((EXTRACTED_PHASE + 1))
  NEXT_PHASE_FILE=$(printf "%s/phases/phase-%02d.md" "$ACTIVE_PLAN_DIR" "$NEXT_PHASE")
  if [ -f "$NEXT_PHASE_FILE" ]; then
    echo "$NEXT_PHASE" > "$ACTIVE_PLAN_DIR/.current-phase"
  else
    # Next phase does not exist; plan may be complete — record the current completed phase
    echo "$EXTRACTED_PHASE" > "$ACTIVE_PLAN_DIR/.current-phase"
  fi
fi

exit 0

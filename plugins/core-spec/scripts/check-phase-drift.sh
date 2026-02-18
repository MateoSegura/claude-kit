#!/usr/bin/env bash
# check-phase-drift.sh — PostToolUse hook for Write|Edit
# Advisory drift detection: warns when an edit falls outside the current
# phase's declared scope. Does NOT block — the edit already happened.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/resolve-active-spec.sh"

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Spec files are always in scope
if echo "$FILE_PATH" | grep -qF "${SPEC_ROOT}/"; then
  exit 0
fi

# No active spec — nothing to check against
if [ -z "$ACTIVE_PLAN_DIR" ]; then
  exit 0
fi

ACTIVE=$(basename "$ACTIVE_PLAN_DIR")

# Find current phase number
PHASE_NUM_FILE="${SPEC_ROOT}/${ACTIVE}/.current-phase"
if [ -f "$PHASE_NUM_FILE" ]; then
  PHASE_NUM=$(cat "$PHASE_NUM_FILE" | tr -d '[:space:]')
else
  PHASE_NUM=""
  for f in "${SPEC_ROOT}/${ACTIVE}/phases"/phase-*.md; do
    [ -f "$f" ] || continue
    if grep -q '\- \[ \]' "$f" 2>/dev/null; then
      PHASE_NUM=$(basename "$f" | grep -o '[0-9]\+' | head -1 | sed 's/^0*//')
      break
    fi
  done
fi

if [ -z "$PHASE_NUM" ]; then
  exit 0
fi

PHASE_FILE=$(printf "%s/%s/phases/phase-%02d.md" "$SPEC_ROOT" "$ACTIVE" "$PHASE_NUM")
if [ ! -f "$PHASE_FILE" ]; then
  exit 0
fi

# Check if the edited file appears anywhere in the phase file
BASENAME=$(basename "$FILE_PATH")
if grep -qF "$FILE_PATH" "$PHASE_FILE" 2>/dev/null || grep -qF "$BASENAME" "$PHASE_FILE" 2>/dev/null; then
  exit 0
fi

# Drift detected — advisory message only
TARGETS=$(grep -A30 "## Files to Create/Modify" "$PHASE_FILE" 2>/dev/null \
  | grep '^\s*[-*]' | head -8 | sed 's/^\s*[-*]\s*//' | tr '\n' ', ' | sed 's/, $//')

echo "[spec] Drift: '$FILE_PATH' is not in Phase ${PHASE_NUM}'s declared scope."
if [ -n "$TARGETS" ]; then
  echo "[spec] Phase ${PHASE_NUM} targets: $TARGETS"
fi
echo "[spec] If intentional: update the phase file to include this file, or acknowledge the scope change."

exit 0

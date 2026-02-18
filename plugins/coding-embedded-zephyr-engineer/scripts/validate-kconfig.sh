#!/bin/bash
set -euo pipefail
# validate-kconfig.sh — Validates Kconfig symbol naming and checks for duplicates
# Called by hooks.json as a PostToolUse hook on Write|Edit tools
# Requires: jq

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')

# Only validate .conf and Kconfig files
if ! echo "$FILE_PATH" | grep -qE '\.(conf|Kconfig)$'; then
  exit 0
fi

# For .conf files, check CONFIG_ prefix
if echo "$FILE_PATH" | grep -qE '\.conf$'; then
  # Check for lines without CONFIG_ prefix (excluding comments and empty lines)
  INVALID_LINES=$(echo "$CONTENT" | grep -vE '^\s*(#|$)' | grep -vE '^CONFIG_' || true)
  if [[ -n "$INVALID_LINES" ]]; then
    echo "WARNING: Configuration file contains lines without CONFIG_ prefix. All Kconfig symbols must start with CONFIG_." >&2
    echo "$INVALID_LINES" | head -n 3 >&2
  fi

  # Check for duplicate symbols
  SYMBOLS=$(echo "$CONTENT" | grep -E '^CONFIG_' | sed 's/=.*//' | sort)
  DUPLICATES=$(echo "$SYMBOLS" | uniq -d)
  if [[ -n "$DUPLICATES" ]]; then
    echo "WARNING: Configuration file contains duplicate symbols. Last occurrence wins. Duplicates found:" >&2
    echo "$DUPLICATES" >&2
  fi
fi

# For Kconfig files, check for proper symbol definitions
if echo "$FILE_PATH" | grep -qE 'Kconfig$'; then
  # Check that config symbols don't include CONFIG_ prefix in definition
  if echo "$CONTENT" | grep -qE '^\s*config\s+CONFIG_'; then
    echo "WARNING: Kconfig file defines symbols with CONFIG_ prefix. The prefix is added automatically. Use 'config MY_SYMBOL' not 'config CONFIG_MY_SYMBOL'." >&2
  fi
fi

exit 0

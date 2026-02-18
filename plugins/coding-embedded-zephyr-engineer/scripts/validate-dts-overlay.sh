#!/bin/bash
set -euo pipefail
# validate-dts-overlay.sh — Validates devicetree overlay syntax and documentation
# Called by hooks.json as a PostToolUse hook on Write|Edit tools
# Requires: jq

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')

# Only validate .overlay and .dts files
if ! echo "$FILE_PATH" | grep -qE '\.(overlay|dts)$'; then
  exit 0
fi

# Check for balanced braces
OPEN_BRACES=$(echo "$CONTENT" | grep -o '{' | wc -l || echo 0)
CLOSE_BRACES=$(echo "$CONTENT" | grep -o '}' | wc -l || echo 0)

if [[ "$OPEN_BRACES" -ne "$CLOSE_BRACES" ]]; then
  echo "WARNING: Devicetree file has unbalanced braces (${OPEN_BRACES} open, ${CLOSE_BRACES} close). This will cause build errors." >&2
fi

# Check for at least one comment explaining a property
if ! echo "$CONTENT" | grep -qE '//.*='; then
  if ! echo "$CONTENT" | grep -qE '/\*.*\*/'; then
    echo "ADVISORY: Devicetree overlay lacks explanatory comments. Consider adding comments to document non-obvious properties and their purpose." >&2
  fi
fi

# Check for semicolons (DTS properties must end with semicolons)
if echo "$CONTENT" | grep -qE '=\s*[^;]+$' | head -n 1; then
  echo "WARNING: Devicetree property assignment may be missing semicolon. All properties must end with ';'." >&2
fi

exit 0

#!/usr/bin/env bash
set -euo pipefail
# validate-debug-config.sh — Validates debug configuration files after edits
# Called by hooks.json as a PostToolUse hook on Write|Edit tools
# Checks GDB scripts, launch.json, and overlay files for common issues.
# Non-blocking: always exits 0. Diagnostics are printed as informational output.
# Requires: jq

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Check GDB init/command scripts for common mistakes
if echo "$FILE_PATH" | grep -qE '\.(gdbinit|gdb|gdbcmds)$'; then
  echo "INFO: GDB script modified: $FILE_PATH" >&2
  # Warn if the script contains hardcoded absolute paths to ELF files
  if grep -qE '/home/|/Users/' "$FILE_PATH" 2>/dev/null; then
    echo "WARNING: GDB script contains hardcoded absolute paths. Use relative paths or \${workspaceFolder} for portability." >&2
  fi
fi

# Check launch.json / .vscode debug configs
if echo "$FILE_PATH" | grep -qE '(launch\.json|\.vscode/.*\.json)$'; then
  echo "INFO: VS Code debug config modified: $FILE_PATH" >&2
  # Validate JSON syntax
  if command -v jq &>/dev/null; then
    if ! jq . "$FILE_PATH" >/dev/null 2>&1; then
      echo "WARNING: $FILE_PATH contains invalid JSON. Debug launch configurations may not load correctly." >&2
    fi
  fi
fi

# Check devicetree overlay files modified during debug sessions
if echo "$FILE_PATH" | grep -qE '\.overlay$'; then
  echo "INFO: Devicetree overlay modified during debug session: $FILE_PATH" >&2
  echo "NOTE: Rebuild required for overlay changes to take effect. Run: west build" >&2
fi

# Check Kconfig fragments modified during debug sessions
if echo "$FILE_PATH" | grep -qE '(prj\.conf|\.conf)$'; then
  echo "INFO: Kconfig file modified during debug session: $FILE_PATH" >&2
  # Warn if debug-related configs are being changed
  if grep -qE '(CONFIG_DEBUG|CONFIG_LOG|CONFIG_ASSERT|CONFIG_THREAD_ANALYZER)' "$FILE_PATH" 2>/dev/null; then
    echo "NOTE: Debug-related Kconfig options changed. Rebuild required: west build" >&2
  fi
fi

# Always exit 0 — validation is informational, never blocking
exit 0

#!/bin/bash
set -euo pipefail
# block-write-edit.sh — Unconditionally block Write and Edit tool invocations
# Called by hooks.json as a PreToolUse hook on Write|Edit tools
# Requires: jq

echo "BLOCKED: This is a read-only diagnostic plugin. Write and Edit tools are not permitted. Use the engineer plugin to apply fixes." >&2
exit 2

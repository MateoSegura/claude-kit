#!/bin/bash
set -euo pipefail

# Block all Write and Edit tool invocations.
# The debugger is strictly read-only — it investigates and diagnoses,
# it never modifies code, configuration, or firmware.
# Requires: none

echo "BLOCKED: Debugger agents are strictly read-only. The debugger investigates and diagnoses — it never modifies code, configuration, or firmware. Use the engineer plugin to apply fixes." >&2
exit 2

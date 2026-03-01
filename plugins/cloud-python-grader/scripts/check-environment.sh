#!/usr/bin/env bash
set -euo pipefail
# check-environment.sh — Verifies static analysis tools are available at session start
# Called by hooks.json as a SessionStart hook
# Requires: jq (checked inline)
#
# Non-blocking: warns if tools are missing but always exits 0.
# The grader requires mypy, ruff, and optionally pyright for full analysis coverage.

MISSING_TOOLS=()
DEGRADED_TOOLS=()

# Check jq — required by all hook scripts
if ! command -v jq &>/dev/null; then
  MISSING_TOOLS+=("jq")
fi

# Check ruff — required for style/lint grading dimension
if ! command -v ruff &>/dev/null; then
  MISSING_TOOLS+=("ruff")
fi

# Check mypy — required for type correctness grading dimension
if ! command -v mypy &>/dev/null; then
  MISSING_TOOLS+=("mypy")
fi

# Check pyright — optional but preferred for strict type checking
if ! command -v pyright &>/dev/null; then
  DEGRADED_TOOLS+=("pyright")
fi

# Check python3 — baseline requirement
if ! command -v python3 &>/dev/null; then
  MISSING_TOOLS+=("python3")
fi

# Check pytest — required for test coverage grading dimension
if ! command -v pytest &>/dev/null; then
  DEGRADED_TOOLS+=("pytest")
fi

# Report missing required tools
if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
  echo "WARNING: cloud-python-grader — required analysis tools are missing: ${MISSING_TOOLS[*]}" >&2
  echo "Some grading dimensions will be unavailable. Install missing tools:" >&2
  for tool in "${MISSING_TOOLS[@]}"; do
    case "$tool" in
      jq)     echo "  jq:     apt install jq  OR  brew install jq" >&2 ;;
      ruff)   echo "  ruff:   pip install ruff" >&2 ;;
      mypy)   echo "  mypy:   pip install mypy" >&2 ;;
      python3) echo "  python3: Install from python.org or your system package manager" >&2 ;;
    esac
  done
fi

# Report optional tools that improve grading quality
if [ ${#DEGRADED_TOOLS[@]} -gt 0 ]; then
  echo "INFO: cloud-python-grader — optional tools not found (grading quality may be reduced): ${DEGRADED_TOOLS[*]}" >&2
  for tool in "${DEGRADED_TOOLS[@]}"; do
    case "$tool" in
      pyright) echo "  pyright: npm install -g pyright  (improves type correctness scoring)" >&2 ;;
      pytest)  echo "  pytest:  pip install pytest  (required for test execution dimension)" >&2 ;;
    esac
  done
fi

# Report clean environment
if [ ${#MISSING_TOOLS[@]} -eq 0 ] && [ ${#DEGRADED_TOOLS[@]} -eq 0 ]; then
  echo "INFO: cloud-python-grader — all analysis tools available (ruff, mypy, pyright, pytest)" >&2
fi

# Ensure analysis output directory exists
mkdir -p /tmp/grader-analysis

# Always non-blocking — grader can still operate in reduced capacity
exit 0

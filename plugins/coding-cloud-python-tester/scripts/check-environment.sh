#!/bin/bash
set -euo pipefail
# check-environment.sh — Verifies required tools are present at session start
# Called by hooks.json as a SessionStart hook (non-blocking)
# Checks: python3, pytest, ruff, docker, uv
# Requires: (none — this script bootstraps the environment check)

MISSING=()
WARNINGS=()

# Check python3
if ! command -v python3 &>/dev/null; then
  MISSING+=("python3")
else
  PYTHON_VERSION=$(python3 --version 2>&1)
  echo "  python3: ${PYTHON_VERSION}"
fi

# Check pytest
if ! command -v pytest &>/dev/null; then
  MISSING+=("pytest")
  WARNINGS+=("Install with: pip install pytest  OR  uv add pytest")
else
  PYTEST_VERSION=$(pytest --version 2>&1 | head -1)
  echo "  pytest: ${PYTEST_VERSION}"
fi

# Check ruff
if ! command -v ruff &>/dev/null; then
  MISSING+=("ruff")
  WARNINGS+=("Install ruff with: pip install ruff  OR  uv add ruff")
else
  RUFF_VERSION=$(ruff --version 2>&1)
  echo "  ruff: ${RUFF_VERSION}"
fi

# Check docker
if ! command -v docker &>/dev/null; then
  MISSING+=("docker")
  WARNINGS+=("Install Docker from: https://docs.docker.com/get-docker/")
else
  DOCKER_VERSION=$(docker --version 2>&1)
  echo "  docker: ${DOCKER_VERSION}"
fi

# Check uv
if ! command -v uv &>/dev/null; then
  MISSING+=("uv")
  WARNINGS+=("Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh")
else
  UV_VERSION=$(uv --version 2>&1)
  echo "  uv: ${UV_VERSION}"
fi

# Check jq (required by hook scripts)
if ! command -v jq &>/dev/null; then
  MISSING+=("jq")
  WARNINGS+=("Install jq with: apt install jq  OR  brew install jq")
fi

# Report
if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "" >&2
  echo "WARNING [coding-cloud-python-tester]: The following required tools are missing:" >&2
  for tool in "${MISSING[@]}"; do
    echo "  - ${tool}" >&2
  done
  echo "" >&2
  echo "Installation hints:" >&2
  for hint in "${WARNINGS[@]}"; do
    echo "  ${hint}" >&2
  done
  echo "" >&2
  echo "Hook scripts and test runs may fail until these tools are installed." >&2
fi

# Always exit 0 — environment check is non-blocking
exit 0

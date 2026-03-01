#!/usr/bin/env bash
set -euo pipefail
# check-environment.sh — Verifies required tools are available at session start
# Called by hooks.json as a SessionStart hook
# Non-blocking: always exits 0, prints warnings for missing tools
# Requires: nothing (self-contained)

WARNINGS=()
INFOS=()

# --- Required tools ---
REQUIRED_TOOLS=(jq python3 uv ruff mypy docker)

for tool in "${REQUIRED_TOOLS[@]}"; do
  if ! command -v "$tool" &>/dev/null; then
    WARNINGS+=("$tool is not installed or not on PATH")
  fi
done

# --- Python version check (3.11+) ---
if command -v python3 &>/dev/null; then
  PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
  PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
  PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
  if [[ "$PY_MAJOR" -lt 3 ]] || { [[ "$PY_MAJOR" -eq 3 ]] && [[ "$PY_MINOR" -lt 11 ]]; }; then
    WARNINGS+=("Python $PY_VERSION detected, but 3.11+ is required. Upgrade via pyenv or your system package manager.")
  else
    INFOS+=("Python $PY_VERSION OK")
  fi
fi

# --- Detect project type from working directory ---
CWD=$(pwd)
PROJECT_TYPE="unknown"

if [[ -f "$CWD/pyproject.toml" ]]; then
  if grep -q 'fastapi' "$CWD/pyproject.toml" 2>/dev/null; then
    PROJECT_TYPE="FastAPI"
  elif grep -q 'django' "$CWD/pyproject.toml" 2>/dev/null; then
    PROJECT_TYPE="Django"
  elif grep -q 'flask' "$CWD/pyproject.toml" 2>/dev/null; then
    PROJECT_TYPE="Flask"
  else
    PROJECT_TYPE="Python (pyproject.toml)"
  fi
fi

if [[ -f "$CWD/uv.lock" ]]; then
  INFOS+=("uv.lock found — using uv as package manager")
elif [[ -f "$CWD/poetry.lock" ]]; then
  INFOS+=("poetry.lock found — using poetry as package manager")
elif [[ -f "$CWD/requirements.txt" ]]; then
  INFOS+=("requirements.txt found — using pip as package manager")
fi

if [[ -f "$CWD/alembic.ini" ]] || [[ -d "$CWD/alembic" ]]; then
  INFOS+=("Alembic detected — database migration support available")
fi

if [[ -f "$CWD/docker-compose.yml" ]] || [[ -f "$CWD/docker-compose.yaml" ]]; then
  INFOS+=("Docker Compose found — local service stack available")
fi

if [[ -d "$CWD/k8s" ]] || [[ -d "$CWD/helm" ]] || [[ -d "$CWD/charts" ]]; then
  INFOS+=("Kubernetes/Helm manifests detected")
fi

# --- Output results ---
if [[ "${#INFOS[@]}" -gt 0 ]]; then
  echo "=== Environment Check ===" >&2
  echo "Project type: $PROJECT_TYPE" >&2
  for info in "${INFOS[@]}"; do
    echo "  OK: $info" >&2
  done
fi

if [[ "${#WARNINGS[@]}" -gt 0 ]]; then
  echo "=== Environment Warnings ===" >&2
  for warn in "${WARNINGS[@]}"; do
    echo "  WARNING: $warn" >&2
  done
  echo "Some tools are missing. The agent may not function correctly. Install missing tools before proceeding." >&2
fi

# Non-blocking — always exit 0 so the session can continue
exit 0

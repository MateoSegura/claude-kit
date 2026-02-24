#!/bin/bash
set -euo pipefail
# check-test-file.sh — Enforces test-file-only write policy
# Called by hooks.json as a PreToolUse hook on Write|Edit tools
# Allowed targets: test_*.py, conftest.py, pytest config in pyproject.toml
# Blocked targets: production source, migrations, deployment configs
# Requires: jq

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Derive the basename for basename-level checks
BASENAME=$(basename "$FILE_PATH")

# ------------------------------------------------------------------
# ALLOW LIST — permit writes to recognised test infrastructure files
# ------------------------------------------------------------------

# Allow: test_*.py anywhere in the tree
if echo "$BASENAME" | grep -qE '^test_.+\.py$'; then
  exit 0
fi

# Allow: conftest.py (pytest fixture file) anywhere
if [[ "$BASENAME" == "conftest.py" ]]; then
  exit 0
fi

# Allow: pyproject.toml — but ONLY when it lives at a path that
# includes a pytest/tool.pytest section. We cannot parse TOML here
# so we allow pyproject.toml writes unconditionally and rely on the
# PostToolUse prompt hook to catch abuse. The tester agent should
# only be touching [tool.pytest.ini_options] sections anyway.
if [[ "$BASENAME" == "pyproject.toml" ]]; then
  exit 0
fi

# Allow: pytest.ini, setup.cfg (pytest config files)
if [[ "$BASENAME" == "pytest.ini" || "$BASENAME" == "setup.cfg" ]]; then
  exit 0
fi

# ------------------------------------------------------------------
# BLOCK LIST — explicit high-risk patterns
# ------------------------------------------------------------------

# Block: database migration files
if echo "$FILE_PATH" | grep -qE '/(migrations?|alembic/versions?)/'; then
  echo "BLOCKED: Writing to migration files is not allowed for the tester role. Path: ${FILE_PATH}" >&2
  echo "Only test_*.py, conftest.py, and pytest configuration files may be written." >&2
  exit 2
fi

# Block: deployment / infrastructure configs
if echo "$FILE_PATH" | grep -qE '\.(tf|tfvars|yaml|yml|json|toml|ini|env)$'; then
  # Allow pyproject.toml already handled above; catch other TOML/config files
  if echo "$FILE_PATH" | grep -qE '/(deploy|infra|terraform|helm|k8s|kubernetes|ansible|docker-compose|\.github/workflows)/'; then
    echo "BLOCKED: Writing to deployment or infrastructure configuration is not allowed for the tester role. Path: ${FILE_PATH}" >&2
    exit 2
  fi

  # Block Dockerfile variants
  if echo "$BASENAME" | grep -qiE '^dockerfile(\..+)?$'; then
    echo "BLOCKED: Dockerfiles are not test files. Path: ${FILE_PATH}" >&2
    exit 2
  fi

  # Block docker-compose files
  if echo "$BASENAME" | grep -qiE '^docker-compose.*\.(yml|yaml)$'; then
    echo "BLOCKED: Docker Compose files are not test files. Path: ${FILE_PATH}" >&2
    exit 2
  fi

  # Block CI/CD workflow files
  if echo "$FILE_PATH" | grep -qE '\.github/workflows/'; then
    echo "BLOCKED: CI/CD workflow files are protected. Path: ${FILE_PATH}" >&2
    exit 2
  fi
fi

# Block: production Python source files that are NOT test files
# Heuristic: any .py file whose basename does not start with test_ and is not conftest.py
if echo "$BASENAME" | grep -qE '\.py$'; then
  # At this point test_*.py and conftest.py are already allowed above.
  # Any remaining .py file is production source — block it.
  echo "BLOCKED: '${BASENAME}' is not a test file. The tester role may only write test_*.py or conftest.py." >&2
  echo "If you need to create a new source module, that is the engineer role's responsibility." >&2
  exit 2
fi

# Default: block anything not explicitly allowed
echo "BLOCKED: '${FILE_PATH}' is not a recognised test file. Allowed writes: test_*.py, conftest.py, pyproject.toml (pytest config only)." >&2
exit 2

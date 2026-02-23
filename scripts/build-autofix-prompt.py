#!/usr/bin/env python3
"""Build the Claude auto-fix prompt for a CI failure log.

Usage: python3 scripts/build-autofix-prompt.py <log-file>
Writes the prompt to stdout.
"""
import pathlib
import sys

if len(sys.argv) < 2:
    sys.exit("Usage: build-autofix-prompt.py <log-file>")

logs = pathlib.Path(sys.argv[1]).read_text()
cwd = pathlib.Path.cwd()

prompt = f"""You are fixing CI failures in a Claude Code plugin repository.

The CI check "fast-validate" failed on this PR. It runs three checks:
1. Python syntax check: python3 -m py_compile claude-kit
2. CLI smoke tests: bash scripts/test-cli.sh
3. Tier 1 plugin validation: python3 scripts/validate-plugins.py --changed --json

Here are the failure logs:
---
{logs}
---

Fix the failing check(s) by editing the relevant files in the repository.
The repository root is: {cwd}

Rules:
- Read any file before editing it
- Make only the minimal change needed to fix the specific failure
- Do not refactor or clean up unrelated code
- After fixing, output "FIXES_COMPLETE" followed by a one-line summary of what you changed
"""

print(prompt)

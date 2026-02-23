#!/usr/bin/env python3
"""Build the Claude auto-fix prompt for a nightly review output.

Usage: python3 scripts/build-nightly-prompt.py <review-file>
Writes the prompt to stdout.
"""
import pathlib
import sys

if len(sys.argv) < 2:
    sys.exit("Usage: build-nightly-prompt.py <review-file>")

review = pathlib.Path(sys.argv[1]).read_text()
cwd = pathlib.Path.cwd()

prompt = f"""You are fixing plugin quality issues found in an automated nightly review.

Here is the review output:
{review}

Fix ALL WARN findings by directly editing the plugin files in the repository.

Rules:
- Fix only what the review explicitly flagged as WARN or FATAL
- Do not fix NOTEs (they are informational only)
- Do not add new agents, commands, or skills
- Read each affected file before editing it
- After all fixes are complete, output a summary titled "## Fixes Applied" listing each change

The plugin files are in: {cwd}/plugins/
"""

print(prompt)

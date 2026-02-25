# Cross-Team Consistency — Mandatory for All Plugin Bug Fixes

## Rule

When fixing a bug or making an improvement in **any** plugin that belongs to a
team (engineer, grader, tester, debugger, knowledge), you MUST check whether the
same issue exists in the equivalent plugins across ALL other teams and fix them
too.

## Teams

The repository currently has three plugin teams sharing the same role
architecture:

| Team prefix | Roles |
|-------------|-------|
| `embedded-zephyr-` | engineer, grader, tester, debugger, knowledge |
| `frontend-svelte-` | engineer, grader, tester, debugger, knowledge |
| `cloud-python-` | engineer, grader, tester, debugger, knowledge |

## What to check

When you fix something in one plugin, scan the **same role** in every other
team first:

```
# Example: fixing a hook script bug in the zephyr engineer
# You MUST also check:
plugins/frontend-svelte-engineer/
plugins/cloud-python-engineer/
```

Then check whether the same pattern exists in **other roles within the same
team** (e.g., a hook bug in the engineer may also affect the tester):

```
# Same team, different roles
plugins/embedded-zephyr-tester/
plugins/embedded-zephyr-grader/
plugins/embedded-zephyr-debugger/
plugins/embedded-zephyr-knowledge/
```

## Specific patterns to always cross-check

| Category | What to grep / inspect |
|----------|----------------------|
| Hook scripts | `scripts/*.sh` — same logic bugs, same `jq` patterns, same `set -euo pipefail` edge cases |
| hooks.json | `hooks/hooks.json` — same hook types, same matchers, same prompt wording patterns |
| Report output paths | `commands/grade.md`, `commands/compare.md`, report-generator agents — same directory conventions |
| Agent frontmatter | `agents/*.md` — `tools:` vs `allowed-tools:` mistakes, missing `identity` in skills list |
| Version consistency | If bumping one plugin, check if the same fix applies to siblings that also need a bump |

## Verification

After applying cross-team fixes, run:

```bash
python3 scripts/validate-plugins.py --all --strict
```

And manually confirm version + README badge consistency for every plugin you
touched.

## Why this rule exists

Plugins across teams share the same architectural patterns (hooks, agents,
commands, scripts). A bug in one team's hook script almost always means the
same bug exists in the other two teams. Fixing only one team creates silent
drift that surfaces later as confusing errors for users.

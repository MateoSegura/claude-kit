---
allowed-tools: Bash, Read
description: Run Tier 1 structural checks on all plugins, then invoke system-maker:validate for semantic review. Reports combined summary. Read-only — does not fix anything.
---

# Validate All Plugins

Run a two-tier validation pass over every plugin in `plugins/`.

## Step 1 — Tier 1 (fast, structural)

Run the Python validator against all plugins:

```bash
python3 scripts/validate-plugins.py --all
```

Report the output verbatim to the user. If any FATAL failures are found, flag
them clearly before proceeding.

## Step 2 — Tier 2-4 (semantic, requires system-maker)

Note to the user:

> **Semantic review requires system-maker loaded.** To run it:
>
> ```bash
> claude-kit --kit system-maker
> ```
>
> Then invoke: `/system-maker:validate` (validates all plugins)

## Step 3 — Combined Summary

After Tier 1 completes, present:

- Total plugins checked
- Pass / warn / fail counts from Tier 1
- Exit code (0 = all pass, 1 = failures, 2 = warnings only)
- Reminder to run semantic review if not already done
- Specific actionable fixes for any failures found

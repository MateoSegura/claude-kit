---
allowed-tools: Bash, Read
description: Run Tier 1 structural checks on all plugins, then invoke system-maker:validate for semantic review. Reports combined summary. Read-only — does not fix anything.
---

# Validate All Plugins

Run a two-tier validation pass over every plugin in `plugins/`.

## Step 1 — Tier 1 (fast, structural)

Run the Python validator against all plugins:

```bash
python3 scripts/validate-plugins.py --all --strict
```

Report the output verbatim to the user. If any FATAL failures are found, flag
them clearly before proceeding.

<!-- Enriched by core-ai:instrument on 2026-03-02 — added: Steps 2-5 for full CI parity -->

## Step 2 — Plugin Consistency

Run cross-reference and frontmatter checks:

```bash
bash scripts/test-plugin-consistency.sh
```

This checks version badge alignment, agent skill cross-references, hook type
safety, frontmatter field names, and CHANGELOG version entries.

## Step 3 — CLI Validation

Run syntax check and smoke tests:

```bash
python3 -m py_compile claude-kit && echo "Syntax OK"
bash scripts/test-cli.sh
```

## Step 4 — Docs Validation

Run the structured documentation checks:

```bash
bash scripts/validate-docs.sh
```

## Step 5 — Library Unit Tests

Run the `claude_kit` library test suite:

```bash
.venv-lib/bin/python -m pytest test/ -v --tb=short \
  --ignore=test/scenarios --ignore=test/src
```

If `.venv-lib` does not exist, create it first:

```bash
python3 -m venv .venv-lib && .venv-lib/bin/pip install -q -e ".[dev]"
```

## Step 6 — API Tests

Run the FastAPI telemetry API test suite:

```bash
cd api && .venv/bin/python -m pytest -v --tb=short
```

If `api/.venv` does not exist, create it first:

```bash
cd api && python3 -m venv .venv && .venv/bin/pip install -q -e ".[dev]"
```

## Step 7 — Upgrade Safety Check

Run the upgrade safety check (skipped on main):

```bash
bash scripts/test-upgrade-safety.sh --from HEAD~1 --to HEAD --ci --json
```

Review output for breaking or cautionary changes.

## Step 8 — Semantic Review (requires system-maker)

Note to the user:

> **Semantic review requires system-maker loaded.** To run it:
>
> ```bash
> claude-kit --kit system-maker
> ```
>
> Then invoke: `/system-maker:validate` (validates all plugins)

## Step 9 — Combined Summary

After all steps complete, present:

- Total plugins checked
- Pass / warn / fail counts from Tier 1
- Plugin consistency: pass / fail
- CLI syntax + smoke tests: pass / fail
- Docs validation: pass / fail
- Library tests: pass / fail (with test count)
- API tests: pass / fail (with test count)
- Upgrade safety: breaking / cautionary / clean
- Reminder to run semantic review if not already done
- Specific actionable fixes for any failures found

---
description: Run a full documentation site health report
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# /pal-docs-health -- Documentation Site Health Report

You are running a full health check on the documentation site. Follow this
workflow exactly.

## Workflow

### Step 1: Run the site validator

```bash
bash docs-site/validate-site.sh
```

This checks:
1. Every nav entry points to an existing source file
2. No duplicate nav entries
3. No orphan pages (files not wired into nav)
4. Cross-references (PROC-XXX) resolve to real files
5. `site.json` is valid JSON with a semver version

### Step 2: Check for stale content

Find documentation files not modified in the last 6 months:

```bash
find processes/ mappings/ -name "*.md" -type f -mtime +180
```

Report these as candidates for review.

### Step 3: Read site metadata

```bash
cat docs-site/site.json
```

Report version, build number, last build date, page count, and content hash.

### Step 4: Compile the report

Present a structured report:

```
Documentation Site Health Report
================================

Version: X.Y.Z (build N)
Last build: <date>
Pages: <count>

Nav Consistency:  PASS/FAIL  (N entries checked)
Orphan Pages:     PASS/WARN  (N orphans found)
Cross-References: PASS/WARN  (N refs checked, M broken)
Site Metadata:    PASS/FAIL
Stale Content:    N files older than 6 months

Issues:
  - <list any errors or warnings>
```

Exit with the same code as `validate-site.sh` -- 0 if clean, 1 if errors.

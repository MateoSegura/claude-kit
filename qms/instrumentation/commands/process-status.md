---
description: Report QMS process health, maturity levels, governance coverage, and staleness
allowed-tools: Read, Glob, Grep, Bash
---

# QMS Process Status Report

Generate a comprehensive Process Asset Library health report.

## Steps

1. **Count processes by status and maturity:**
   - Scan `qms/processes/base/` and `qms/processes/gov/` for all PROC-*.md files
   - Extract `**Status:**` and `**Maturity:**` fields from each
   - Tally counts by status (draft/active/deprecated) and maturity level

2. **Check governance coverage:**
   - For each subdirectory in `docs/`, check if `INDEX.md` has a `**Governing Process:**` field
   - List any ungoverned directories

3. **Check staleness:**
   - Extract `**Last Reviewed:**` dates from all process documents
   - Flag any process not reviewed in the last 6 months (180 days)
   - List the 5 oldest processes by review date

4. **Check validation health:**
   - Run `bash qms/scripts/validate-processes.sh` and capture results
   - Run `bash scripts/validate-docs.sh` and capture results
   - Report pass/fail/warn counts

5. **Format the report:**

```
## QMS Process Status Report — <date>

### Summary
- Total processes: X (base: Y, gov: Z)
- Status: X active, Y draft, Z deprecated
- Maturity: X initial, Y managed, Z defined, W measured, V optimizing

### Governance Coverage
- Governed directories: X/Y
- Ungoverned: <list or "none">

### Staleness Warnings
- <process>: last reviewed <date> (<N> days ago)

### Validation
- Layer 4 (docs): X pass, Y warn, Z fail
- Layer 5 (processes): X pass, Y warn, Z fail

### Maturity Distribution
| Level | Count | Processes |
|-------|-------|-----------|
| initial | X | PROC-LC-001, ... |
| managed | X | ... |
| defined | X | ... |
| measured | X | ... |
| optimizing | X | ... |
```

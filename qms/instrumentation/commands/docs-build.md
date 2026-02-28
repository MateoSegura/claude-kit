---
description: Build the production documentation site with version tracking
allowed-tools:
  - Bash
  - Read
  - Glob
---

# /qms-docs-build — Build Production Documentation Site

You are building the production documentation site. Follow this workflow
exactly.

## Workflow

### Step 1: Run the production build

```bash
bash qms/docs-site/build.sh --prod
```

This will:
1. Merge content from `docs/` and `qms/` into `.docs-build/`
2. Build the site with `mkdocs build --strict`
3. Increment `buildNumber` in `qms/docs-site/site.json`
4. Compute `contentHash` from all source markdown files
5. Record `pageCount` and `siteSize`

### Step 2: Validate

Run the site health check:

```bash
bash qms/docs-site/validate-site.sh
```

### Step 3: Report results

Read `qms/docs-site/site.json` and report:
- Version and build number
- Content hash (note if unchanged from previous build)
- Page count and site size
- Any warnings from the build or validation

### Step 4: Check for issues

If the build fails:
1. Check the error output for missing files referenced in `mkdocs.yml` nav
2. Verify all nav entries point to files in `docs/` or `qms/` (not `.docs-build/`)
3. Check YAML syntax in `mkdocs.yml`

---
description: Build the production documentation site with version tracking
allowed-tools:
  - Bash
  - Read
  - Glob
---

# /pal-docs-build -- Build Production Documentation Site

You are building the production documentation site. Follow this workflow
exactly.

## Workflow

### Step 1: Run the production build

```bash
bash docs-site/build.sh --prod
```

This will:
1. Merge content from `processes/` and `mappings/` into `.docs-build/`
2. Build the site with `mkdocs build`
3. Increment `buildNumber` in `docs-site/site.json`
4. Compute `contentHash` from all source markdown files
5. Record `pageCount` and `siteSize`

### Step 2: Validate

Run the site health check:

```bash
bash docs-site/validate-site.sh
```

### Step 3: Report results

Read `docs-site/site.json` and report:
- Version and build number
- Content hash (note if unchanged from previous build)
- Page count and site size
- Any warnings from the build or validation

### Step 4: Check for issues

If the build fails:
1. Check the error output for missing files referenced in `mkdocs.yml` nav
2. Verify all nav entries point to files in `processes/` or `mappings/` (not `.docs-build/`)
3. Check YAML syntax in `mkdocs.yml`

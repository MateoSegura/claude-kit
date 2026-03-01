---
description: Deploy the documentation site to GitHub Pages
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - AskUserQuestion
---

# /pal-docs-deploy -- Deploy to GitHub Pages

You are deploying the documentation site. Follow this workflow exactly.

## Workflow

### Step 1: Build for production

```bash
bash docs-site/build.sh --prod
```

### Step 2: Check content changes

Read `docs-site/site.json` and check `contentHash`. If it changed since the
last build, ask the user what version bump to apply:

- **patch** -- content edits, CSS tweaks, typo fixes
- **minor** -- new section or tab added, navigation restructured
- **major** -- full redesign, breaking URL changes

Update `site.json`:
- Set the new version
- Add a changelog entry with today's date and a brief summary

### Step 3: Verify branch

Check the current git branch:

```bash
git branch --show-current
```

If not on `main`, warn the user that GitHub Pages typically deploys from `main`.
Ask whether to proceed anyway.

### Step 4: Deploy

Use `mkdocs gh-deploy` or push the built site:

```bash
cd "$(git rev-parse --show-toplevel)"
mkdocs gh-deploy -f .docs-build/mkdocs.yml --force
```

### Step 5: Report

Print:
- Deployed version and build number
- The GitHub Pages URL (typically `https://<org>.github.io/<repo>/`)
- Remind the user to commit the updated `site.json` if the version changed

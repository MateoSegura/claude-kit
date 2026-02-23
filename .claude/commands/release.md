---
allowed-tools: Bash, Read, Edit
description: Finalize a release — run preflight checks, promote [Unreleased] to a versioned CHANGELOG section, commit, tag, and ask before pushing. Requires no uncommitted changes.
---

# Release

Prepare and create a new claude-kit release from the current `[Unreleased]`
CHANGELOG draft.

## Step 1 — Preflight: Uncommitted Changes

Check for uncommitted changes:

```bash
git status --short
```

If any uncommitted files are found, stop and tell the user to commit or stash
them before releasing.

## Step 2 — Preflight: Tier 1 Validation (Strict)

Run the validator in strict mode (warnings = failures):

```bash
python3 scripts/validate-plugins.py --all --strict
```

If any failures are found, stop and report them. Do not proceed with a release
that has broken plugins.

## Step 3 — Read the [Unreleased] Draft

Read `CHANGELOG.md` and extract the content of the `## [Unreleased]` section.

If the section is empty or missing, tell the user: "Nothing staged for release.
Use `/bump-plugin` to prepare changes first."

## Step 4 — Compute Release Version

From the `[Unreleased]` content, identify the highest-severity bump across all
plugin changes listed:
- If any plugin had a **major** bump → repo version is major bump from last tag
- If any plugin had a **minor** bump → repo version is minor bump from last tag
- Otherwise → repo version is patch bump from last tag

Show the computed version and ask for confirmation:
> "Computed version: v1.2.0 — proceed?"

The user may override with a specific version.

## Step 5 — Get Last Tag

```bash
git describe --tags --abbrev=0 2>/dev/null || echo "none"
```

If no tags exist, the release version is the computed version (starting from
the [Unreleased] content).

## Step 6 — Finalize CHANGELOG

In `CHANGELOG.md`:
1. Replace `## [Unreleased]` with `## [x.y.z] - YYYY-MM-DD` (today's date)
2. Add a new empty `## [Unreleased]` section above it for future drafts

## Step 7 — Commit

```bash
git add CHANGELOG.md plugins/*/\\.claude-plugin/plugin.json
git commit -m "chore: release vX.Y.Z"
```

## Step 8 — Tag

```bash
git tag -a "vX.Y.Z" -m "Release vX.Y.Z"
```

## Step 9 — Confirm Before Push

Show the user:
- The commit that was made
- The tag that was created
- What `git push && git push --tags` will do

Then ask: **"Push to origin? [y/N]"**

If confirmed:
```bash
git push && git push --tags
```

The `release.yml` workflow will then create the GitHub Release automatically.

If declined, tell the user they can push manually when ready.

---
allowed-tools: Bash, Read, Edit, Glob, Grep, Write
description: Finalize a release — run preflight checks, promote [Unreleased] to a versioned CHANGELOG section, commit, tag, push, monitor CI until the GitHub Release is published, and auto-fix any CI failures along the way.
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

## Step 7 — Update Roadmap

Read `ROADMAP.md` and update it to reflect the release:

1. Add the new version to the **Shipped** section (top of the list, most recent
   first) with a one-line summary and today's date:
   ```
   - **vX.Y.Z** — Short Summary (Mon DD, YYYY)
     Brief description of what shipped
   ```

2. If any **In Progress** items were completed by this release, move them to
   Shipped or remove them.

3. If there are no remaining items in **In Progress** or **Planned**, remove
   those sections entirely. An empty roadmap with only **Shipped** is valid.

4. Show the updated roadmap to the user for confirmation before proceeding.

The goal is to keep ROADMAP.md honest — it should only contain real plans, not
placeholders. "No upcoming plans" is fine.

## Step 8 — Commit

```bash
git add CHANGELOG.md ROADMAP.md plugins/*/\\.claude-plugin/plugin.json
git commit -m "chore: release vX.Y.Z"
```

## Step 9 — Tag

```bash
git tag -a "vX.Y.Z" -m "Release vX.Y.Z"
```

## Step 10 — Confirm Before Push

Show the user:
- The commit that was made
- The tag that was created
- What `git push && git push --tags` will do

Then ask: **"Push to origin? [y/N]"**

If confirmed:
```bash
git push && git push --tags
```

If declined, tell the user they can push manually when ready and **stop here**.

If pushed, proceed to Step 11.

## Step 11 — Monitor CI Until Complete

After pushing, enter a monitoring loop. Two CI workflows will trigger:
1. **fast-validate** (push.yml) — triggered by the branch push
2. **release** (release.yml) — triggered by the tag push (creates the GitHub
   Release)

### Monitoring procedure

1. Wait 15 seconds for CI to register the push.

2. Find the workflow runs triggered by this push:

```bash
# Get the commit SHA we just pushed
HEAD_SHA=$(git rev-parse HEAD)
TAG_NAME="vX.Y.Z"  # the tag we just pushed

# Find fast-validate run for this commit
gh run list --workflow=push.yml --branch=$(git branch --show-current) --limit=3 --json databaseId,status,conclusion,headSha --jq '.[] | select(.headSha=="'$HEAD_SHA'")'

# Find release run for this tag
gh run list --workflow=release.yml --limit=3 --json databaseId,status,conclusion,headSha --jq '.[] | select(.headSha=="'$HEAD_SHA'")'
```

3. Poll every 20 seconds until **both** workflows reach a terminal state
   (`completed`). On each poll, report the current status concisely:

```
CI status: fast-validate=in_progress, release=queued
```

4. If a workflow has been `queued` for more than 3 minutes with no progress,
   note this to the user but keep polling — the self-hosted runner may be busy.

5. Once both workflows complete, check their conclusions:
   - Both `success` → proceed to **Step 13** (Verify Release)
   - Any `failure` → proceed to **Step 12** (Auto-Fix)
   - Any `cancelled` → report and ask the user what to do

## Step 12 — Auto-Fix CI Failures

When a CI workflow fails, attempt to diagnose and fix it locally. This step
may loop up to **3 times** — if all 3 attempts fail, stop and report.

### 12a. Fetch failure logs

```bash
gh run view <FAILED_RUN_ID> --log 2>&1 | tail -300
```

Read the log output and identify the root cause. Common failures:

| Failure | Fix strategy |
|---------|-------------|
| Plugin validation error (validate-plugins.py) | Fix the plugin file locally with Edit |
| CLI syntax error (py_compile) | Fix the CLI script with Edit |
| Plugin consistency check (test-plugin-consistency.sh) | Fix cross-references, frontmatter, or hook config |
| CLI smoke test failure (test-cli.sh) | Fix the CLI script or test expectations |
| CHANGELOG entry missing for tag | Fix CHANGELOG.md with Edit |
| Release body extraction failed | Fix CHANGELOG formatting with Edit |

### 12b. Apply the fix

Use Read and Edit to fix the identified issue. Run the same check locally to
verify:

```bash
# Depending on what failed:
python3 scripts/validate-plugins.py --all --strict
bash scripts/test-cli.sh
bash scripts/test-plugin-consistency.sh
python3 -m py_compile claude-kit
```

### 12c. Re-commit, re-tag, re-push

After fixing:

```bash
# Stage and commit the fix
git add -A
git commit -m "fix: <description of what was fixed>"

# Delete the old tag locally and remotely, then recreate
git tag -d "vX.Y.Z"
git push origin :refs/tags/vX.Y.Z
git tag -a "vX.Y.Z" -m "Release vX.Y.Z"

# Push the fix commit and the new tag
git push && git push --tags
```

### 12d. Resume monitoring

Go back to **Step 11** with the new commit SHA. Increment the attempt counter.

If this is already the 3rd attempt, **stop** and report:

```
Release failed after 3 auto-fix attempts. The remaining issue requires
manual intervention:

<describe the failure>

The tag vX.Y.Z has been left on the latest commit. You can:
- Fix manually and force-push
- Delete the tag with: git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z
```

## Step 13 — Verify Release Published

After both CI workflows succeed, verify the GitHub Release was actually created:

```bash
gh release view "vX.Y.Z" --json tagName,name,isDraft,isPrerelease,url,createdAt
```

If the release exists and is not a draft:

```
Release vX.Y.Z published successfully!

  URL:     <release URL>
  Tag:     vX.Y.Z
  Created: <timestamp>

The release is now available for download via:
  claude-kit update
```

If the release does not exist (the `gh release view` command fails), check
whether `release.yml` created it but as a draft, or if the workflow had a
partial failure. Report what happened and suggest next steps.

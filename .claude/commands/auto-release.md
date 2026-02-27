---
allowed-tools: Bash, Read, Edit, Glob, Grep, Write
description: Fully automated release for CI — no confirmations, no approvals. Commits dirty trees, validates, finalizes CHANGELOG, opens and merges PR, tags, pushes, monitors CI, and auto-fixes failures. Exits non-zero on unrecoverable failure.
---

# Auto-Release

Fully automated release pipeline designed for CI environments. Identical to
`/release` but with **zero user interaction** — all confirmation gates are
removed and decisions are made automatically.

**This command must never ask the user a question.** If a decision point is
ambiguous, choose the safe default and log the reasoning.

## Abort conditions

Stop immediately (do not attempt recovery) if any of these are true:

- No changes exist since the last tag (nothing committed, nothing uncommitted)
- Current branch is not `main` and not a `release/*` branch (unless dirty tree
  triggers branch creation)
- Unfixable architectural violations are found (knowledge plugin with agents,
  broken companions, role mismatch)
- 3 auto-fix attempts have been exhausted

When stopping, print a clear `AUTO-RELEASE FAILED:` message with the reason
and exit. Do not suggest manual steps — CI logs should be self-explanatory.

---

## Step 1 — Analyze Changes & Draft [Unreleased]

Read `CHANGELOG.md` and extract the `## [Unreleased]` section content.

### If [Unreleased] already has content

Skip to Step 2 — the draft is ready.

### If [Unreleased] is empty or missing

Auto-analyze all changes since the last tag, bump plugin versions, and draft
the CHANGELOG section. No confirmation — all decisions are automatic.

#### 1a. Get baseline

```bash
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
```

#### 1b. Find all changed files

Include both committed and uncommitted changes:

```bash
# Committed changes since last tag
if [ -n "$LAST_TAG" ]; then
  git diff --name-only "$LAST_TAG"...HEAD
else
  git ls-files
fi

# Uncommitted changes
git status --short
```

If no changes at all:

```
AUTO-RELEASE FAILED: no changes since $LAST_TAG. Nothing to release.
```

Stop here.

#### 1c. Identify and bump changed plugins

From the changed files, extract unique plugin names under `plugins/`. For each:

1. **Read current `plugin.json`** to get the current version.

2. **Get old version** from the last tag:

```bash
git show "$LAST_TAG:plugins/<name>/.claude-plugin/plugin.json" 2>/dev/null | jq -r .version
```

3. **Classify the change** by examining what files changed:

| What changed | Classification | Bump |
|-------------|---------------|------|
| Agent removed or renamed | Breaking | MAJOR |
| Command removed or renamed | Breaking | MAJOR |
| Skill directory removed or renamed | Breaking | MAJOR |
| New agent added | New capability | MINOR |
| New command added | New capability | MINOR |
| New skill directory added | New capability | MINOR |
| New plugin (didn't exist at last tag) | New capability | MINOR |
| Everything else (content, docs, hooks, scripts) | Fix/improvement | PATCH |

Check what existed at `$LAST_TAG` vs now:

```bash
# Agents
git show "$LAST_TAG:plugins/<name>/agents/" 2>/dev/null
ls plugins/<name>/agents/ 2>/dev/null

# Commands
git show "$LAST_TAG:plugins/<name>/commands/" 2>/dev/null
ls plugins/<name>/commands/ 2>/dev/null

# Skills
git show "$LAST_TAG:plugins/<name>/skills/" 2>/dev/null
ls plugins/<name>/skills/ 2>/dev/null
```

4. **Compute new version** — apply the bump to the old version:
   - PATCH: `x.y.z` → `x.y.(z+1)`
   - MINOR: `x.y.z` → `x.(y+1).0`
   - MAJOR: `x.y.z` → `(x+1).0.0`

5. **Update `plugin.json`** with the new version.

6. **Update README version badge** to match.

Log each bump:

```
Auto-bump: <plugin-name> <old> → <new> (MINOR: new agent added)
```

#### 1d. Identify non-plugin changes

Categorize remaining files into: CLI (`claude-kit`, `install.sh`),
Config (`.claude/`), Scripts (`scripts/`), CI (`.github/`), Docs (`docs/`).

#### 1e. Draft and write [Unreleased]

Compose the section using this structure:

```markdown
## [Unreleased]

### Added
- **<new-plugin-name>** <version> — <description from plugin.json>

### Changed
- **<plugin-name>** — <summary of change>
  - `<plugin-name>`: <old> → <new>

### Fixed
- **<plugin-name>** — <summary of fix>
```

Rules:
- Read actual diffs to write accurate summaries — do not guess
- Include a `### Plugin versions` section listing all bumped plugins
- Omit empty headings (no empty `### Fixed` etc.)
- Match the existing CHANGELOG style

Write the draft to CHANGELOG.md using Edit. No confirmation.

## Step 2 — Compute Release Version

```bash
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
```

From the `[Unreleased]` content, compute the version automatically:
- Any **major** plugin bump → major bump from last tag
- Any **minor** plugin bump (no major) → minor bump from last tag
- Otherwise → patch bump from last tag

Log the decision:

```
Auto-release: last tag=$LAST_TAG, highest bump=minor → vX.Y.Z
```

No confirmation — proceed with the computed version.

## Step 3 — Handle Working Tree & Branch

```bash
git status --short
git branch --show-current
```

### Clean tree on `main`

Continue to Step 4.

### Clean tree on `release/*`

Resuming interrupted auto-release. Continue to Step 4.

### Dirty tree on `main` or `release/*`

1. Create `release/vX.Y.Z` branch if not already on a release branch:

```bash
git checkout -b release/vX.Y.Z
```

2. Stage and commit ALL uncommitted changes in a single commit:

```bash
git add -A
git commit -m "chore: stage uncommitted changes for vX.Y.Z release"
```

A single commit is preferred over categorized commits in CI — speed and
atomicity matter more than commit aesthetics here.

3. Verify clean:

```bash
git status --short
```

### Dirty tree on any other branch

```
AUTO-RELEASE FAILED: on branch <name> with uncommitted changes.
Must be on main or a release/* branch.
```

Stop here.

## Step 4 — Tier 1 Validation (Strict)

```bash
python3 scripts/validate-plugins.py --all --strict
```

If failures are found:
1. Attempt auto-fixes (frontmatter keys, extra plugin.json fields, README
   version badges)
2. Re-run validation
3. If still failing:

```
AUTO-RELEASE FAILED: Tier 1 validation errors remain after auto-fix.
<paste validation output>
```

Stop here.

If auto-fixes were applied, commit them:

```bash
git add -A
git commit -m "fix: auto-fix tier 1 validation issues"
```

## Step 5 — Semantic Impact Analysis

### 5a. Identify changed plugins

```bash
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
  git diff --name-only "$LAST_TAG"...HEAD -- plugins/
else
  git diff --name-only HEAD -- plugins/
fi
```

### 5b. Architectural integrity checks

For every changed plugin, check all invariants from the table in `/release`
Step 5b. Auto-fix what can be auto-fixed (plugin.json extra fields, frontmatter
keys, README badges).

### 5c. Version bump severity

Compare each plugin's actual version bump against the required severity. If the
bump is too low, **auto-fix it** — bump the version in `plugin.json` to the
correct level and update the README badge to match.

Log each correction:

```
Auto-fix: <plugin-name> needs MINOR bump (new agent added), was PATCH → bumped to X.Y.Z
```

### 5d. Cross-team consistency

Check sibling plugins across teams. If inconsistencies are found that are
auto-fixable (same frontmatter bug, same script issue), fix them. If not
auto-fixable (architectural violation), stop:

```
AUTO-RELEASE FAILED: architectural violation in <plugin>.
<description of violation>
```

### 5e. Commit fixes

If any fixes were applied in this step:

```bash
git add -A
git commit -m "fix: address semantic analysis findings"
```

## Step 6 — Finalize CHANGELOG

In `CHANGELOG.md`:
1. Replace `## [Unreleased]` with `## [x.y.z] - YYYY-MM-DD` (today's date)
2. Add a new empty `## [Unreleased]` section above it

## Step 7 — Update Roadmap

Read `ROADMAP.md` and update:

1. Add the new version to **Shipped** (top of list, most recent first):
   ```
   - **vX.Y.Z** — Short Summary (Mon DD, YYYY)
     Brief description derived from the [Unreleased] content
   ```

2. Move any completed **In Progress** items to Shipped or remove them.

3. Remove empty **In Progress** or **Planned** sections.

No confirmation — apply the update directly.

## Step 8 — Commit Release Finalization

```bash
git add CHANGELOG.md ROADMAP.md plugins/*/\.claude-plugin/plugin.json
git commit -m "chore: release vX.Y.Z"
```

## Step 9 — Push & PR Flow

```bash
CURRENT_BRANCH=$(git branch --show-current)
```

### If on a `release/*` branch

1. **Push:**

```bash
git push -u origin release/vX.Y.Z
```

2. **Create PR:**

```bash
gh pr create \
  --title "release: vX.Y.Z" \
  --body "$(cat <<'EOF'
## Release vX.Y.Z

Automated release — all preflight checks passed.

- Tier 1 validation: passed (strict)
- Semantic analysis: passed
- CHANGELOG: finalized
- ROADMAP: updated
EOF
)"
```

3. **Wait for PR CI:**

```bash
gh pr checks release/vX.Y.Z --watch --fail-fast
```

If checks fail, auto-fix (up to 3 attempts):
- Fetch failure logs: `gh run view <ID> --log 2>&1 | tail -300`
- Diagnose and fix with Edit
- Verify locally
- Commit and push — PR checks re-run automatically
- Resume watching: `gh pr checks release/vX.Y.Z --watch --fail-fast`

If 3 attempts exhausted:

```
AUTO-RELEASE FAILED: PR checks failed after 3 auto-fix attempts.
PR: <PR URL>
```

Stop here. Leave the PR open for manual inspection.

4. **Merge immediately** (no confirmation):

```bash
gh pr merge release/vX.Y.Z --squash --delete-branch
```

5. **Sync main:**

```bash
git checkout main
git pull
```

### If on `main`

Already on main with release commit. Continue to Step 10.

## Step 10 — Tag

```bash
git tag -a "vX.Y.Z" -m "Release vX.Y.Z"
```

## Step 11 — Push (No Confirmation)

```bash
git push && git push --tags
```

No confirmation gate — this is CI, push immediately.

## Step 12 — Monitor Release CI

Wait 15 seconds, then monitor both workflows:

```bash
HEAD_SHA=$(git rev-parse HEAD)

# Poll every 20 seconds
# Find fast-validate run
gh run list --workflow=push.yml --branch=main --limit=3 --json databaseId,status,conclusion,headSha --jq '.[] | select(.headSha=="'$HEAD_SHA'")'

# Find release run
gh run list --workflow=release.yml --limit=3 --json databaseId,status,conclusion,headSha --jq '.[] | select(.headSha=="'$HEAD_SHA'")'
```

Poll every 20 seconds until both reach terminal state. Log each poll:

```
CI poll: fast-validate=in_progress, release=queued
```

If queued for >3 minutes, log a warning but keep polling.

On completion:
- Both `success` → Step 14
- Any `failure` → Step 13
- Any `cancelled` → treat as failure, proceed to Step 13

## Step 13 — Auto-Fix CI Failures

Up to **3 attempts**. On each attempt:

1. Fetch logs:

```bash
gh run view <FAILED_RUN_ID> --log 2>&1 | tail -300
```

2. Diagnose and fix with Read + Edit.

3. Verify locally:

```bash
python3 scripts/validate-plugins.py --all --strict
bash scripts/test-cli.sh
bash scripts/test-plugin-consistency.sh
python3 -m py_compile claude-kit
```

4. Re-commit, re-tag, re-push:

```bash
git add -A
git commit -m "fix: <description>"

git tag -d "vX.Y.Z"
git push origin :refs/tags/vX.Y.Z
git tag -a "vX.Y.Z" -m "Release vX.Y.Z"

git push && git push --tags
```

5. Return to Step 12.

After 3 failed attempts:

```
AUTO-RELEASE FAILED: CI failures persist after 3 auto-fix attempts.

Last failure: <description>
Tag vX.Y.Z left on commit <SHA>.

To clean up:
  git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z
```

Stop here.

## Step 14 — Verify Release

```bash
gh release view "vX.Y.Z" --json tagName,name,isDraft,isPrerelease,url,createdAt
```

If the release exists and is not a draft:

```
AUTO-RELEASE SUCCESS: vX.Y.Z

  URL:     <release URL>
  Tag:     vX.Y.Z
  Created: <timestamp>
```

If the release does not exist, wait 30 seconds and retry once. If still missing:

```
AUTO-RELEASE WARNING: tag pushed and CI passed, but GitHub Release not found.
Check release.yml workflow manually.
```

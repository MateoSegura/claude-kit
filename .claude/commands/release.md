---
allowed-tools: Bash, Read, Edit, Glob, Grep, Write
description: Finalize a release — run preflight checks, promote [Unreleased] to a versioned CHANGELOG section, commit, tag, push, monitor CI until the GitHub Release is published, and auto-fix any CI failures along the way.
---

# Release

Prepare and create a new claude-kit release from the current `[Unreleased]`
CHANGELOG draft. Handles uncommitted changes automatically — creates a release
branch, commits, pushes, opens a PR, waits for CI, and tags on main after merge.

## Step 1 — Analyze Changes & Draft [Unreleased]

Read `CHANGELOG.md` and extract the content of the `## [Unreleased]` section.

### If [Unreleased] already has content

Skip to Step 2 — the draft is ready.

### If [Unreleased] is empty or missing

Auto-analyze all changes since the last tag and generate the draft:

#### 1a. Get baseline

```bash
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
```

#### 1b. Find all changed files since last tag

Include both committed and uncommitted changes:

```bash
# Committed changes since last tag
if [ -n "$LAST_TAG" ]; then
  git diff --name-only "$LAST_TAG"...HEAD
else
  git ls-files
fi

# Uncommitted changes (staged + unstaged + untracked)
git status --short
```

If there are no changes at all (committed or uncommitted) since the last tag,
tell the user: "No changes found since $LAST_TAG. Nothing to release." and stop.

#### 1c. Identify changed plugins

From the changed files, extract unique plugin names (the directory name under
`plugins/`). For each changed plugin:

1. **Read the current `plugin.json`** to get the current version
2. **Get the old version** from the last tag (if the plugin existed):

```bash
git show "$LAST_TAG:plugins/<name>/.claude-plugin/plugin.json" 2>/dev/null | jq -r .version
```

3. **Classify the change** by examining what files changed within the plugin:

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

For each classification, check what files existed at `$LAST_TAG` vs now:

```bash
# Check for new/removed agents
git show "$LAST_TAG:plugins/<name>/agents/" 2>/dev/null
ls plugins/<name>/agents/ 2>/dev/null

# Check for new/removed commands
git show "$LAST_TAG:plugins/<name>/commands/" 2>/dev/null
ls plugins/<name>/commands/ 2>/dev/null

# Check for new/removed skills
git show "$LAST_TAG:plugins/<name>/skills/" 2>/dev/null
ls plugins/<name>/skills/ 2>/dev/null
```

4. **Compute the new version** by applying the bump to the old version (or
   current version if no old version exists). Follow semver:
   - PATCH: `x.y.z` → `x.y.(z+1)`
   - MINOR: `x.y.z` → `x.(y+1).0`
   - MAJOR: `x.y.z` → `(x+1).0.0`

5. **Update `plugin.json`** with the new version using Edit.

6. **Update the README version badge** to match:
   ```
   > **Role:** <Role> · **Version:** <new-version>
   ```

#### 1d. Identify non-plugin changes

Categorize remaining changed files:

| Category | File patterns | CHANGELOG heading |
|----------|--------------|-------------------|
| CLI | `claude-kit`, `install.sh` | `### Changed` or `### Added` |
| Config | `.claude/rules/`, `.claude/hooks.json`, `.claude/commands/` | `### Changed` |
| Scripts | `scripts/` | `### Changed` |
| CI | `.github/workflows/` | `### Changed` |
| Docs | `docs/`, root `README.md` | `### Changed` |

#### 1e. Draft the [Unreleased] section

Compose the `## [Unreleased]` content using this structure:

```markdown
## [Unreleased]

### Added
- **<new-plugin-name>** <version> — <description from plugin.json>
- **<feature>** — <summary of new non-plugin capability>

### Changed
- **<plugin-name>** — <summary of what changed>
  - `<plugin-name>`: <old-version> → <new-version>
- **<non-plugin change>** — <summary>

### Fixed
- **<plugin-name>** — <summary of fix>
  - `<plugin-name>`: <old-version> → <new-version>
```

Rules for drafting:
- Group by `Added` (new plugins, new capabilities), `Changed` (modifications),
  `Fixed` (bug fixes) — omit empty headings
- For plugin changes, read the actual diffs to write accurate summaries — do
  not guess
- Include a `### Plugin versions` section at the end listing all bumped plugins:
  ```
  - `<plugin-name>`: <old> → <new>
  ```
- Keep entries concise (1-2 lines each) — match the style of existing entries
  in the CHANGELOG

#### 1f. Write the draft to CHANGELOG.md

Use Edit to replace the empty `## [Unreleased]` section with the drafted
content.

#### 1g. Show the draft and confirm

Present the drafted `[Unreleased]` content to the user:

> "Auto-generated release draft:"
> _(show the content)_
> "Proceed with this draft?"

The user may request edits before continuing.

## Step 2 — Compute Release Version

Get the last tag:

```bash
git describe --tags --abbrev=0 2>/dev/null || echo "none"
```

From the `[Unreleased]` content, identify the highest-severity bump across all
plugin changes listed:
- If any plugin had a **major** bump → repo version is major bump from last tag
- If any plugin had a **minor** bump → repo version is minor bump from last tag
- Otherwise → repo version is patch bump from last tag

Show the computed version and ask for confirmation:
> "Computed version: v1.2.0 — proceed?"

The user may override with a specific version.

## Step 3 — Preflight: Working Tree & Branch

Check for uncommitted changes and determine the current branch:

```bash
git status --short
git branch --show-current
```

### Case A: Clean working tree on `main`

Continue to Step 4. This is the traditional release path.

### Case B: Clean working tree on a `release/*` branch

This means a previous release run was interrupted after committing. Skip to
Step 4 and continue from where things left off.

### Case C: Dirty working tree (uncommitted changes exist)

Automatically stage, commit, and prepare a release branch:

1. **Create the release branch** (if not already on one):

```bash
git checkout -b release/vX.Y.Z
```

If already on `main`, this creates the branch from HEAD. If already on a
`release/*` branch, stay on it.

2. **Categorize the uncommitted changes** by reading `git status --short` and
   grouping files:

| Category | File patterns | Commit message |
|----------|--------------|----------------|
| CLI changes | `claude-kit`, `install.sh` | `feat(cli): <summary of CLI changes>` |
| Plugin changes | `plugins/*/` | `feat(plugins): <summary>` or `fix(plugins): <summary>` |
| New plugins | `plugins/<new>/` (untracked dirs) | `feat(plugins): add <plugin-name>` |
| Config/rules | `.claude/rules/`, `.claude/hooks.json`, `.claude/.instrumentation.json` | `chore(config): update claude rules and hooks` |
| Scripts | `scripts/` | `chore(scripts): <summary>` |
| Commands | `.claude/commands/` | `chore(commands): update <command-name>` |
| Docs/research | `docs/` | `docs: <summary>` |

3. **Create commits** — group related files into logical commits. Prefer fewer
   commits (1-3) over many tiny ones. Use Conventional Commits format for each.
   Stage specific files by name — do not use `git add -A` or `git add .`.

4. **Verify** the working tree is now clean:

```bash
git status --short
```

If any files remain unstaged, investigate and commit them. Do not leave a dirty
working tree.

### Case D: Dirty working tree on a non-release, non-main branch

Tell the user:
> "You're on branch `<name>` with uncommitted changes. Switch to `main` or a
> `release/*` branch before releasing."

Stop here.

## Step 4 — Preflight: Full Validation Suite

<!-- Enriched by core-ai:instrument on 2026-03-02 — added: Layer 2-6 checks beyond Tier 1 -->

Run the full CI validation suite to catch issues before releasing:

### 4a. Tier 1 plugin validation (strict)

```bash
python3 scripts/validate-plugins.py --all --strict
```

If any failures are found, attempt to fix them automatically (frontmatter keys,
extra plugin.json fields, README version badges). If unfixable failures remain,
stop and report them.

### 4b. Plugin consistency checks

```bash
bash scripts/test-plugin-consistency.sh
```

### 4c. CLI validation

```bash
python3 -m py_compile claude-kit && echo "Syntax OK"
bash scripts/test-cli.sh
```

### 4d. Docs validation

```bash
bash scripts/validate-docs.sh
```

### 4e. Library unit tests

```bash
.venv-lib/bin/python -m pytest test/ -v --tb=short \
  --ignore=test/scenarios --ignore=test/src
```

If `.venv-lib` does not exist, create it:
```bash
python3 -m venv .venv-lib && .venv-lib/bin/pip install -q -e ".[dev]"
```

### 4f. API tests

```bash
cd api && .venv/bin/python -m pytest -v --tb=short
```

If `api/.venv` does not exist, create it:
```bash
cd api && python3 -m venv .venv && .venv/bin/pip install -q -e ".[dev]"
```

If any step fails, fix the issue before proceeding. All six layers must pass
before a release can continue.

## Step 5 — Semantic Impact Analysis

Before finalizing the release, analyze what the changes **mean** architecturally.
This catches issues that Tier 1 structural checks miss.

### 5a. Identify all plugin changes since last tag

```bash
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
  git diff --name-only "$LAST_TAG"...HEAD -- plugins/
else
  git diff --name-only HEAD -- plugins/
fi
```

For each changed plugin, read its current state and the diff.

### 5b. Architectural integrity checks

For every changed plugin, verify these invariants:

| Check | Rule | Auto-fixable? |
|-------|------|---------------|
| Knowledge plugins have no `agents/` or `commands/` | architecture.md | No — report to user |
| Team plugins follow 5-role architecture | architecture.md | No — report to user |
| All `companions[]` entries resolve to existing plugin dirs | plugin-conventions.md | No — report to user |
| `ctl.json` role matches plugin naming convention | architecture.md | No — report to user |
| `plugin.json` has only `name`, `description`, `version` | plugin-conventions.md | Yes — remove extras |
| Agent frontmatter uses `tools:` not `allowed-tools:` | code-style.md | Yes — rename key |
| Command frontmatter uses `allowed-tools:` not `tools:` | code-style.md | Yes — rename key |
| README version badge matches `plugin.json` version | plugin-versions.md | Yes — update badge |

### 5c. Version bump severity validation

For each changed plugin, determine what kind of change was made:

- **Breaking** (removed/renamed agent, command, or skill) → requires MAJOR bump
- **New capability** (added agent, command, or skill) → requires at least MINOR bump
- **Content/doc/fix** (everything else) → PATCH is sufficient

Compare the actual version bump in `plugin.json` against the required severity.
If the bump is too low (e.g., breaking change with only a PATCH bump), flag it.

```bash
# For each changed plugin, compare old vs new version
git show "$LAST_TAG:plugins/<name>/.claude-plugin/plugin.json" 2>/dev/null | jq -r .version
jq -r .version plugins/<name>/.claude-plugin/plugin.json
```

### 5d. Cross-team consistency check

If a plugin in one team was changed, check whether the same issue exists in the
equivalent plugins across other teams (per `cross-team-consistency.md`):

```
# Example: if embedded-zephyr-engineer changed, also check:
plugins/frontend-svelte-engineer/
plugins/cloud-python-engineer/
```

### 5e. Report findings

Present findings in three categories:

**Auto-fixed** (applied silently):
- Frontmatter key corrections
- README badge updates
- Extra fields removed from plugin.json

**Needs attention** (ask user before proceeding):
- Version bump severity mismatches
- Architectural violations (knowledge plugin with agents, broken companions)
- Cross-team inconsistencies (same bug exists in sibling plugins)

**Clean** (no issues):
- Plugins that pass all checks

If there are "needs attention" items, present them clearly and ask the user
whether to fix them now (which means additional commits before the release) or
proceed anyway. Do NOT silently proceed past architectural violations.

If auto-fixes or user-requested fixes were applied, commit them:

```bash
git add -A
git commit -m "fix: address release preflight findings"
```

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

## Step 8 — Commit Release Finalization

```bash
git add CHANGELOG.md ROADMAP.md
git commit -m "chore: release vX.Y.Z"
```

Include any auto-fixed plugin files if they were modified in Steps 4-5:

```bash
git add CHANGELOG.md ROADMAP.md plugins/*/\.claude-plugin/plugin.json
git commit -m "chore: release vX.Y.Z"
```

## Step 9 — Push & PR Flow

Determine the current branch:

```bash
git branch --show-current
```

### If on a `release/*` branch (the auto-commit path)

This is the full PR flow:

1. **Push the release branch:**

```bash
git push -u origin release/vX.Y.Z
```

2. **Create a PR:**

```bash
gh pr create \
  --title "release: vX.Y.Z" \
  --body "$(cat <<'EOF'
## Release vX.Y.Z

<1-3 bullet summary of what this release includes>

## Checklist
- [x] Tier 1 validation passed (`--all --strict`)
- [x] Semantic impact analysis completed
- [x] CHANGELOG finalized
- [x] ROADMAP updated
EOF
)"
```

3. **Monitor PR CI** — two required checks must pass:
   - `fast-validate` (push.yml)
   - `validate-tier1` (pr.yml)

```bash
# Wait 15 seconds for CI to register
# Then poll every 20 seconds
gh pr checks release/vX.Y.Z --watch --fail-fast
```

If checks fail, follow the auto-fix procedure from Step 12 (fetch logs,
diagnose, fix, commit, push). The PR checks will re-run automatically.

4. **Merge the PR** — ask the user for confirmation first:

> "PR checks are green. Merge to main? [y/N]"

If confirmed:

```bash
gh pr merge release/vX.Y.Z --squash --delete-branch
```

5. **Sync local main:**

```bash
git checkout main
git pull
```

### If on `main` (clean start, traditional path)

The release commit is already on main. No PR needed — continue to Step 10.

## Step 10 — Tag

```bash
git tag -a "vX.Y.Z" -m "Release vX.Y.Z"
```

## Step 11 — Confirm Before Push

Show the user:
- The commit that was tagged (show SHA and message)
- The tag that was created
- What `git push && git push --tags` will do

Then ask: **"Push tag to origin? [y/N]"**

If confirmed:
```bash
git push && git push --tags
```

If declined, tell the user they can push manually when ready and **stop here**.

If pushed, proceed to Step 12.

## Step 12 — Monitor CI Until Complete

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
   - Both `success` → proceed to **Step 14** (Verify Release)
   - Any `failure` → proceed to **Step 13** (Auto-Fix)
   - Any `cancelled` → report and ask the user what to do

## Step 13 — Auto-Fix CI Failures

When a CI workflow fails, attempt to diagnose and fix it locally. This step
may loop up to **3 times** — if all 3 attempts fail, stop and report.

### 13a. Fetch failure logs

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

### 13b. Apply the fix

Use Read and Edit to fix the identified issue. Run the same check locally to
verify:

```bash
# Depending on what failed — run all affected layers:
python3 -m py_compile claude-kit
bash scripts/test-cli.sh
python3 scripts/validate-plugins.py --all --strict
bash scripts/test-plugin-consistency.sh
bash scripts/validate-docs.sh
.venv-lib/bin/python -m pytest test/ -v --tb=short \
  --ignore=test/scenarios --ignore=test/src
cd api && .venv/bin/python -m pytest -v --tb=short
```

### 13c. Re-commit, re-tag, re-push

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

### 13d. Resume monitoring

Go back to **Step 12** with the new commit SHA. Increment the attempt counter.

If this is already the 3rd attempt, **stop** and report:

```
Release failed after 3 auto-fix attempts. The remaining issue requires
manual intervention:

<describe the failure>

The tag vX.Y.Z has been left on the latest commit. You can:
- Fix manually and force-push
- Delete the tag with: git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z
```

## Step 14 — Verify Release Published

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

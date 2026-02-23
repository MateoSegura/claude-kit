# claude-kit Repository Rules

These rules apply when Claude is working in the claude-kit repository itself —
editing plugins, scripts, workflows, or tooling. They do NOT apply to the
plugins that claude-kit distributes.

## Plugin File Schema — Critical

`plugin.json` is parsed by Claude Code's plugin loader. Only these fields are
safe:

```json
{ "name": "...", "description": "...", "version": "x.y.z" }
```

**Any extra field (`author`, `role`, `companions`, `keywords`, etc.) causes the
plugin to SILENTLY FAIL TO LOAD.** The old template had an `author` field —
ignore it. Put `role` and `companions` in `ctl.json` instead.

## Frontmatter Key Names — Critical

| File type | Tool restriction key | Wrong key |
|-----------|---------------------|-----------|
| `agents/*.md` | `tools:` | ~~allowed-tools:~~ |
| `commands/*.md` | `allowed-tools:` | ~~tools:~~ |
| `skills/*/SKILL.md` | `allowed-tools:` (if needed) | ~~tools:~~ |

Mixing these up causes silent failures. Both are required by the plugin loader
and are different fields with different semantics.

## Script Path Convention

All hook scripts must use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths:

```bash
# Correct
"command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"

# Wrong — breaks on any machine
"command": "/home/mateo/claude-kit/plugins/my-plugin/scripts/validate.sh"
```

## Knowledge Plugins

A knowledge plugin (`ctl.json` → `"role": "knowledge"`) serves as companion
reference material. It must NOT contain `agents/` or `commands/` directories.
Skills and hooks only.

## Companion Declarations

All plugins listed in `ctl.json` → `companions[]` must already exist as
directories under `plugins/` before committing. The validator (`check 5`)
enforces this at CI time.

## Git Workflow — Required for Every Change

**Never commit directly to `main`.** Every change goes through a branch + PR.

### Step-by-step

1. **Create a branch** with the enforced naming convention:
   ```
   <type>/<short-description>
   ```
   Valid types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`, `style`, `release`, `hotfix`

   ```bash
   git checkout -b fix/install-claude-guard
   git checkout -b feat/new-plugin-xyz
   git checkout -b docs/update-readme
   ```

2. **Make changes, validate, commit.**
   - Commits follow Conventional Commits: `<type>(<scope>): <description>`
   - Max 72 chars on the subject line, imperative mood
   - Run `claude-kit validate --changed` before committing plugin changes

3. **Push and open a PR:**
   ```bash
   git push -u origin <branch>
   gh pr create --title "<type>: <description>" --body "..."
   ```

4. **Wait for CI to pass** (fast-validate + validate-tier1 are required status checks).
   - `claude-validate` runs automatically if plugins changed
   - Do not merge until both jobs are green

5. **Merge via GitHub** (squash merge preferred to keep main history clean).

6. **Sync local main** after merge:
   ```bash
   git checkout main && git pull
   ```

### Branch naming is CI-enforced

`push.yml` rejects any branch that doesn't match the pattern. If CI fails with
"Branch name does not follow convention", rename the branch:
```bash
git branch -m <old-name> <type>/<description>
git push origin -u <type>/<description>
```

---

## Validation Before Committing

Before committing a plugin change, run Tier 1 validation locally:

```bash
# Single plugin
claude-kit validate <plugin-name>

# All plugins
claude-kit validate --all

# Only files changed since last commit
claude-kit validate --changed
```

Or use the `/validate-all` command for combined Tier 1 + semantic review.

## Version Bumps and Releases

- **Version bumps:** use `/bump-plugin` — never edit `plugin.json` version or
  CHANGELOG manually.
- **Releases:** use `/release` — it runs preflight checks, finalizes CHANGELOG,
  commits, tags, and asks before pushing.

## Plugin Creation and Enhancement

- **New plugin:** `claude-kit --kit system-maker` → `/system-maker:make-agent`
- **Enhance existing:** `claude-kit --kit system-updater` →
  `/system-updater:update-agent`

## Plugin Version Strategy

| Bump | When |
|------|------|
| patch | Content/doc improvement, hook tweak, script fix |
| minor | New agent, command, or skill added |
| major | Breaking change — renamed command, removed agent, changed skill API |

Repo tag version is determined by the highest-severity plugin bump in the
release draft.

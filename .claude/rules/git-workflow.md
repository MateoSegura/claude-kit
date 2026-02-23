# Git Workflow — Required for Every Change in This Repo

**Never commit directly to `main`.** Every change goes through a branch + PR.

## Step-by-step

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
   - Run `claude-kit validate --changed` before committing any plugin changes

3. **Push and open a PR:**
   ```bash
   git push -u origin <branch>
   gh pr create --title "<type>: <description>" --body "..."
   ```

4. **Wait for CI to pass.**
   - `fast-validate` and `validate-tier1` are required status checks
   - `claude-validate` runs automatically when plugins are changed
   - Do not merge until all required checks are green

5. **Merge via GitHub** (squash merge to keep main history clean).

6. **Sync local main** after merge:
   ```bash
   git checkout main && git pull
   ```

## Branch Naming is CI-Enforced

`push.yml` rejects any branch that doesn't match the pattern above. If CI fails
with "Branch name does not follow convention", rename the branch:

```bash
git branch -m <old-name> <type>/<description>
git push origin -u <type>/<description>
```

## Releases

- **Version bumps:** edit `plugin.json` and `CHANGELOG.md` manually on a `release/vX.Y.Z` branch
- **Releases:** squash-merge the release branch, tag with `git tag -a vX.Y.Z -m "vX.Y.Z"`, push tag, create GitHub release with `gh release create`
- Do not push tags from a feature or fix branch — only from release branches after the PR is merged to main

---

## Version Number System

Every version number has three parts: `MAJOR.MINOR.PATCH`

```
system-maker 0  .  1  .  1
             ^     ^     ^
           MAJOR MINOR PATCH
```

### Plugin versions (in `plugin.json`)

Each plugin carries its own independent version. Bump the appropriate part
based on the nature of the change:

| Bump | When | Examples |
|------|------|---------|
| **PATCH** | Content improvement, doc update, hook tweak, script fix | Update a skill's reference material, add a README, tighten a hook regex, fix a shell script bug |
| **MINOR** | New capability added — new agent, command, or skill | Add a new agent to an existing plugin, add a new slash command, add a new skill directory |
| **MAJOR** | Breaking change that removes or renames existing API | Rename a command (users' muscle memory breaks), remove an agent, change a skill's `name:` field |

**Rule of thumb:**
- Does the change break anything a user was already using? → MAJOR
- Does the change add something new that wasn't there before? → MINOR
- Does the change improve or document something that already existed? → PATCH

### Repo release tag (e.g. `v0.0.13`)

The repo tag version follows the **highest-severity** plugin bump across all
plugins included in the release:

| If any plugin got… | Repo tag bumps… |
|--------------------|----------------|
| A MAJOR bump | MAJOR (e.g. v0.0.13 → v1.0.0) |
| A MINOR bump (no MAJOR) | MINOR (e.g. v0.0.13 → v0.1.0) |
| Only PATCH bumps | PATCH (e.g. v0.0.13 → v0.0.14) |
| No plugin changes (CI/tooling only) | PATCH — always bump something |

### What does NOT trigger a plugin version bump

- Changes only to `README.md` at the repo root
- Changes only to `.github/workflows/`, `.claude/rules/`, or `scripts/`
- Changes only to `CHANGELOG.md` or `install.sh`

Plugin `README.md` files live inside `plugins/<name>/` and do count as doc
changes → PATCH bump for that plugin.

### Release cadence

Group multiple plugin changes into a single release rather than releasing
after every commit. A release makes sense when:
- A meaningful batch of fixes or features is ready
- A PR that touched plugins has been merged
- Before a demo or handoff

---

## CI Checks

Two workflows run on every PR:

### `fast-validate` (push.yml) — required
- Python syntax check on the CLI script
- Tier 1 structural validation on all plugins
- Branch naming enforcement
- Runs in ~10 seconds

### `claude-validate` (pr.yml) — informational only
- Runs on every PR but is **NOT a required merge gate**
- For non-plugin PRs: exits immediately with "no plugin changes" message
- For plugin PRs: runs a full Claude semantic review (~5–10 min, costs tokens)
- Results are posted as a PR comment for human review
- Because it's slow and expensive, it is **not** required to pass before merging

### Nightly semantic review (`nightly.yml`) — scheduled
- Runs `claude-validate` on all plugins against main at 02:00 UTC every night
- Catches drift between plugin content and quality standards over time
- Does not block any PR or release

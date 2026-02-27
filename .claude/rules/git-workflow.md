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

## CI Workflows

Seven workflows run across the repository. Two are required merge gates; the
rest are informational, scheduled, or reactive.

### `fast-validate` (push.yml) — required

Triggers on every push to any branch and on PRs to main.

- **Branch naming enforcement** — rejects branches not matching
  `<type>/<description>` (skipped on pushes to main)
- **Python syntax check** — `python3 -m py_compile claude-kit`
- **CLI smoke tests** — `bash scripts/test-cli.sh`
- **Plugin consistency checks** — `bash scripts/test-plugin-consistency.sh`
- **Tier 1 changed plugins** — `python3 scripts/validate-plugins.py --changed --json`
- Runs in ~10 seconds on self-hosted runner

### `pr-validate` (pr.yml) — required + informational

Triggers on PRs to main (opened, synchronize, reopened). Two jobs:

1. **`validate-tier1`** (required) — runs Tier 1 on ALL plugins (`--all --json`),
   posts results as a PR comment (updates existing comment on re-push)
2. **`semantic-check`** (informational) — only runs when plugins changed. Uses
   Claude Haiku (`--model haiku`) with a focused prompt built by
   `scripts/build-semantic-prompt.py`. Reviews only CHANGED plugins for identity
   coherence, content depth, domain specificity, and cross-agent contradictions.
   Posts results as a separate PR comment. Timeout: 4 minutes. **Not a merge gate.**

### `pr-autofix` (pr-autofix.yml) — reactive

Triggers when `fast-validate` completes. Only runs when:
- `fast-validate` **failed**
- The branch is **not main**
- An open PR exists for the branch
- The PR has **fewer than 3** `autofix-attempt-N` labels

When triggered:
1. Fetches the failure logs from the failed `fast-validate` run
2. Builds a fix prompt via `scripts/build-autofix-prompt.py`
3. Runs Claude with full edit tools to auto-fix the issue
4. If changes are made: commits, pushes, and labels the PR with
   `autofix-attempt-N` (where N increments 1→2→3)
5. If no changes: posts a comment suggesting the failure may be transient
6. Maximum 3 attempts per PR — after that, manual intervention is required

### `release` (release.yml) — tag-triggered

Triggers on tag pushes matching `v*.*.*`.

1. Tier 1 strict validation (`--all --strict --json`)
2. Verifies a matching `## [x.y.z]` entry exists in `CHANGELOG.md`
3. Extracts the CHANGELOG section for the release body
4. Creates (or updates) the GitHub Release via `actions/github-script`

### `nightly-plugin-review` (nightly.yml) — scheduled

Runs at 02:00 UTC daily on main.

1. Full semantic review of ALL plugins using `system-maker:validate`
2. If WARN or FATAL findings exist: creates a `fix/nightly-plugin-review-YYYYMMDD`
   branch, runs Claude auto-fix, opens a PR with auto-merge enabled
3. The fix PR auto-merges once `fast-validate` and `validate-tier1` pass
4. Writes a workflow summary to the GitHub Actions step summary

### `weekly-full-audit` (weekly.yml) — scheduled

Runs every Monday at 09:00 UTC.

1. Tier 1 strict on all plugins (`--all --strict --json`)
2. Full Claude cross-coherence semantic review (checks companion relationships,
   contradictions across same-team plugins)
3. On failure: creates a GitHub issue with the `audit-failure` label (skips if
   an open audit-failure issue already exists)

### `publish-devcontainer` (publish-devcontainer.yml) — main only

Triggers on pushes to main when `.devcontainer/Dockerfile` or the workflow file
itself changes. Builds and pushes `ghcr.io/mateosegura/dev-env-claude-kit:latest`
using BuildKit with dual-layer caching (local Docker cache + registry cache).

---

### Summary table

| Workflow | Trigger | Required? | Auto-fixes? |
|----------|---------|-----------|-------------|
| `fast-validate` | push, PR | Yes | No |
| `pr-validate` (tier1) | PR | Yes | No |
| `pr-validate` (semantic) | PR + plugins changed | No | No |
| `pr-autofix` | fast-validate failure | No | Yes (3 max) |
| `release` | tag `v*.*.*` | N/A (gate) | No |
| `nightly-plugin-review` | 02:00 UTC daily | No | Yes (opens PR) |
| `weekly-full-audit` | Monday 09:00 UTC | No | No (opens issue) |
| `publish-devcontainer` | push to main + Dockerfile | N/A | No |

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

- **Version bumps:** `/bump-plugin` — never edit `plugin.json` or CHANGELOG manually
- **Releases:** `/release` — runs preflight, finalizes CHANGELOG, tags, and asks before pushing
- Do not push tags manually; `/release` handles it

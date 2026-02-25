# Branching Strategies -- Deep Reference

## Trunk-Based Development in Detail

### Feature Flags Pattern

Feature flags allow merging incomplete features to main safely.

```
# Application code uses flags to gate features
if feature_enabled("new-checkout"):
    run_new_checkout()
else:
    run_old_checkout()
```

**Flag lifecycle:**
1. Create flag before starting feature
2. Develop behind flag on main (or short branch)
3. Test with flag on in staging
4. Gradually roll out (canary -> percentage -> full)
5. Remove flag and dead code path

### Short-Lived Branch Rules

```bash
# Create branch
git checkout -b feat/add-search main

# Work (ideally < 1 day of changes)
git add -A && git commit -m "feat: add search endpoint"

# Rebase before merging to avoid merge commits
git fetch origin && git rebase origin/main

# Merge (fast-forward preferred)
git checkout main && git merge --ff-only feat/add-search
```

**Warning signs your branch is too long-lived:**
- Branch exists > 2 days
- More than 5 commits without merging
- Merge conflicts appearing
- Other team members duplicating work

### Branch-by-Abstraction

For large refactors that cannot be done in a single short branch:

1. Introduce an abstraction layer over the code to change
2. Migrate callers to use the abstraction (multiple small PRs)
3. Implement the new version behind the abstraction
4. Switch the abstraction to point to new implementation
5. Remove the old implementation and abstraction

## GitHub Flow in Detail

### PR Workflow

```bash
# 1. Create feature branch
git checkout -b feat/user-search main

# 2. Work in small commits
git commit -m "feat: add search index builder"
git commit -m "feat: add search API endpoint"
git commit -m "test: add search integration tests"

# 3. Push and open PR
git push -u origin feat/user-search
gh pr create --title "feat: add user search" --body "..."

# 4. Address review comments
git commit -m "refactor: rename search index method"
git push

# 5. Merge (squash preferred for clean history)
gh pr merge --squash
```

### Deploy on Merge

GitHub Flow assumes main is always deployable:

```
merge to main -> CI passes -> auto-deploy to production
```

If this is not safe for your team, consider adding:
- Deploy locks (prevent deploy during incidents)
- Canary deployments (deploy to subset first)
- Manual deploy approval gate

## GitFlow in Detail

### Feature Branch Lifecycle

```bash
# Start feature from develop
git checkout -b feature/payment-gateway develop

# Work on feature
git commit -m "feat(payment): add Stripe integration"
git commit -m "test(payment): add payment flow tests"

# Finish feature -- merge back to develop
git checkout develop
git merge --no-ff feature/payment-gateway
git branch -d feature/payment-gateway
```

### Release Branch Lifecycle

```bash
# Cut release from develop
git checkout -b release/2.0.0 develop

# Only bug fixes and version bumps on release branch
git commit -m "fix: correct currency formatting"
git commit -m "chore: bump version to 2.0.0"

# Merge to main and tag
git checkout main
git merge --no-ff release/2.0.0
git tag -a v2.0.0 -m "v2.0.0"

# Back-merge to develop
git checkout develop
git merge --no-ff release/2.0.0
git branch -d release/2.0.0
```

### Hotfix Branch Lifecycle

```bash
# Branch from main
git checkout -b hotfix/fix-crash main

# Fix the issue
git commit -m "fix: prevent null pointer in checkout"

# Merge to main and tag
git checkout main
git merge --no-ff hotfix/fix-crash
git tag -a v2.0.1 -m "v2.0.1"

# Back-merge to develop
git checkout develop
git merge --no-ff hotfix/fix-crash
git branch -d hotfix/fix-crash
```

## Release Branching in Detail

### Cherry-Pick Workflow

```bash
# Fix lands on main first
git checkout main
git commit -m "fix: buffer overflow in parser"
# Note the commit hash: abc1234

# Cherry-pick to supported release branch
git checkout release/1.x
git cherry-pick abc1234
git tag -a v1.2.3 -m "v1.2.3"

# Cherry-pick to another release if affected
git checkout release/2.x
git cherry-pick abc1234
git tag -a v2.0.1 -m "v2.0.1"
```

### Version Support Matrix

Track which releases are actively supported:

```
| Branch       | Status      | EOL        |
|-------------|-------------|------------|
| release/3.x | Active      | --         |
| release/2.x | Maintenance | 2025-06-01 |
| release/1.x | EOL         | 2024-01-01 |
```

**Active:** receives features and fixes
**Maintenance:** receives critical fixes only
**EOL:** no updates, branch is archived

## Environment Branching

Maps branches to deployment environments:

```
main       -> production
staging    -> staging environment
develop    -> development environment
```

**Caution:** This pattern conflates branch management with deployment. Prefer
feature flags + trunk-based for new projects. Environment branches tend to
accumulate drift between environments over time.

## Migrating Between Strategies

### GitFlow -> GitHub Flow

1. Stop creating new feature branches from `develop`
2. Start branching from `main` directly
3. Merge PRs to `main` instead of `develop`
4. Once all `develop` changes are in `main`, delete `develop`
5. Adopt feature flags for incomplete features

### GitHub Flow -> Trunk-Based

1. Enforce shorter branch lifetimes (< 1 day)
2. Adopt feature flags
3. Set up CI to run on every push to main
4. Gradually eliminate PR requirement for small changes (pair-programmed commits go direct)

## Protected Branch Configuration

### GitHub

```bash
# Require PR reviews
gh api repos/{owner}/{repo}/branches/main/protection -X PUT -f \
  required_pull_request_reviews='{"required_approving_review_count":1}'

# Require status checks
gh api repos/{owner}/{repo}/branches/main/protection -X PUT -f \
  required_status_checks='{"strict":true,"contexts":["ci/tests"]}'
```

### Common Protection Rules

| Rule | Trunk-Based | GitHub Flow | GitFlow |
|------|-------------|-------------|---------|
| Require PR | Optional | Yes | Yes |
| Require reviews | Optional | 1+ | 1+ |
| Require CI pass | Yes | Yes | Yes |
| Restrict force push | Yes | Yes | Yes |
| Require linear history | Recommended | Optional | No |

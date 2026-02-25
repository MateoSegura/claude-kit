---
name: core-git:branching-strategies
description: "Git branching strategies -- trunk-based, GitHub Flow, GitFlow, release branching"
user-invocable: false
---

# Branching Strategies Quick Reference

## Strategy Selection Matrix

| Factor | Trunk-Based | GitHub Flow | GitFlow | Release Branching |
|--------|-------------|-------------|---------|-------------------|
| Team size | Any | Small-medium | Medium-large | Medium-large |
| Release cadence | Continuous | Continuous | Scheduled | Scheduled |
| Hotfix speed | Instant | Fast | Moderate | Moderate |
| Complexity | Low | Low | High | Medium |
| Best for | SaaS, microservices | Web apps, APIs | Mobile, desktop | Libraries, firmware |

## Trunk-Based Development

All developers commit to `main` (or short-lived branches merged within 1-2 days).

```
main ──●──●──●──●──●──●──●──●──●──●──
        \   /     \   /
         ●─●       ●─●
       (< 2 days)  (< 1 day)
```

**Rules:**
- Branches live at most 1-2 days
- Feature flags gate incomplete work
- CI runs on every push to main
- No long-lived feature branches

**When to use:** Continuous deployment, strong CI/CD, experienced team.

## GitHub Flow

Single main branch + short-lived feature branches merged via pull request.

```
main ──●──────●──────●──────●──────●──
        \    / \    / \    /
         ●──●   ●──●   ●──●
        feat-A  feat-B  fix-C
```

**Rules:**
- Branch from `main`, PR back to `main`
- Deploy from `main` after merge
- No release branches -- main is always deployable
- Descriptive branch names: `feat/user-auth`, `fix/null-pointer`

**When to use:** Web services, SaaS, teams wanting simplicity with code review.

## GitFlow

Long-lived `main` and `develop` branches with feature, release, and hotfix branches.

```
main    ──●───────────────●──────●──
           \             / \    /
develop ────●──●──●──●──●   \  /
              \  /  \  /    hotfix
             feat-A  feat-B
              \    /
           release/1.0
```

**Rules:**
- `main` holds production releases (tagged)
- `develop` is the integration branch
- Feature branches: `feature/xyz` from `develop`
- Release branches: `release/x.y.z` from `develop`, merge to both `main` and `develop`
- Hotfix branches: `hotfix/xyz` from `main`, merge to both `main` and `develop`

**When to use:** Versioned releases, multiple supported versions, mobile/desktop apps.

## Release Branching

Long-lived release branches for each supported version.

```
main      ──●──●──●──●──●──●──●──
             \        \
release/1.x   ●──●──●  \
                        \
release/2.x              ●──●──●
```

**Rules:**
- `main` is the development trunk
- Cut `release/X.Y` when preparing a release
- Cherry-pick fixes from main into supported release branches
- Tag releases: `v1.0.0`, `v1.0.1`, `v2.0.0`

**When to use:** Libraries, SDKs, firmware, anything with multiple supported versions.

## Branch Naming Conventions

```
<type>/<short-description>

# Examples
feat/user-authentication
fix/memory-leak-on-disconnect
chore/update-dependencies
docs/api-reference
release/v2.1.0
hotfix/critical-null-check
```

| Prefix | Purpose |
|--------|---------|
| `feat/` | New feature |
| `fix/` | Bug fix |
| `chore/` | Maintenance, deps, tooling |
| `docs/` | Documentation only |
| `refactor/` | Code restructuring |
| `test/` | Test additions or fixes |
| `release/` | Release preparation |
| `hotfix/` | Urgent production fix |

## Additional Resources

For deeper coverage of each strategy, migration paths between strategies, and environment branching patterns, see [branching-reference.md](branching-reference.md).

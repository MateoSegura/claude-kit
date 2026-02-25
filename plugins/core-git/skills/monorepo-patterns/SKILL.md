---
name: core-git:monorepo-patterns
description: "Monorepo patterns -- sparse checkout, path-based ownership, affected-only CI, dependency graphs"
user-invocable: false
---

# Monorepo Patterns Quick Reference

## When to Use a Monorepo

| Factor | Monorepo | Polyrepo |
|--------|----------|----------|
| Code sharing | Easy, same repo | Requires publishing packages |
| Atomic changes | Single commit across packages | Multiple PRs across repos |
| Dependency management | Unified, single lockfile | Per-repo, version pinning |
| CI complexity | Needs affected-only filtering | Simple per-repo CI |
| Repo size | Can grow large | Small and focused |
| Access control | Path-based (CODEOWNERS) | Repo-level permissions |
| Best for | Tightly coupled packages | Independent services |

## Monorepo Directory Layouts

### Apps + Libraries

```
repo/
├── apps/
│   ├── web/
│   ├── mobile/
│   └── api/
├── libs/
│   ├── shared-ui/
│   ├── auth/
│   └── utils/
├── tools/
│   └── scripts/
└── package.json (root)
```

### Packages Only

```
repo/
├── packages/
│   ├── core/
│   ├── cli/
│   ├── plugin-a/
│   └── plugin-b/
└── package.json (root)
```

## Sparse Checkout

Clone only the directories you need from a large monorepo.

```bash
# Clone with no checkout
git clone --no-checkout <url> my-repo
cd my-repo

# Enable sparse checkout
git sparse-checkout init --cone

# Check out only specific directories
git sparse-checkout set apps/web libs/shared-ui libs/utils

# Add more directories later
git sparse-checkout add apps/api

# View current sparse checkout config
git sparse-checkout list

# Disable sparse checkout (get everything)
git sparse-checkout disable
```

**Cone mode** (recommended) restricts patterns to directory-level includes, which is much faster than arbitrary gitignore-style patterns.

## CODEOWNERS (Path-Based Ownership)

```
# .github/CODEOWNERS

# Default owners
* @org/core-team

# Per-directory ownership
/apps/web/          @org/frontend-team
/apps/api/          @org/backend-team
/libs/shared-ui/    @org/frontend-team @org/design-team
/libs/auth/         @org/security-team
/tools/             @org/platform-team

# Per-file-type ownership
*.proto             @org/api-team
*.sql               @org/data-team
```

**Rules:**
- Later rules override earlier ones
- Owners are required reviewers on PRs that touch their paths
- Combine with branch protection to enforce reviews

## Affected-Only CI

Only build and test packages that changed (or depend on changed packages).

### Git-Based Change Detection

```bash
# Find changed files between branches
git diff --name-only origin/main...HEAD

# Find changed directories (top-level packages)
git diff --name-only origin/main...HEAD | cut -d'/' -f1-2 | sort -u

# Example output:
# apps/web
# libs/shared-ui
```

### Dependency-Aware Affected Detection

Changed `libs/utils` should trigger CI for everything that depends on it:

```
libs/utils (CHANGED)
  ├── libs/auth (depends on utils) --> AFFECTED
  │     └── apps/api (depends on auth) --> AFFECTED
  └── apps/web (depends on utils) --> AFFECTED
```

Build tools like Nx, Turborepo, and Bazel compute this automatically.

## Monorepo Tooling Overview

| Tool | Language | Key Feature |
|------|----------|-------------|
| Nx | Any (JS-native) | Dependency graph, computation caching, affected commands |
| Turborepo | JS/TS | Remote caching, pipeline definition, incremental builds |
| Bazel | Any | Hermetic builds, remote execution, massive scale |
| Lerna | JS/TS | Package publishing, versioning (often paired with Nx) |
| Rush | JS/TS | Phantom dependency prevention, incremental builds |
| Pants | Python/Go/Java | Fine-grained target graph, remote caching |

### Common Patterns Across Tools

**Task pipeline definition:**
```
build depends on: ^build (all dependencies must build first)
test depends on: build (must build before testing)
lint depends on: nothing (can run in parallel)
```

**Computation caching:**
- Hash inputs (source files, config, deps) to create cache key
- If cache hit, skip execution and restore outputs
- Remote cache shares results across CI and developers

## Git Performance for Large Repos

```bash
# Partial clone (fetch objects on demand)
git clone --filter=blob:none <url>

# Shallow clone (limited history)
git clone --depth=1 <url>

# Fetch deeper history if needed
git fetch --deepen=100

# Enable filesystem monitor for faster status
git config core.fsmonitor true

# Enable commit graph for faster log/merge-base
git commit-graph write --reachable
```

## Additional Resources

For detailed monorepo CI patterns, workspace configuration, and cross-package dependency management, see [monorepo-reference.md](monorepo-reference.md).

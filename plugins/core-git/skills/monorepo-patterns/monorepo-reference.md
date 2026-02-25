# Monorepo Patterns -- Deep Reference

## Affected-Only CI Implementation

### GitHub Actions with Path Filters

```yaml
name: CI

on:
  pull_request:
    paths:
      - 'apps/web/**'
      - 'libs/shared-ui/**'
      - 'libs/utils/**'

jobs:
  build-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build --workspace=apps/web
      - run: npm run test --workspace=apps/web
```

**Limitation:** Path filters do not understand dependency graphs. If `apps/web`
depends on `libs/auth`, a change to `libs/auth` will not trigger the web build
unless `libs/auth/**` is also listed.

### Dependency-Aware CI with Change Detection Script

```bash
#!/bin/bash
# detect-affected.sh
# Determine which packages are affected by changes on this branch

BASE_REF="${1:-origin/main}"
CHANGED_FILES=$(git diff --name-only "$BASE_REF"...HEAD)

AFFECTED=()

for file in $CHANGED_FILES; do
    # Extract package path (first two directory levels)
    pkg=$(echo "$file" | cut -d'/' -f1-2)
    AFFECTED+=("$pkg")
done

# Deduplicate
printf '%s\n' "${AFFECTED[@]}" | sort -u
```

### Nx Affected Commands

```bash
# Show affected projects
npx nx affected -t build --base=origin/main

# Run tests only for affected
npx nx affected -t test --base=origin/main

# Graph affected projects
npx nx affected:graph --base=origin/main
```

### Turborepo Filtering

```bash
# Run build for changed packages
npx turbo run build --filter=...[origin/main]

# Run tests for a specific package and its dependents
npx turbo run test --filter=@org/utils...
```

## Workspace Configuration

### npm Workspaces

```json
{
  "name": "monorepo-root",
  "private": true,
  "workspaces": [
    "apps/*",
    "libs/*",
    "tools/*"
  ]
}
```

```bash
# Install all workspace dependencies
npm install

# Run a script in a specific workspace
npm run build --workspace=apps/web

# Run a script across all workspaces
npm run test --workspaces

# Add a dependency to a specific workspace
npm install lodash --workspace=apps/web

# Add a workspace dependency
npm install @org/utils --workspace=apps/web
```

### pnpm Workspaces

```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'libs/*'
  - 'tools/*'
```

```bash
# Install all
pnpm install

# Run in specific package
pnpm --filter @org/web build

# Run in all packages
pnpm -r run test

# Add dependency to specific package
pnpm --filter @org/web add lodash

# Add workspace dependency
pnpm --filter @org/web add @org/utils --workspace
```

### Yarn Workspaces

```json
{
  "private": true,
  "workspaces": [
    "apps/*",
    "libs/*"
  ]
}
```

## Cross-Package Dependencies

### Internal Package References

```json
{
  "name": "@org/web",
  "dependencies": {
    "@org/utils": "workspace:*",
    "@org/shared-ui": "workspace:^1.0.0"
  }
}
```

### Dependency Graph Visualization

```
                  apps/web
                 /        \
          libs/shared-ui   libs/auth
                 \        /
                  libs/utils
```

**Build order** (topological sort):
1. `libs/utils` (no deps)
2. `libs/shared-ui` and `libs/auth` (parallel, both depend on utils)
3. `apps/web` (depends on shared-ui and auth)

### Preventing Circular Dependencies

Rules to enforce:
- `apps/` can depend on `libs/`, never the reverse
- `libs/` can depend on other `libs/`, but no circular chains
- Enforce with lint rules (e.g., Nx module boundaries, ESLint import restrictions)

```json
// Nx module boundary example in .eslintrc
{
  "rules": {
    "@nx/enforce-module-boundaries": [
      "error",
      {
        "depConstraints": [
          { "sourceTag": "scope:app", "onlyDependOnLibsWithTags": ["scope:lib"] },
          { "sourceTag": "scope:lib", "onlyDependOnLibsWithTags": ["scope:lib"] }
        ]
      }
    ]
  }
}
```

## Versioning Strategies

### Fixed (Locked) Versioning

All packages share the same version number:

```
@org/core     2.3.0
@org/cli      2.3.0
@org/plugin-a 2.3.0
```

**Pros:** Simple, clear which versions go together
**Cons:** Bumps all packages even if only one changed

### Independent Versioning

Each package has its own version:

```
@org/core     2.3.0
@org/cli      1.5.2
@org/plugin-a 0.8.1
```

**Pros:** Granular, consumers only update what changed
**Cons:** More complex release process, compatibility matrix

### Publishing Workflow

```bash
# With Lerna (independent mode)
npx lerna version --independent
npx lerna publish from-package

# With Changesets
npx changeset        # create a changeset describing the change
npx changeset version # apply version bumps
npx changeset publish # publish to registry
```

## Git Performance Tuning

### Partial Clone Strategies

```bash
# Blobless clone -- fetch file contents on demand
git clone --filter=blob:none <url>
# Good for: CI, developers who work on a subset

# Treeless clone -- fetch trees and blobs on demand
git clone --filter=tree:0 <url>
# Good for: CI that only needs specific paths

# Sparse checkout + partial clone (best combo for huge repos)
git clone --filter=blob:none --sparse <url>
cd repo
git sparse-checkout set apps/web libs/utils
```

### Commit Graph

```bash
# Write commit graph (speeds up log, merge-base, ahead/behind)
git commit-graph write --reachable

# Enable automatic commit graph updates
git config fetch.writeCommitGraph true
```

### Filesystem Monitor

```bash
# Enable built-in fs monitor (Git 2.37+)
git config core.fsmonitor true

# Or use watchman for older Git versions
git config core.fsmonitor "$(which watchman)"
```

### Maintenance Scheduling

```bash
# Enable automatic maintenance (gc, commit-graph, prefetch)
git maintenance start

# This creates a cron/scheduled task that runs:
# - Hourly: commit-graph, prefetch
# - Daily: loose-objects, incremental-repack
```

## Large File Handling

### Git LFS

```bash
# Install and initialize
git lfs install

# Track file patterns
git lfs track "*.psd"
git lfs track "*.zip"
git lfs track "assets/videos/**"

# View tracked patterns
git lfs track

# View LFS objects
git lfs ls-files

# Migrate existing files to LFS
git lfs migrate import --include="*.psd" --everything
```

### .gitattributes for LFS

```
# .gitattributes
*.psd filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.wasm filter=lfs diff=lfs merge=lfs -text
assets/large/** filter=lfs diff=lfs merge=lfs -text
```

## Monorepo Migration

### From Polyrepo to Monorepo

```bash
# Create the monorepo
mkdir monorepo && cd monorepo && git init

# Import each repo preserving history
git remote add repo-a <url-a>
git fetch repo-a
git merge repo-a/main --allow-unrelated-histories --no-commit
git mv <files> apps/repo-a/
git commit -m "feat: import repo-a into monorepo"

# Repeat for each repo
git remote add repo-b <url-b>
git fetch repo-b
git merge repo-b/main --allow-unrelated-histories --no-commit
git mv <files> apps/repo-b/
git commit -m "feat: import repo-b into monorepo"

# Clean up remotes
git remote remove repo-a
git remote remove repo-b
```

### Using git-filter-repo for Clean Import

```bash
# Rewrite repo history to live under a subdirectory
git filter-repo --to-subdirectory-filter apps/web

# Then merge into monorepo with --allow-unrelated-histories
```

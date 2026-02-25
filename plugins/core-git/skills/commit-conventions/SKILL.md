---
name: core-git:commit-conventions
description: "Commit conventions -- Conventional Commits, semantic messages, atomic commits, merge strategies"
user-invocable: false
---

# Commit Conventions Quick Reference

## Conventional Commits Format

```
<type>(<optional-scope>): <description>

<optional body>

<optional footer(s)>
```

### Types

| Type | Purpose | Triggers version bump? |
|------|---------|----------------------|
| `feat` | New feature | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Documentation only | No |
| `style` | Formatting, whitespace | No |
| `refactor` | Code restructuring, no behavior change | No |
| `perf` | Performance improvement | PATCH |
| `test` | Adding or updating tests | No |
| `build` | Build system or dependencies | No |
| `ci` | CI configuration | No |
| `chore` | Other maintenance | No |

### Breaking Changes

Append `!` after type/scope or add `BREAKING CHANGE:` footer:

```
feat!: remove deprecated /v1 API endpoints

BREAKING CHANGE: All /v1 endpoints have been removed. Migrate to /v2.
```

### Examples

```bash
# Simple feature
git commit -m "feat(auth): add OAuth2 login flow"

# Bug fix with scope
git commit -m "fix(parser): handle empty input without panic"

# Docs update
git commit -m "docs: update API authentication guide"

# Refactor with body
git commit -m "refactor(db): extract connection pooling logic

Move connection pool management from individual repositories
into a shared ConnectionPool service to reduce duplication
and ensure consistent timeout handling."

# Breaking change
git commit -m "feat(api)!: change pagination to cursor-based

BREAKING CHANGE: offset-based pagination on /users and /orders
has been replaced with cursor-based pagination. Update clients
to use the 'cursor' parameter instead of 'page'."
```

## Atomic Commits

Each commit should be a single logical change that:

1. **Compiles/builds** on its own
2. **Passes tests** on its own
3. **Makes sense** as an isolated change
4. **Can be reverted** without side effects

### Good Atomic Commits

```
feat(auth): add password hashing utility
feat(auth): add user registration endpoint
feat(auth): add login endpoint with JWT tokens
test(auth): add authentication integration tests
```

### Bad Non-Atomic Commits

```
wip: started auth stuff
fix: more auth work and also fixed a typo in readme
feat: finish auth and update deps and fix linting
```

## Commit Message Quality Rules

**Subject line:**
- Max 72 characters
- Imperative mood ("add" not "added" or "adds")
- No trailing period
- Lowercase after type prefix

**Body (when needed):**
- Explain WHY, not WHAT (the diff shows what)
- Wrap at 80 characters
- Separate from subject with blank line

**When to include a body:**
- Non-obvious reasoning behind the change
- Breaking changes that need migration notes
- Changes that affect behavior in subtle ways
- Context that helps future readers understand trade-offs

## Merge Strategies

### Squash Merge

Combines all branch commits into a single commit on the target branch.

```
Feature branch:          main after squash merge:
  ●──●──●──●             ●──●  (single new commit)
 "wip" "fix" "done"       "feat: add search"
```

**When to use:**
- Branch has messy WIP commits
- Feature is a single logical unit
- You want a clean main history

```bash
git checkout main
git merge --squash feat/search
git commit -m "feat: add full-text search"
```

### Merge Commit (--no-ff)

Creates an explicit merge commit preserving branch topology.

```
main ──●──────────●──  (merge commit)
        \        /
         ●──●──●       (branch commits preserved)
```

**When to use:**
- Branch commits are well-structured and atomic
- You want to preserve the feature branch timeline
- GitFlow workflow

```bash
git checkout main
git merge --no-ff feat/search
```

### Rebase and Merge

Replays branch commits on top of the target, then fast-forwards.

```
Before:                    After rebase + merge:
main ──●──●                main ──●──●──●'──●'──●'
        \                               (rebased commits)
         ●──●──●
```

**When to use:**
- Branch commits are clean and atomic
- You want linear history without merge commits
- Trunk-based or GitHub Flow

```bash
git checkout feat/search
git rebase main
git checkout main
git merge --ff-only feat/search
```

### Decision Matrix

| Factor | Squash | Merge Commit | Rebase |
|--------|--------|-------------|--------|
| History clarity | Very clean | Grouped | Linear |
| Individual commits preserved | No | Yes | Yes (rewritten) |
| Bisect-friendly | Less (one big commit) | Yes | Yes |
| Conflict resolution | Once | Once | Per-commit |
| Best for | Messy branches | Structured branches | Clean branches |

## Additional Resources

For commit message templates, automated commit linting setup, changelog generation, and signing conventions, see [conventions-reference.md](conventions-reference.md).

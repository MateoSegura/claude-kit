# Commit Conventions -- Deep Reference

## Commit Message Templates

### Git Commit Template

Create `~/.gitmessage`:

```
# <type>(<scope>): <description>
#
# [optional body]
#
# [optional footer(s)]
#
# Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore
# Scope: component or module affected (optional)
#
# Rules:
# - Subject: max 72 chars, imperative mood, no period
# - Body: explain WHY not WHAT, wrap at 80 chars
# - Footer: BREAKING CHANGE:, Fixes #123, Refs #456
```

Activate:

```bash
git config --global commit.template ~/.gitmessage
```

### Scope Conventions

Define scope by project layer or module:

```
# By module
feat(auth): add two-factor authentication
fix(parser): handle nested brackets correctly
refactor(db): simplify query builder interface

# By layer
feat(api): add /users/{id}/preferences endpoint
fix(ui): prevent double-submit on checkout button
perf(cache): add LRU eviction to session store
```

## Commit Linting

### commitlint Configuration

```json
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [2, "always", [
      "feat", "fix", "docs", "style", "refactor",
      "perf", "test", "build", "ci", "chore"
    ]],
    "subject-max-length": [2, "always", 72],
    "body-max-line-length": [1, "always", 80]
  }
}
```

### Git Hook for Commit Message Validation

`.git/hooks/commit-msg` (basic pattern):

```bash
#!/bin/sh
commit_regex='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\(.+\))?(!)?: .{1,72}$'
if ! head -1 "$1" | grep -qE "$commit_regex"; then
    echo "ERROR: Commit message does not follow Conventional Commits format."
    echo "Expected: <type>(<scope>): <description>"
    exit 1
fi
```

## Changelog Generation

### From Conventional Commits to CHANGELOG

Conventional Commits enable automatic changelog generation:

```
## [2.1.0] - 2025-03-15

### Features
- **auth**: add OAuth2 login flow (abc1234)
- **search**: add full-text search with fuzzy matching (def5678)

### Bug Fixes
- **parser**: handle empty input without panic (ghi9012)
- **api**: correct rate limit header calculation (jkl3456)

### Breaking Changes
- **api**: change pagination to cursor-based (mno7890)
```

### Mapping Commits to Changelog Sections

| Commit Type | Changelog Section | Included? |
|------------|-------------------|-----------|
| `feat` | Features | Always |
| `fix` | Bug Fixes | Always |
| `perf` | Performance | Always |
| `docs` | Documentation | Optional |
| `refactor` | Code Refactoring | Optional |
| `BREAKING CHANGE` | Breaking Changes | Always |
| `build`, `ci`, `chore` | Maintenance | Rarely |

## Signed Commits

### GPG Signing

```bash
# Configure GPG key
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true

# Sign a single commit
git commit -S -m "feat: add signed commit"

# Verify signatures
git log --show-signature
```

### SSH Signing (Git 2.34+)

```bash
# Configure SSH signing
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

## Commit Fixup and Autosquash

For cleaning up commit history before merge:

```bash
# Create a fixup commit targeting a previous commit
git commit --fixup=abc1234

# Later, autosquash during rebase
git rebase -i --autosquash main
```

The fixup commit will automatically be ordered and marked for squashing into
the target commit during interactive rebase.

## Atomic Commit Patterns

### Separate Concerns

```bash
# Bad: mixed concerns
git add . && git commit -m "add search and fix typos and update deps"

# Good: separate commits
git add src/search/ && git commit -m "feat: add search module"
git add docs/ && git commit -m "docs: fix typos in API guide"
git add package.json package-lock.json && git commit -m "chore: update dependencies"
```

### Stage Hunks for Precise Commits

```bash
# Stage specific hunks from a file
git add -p src/app.py

# Review what's staged vs unstaged
git diff --cached    # staged
git diff             # unstaged
```

### Split a Large Change into Atomic Commits

1. Make all changes on your branch
2. Soft reset to unstage everything: `git reset HEAD~N` (where N = number of commits)
3. Re-stage and commit in logical groups
4. Verify each commit builds: `git rebase -i main --exec "make test"`

## Revert Conventions

```bash
# Revert creates a new commit that undoes a previous one
git revert abc1234

# Revert message format (auto-generated)
# Revert "feat(auth): add OAuth2 login flow"
#
# This reverts commit abc1234.
# Reason: OAuth2 provider changed their API and this integration
# is no longer functional. Will re-implement in #456.
```

Always add a reason in the revert commit body explaining WHY the change is
being reverted.

## Multi-Line Commit Messages from CLI

```bash
# Using heredoc
git commit -m "$(cat <<'EOF'
feat(auth): add two-factor authentication

Adds TOTP-based 2FA using the authenticator app pattern.
Users can enable 2FA from their security settings page.

Refs #234
EOF
)"

# Using multiple -m flags (each becomes a paragraph)
git commit -m "feat(auth): add two-factor authentication" \
           -m "Adds TOTP-based 2FA using the authenticator app pattern." \
           -m "Refs #234"
```

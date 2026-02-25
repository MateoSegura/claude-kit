---
name: core-git:advanced-operations
description: "Advanced git operations -- interactive rebase, cherry-pick, bisect, reflog, stash, worktrees, submodules"
user-invocable: false
---

# Advanced Operations Quick Reference

## Interactive Rebase

Rewrite, reorder, squash, or edit commits before pushing.

```bash
# Rebase last 5 commits
git rebase -i HEAD~5

# Rebase onto main
git rebase -i main
```

**Interactive rebase commands:**

| Command | Short | Effect |
|---------|-------|--------|
| `pick` | `p` | Keep commit as-is |
| `reword` | `r` | Keep commit, edit message |
| `edit` | `e` | Pause to amend commit |
| `squash` | `s` | Merge into previous, combine messages |
| `fixup` | `f` | Merge into previous, discard message |
| `drop` | `d` | Remove commit entirely |
| `reorder` | -- | Move lines to reorder commits |

```bash
# Example: squash WIP commits
pick abc1234 feat: add search module
squash def5678 wip: search tweaks
squash ghi9012 fix: search edge case
pick jkl3456 test: add search tests
```

**Safety:** Never rebase commits that have been pushed to a shared branch.

## Cherry-Pick

Apply specific commits from one branch to another.

```bash
# Pick a single commit
git cherry-pick abc1234

# Pick multiple commits
git cherry-pick abc1234 def5678

# Pick a range (exclusive start, inclusive end)
git cherry-pick abc1234..ghi9012

# Cherry-pick without committing (stage only)
git cherry-pick --no-commit abc1234
```

**Conflict resolution during cherry-pick:**

```bash
# After resolving conflicts
git add <resolved-files>
git cherry-pick --continue

# Abort the cherry-pick
git cherry-pick --abort
```

## Git Bisect

Binary search through commit history to find which commit introduced a bug.

```bash
# Start bisect
git bisect start

# Mark current state as bad
git bisect bad

# Mark a known-good commit
git bisect good v1.0.0

# Git checks out a middle commit -- test it, then:
git bisect good   # if this commit is fine
git bisect bad    # if this commit has the bug

# Repeat until git identifies the culprit
# "abc1234 is the first bad commit"

# Done -- return to original branch
git bisect reset
```

**Automated bisect with a test script:**

```bash
# Run a command at each step -- exit 0 = good, exit 1 = bad
git bisect start HEAD v1.0.0
git bisect run ./test-script.sh
```

## Reflog Recovery

The reflog records every HEAD movement. Use it to recover "lost" commits.

```bash
# View reflog
git reflog

# Output example:
# abc1234 HEAD@{0}: commit: feat: add search
# def5678 HEAD@{1}: checkout: moving from main to feat/search
# ghi9012 HEAD@{2}: reset: moving to HEAD~3

# Recover a commit after accidental reset
git checkout -b recovery-branch abc1234

# Recover after accidental branch deletion
git reflog
# Find the last commit on the deleted branch
git checkout -b restored-branch HEAD@{N}
```

**Reflog entries expire after 90 days (30 for unreachable commits).**

## Stash Management

Temporarily shelve changes without committing.

```bash
git stash                                  # stash tracked changes
git stash push -m "WIP: feature" -u        # with message, include untracked
git stash list                             # list all stashes
git stash pop                              # apply + remove most recent
git stash apply stash@{2}                  # apply specific stash (keep it)
git stash show -p stash@{0}               # view stash diff
git stash drop stash@{1}                  # drop specific stash
```

## Worktrees

Check out multiple branches simultaneously in separate directories.

```bash
# Create a worktree for a hotfix while keeping current work
git worktree add ../hotfix-branch hotfix/urgent-fix

# Create worktree with new branch
git worktree add -b feat/new-feature ../new-feature main

# List worktrees
git worktree list

# Remove a worktree
git worktree remove ../hotfix-branch

# Prune stale worktree references
git worktree prune
```

**Use cases:**
- Fix a bug on main while keeping feature branch work intact
- Review a PR locally without switching branches
- Run tests on multiple branches simultaneously

## Submodules vs Subtrees

| Factor | Submodules | Subtrees |
|--------|-----------|----------|
| Complexity | Higher | Lower |
| Clone experience | Requires `--recurse-submodules` | Works automatically |
| History | Separate repo history | Merged into parent |
| Contributor friction | High | Low (just a directory) |

```bash
# Submodules: embed repo as pointer to a specific commit
git submodule add https://github.com/org/lib.git libs/lib
git clone --recurse-submodules <url>
git submodule update --init --recursive

# Subtrees: merge repo history into a subdirectory
git subtree add --prefix=libs/lib https://github.com/org/lib.git main --squash
git subtree pull --prefix=libs/lib https://github.com/org/lib.git main --squash
```

**Rule of thumb:** Use subtrees for vendored dependencies. Use submodules when you actively develop in both repos.

## Additional Resources

For detailed rebase workflows, conflict resolution strategies, and advanced recovery patterns, see [operations-reference.md](operations-reference.md).

# Advanced Operations -- Deep Reference

## Rebase Workflows

### Rebase onto Updated Main

```bash
# Fetch latest main
git fetch origin

# Rebase your feature branch onto updated main
git rebase origin/main

# If conflicts arise:
# 1. Resolve conflicts in the files
# 2. Stage resolved files
git add <resolved-files>
# 3. Continue rebase
git rebase --continue

# To abort and return to pre-rebase state
git rebase --abort
```

### Rebase with Exec (Verify Each Commit)

```bash
# Run tests after each rebased commit to ensure no broken commits
git rebase -i main --exec "make test"
```

### Splitting a Commit During Interactive Rebase

```bash
# In interactive rebase, mark the commit as 'edit'
# When git stops at that commit:

# Undo the commit but keep changes staged
git reset HEAD~1

# Stage and commit in parts
git add src/module-a/ && git commit -m "refactor: extract module A"
git add src/module-b/ && git commit -m "refactor: extract module B"

# Continue rebase
git rebase --continue
```

### Rebase Preserving Merge Commits

```bash
# Preserve merge topology during rebase
git rebase --rebase-merges main
```

## Conflict Resolution Strategies

### Understanding Conflict Markers

```
<<<<<<< HEAD (or ours)
Code from the current branch
=======
Code from the incoming branch
>>>>>>> branch-name (or theirs)
```

### Resolution Commands

```bash
# Accept our version entirely
git checkout --ours path/to/file

# Accept their version entirely
git checkout --theirs path/to/file

# Use a merge tool
git mergetool

# After resolving, mark as resolved
git add path/to/file
```

### Rerere (Reuse Recorded Resolution)

Git can remember how you resolved a conflict and auto-apply it next time.

```bash
# Enable rerere
git config --global rerere.enabled true

# View recorded resolutions
git rerere status

# Forget a recorded resolution
git rerere forget path/to/file
```

### Reduce Conflict Pain

- Rebase frequently (daily) to reduce drift
- Keep branches short-lived
- Communicate with team about overlapping file changes
- Use `git diff main...HEAD -- path/` to preview potential conflicts

## Advanced Cherry-Pick

### Cherry-Pick a Merge Commit

```bash
# Must specify which parent to use as the base
# -m 1 uses the first parent (usually the branch merged into)
git cherry-pick -m 1 <merge-commit-hash>
```

### Cherry-Pick to Create a Backport

```bash
# Fix is on main
git log --oneline main
# abc1234 fix: prevent race condition in scheduler

# Apply to release branch
git checkout release/2.x
git cherry-pick abc1234

# If cherry-pick needs modifications for the older codebase
git cherry-pick --no-commit abc1234
# Edit files as needed for compatibility
git commit -m "fix: prevent race condition in scheduler (backport)"
```

## Advanced Bisect

### Bisect with Multiple Good Commits

```bash
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
git bisect good v1.1.0  # can specify multiple known-good points
```

### Skip Untestable Commits

```bash
# If a commit cannot be tested (broken build, etc.)
git bisect skip
```

### Bisect a Specific Path

```bash
# Only consider commits that changed specific paths
git bisect start -- src/scheduler/
```

## Reflog Advanced Patterns

### Recover from Bad Rebase

```bash
# Find the pre-rebase state
git reflog
# Look for "rebase (start)" entry
# The entry BEFORE it is your pre-rebase state

# Reset to pre-rebase state
git reset --hard HEAD@{N}
```

### Recover Deleted Stash

```bash
# Stashes are stored as commits -- find them in reflog
git fsck --unreachable | grep commit

# Or search for stash-like entries
git log --all --oneline --graph --decorate $(git fsck --no-reflog 2>/dev/null | grep "dangling commit" | cut -d' ' -f3)

# Once you find the hash
git stash apply <hash>
```

### Time-Based Reflog Queries

```bash
# Where was HEAD 2 hours ago?
git reflog show HEAD@{2.hours.ago}

# Where was main yesterday?
git reflog show main@{yesterday}

# Diff between now and 1 hour ago
git diff HEAD@{1.hour.ago}
```

## Advanced Stash

### Stash Individual Files

```bash
# Stash specific files only
git stash push -m "stash login changes" src/login.py src/auth.py

# Stash everything except staged changes
git stash push --keep-index -m "stash unstaged only"
```

### Create Branch from Stash

```bash
# Applies stash and creates a new branch
git stash branch feat/from-stash stash@{0}
```

## Worktree Patterns

### CI/CD with Worktrees

```bash
# Use worktrees for parallel CI builds
git worktree add --detach /tmp/build-pr-123 origin/pr/123
cd /tmp/build-pr-123
make test
cd -
git worktree remove /tmp/build-pr-123
```

### Review Multiple PRs

```bash
# Set up worktrees for each PR
git worktree add ../review-pr-100 origin/feat/user-search
git worktree add ../review-pr-101 origin/fix/memory-leak

# Review each in its own directory
# Clean up when done
git worktree remove ../review-pr-100
git worktree remove ../review-pr-101
```

## File History and Blame

### Track File Across Renames

```bash
# Follow file through renames
git log --follow -- path/to/file.py

# Blame with rename detection
git blame -C path/to/file.py
```

### Find When a Line Was Deleted

```bash
# Search for when a string was added or removed
git log -S "function_name" --oneline

# With patch to see the actual changes
git log -S "function_name" -p

# Regex version
git log -G "def\s+old_function" --oneline
```

### Blame Ignore Formatting Commits

```bash
# Create .git-blame-ignore-revs
echo "abc1234  # bulk formatting change" >> .git-blame-ignore-revs

# Configure git to use it
git config blame.ignoreRevsFile .git-blame-ignore-revs

# Blame will now skip those commits
git blame path/to/file.py
```

## Reset Modes

```bash
# Soft: undo commit, keep changes staged
git reset --soft HEAD~1

# Mixed (default): undo commit, unstage changes, keep in working dir
git reset HEAD~1

# Hard: undo commit, discard all changes (DESTRUCTIVE)
git reset --hard HEAD~1
```

| Mode | HEAD | Index (stage) | Working dir |
|------|------|---------------|-------------|
| `--soft` | Moves | Unchanged | Unchanged |
| `--mixed` | Moves | Reset | Unchanged |
| `--hard` | Moves | Reset | Reset |

## Clean and Maintenance

```bash
# Remove untracked files (dry run first)
git clean -n     # preview
git clean -f     # execute
git clean -fd    # include directories
git clean -fX    # only gitignored files
git clean -fx    # everything untracked

# Garbage collection
git gc

# Aggressive cleanup (slow, for large repos)
git gc --aggressive --prune=now

# Check repository integrity
git fsck
```

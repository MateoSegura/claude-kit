# Developer Workflow Automation — claude-kit Repo

This rule governs how you behave when developing **inside** the claude-kit
repository. It complements the global `[kit:]` debug traces with `[dev:]`
traces and makes you proactively execute development workflows so the
developer never has to ask.

---

## 1. Dev Session Header

At the start of every conversation turn where you perform an action, print a
`[dev:session]` line **before** the `[kit:session]` line:

```
[dev:session] branch: <branch> | dirty: <file zones> | layers: <affected test layers>
```

- **branch**: current git branch (warn if `main`)
- **dirty**: summarize what zones have uncommitted changes — `cli`, `plugins`,
  `scripts`, `docs`, `rules`, `ci`, `templates`, or `clean`
- **layers**: which test layers are relevant based on dirty zones — `1`, `2`,
  `3`, `4`, or `all`

To determine these values, check `git branch --show-current` and categorize
the output of `git diff --name-only` (both staged and unstaged). Cache the
result for the turn — do not re-run git on every tool call.

Example:
```
[dev:session] branch: fix/hook-script-path | dirty: plugins, scripts | layers: 2, 3
[kit:session] core: architecture, git, kit | teams: none | system: maker, updater | routing: active
```

---

## 2. Branch Guard

If you detect that the current branch is `main` and the user's intent requires
code changes, **create a branch before doing anything else**. Print:

```
[dev:guard] on main — creating branch <type>/<description>
```

Use the branch naming convention from `git-workflow.md`. Infer the type from
the user's intent (`feat`, `fix`, `docs`, `chore`, etc.). If ambiguous, ask.

---

## 3. Auto-Validation

After you finish a batch of edits (before committing or when the user pauses),
proactively run the test layers affected by your changes. Do not wait to be
asked. Print:

```
[dev:validate] running layers <N, N> — triggered by changes to <zone>
```

### Zone-to-Layer Map

| Changed zone | Run layers | Commands |
|--------------|-----------|----------|
| `claude-kit` (the CLI file) | 1, 2 | `python3 -m py_compile claude-kit && bash scripts/test-cli.sh` |
| `scripts/test-cli.sh` | 2 | `bash scripts/test-cli.sh` |
| `plugins/**` | 3 | `python3 scripts/validate-plugins.py --changed --strict && bash scripts/test-plugin-consistency.sh` |
| `scripts/validate-plugins.py` or `scripts/test-plugin-consistency.sh` | 3 | `python3 scripts/validate-plugins.py --all --strict && bash scripts/test-plugin-consistency.sh` |
| `docs/**` | 4 | `bash scripts/validate-docs.sh` |
| `scripts/validate-docs.sh` | 4 | `bash scripts/validate-docs.sh` |
| Multiple zones | union of layers | Run each affected layer in order |

If validation fails, **fix the issue before proceeding**. Do not commit broken
code and do not ask the user whether to fix it — just fix it.

---

## 4. Cross-Team Consistency

When you edit a file inside a team plugin (e.g., `plugins/embedded-zephyr-engineer/`),
**proactively check the same role in every other team** before committing. Print:

```
[dev:xteam] checking <role> across teams: <team1>, <team2>, ...
            same issue found in: <list or "none">
```

Apply the same fix to all affected siblings. This rule is non-negotiable — the
`cross-team-consistency.md` rule defines the patterns to check.

---

## 5. Pre-Commit Gate

Before every `git commit`, run the full validation suite for all affected
layers. Print:

```
[dev:gate] pre-commit — running layers <N, N, ...>
```

If any layer fails, do not commit. Fix first, then retry.

After a successful commit, print:

```
[dev:commit] <short hash> on <branch> — <commit subject>
```

---

## 6. Version Bump Awareness

When you modify plugin content files (agents, commands, skills, hooks, scripts)
— not just README or docs — check whether a version bump is needed. Print:

```
[dev:version] <plugin-name> modified — bump needed: <patch|minor|major|none>
              reason: <what changed>
```

Determine bump level using the rules from `plugin-versions.md`:
- New agent/command/skill → minor
- Content fix, hook tweak, script fix → patch
- Renamed/removed agent/command/skill → major
- README-only or doc-only → none

If a bump is needed and hasn't been done yet, do it proactively (update
`plugin.json` version and README badge) unless the user is mid-flow and
clearly not done with changes to that plugin.

---

## 7. Auto-Routing for Developer Commands

When the user's message matches a repo-level workflow, invoke the
corresponding `.claude/commands/` skill immediately. Do not explain that
a command exists — just run it.

| Intent | Invoke | Trace |
|--------|--------|-------|
| "validate", "check plugins", "run checks" | `validate-all` | `[dev:route] validate → validate-all` |
| "bump version", "bump the plugin" | `bump-plugin` | `[dev:route] bump → bump-plugin` |
| "release", "publish", "ship it" | `release` | `[dev:route] release → release` |
| "auto release", "CI release" | `auto-release` | `[dev:route] ci-release → auto-release` |

This extends the `[kit:route]` system — `[dev:route]` handles repo-internal
commands while `[kit:route]` handles plugin-loaded skills.

---

## 8. Post-Push CI Awareness

After pushing a branch, check CI status proactively:

```
[dev:ci] watching fast-validate on <branch>...
```

Use `gh run list --branch <branch> --limit 1` to check. If CI fails, fetch
the logs and diagnose without being asked.

---

## 9. Debug Trace Reference

All `[dev:]` prefixes at a glance:

| Prefix | When |
|--------|------|
| `[dev:session]` | Start of every action turn |
| `[dev:guard]` | Branch protection triggered |
| `[dev:validate]` | Auto-validation running |
| `[dev:xteam]` | Cross-team consistency check |
| `[dev:gate]` | Pre-commit validation gate |
| `[dev:commit]` | Commit completed |
| `[dev:version]` | Version bump assessment |
| `[dev:route]` | Developer command auto-routing |
| `[dev:ci]` | CI status monitoring |

These print **alongside** the `[kit:]` traces, not instead of them. A typical
turn header looks like:

```
[dev:session] branch: feat/new-agent | dirty: plugins | layers: 3
[kit:session] core: kit, architecture | teams: none | system: maker | routing: active
```

---

## 10. Extension Point

To add new developer automation behaviors, add a new numbered section to this
file following the pattern:

1. Describe the **trigger** (what the agent observes)
2. Describe the **action** (what the agent does proactively)
3. Assign a **`[dev:tag]`** trace prefix
4. Add the tag to the reference table in section 9

---
allowed-tools: Read, Edit, Glob, Bash
description: Interactively bump a plugin's semver version and add a draft CHANGELOG entry. Shows diff, does NOT commit.
---

# Bump Plugin Version

Guide the user through a version bump for a single plugin.

## Step 1 — Identify the Plugin

Ask the user which plugin to bump if not specified in the arguments. List
available plugins:

```bash
ls plugins/
```

## Step 2 — Show Current Version

Read the plugin's `plugin.json`:

```
plugins/<name>/.claude-plugin/plugin.json
```

Display: `Current version: x.y.z`

## Step 3 — Select Bump Type

Ask the user which semver component to bump:

| Type | When to use |
|------|-------------|
| **patch** | Content/doc improvement, hook tweak, script fix |
| **minor** | New agent, command, or skill added |
| **major** | Breaking change — renamed command, removed agent, changed skill API |

## Step 4 — Get Description

Ask for a one-line description of what changed (e.g. "Added X agent", "Fixed Y
hook"). This goes in the CHANGELOG.

## Step 5 — Compute New Version

Calculate the new version by incrementing the selected component and resetting
lower components to 0:
- patch: `x.y.z` → `x.y.(z+1)`
- minor: `x.y.z` → `x.(y+1).0`
- major: `x.y.z` → `(x+1).0.0`

## Step 6 — Update plugin.json

Edit `plugins/<name>/.claude-plugin/plugin.json` to set the new version.

## Step 7 — Update CHANGELOG.md

Add an entry under the `## [Unreleased]` section. If it does not exist, create
it at the top of the file (after the `# Changelog` header).

Format:

```markdown
## [Unreleased]
### Plugins Changed
- **<plugin-name>** x.y.z → a.b.c — <description>
```

If the `[Unreleased]` section already exists, append the new line under
`### Plugins Changed` (create that subsection if missing).

## Step 8 — Show Diff

Display the changes made to both files so the user can review before committing.

Do NOT commit or stage anything. The user will commit when ready.

# Plugin Conventions — claude-kit

These rules apply when working in the claude-kit repository itself —
editing plugins, scripts, workflows, or tooling. They do NOT apply to the
plugins that claude-kit distributes.

## Plugin File Schema — Critical

`plugin.json` is parsed by Claude Code's plugin loader. Only these fields are
safe:

```json
{ "name": "...", "description": "...", "version": "x.y.z" }
```

**Any extra field (`author`, `role`, `companions`, `keywords`, etc.) causes the
plugin to SILENTLY FAIL TO LOAD.** The old template had an `author` field —
ignore it. Put `role` and `companions` in `ctl.json` instead.

## Frontmatter Key Names — Critical

| File type | Tool restriction key | Wrong key |
|-----------|---------------------|-----------|
| `agents/*.md` | `tools:` | ~~allowed-tools:~~ |
| `commands/*.md` | `allowed-tools:` | ~~tools:~~ |
| `skills/*/SKILL.md` | `allowed-tools:` (if needed) | ~~tools:~~ |

Mixing these up causes silent failures. Both are required by the plugin loader
and are different fields with different semantics.

## Script Path Convention

All hook scripts must use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths:

```bash
# Correct
"command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"

# Wrong — breaks on any machine
"command": "/home/mateo/claude-kit/plugins/my-plugin/scripts/validate.sh"
```

## Knowledge Plugins

A knowledge plugin (`ctl.json` → `"role": "knowledge"`) serves as companion
reference material. It must NOT contain `agents/` or `commands/` directories.
Skills and hooks only.

## Companion Declarations

All plugins listed in `ctl.json` → `companions[]` must already exist as
directories under `plugins/` before committing. The validator (`check 5`)
enforces this at CI time.

## Validation Before Committing

Before committing a plugin change, run Tier 1 validation locally:

```bash
claude-kit validate --changed   # only what changed
claude-kit validate --all       # all plugins
claude-kit validate <name>      # one plugin
```

Or use the `/validate-all` command for combined Tier 1 + semantic review.

## Plugin Creation and Enhancement

- **New plugin:** `claude-kit --kit system-maker` → `/system-maker:make-agent`
- **Enhance existing:** `claude-kit --kit system-updater` → `/system-updater:update-agent`

## Plugin Version Strategy

| Bump | When |
|------|------|
| patch | Content/doc improvement, hook tweak, script fix |
| minor | New agent, command, or skill added |
| major | Breaking change — renamed command, removed agent, changed skill API |

Repo tag version is determined by the highest-severity plugin bump in the release draft.

# Plugin Version Convention

## New Plugins Start at 0.0.1

Every newly created plugin MUST have `"version": "0.0.1"` in its `.claude-plugin/plugin.json`. Never start a new plugin at `1.0.0` — that implies a stable, production-ready release.

The `0.x.y` range signals that the plugin is in active development and its API (commands, agents, skills) may change without notice. A `1.0.0` release is a deliberate decision made via the release workflow, not an automatic default.

## README Version Badge

Every plugin README includes a version badge on line 3:

```
> **Role:** <Role> · **Version:** <version>
```

This MUST match the `version` field in `.claude-plugin/plugin.json` exactly. When bumping a plugin version, always update both files.

## Version Bump Rules

| Bump  | When | Example |
|-------|------|---------|
| PATCH | Content improvement, doc update, hook tweak, script fix | 0.0.1 → 0.0.2 |
| MINOR | New agent, command, or skill added | 0.0.1 → 0.1.0 |
| MAJOR | Breaking change — renamed command, removed agent, changed skill name | 0.1.0 → 1.0.0 |

## Verification

Before committing any plugin change, verify version consistency:

```bash
# Check a specific plugin
jq -r .version plugins/<name>/.claude-plugin/plugin.json
grep "Version:" plugins/<name>/README.md
```

Both values must match. The `/bump-plugin` command handles this automatically.

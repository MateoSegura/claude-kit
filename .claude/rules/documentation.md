# Documentation Rules — claude-kit

These rules apply when working in the claude-kit repository. They govern when and how plugin documentation must be updated.

## Plugin README Maintenance

Every plugin directory (`plugins/<name>/`) has a `README.md` that documents its agents, commands, and skills.

### When You MUST Update a Plugin README

- **Modifying any file under `plugins/<name>/`** — review `plugins/<name>/README.md` and update it to reflect the change
- **Adding or removing an agent** — update the Agents table in the plugin's README
- **Adding or removing a command** — update the Commands section in the plugin's README
- **Adding or removing a skill** (knowledge plugins) — update the Skills Inventory table
- **Changing an agent's `description:` frontmatter field** — update the matching row in the Agents table
- **Changing a command's purpose or name** — update the Commands section

### When You MUST Update the Main README

- **Adding a new plugin team** — add a team blurb and link-table entry in the Plugins section of `README.md`
- **Renaming a plugin** — update the plugin name in both the team table and the link

### When Creating a New Plugin

Before committing, create `plugins/<name>/README.md` following the template for the plugin's role:

- **Knowledge plugin** — Skills Inventory table + auto-loading note
- **Engineer / Grader / Tester** — Agents table + Commands section + companion note + launch instructions
- **System plugin** — Agents table + Commands section + launch instructions

## README Content Rules

- Agent descriptions must come from the `description:` field in each `agents/*.md` frontmatter — do not paraphrase or summarize
- Command descriptions must accurately reflect what the command orchestrates
- Skill names in knowledge plugins must match the `name:` field in each `skills/*/SKILL.md` frontmatter
- Version badge must match the `version` field in `.claude-plugin/plugin.json`

## Validation

Run Tier 1 validation after any plugin change — it does not validate README content, so README accuracy is a manual responsibility:

```bash
claude-kit validate --changed
```

## docs/ and QMS Awareness

For docs/ artifacts governed by QMS processes, follow
`qms-artifact-management.md` for creation workflow and template compliance.
See `docs-system.md` for the layer reference and cross-reference format.

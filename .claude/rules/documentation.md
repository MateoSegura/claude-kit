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

## docs/ System Awareness

Plugin READMEs are part of a broader documentation system in `docs/`. When
making significant changes to plugins or the CLI, check whether related
documentation exists in the structured docs layers:

- **Architecture changes** — check `docs/architecture/decisions/` for ADRs that
  may need superseding, and `docs/architecture/components/` for component docs
  that may need updating
- **New features** — check `docs/requirements/` for the driving REQ and
  `docs/specs/` for the implementing SPEC; update their status fields
- **Breaking changes** — check `docs/operations/migration/` for migration guides
  that may need creating

See `.claude/rules/docs-system.md` for the full documentation system reference.

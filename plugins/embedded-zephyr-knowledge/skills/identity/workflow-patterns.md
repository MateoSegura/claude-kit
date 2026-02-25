# Zephyr Knowledge — Usage Patterns

How this knowledge plugin is consumed by companion role plugins (engineer, grader, tester) and how to maintain its content.

## Consumption Model

This is a **knowledge companion** plugin — it has no agents or commands of its own. Its skills are loaded by role plugins via the `companions` field in their `ctl.json`:

```json
{
  "role": "engineer",
  "companions": ["embedded-zephyr-knowledge"]
}
```

When a role plugin's agent lists a skill from this plugin in its `skills:` frontmatter, the skill is auto-loaded at agent startup. The agent then has access to all reference material in that skill directory.

## Skill Loading Priority

Role plugin agents should list knowledge skills after their own identity skill:

```yaml
skills: identity, embedded-zephyr-knowledge:zephyr-kernel, embedded-zephyr-knowledge:design-patterns
```

The SKILL.md entry point is auto-loaded. Reference files (API docs, examples, pattern catalogs) are loaded on demand via the Read tool when the agent needs deeper detail.

## Content Maintenance Workflow

### Adding a New Hardware Target

1. Create a new skill directory: `skills/<vendor>-hardware/`
2. Write `SKILL.md` with board overview, pin mappings, peripheral summary
3. Write example files: `<board>-examples.md` with compilable code per peripheral
4. Add devicetree overlay examples for common configurations
5. Update the identity `SKILL.md` to list the new target in the Domain Scope section

### Adding a New API Domain

1. Create a new skill directory: `skills/<domain>/` (e.g., `skills/usb-device/`)
2. Write `SKILL.md` with API overview, key structs, initialization sequence
3. Write reference files for sub-APIs (e.g., `cdc-acm.md`, `mass-storage.md`)
4. Include Kconfig dependencies and common configuration snippets
5. Cross-reference from related skills (e.g., link USB from `hardware-nordic` if nRF has USB)

### Updating Existing Content

1. Read the current skill files to understand scope and structure
2. Verify changes against Zephyr upstream docs (prefer `docs.zephyrproject.org`)
3. Update code examples to compile against the current Zephyr version
4. Mark deprecated patterns with `[DEPRECATED]` — do not remove them immediately
5. Update version references if API signatures changed between Zephyr releases

## Quality Checks

Before any content is committed, verify:

- All code examples have required `#include` directives
- Devicetree overlays specify the target board in a comment
- Kconfig symbols exist in the current Zephyr tree
- API function signatures match the current Zephyr headers
- Cross-references to other skills resolve to existing directories
- No role-specific content leaked in (no agent prompts, no grading rubrics, no test strategies)

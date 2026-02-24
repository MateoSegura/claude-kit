# system-maker

> **Role:** System · **Version:** 0.2.2

Agent Maker — guides users through designing and building Claude Code domain-expert plugins (single or full teams) via structured multi-phase workflows with parallel subagent execution.

```bash
claude-kit --kit system-maker
```

**Companion auto-loaded:** `core-spec` (spec-driven development and progress tracking)

---

## Agents

| Agent | Description |
|-------|-------------|
| `questionnaire-builder` | Generates a targeted 10-20 question questionnaire to capture user requirements that cannot be inferred from the domain analysis alone. Use after domain analysis is complete. |
| `domain-analyzer` | Deep-dives into a single facet of a coding domain. Launched 3x in parallel (technical, workflow, tools) so the orchestrator can merge three focused analyses into one domain map. |
| `arch-designer` | Designs a complete plugin architecture proposal for a given strategy. Launched 3x in parallel (minimal, comprehensive, progressive) so the reviewer can compare and unify. |
| `arch-reviewer` | Senior architect that critiques three parallel architecture proposals (minimal, comprehensive, progressive) and produces a single unified, buildable design. Use sequentially after all three arch-designers complete. |
| `identity-writer` | Writes the identity skill for a new plugin. The identity skill defines WHO the agent is: personality, non-negotiables, methodology, coding standards, and communication style. |
| `skill-writer` | Writes domain knowledge skills for a new plugin, following the multi-file skill structure (SKILL.md + reference.md + examples.md). |
| `agent-writer` | Writes subagent .md definition files with correct frontmatter, system prompts, and tool access for a new plugin. |
| `hook-writer` | Writes hooks.json configuration and hook shell scripts for a new plugin using all three hook types (command, prompt, agent). |
| `plugin-reviewer` | Exhaustive quality auditor for newly built plugins. Performs a 9-category deep review covering structure, frontmatter, cross-references, content quality, hooks, JSON validity, and anti-patterns. Returns a graded report with categorized findings and specific fix instructions. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/system-maker:make-agent` | Multi-phase plugin creation orchestrator. Guides through an 11-phase workflow (discovery → analysis → design → implementation → quality gate → finalization) to produce a complete, validated plugin. |
| `/system-maker:make-team` | Batch team creation workflow. Builds all 4 role plugins (knowledge, engineer, grader, tester) for a domain in parallel, sharing domain analysis across all roles. |
| `/system-maker:validate` | Semantic validation and quality review of one or more plugins using the plugin-reviewer agent. Produces a structured PASS/FAIL report per plugin. |

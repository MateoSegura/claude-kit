# system-maker

> **Role:** System · **Version:** 0.5.0

Team Maker — guides users through designing and building Claude Code domain-expert plugin teams via structured multi-phase workflows with parallel subagent execution.

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
| `identity-writer` | Writes the identity skill for a new plugin. The identity skill defines WHO the agent is: personality, non-negotiables, methodology, coding standards, and communication style. Use during Phase 8 implementation, runs in parallel with skill-writer, agent-writer, and hook-writer. |
| `skill-writer` | Writes multi-file skill directories and command .md orchestration files for a new plugin. Use during Phase 8 implementation, runs in parallel with identity-writer, agent-writer, and hook-writer. |
| `agent-writer` | Writes subagent .md definition files with correct frontmatter, system prompts, and tool access for a new plugin. Use during Phase 8 implementation, runs in parallel with identity-writer, skill-writer, and hook-writer. |
| `hook-writer` | Writes hooks.json configuration and hook shell scripts for a new plugin using all three hook types (command, prompt, agent). Use during Phase 8 implementation, runs in parallel with identity-writer, skill-writer, and agent-writer. |
| `plugin-reviewer` | Exhaustive quality auditor for newly built plugins. Performs a 9-category deep review covering structure, frontmatter, cross-references, content quality, hooks, JSON validity, and anti-patterns. Returns a graded report with categorized findings and specific fix instructions. Use during Phase 10 after all plugin files are assembled. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/system-maker:make-team` | Team creation workflow. Builds all role plugins (knowledge, engineer, grader, tester) for a domain in one session, sharing domain analysis across all roles with batched implementation. |
| `/system-maker:validate` | Semantic validation and quality review of one or more plugins using the plugin-reviewer agent. Produces a structured PASS/FAIL report per plugin. |

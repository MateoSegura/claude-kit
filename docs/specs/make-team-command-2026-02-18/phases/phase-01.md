# Phase 01: Questionnaire-builder TEAM_MODE

## Objective
Extend the questionnaire-builder agent to accept a TEAM_MODE flag and produce role-aware questionnaire output (shared + per-role delta questions).

## Satisfies
- R4 (questionnaire-builder accepts TEAM_MODE flag with dual output format)

## Steps
1. [x] Read current `plugins/system-maker/agents/questionnaire-builder.md` to understand input/output contract
2. [x] Add `TEAM_MODE` and `ROLES` to the `<input>` section — TEAM_MODE is a boolean, ROLES is a list of role names
3. [x] Update `<process>` section to describe the delta-question derivation: identify which questions are domain-wide (shared) vs. role-specific (delta)
4. [x] Add a `<team_mode_output>` section with the JSON schema for TEAM_MODE: true output format
5. [x] Update `<constraints>` to specify: when TEAM_MODE is false or absent, output is identical to current format (backward compatible)
6. [x] Verify the updated agent file has valid frontmatter (tools: Read, Glob, Grep — unchanged)

## Files to Create/Modify
- `plugins/system-maker/agents/questionnaire-builder.md` — add TEAM_MODE input, dual output format, delta question logic

## Acceptance Criteria
- [ ] questionnaire-builder.md accepts TEAM_MODE: true with ROLES list and produces `{"shared_questions": [...], "delta_questions": {"engineer": [...], "grader": [...]}}`
- [ ] questionnaire-builder.md with TEAM_MODE: false (or absent) produces identical output format to current version (`{"questions": [...]}`)
- [ ] No changes to frontmatter fields (name, model, tools, skills, etc.)
- [ ] Delta questions are role-specific: grader gets rubric questions, debugger gets tool questions, etc.
- [ ] Shared questions cover domain-wide concerns: coding style, build system, target platforms, etc.

## Dependencies
- Requires: None (first phase)
- Blocks: Phase 02 (make-team.md needs the updated questionnaire-builder format)

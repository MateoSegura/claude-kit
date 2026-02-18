# Phase 03: Backward Compatibility Update

## Objective
Add TEAM_MODE: false to make-agent.md's Phase 4 questionnaire-builder prompt so the existing single-plugin workflow explicitly opts out of team mode.

## Satisfies
- R8 (make-agent.md passes TEAM_MODE: false to questionnaire-builder)

## Steps
1. [x] Read `plugins/system-maker/commands/make-agent.md` Phase 4 section to locate the exact questionnaire-builder prompt
2. [x] Add `TEAM_MODE: false` line to the prompt passed to the questionnaire-builder subagent (after DOMAIN_MAP line)
3. [x] Verify no other changes are needed — the questionnaire-builder's backward-compatible behavior means this is purely a documentation/explicitness change

## Files to Create/Modify
- `plugins/system-maker/commands/make-agent.md` — add one line to Phase 4 prompt: `TEAM_MODE: false`

## Acceptance Criteria
- [ ] make-agent.md Phase 4 prompt includes `TEAM_MODE: false` in the questionnaire-builder call
- [ ] No other changes to make-agent.md
- [ ] make-agent workflow behavior is completely unchanged (TEAM_MODE: false produces identical output to current)

## Dependencies
- Requires: Phase 01 (questionnaire-builder must understand TEAM_MODE before make-agent references it)
- Blocks: None (final phase)

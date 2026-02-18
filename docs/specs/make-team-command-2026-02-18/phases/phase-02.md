# Phase 02: Create make-team.md Command

## Objective
Write the full `/system-maker:make-team` orchestrator command that builds multiple role plugins for a single domain in one session.

## Satisfies
- R1 (make-team command exists and orchestrates multi-plugin creation)
- R2 (active spec gate)
- R3 (shared domain analysis)
- R5 (parallel architecture design)
- R6 (batched implementation at 3 plugins/batch)
- R7 (batched review at 3 plugins/batch)
- R9 (re-uses all existing subagent types)

## Steps
1. [x] Create `plugins/system-maker/commands/make-team.md` with correct frontmatter: `allowed-tools: Task, AskUserQuestion, Read, Glob, Grep, Write, Edit, Bash`
2. [x] Write Phase 0: Active Spec Gate — check `<SPEC_ROOT>/.active` exists, halt with informative message if missing
3. [x] Write Phase 1: Type Selection — same as make-agent Phase 1 (currently only "coding")
4. [x] Write Phase 2: Domain Capture & Role Selection — capture domain description, derive base name (`<type>-<domain>-<tech>`), then ask user which roles to build (engineer, grader, tester, debugger, deployer, migrator — multi-select). Derive full plugin names from base + roles.
5. [x] Write Phase 2.5: Knowledge Plugin Check — same as make-agent Phase 2.5, but runs once for the shared domain. If knowledge plugin missing, create it before role plugins.
6. [x] Write Phase 3: Shared Domain Analysis — identical to make-agent Phase 3 (team of 4 domain-analyzers), runs once, DOMAIN_MAP shared across all role plugins
7. [x] Write Phase 4: Unified Questionnaire — call questionnaire-builder with TEAM_MODE: true and ROLES list. Present shared questions first, then per-role delta questions. Store combined USER_ANSWERS keyed by "shared" and per-role.
8. [x] Write Phase 5: Parallel Architecture Design — launch N arch-designer subagents in a single response (one per role plugin), each with the shared DOMAIN_MAP + role-specific USER_ANSWERS. User approves each architecture (sequential approval loop).
9. [x] Write Phase 6: Batched Implementation — process plugins in batches of 3. For each batch: create 3 implementation teams (TeamCreate x3), each with 4 parallel writers (identity-writer, skill-writer, agent-writer, hook-writer). Wait for all 3 teams to complete. Move to next batch.
10. [x] Write Phase 7: Assembly — for each plugin sequentially, create plugin.json, ctl.json (with companions if knowledge plugin exists), .lsp.json, .mcp.json as needed. Validate file existence.
11. [x] Write Phase 8: Batched Review — process plugins in batches of 3. For each batch: launch 3 review teams with plugin-reviewer + fix cycle. Wait for all to complete.
12. [x] Write Phase 9: Finalization — present summary of all plugins, ask for final approval, copy all from BUILD_DIR to $CLAUDE_KIT_OUTPUT_DIR
13. [x] Write error handling section — same patterns as make-agent (retry/skip/abort per subagent failure)
14. [x] Write workflow summary table showing all phases, subagent counts, parallelism, duration estimates

## Files to Create/Modify
- `plugins/system-maker/commands/make-team.md` — NEW: full orchestrator command (~1500-2000 lines)

## Acceptance Criteria
- [ ] make-team.md has `allowed-tools:` frontmatter (not `tools:`)
- [ ] Phase 0 checks for active spec and exits with clear message if missing
- [ ] Domain analysis section launches exactly 1 team of 4 domain-analyzers (not N teams)
- [ ] Questionnaire section passes TEAM_MODE: true and ROLES to questionnaire-builder
- [ ] Architecture section launches N parallel arch-designer calls (one per role) in a single response
- [ ] Implementation section batches at 3 plugins/batch, each batch creating 3 teams with 4 writers = 12 parallel subagents
- [ ] Review section batches at 3 plugins/batch with fix cycles
- [ ] All subagent_type references match existing agents: domain-analyzer, questionnaire-builder, arch-designer, arch-reviewer, identity-writer, skill-writer, agent-writer, hook-writer, plugin-reviewer
- [ ] BUILD_DIR per plugin: `/tmp/claude-kit-build-<plugin-name>/`
- [ ] Each plugin gets its own build directory and independent assembly
- [ ] Final approval covers all plugins together (single approval, not per-plugin)

## Dependencies
- Requires: Phase 01 (needs TEAM_MODE questionnaire-builder format)
- Blocks: Phase 03 (make-agent update should be done after make-team is complete to ensure consistency)

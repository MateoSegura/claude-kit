# Build /system-maker:make-team Command

## Context

**Original request:** Build /system-maker:make-team command and update questionnaire-builder agent to support TEAM_MODE, so single-domain teams can be built in one session with shared domain analysis, a unified questionnaire (shared + per-role delta questions), parallel architecture design, and batched parallel implementation/review.

**Conversation state:** Working in the claude-kit repo. Key files analyzed:
- `plugins/system-maker/commands/make-agent.md` (1400-line orchestrator command — the model for make-team)
- `plugins/system-maker/agents/questionnaire-builder.md` (current agent — needs TEAM_MODE extension)
- `plugins/system-maker/.claude-plugin/plugin.json` (plugin manifest)
- `plugins/system-maker/.claude-plugin/ctl.json` (companions: core-spec)
- `plugins/system-maker/skills/identity/SKILL.md` (identity skill with methodology)
- All existing agents: domain-analyzer, questionnaire-builder, arch-designer, arch-reviewer, identity-writer, skill-writer, agent-writer, hook-writer, plugin-reviewer

User constraints:
- make-team.md goes in `plugins/system-maker/commands/`
- Batch implementation at 3 plugins at a time (3 teams x 4 writers = 12 parallel subagents)
- Hard block at top of make-team: require active spec (`<SPEC_ROOT>/.active` must exist)
- One domain per session, human present throughout
- Re-use exact same subagent types as make-agent (no new agents)
- make-agent.md gets a one-line update to pass TEAM_MODE: false to questionnaire-builder in Phase 4

## Requirements

- **R1**: `/system-maker:make-team` command exists at `plugins/system-maker/commands/make-team.md` and orchestrates building multiple role plugins for a single domain in one session
- **R2**: make-team gates execution on an active spec — `<SPEC_ROOT>/.active` must exist or the command refuses to proceed
- **R3**: Domain analysis (make-agent Phase 3 equivalent) runs exactly once and its output is shared across all plugins being built
- **R4**: questionnaire-builder agent accepts a `TEAM_MODE` flag; when true, it produces shared questions + per-role delta questions; when false (or absent), behavior is identical to current
- **R5**: Architecture design runs in parallel — one architect per plugin/role, all launched simultaneously
- **R6**: Implementation is batched at 3 plugins at a time, each batch using 4 parallel writers (identity-writer, skill-writer, agent-writer, hook-writer) = 12 parallel subagents per batch
- **R7**: Plugin review is batched at 3 plugins at a time, with automated fix cycles per batch before moving to the next
- **R8**: make-agent.md passes `TEAM_MODE: false` to questionnaire-builder in its Phase 4 prompt, preserving backward compatibility
- **R9**: No new subagent types are created — make-team re-uses all existing agents (domain-analyzer, questionnaire-builder, arch-designer, arch-reviewer, identity-writer, skill-writer, agent-writer, hook-writer, plugin-reviewer)

## Acceptance Criteria

- [ ] [R1] `plugins/system-maker/commands/make-team.md` exists with correct `allowed-tools:` frontmatter and orchestrates multi-plugin creation
- [ ] [R2] make-team.md first section checks for active spec and halts with informative message if missing
- [ ] [R3] Domain analysis team launches once, and its DOMAIN_MAP is passed to all subsequent per-plugin phases
- [ ] [R4] questionnaire-builder.md handles both TEAM_MODE: true (shared + delta output) and TEAM_MODE: false/absent (current behavior unchanged)
- [ ] [R5] make-team launches N parallel arch-designer subagents (one per role) in a single response
- [ ] [R6] Implementation uses batches of 3 plugins, each batch spawning 3 implementation teams with 4 writers each
- [ ] [R7] Review uses batches of 3 plugins with fix cycles before proceeding to next batch
- [ ] [R8] make-agent.md Phase 4 prompt includes `TEAM_MODE: false` in the questionnaire-builder call
- [ ] [R9] make-team.md references only existing subagent_type values from the system-maker plugin

## Goal

Add team-building capability to the system-maker plugin so that all role plugins for a single domain (engineer, grader, tester, debugger, etc.) can be built in one session. The workflow shares domain analysis and common questionnaire answers across all roles, runs architecture design in parallel, and batches implementation/review at 3 plugins at a time to stay within practical subagent limits. This eliminates the need to run make-agent N times for a complete domain team.

## Architecture Decisions

- **Batch size of 3**: 3 plugins x 4 writers = 12 parallel subagents per batch. This balances throughput against system resource limits (API rate limits, context overhead). User confirmed this number.
- **Shared domain analysis**: The domain is the same for all roles (e.g., "embedded Zephyr"), so analyzing it once and broadcasting the DOMAIN_MAP avoids redundant work and ensures consistency.
- **Unified questionnaire with deltas**: Shared questions cover domain-wide preferences (coding style, build system, etc.). Delta questions are role-specific (e.g., grading rubric for grader, debug tools for debugger). This avoids asking the user the same question N times.
- **Active spec gate**: make-team is a heavy operation (10+ subagents, 30+ minutes). Requiring an active spec ensures the user has thought through the plan and provides continuity if the session needs to restart.
- **Re-use existing agents**: No new agent types. make-team is purely an orchestration command that calls the same domain-analyzer, questionnaire-builder, arch-designer, etc. that make-agent uses, just with different parameters and batch coordination.
- **Knowledge plugin creation happens once**: If no knowledge plugin exists for the domain, make-team creates it first (using Phase 2.5 from make-agent), then all role plugins reference it as a companion.
- **Sequential phase ordering**: Naming/roles -> domain analysis -> questionnaire -> parallel architecture -> batched implementation -> batched review -> sequential finalization. Each phase feeds the next.

## Constraints

- One domain per session (all plugins share the same `<type>-<domain>-<tech>-*` prefix)
- Human present throughout — interactive questions for role selection, architecture approval per plugin, final approval
- No new files in `plugins/system-maker/agents/` — only modify the existing questionnaire-builder.md
- make-agent.md change is minimal (one-line addition to Phase 4 prompt)
- Command file uses `allowed-tools:` frontmatter (not `tools:`)

## Phase Summary

| Phase | Title | Status | Satisfies | Description |
|-------|-------|--------|-----------|-------------|
| 1 | Questionnaire-builder TEAM_MODE | pending | R4 | Extend questionnaire-builder.md to support TEAM_MODE flag with shared + delta question output |
| 2 | Create make-team.md command | pending | R1, R2, R3, R5, R6, R7, R9 | Write the full orchestrator command at plugins/system-maker/commands/make-team.md |
| 3 | Backward compatibility update | pending | R8 | Add TEAM_MODE: false to make-agent.md Phase 4 questionnaire-builder prompt |

## Key Files

- `plugins/system-maker/commands/make-team.md` — NEW: team-building orchestrator command
- `plugins/system-maker/agents/questionnaire-builder.md` — MODIFY: add TEAM_MODE support
- `plugins/system-maker/commands/make-agent.md` — MODIFY: one-line addition to Phase 4
- `plugins/system-maker/skills/identity/SKILL.md` — reference for methodology patterns
- `plugins/system-maker/.claude-plugin/plugin.json` — manifest (may need description update)

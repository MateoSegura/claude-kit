# CLAUDE.md and Rules Behavior - Empirically Verified

## Testing Methodology

Tests were conducted using Claude Code v2.1.39 on a test monorepo with:
- Root CLAUDE.md with a unique secret code (ALPHA-7742)
- Subdirectory CLAUDE.md files in src/frontend/ and src/firmware/ with unique codes
- Path-filtered rules in .claude/rules/ with unique codes
- A global rule (no path filter) in .claude/rules/ with a unique code

Tests used `--tools ""` to disable tools (preventing Claude from proactively searching) and `--output-format json` to track tool usage turns.

## Verified Results

### What IS Auto-Loaded at Startup

| Mechanism | Auto-Loaded? | Survives Compaction? |
|---|---|---|
| Root `./CLAUDE.md` | **YES** | YES - re-injected every turn |
| `~/.claude/CLAUDE.md` (user-level) | **YES** | YES |
| `/etc/claude-code/CLAUDE.md` (managed) | **YES** | YES |
| `.claude/rules/*.md` WITHOUT path frontmatter | **YES** | YES |

### What is NOT Auto-Loaded

| Mechanism | Auto-Loaded? | Notes |
|---|---|---|
| Subdirectory `CLAUDE.md` (e.g., `src/frontend/CLAUDE.md`) | **NO** | NOT auto-loaded when Claude reads files in that directory |
| `.claude/rules/*.md` WITH path frontmatter | **NO** | NOT injected when Claude reads matching files |

### Detailed Test Results

**Test: All tools disabled, ask for root secret code**
- Result: Claude sees ALPHA-7742 (root CLAUDE.md) - LOADED

**Test: All tools disabled, ask for subdirectory secret codes**
- Result: Claude does NOT see BRAVO-9931 or CHARLIE-5508 - NOT LOADED

**Test: Only Read tool, read src/frontend/app.tsx, ask for frontend secret**
- Result: Claude does NOT see BRAVO-9931 after reading a frontend file - NOT LOADED

**Test: All tools enabled, ask for all secrets (JSON output)**
- Result: Claude finds all three BUT took 5 turns (proactively used Glob/Read tools to search for CLAUDE.md files) - NOT auto-loaded, Claude searched manually

**Test: Global rule (no path filter)**
- Result: Claude sees FOXTROT-0000 with tools disabled - LOADED

**Test: Path-filtered rule, read matching file**
- Result: Claude does NOT see DELTA-1234 after reading matching frontend file - NOT LOADED

## Implications for Architecture

1. **Do NOT rely on subdirectory CLAUDE.md for domain-specific context injection** - it is just a regular file that Claude might find if it searches.

2. **Do NOT rely on path-filtered rules for automatic context** - they are not triggered by file access.

3. **DO use root CLAUDE.md and global rules** for instructions that must always be present.

4. **DO use hooks** for deterministic domain-specific context injection (PostToolUse on Edit|Write can detect file paths and inject domain rules).

5. **DO use the plugin system** with subagents that have their own skills and MCP servers for domain isolation.

## CLAUDE.md Loading Hierarchy

Files are loaded in this order (all auto-loaded at startup):

1. `/etc/claude-code/CLAUDE.md` (managed - highest priority, cannot be overridden)
2. `~/.claude/CLAUDE.md` (user-level)
3. `./CLAUDE.md` or `./.claude/CLAUDE.md` (project root)
4. `./.claude/rules/*.md` (global rules only - no path frontmatter)
5. `./CLAUDE.local.md` (personal, gitignored)

Auto-learned memory at `~/.claude/projects/<project>/memory/` is also loaded.

## Codex CLI Comparison (AGENTS.md)

Codex CLI's AGENTS.md files DO chain automatically from root down to CWD:

```
~/.codex/AGENTS.md → repo-root/AGENTS.md → src/AGENTS.md → src/lib/AGENTS.md
```

This is a notable advantage for Codex in monorepo subdirectory context. However, Codex lacks the hook system that makes Claude's enforcement deterministic. See [06-codex-cli-comparison.md](./06-codex-cli-comparison.md).

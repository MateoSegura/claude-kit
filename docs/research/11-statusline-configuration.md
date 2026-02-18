# Status Line Configuration

## Overview

The status line is a customizable bar at the bottom of Claude Code. It runs a shell script that receives JSON session data on stdin and displays whatever the script prints.

## Configuration

Add to `~/.claude/settings.json` (user-level) or `.claude/settings.json` (project-level):

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 2
  }
}
```

Can also use inline commands:
```json
{
  "statusLine": {
    "type": "command",
    "command": "jq -r '\"[\\(.model.display_name)] \\(.context_window.used_percentage // 0)% context\"'"
  }
}
```

## Quick Setup

Use `/statusline` command with natural language:
```
/statusline show model name, agent name, and context percentage with a progress bar
```

## Available JSON Data (Stdin)

| Field | Description |
|---|---|
| `model.id`, `model.display_name` | Current model |
| `cwd`, `workspace.current_dir` | Current working directory |
| `workspace.project_dir` | Directory where Claude Code was launched |
| `cost.total_cost_usd` | Session cost in USD |
| `cost.total_duration_ms` | Wall-clock time since session start |
| `cost.total_api_duration_ms` | Time waiting for API responses |
| `cost.total_lines_added/removed` | Lines of code changed |
| `context_window.used_percentage` | % of context window used |
| `context_window.remaining_percentage` | % remaining |
| `context_window.context_window_size` | Max context size (200000 or 1000000) |
| `context_window.current_usage` | Token counts from last API call |
| `session_id` | Unique session ID |
| `transcript_path` | Path to conversation transcript |
| `version` | Claude Code version |
| `output_style.name` | Current output style |
| `vim.mode` | `NORMAL` or `INSERT` (when vim mode enabled) |
| **`agent.name`** | **Agent name when running with --agent flag** |

## Agent-Aware Status Line

The `agent.name` field is present when running with `--agent` flag or agent settings. This enables showing which specialist profile is active:

```bash
#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
AGENT=$(echo "$input" | jq -r '.agent.name // empty')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)

CYAN='\033[36m'; GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; RESET='\033[0m'

if [ -n "$AGENT" ]; then
  LABEL="${CYAN}[$AGENT]${RESET}"
else
  LABEL="${CYAN}[$MODEL]${RESET}"
fi

if [ "$PCT" -ge 90 ]; then BAR_COLOR="$RED"
elif [ "$PCT" -ge 70 ]; then BAR_COLOR="$YELLOW"
else BAR_COLOR="$GREEN"; fi

FILLED=$((PCT / 10)); EMPTY=$((10 - FILLED))
BAR=$(printf "%${FILLED}s" | tr ' ' '█')$(printf "%${EMPTY}s" | tr ' ' '░')

printf '%b' "$LABEL ${BAR_COLOR}${BAR}${RESET} ${PCT}%%\n"
```

## Update Timing

- Runs after each new assistant message
- Runs when permission mode changes or vim mode toggles
- Debounced at 300ms
- If script is still running when a new update triggers, the in-flight execution is cancelled
- Script changes require a new Claude interaction to take effect

## Output Capabilities

- **Multiple lines**: each echo/print creates a separate row
- **ANSI colors**: `\033[32m` for green, etc.
- **Clickable links**: OSC 8 escape sequences (terminal support required)

## Performance Tips

- Keep output short (status bar has limited width)
- Cache slow operations (like `git status`) to a temp file with TTL
- Scripts run frequently during active sessions

## Note on disableAllHooks

If `disableAllHooks` is `true` in settings, the status line is also disabled. Remove or set to `false` to re-enable.

# Deterministic Workflow Patterns

## The Determinism Spectrum

| Behavior | Mechanism | Deterministic? |
|---|---|---|
| Domain rules injected when editing | PostToolUse hook + shell script | **Yes** - hook always fires, script always runs |
| Status log updated on task completion | TaskCompleted hook + shell script | **Yes** - append-only, script-written |
| Plan required before implementation | PreToolUse hook + shell script | **Yes** - hard block, can't bypass |
| Context recovery after compaction | SessionStart(compact) agent hook | **Hook fires: yes. Agent quality: ~90%** |
| Session-end status check | Stop prompt hook | **Hook fires: yes. Check quality: ~85%** |
| Developer enters right workflow | Skill invocation (/plan, /implement) | **Yes** - explicit user action |
| Claude follows injected rules | systemMessage from hook | **~90%** - strong but not guaranteed |
| Claude updates status.md voluntarily | CLAUDE.md instruction | **~70%** - degrades over time |

**Design rule**: Never rely on probabilistic behavior for anything critical. If it must happen, a hook must force it.

## The File-Based State Layer

```
plan/
├── overview.md    # Goals, architecture, key decisions
├── status.log     # Append-only log (written by hooks, not Claude)
└── phases/
    ├── phase-1.md # Detailed phase plan
    └── phase-2.md
```

- `overview.md`: Written by `/plan` skill, read by compaction recovery hook
- `status.log`: NEVER written by Claude directly. Only appended by the `update-status.sh` hook script on TaskCompleted events
- `phases/`: Created during planning, read during implementation

## Hook-Driven Workflow Configuration

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [{
          "type": "agent",
          "prompt": "Read plan/status.log (last 30 lines) and plan/overview.md. Summarize: (1) current phase, (2) last completed task, (3) next steps.",
          "timeout": 30
        }]
      }
    ],

    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "command": "$CLAUDE_PROJECT_DIR/.shared/hooks/detect-domain.sh"
        }]
      }
    ],

    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "command": "$CLAUDE_PROJECT_DIR/.shared/hooks/verify-plan.sh"
        }]
      }
    ],

    "TaskCompleted": [
      {
        "hooks": [{
          "type": "command",
          "command": "$CLAUDE_PROJECT_DIR/.shared/hooks/update-status.sh"
        }]
      }
    ],

    "Stop": [
      {
        "hooks": [{
          "type": "prompt",
          "prompt": "Check: was plan/status.log updated this session? Are all TaskList items in correct state? Respond {ok: true} or {ok: false, reason: '...'}."
        }]
      }
    ]
  }
}
```

## Key Hook Scripts

### detect-domain.sh (PostToolUse on Edit|Write)
Reads file path from stdin JSON, matches against domain patterns, injects domain-specific rules via systemMessage output.

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE_PATH" ] && exit 0

case "$FILE_PATH" in
  */frontend/* | *.tsx | *.jsx) DOMAIN="frontend" ;;
  */firmware/* | *.c | *.h)    DOMAIN="firmware" ;;
  */backend/* | */api/*)       DOMAIN="backend" ;;
  *) exit 0 ;;
esac

DOMAIN_FILE="$CLAUDE_PROJECT_DIR/.claude/domains/$DOMAIN.md"
if [ -f "$DOMAIN_FILE" ]; then
  RULES=$(cat "$DOMAIN_FILE")
  jq -n --arg msg "Active domain: $DOMAIN. Rules: $RULES" \
    '{systemMessage: $msg}'
fi
exit 0
```

### verify-plan.sh (PreToolUse on Edit|Write)
Blocks edits to source code if no plan exists.

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

case "$FILE_PATH" in
  */src/* | */lib/*)
    if [ ! -f "$CLAUDE_PROJECT_DIR/plan/overview.md" ]; then
      jq -n '{
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "deny",
          permissionDecisionReason: "No plan/overview.md found. Run /plan first."
        }
      }'
    fi
    ;;
esac
exit 0
```

### update-status.sh (TaskCompleted)
Deterministic append-only logging.

```bash
#!/bin/bash
INPUT=$(cat)
TASK_SUBJECT=$(echo "$INPUT" | jq -r '.task.subject // "unknown task"')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
mkdir -p "$CLAUDE_PROJECT_DIR/plan"
echo "[$TIMESTAMP] COMPLETED: $TASK_SUBJECT" \
  >> "$CLAUDE_PROJECT_DIR/plan/status.log"
exit 0
```

## Workflow Flows

### New Feature
```
Dev: /plan "add BLE support"
  → Skill creates plan/overview.md, plan/phases/, TaskList items
Dev: /implement
  → Skill reads plan, starts working
  → Edit firmware/ble.c
    → PostToolUse hook → detect-domain.sh → injects firmware rules
  → Complete a task
    → TaskCompleted hook → update-status.sh → appends to status.log
  → Context compacts
    → SessionStart(compact) → agent reads status.log + overview.md
  → Session ends
    → Stop hook → prompt checks status.log is current
```

### Bug Fix
Same hooks enforce domain rules and status tracking. Smaller plan (maybe single phase).

### Code Review
No plan enforcement needed (reading not writing). Domain detection still fires if review suggests edits.

## What the Minimal Root CLAUDE.md Should Contain

```markdown
# Project
This project uses hook-driven workflow management.
Do not rely on memory for project state - read plan/status.log and plan/overview.md.
Domain-specific rules are injected by hooks based on which files you touch.
Use /plan before implementing. Use /implement to start building.
```

That's it. The hooks do the enforcement. CLAUDE.md is just a bootstrap pointer.

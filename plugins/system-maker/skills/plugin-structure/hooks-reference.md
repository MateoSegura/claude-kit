# Hooks — Complete Reference

This is the exhaustive specification for Claude Code hooks (`hooks/hooks.json`). Every event, hook type, decision control mechanism, and pattern is documented here.

## File Location

Hooks are defined in `plugins/<name>/hooks/hooks.json`. They can also be inlined in `plugin.json` under the `hooks` key, or scoped to specific agents via agent frontmatter.

## CRITICAL: Correct Format

The hooks format uses **event names as top-level keys**, with an array of matcher/hook pairs under each event. This is NOT a flat array.

```json
{
  "hooks": {
    "EVENT_NAME": [
      {
        "matcher": "ToolNamePattern",
        "hooks": [
          {
            "type": "command",
            "command": "shell command to run"
          }
        ]
      }
    ]
  }
}
```

### Common Format Mistakes

```json
// WRONG — flat array, no event keys
{
  "hooks": [
    { "matcher": "Write", "type": "command", "command": "..." }
  ]
}

// WRONG — event key but hooks not nested in array
{
  "hooks": {
    "PreToolUse": {
      "matcher": "Write",
      "hooks": [{ "type": "command", "command": "..." }]
    }
  }
}

// CORRECT — event key → array of matchers → each has hooks array
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          { "type": "command", "command": "..." }
        ]
      }
    ]
  }
}
```

## All 14 Events

| Event | When it fires | Matcher matches against | Can block? |
|-------|--------------|------------------------|------------|
| `PreToolUse` | Before a tool executes | Tool name (e.g., `Write`, `Bash`, `Edit`) | Yes — non-zero exit or `permissionDecision: "deny"` |
| `PostToolUse` | After a tool executes successfully | Tool name | Yes — `decision: "block"` rejects the result |
| `PostToolUseFailure` | After a tool execution fails | Tool name | No |
| `PermissionRequest` | When a permission prompt appears | Permission type | Yes — can auto-allow or auto-deny |
| `UserPromptSubmit` | When the user submits a prompt | — | No |
| `Notification` | When a notification is sent | — | No |
| `Stop` | When the agent is about to stop | — | Yes — `decision: "block"` forces continuation |
| `SubagentStart` | When a subagent is spawned | — | No |
| `SubagentStop` | When a subagent finishes | — | No |
| `SessionStart` | When a session begins | — | No |
| `SessionEnd` | When a session ends | — | No |
| `TeammateIdle` | When a teammate becomes idle | — | No |
| `TaskCompleted` | When a task completes | — | No |
| `PreCompact` | Before context compaction | — | No |

### Event Timing

- **Pre events** (`PreToolUse`): Fire BEFORE the action. Can block or modify.
- **Post events** (`PostToolUse`, `PostToolUseFailure`): Fire AFTER the action. Can reject results.
- **Lifecycle events** (`SessionStart`, `Stop`, etc.): Fire at state transitions.

## Three Hook Types

### 1. Command Hooks

Run a shell command. The simplest and most common type.

```json
{
  "type": "command",
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
}
```

**Behavior:**
- Exit code 0 = pass (allow the operation)
- Exit code 2 on `PreToolUse` = block the tool (convention for explicit blocking)
- Stdout is captured and available as feedback
- Stderr is captured for error reporting
- The command runs in the system shell with access to environment variables

**Best for:**
- File validation (JSON syntax, schema compliance)
- Path protection (blocking writes to sensitive directories)
- Format enforcement (running linters, formatters)
- Simple checks that can be expressed as shell one-liners or scripts

### 2. Prompt Hooks

Evaluate an LLM prompt against the current context. Use `$ARGUMENTS` to interpolate event-specific data (tool inputs, file paths, etc.).

```json
{
  "type": "prompt",
  "prompt": "Review this code change for naming convention compliance. The file being written is: $ARGUMENTS. Check that all function names use snake_case, all class names use PascalCase, and all constants use UPPER_SNAKE_CASE. Respond with {\"ok\": true} if compliant, or {\"ok\": false, \"reason\": \"specific violation description\"} if not.",
  "model": "haiku"
}
```

**Behavior:**
- An LLM evaluates the prompt and returns a JSON response
- `{"ok": true}` = pass
- `{"ok": false, "reason": "..."}` = fail, reason is fed back to Claude
- The `model` field selects which model evaluates (`haiku`, `sonnet`, `opus`)
- `$ARGUMENTS` is replaced with event-specific data

**Best for:**
- Code style and convention checking
- Naming pattern validation
- Documentation quality assessment
- Any check that requires understanding code semantics (not just syntax)

**Model selection for prompt hooks:**
- Use `haiku` for simple pattern checks — fast and cheap
- Use `sonnet` for nuanced code review — better reasoning
- Avoid `opus` in hooks — too slow for inline validation

### 3. Agent Hooks

Spawn a full agentic verifier with tool access. The agent can read files, run commands, and perform multi-step reasoning.

```json
{
  "type": "agent",
  "prompt": "Verify that all test files in the project pass. Run the test suite using the project's test command. If any test fails, report which tests failed and why. Respond with {\"ok\": true} if all pass, or {\"ok\": false, \"reason\": \"test failures description\"}.",
  "timeout": 120
}
```

**Behavior:**
- A full Claude agent is spawned with access to tools (Read, Bash, etc.)
- The agent executes the prompt and returns a JSON response
- `{"ok": true}` = pass
- `{"ok": false, "reason": "..."}` = fail
- The `timeout` field (in seconds) limits execution time
- Agent hooks are HEAVY — they consume API calls and take time

**Best for:**
- Complex validations requiring file system access
- Running and interpreting test suites
- Multi-file consistency checks (e.g., "do all imports resolve?")
- Validations that require running commands and interpreting output

**When NOT to use agent hooks:**
- Simple file existence checks (use command: `test -f path`)
- Format validation (use command: `jq empty file.json`)
- Pattern matching (use command: `grep -q pattern file`)

## Async Hooks

Any hook type can run in the background by setting `"async": true`. Async hooks do NOT block the event — execution continues immediately while the hook runs in the background.

```json
{
  "type": "command",
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/run-full-test-suite.sh",
  "async": true,
  "timeout": 300
}
```

### When to Use Async

- Long-running test suites that shouldn't block conversation flow
- Background builds or compilation
- Deployment verification
- Any hook that takes more than a few seconds

### Timeout

The `timeout` field (in seconds) is especially important for async hooks to prevent runaway processes. Always set a timeout for async hooks.

| Hook duration | Recommended timeout |
|---------------|-------------------|
| Quick checks | 10-30 seconds |
| Linting/formatting | 30-60 seconds |
| Test suites | 120-300 seconds |
| Builds/deployments | 300-600 seconds |

## Hook Decision Control

Hooks can control Claude's behavior through structured JSON output. The format depends on the event type.

### PreToolUse Decision Control

Command hooks on `PreToolUse` can output JSON to stdout to control permissions:

```json
{
  "hookSpecificOutput": {
    "permissionDecision": "allow"
  }
}
```

| `permissionDecision` | Effect |
|---------------------|--------|
| `"allow"` | Skip the permission prompt and proceed — the tool runs without asking the user |
| `"deny"` | Block the tool silently — the tool does not run |
| `"ask"` | Show the normal permission prompt to the user (default behavior) |

**Use cases:**
- Auto-allow writes to the build directory: `if [[ "$TOOL_INPUT_FILE_PATH" == /tmp/build/* ]]; then echo '{"hookSpecificOutput":{"permissionDecision":"allow"}}'; fi`
- Auto-deny writes to production config: `if [[ "$TOOL_INPUT_FILE_PATH" == */production.json ]]; then echo '{"hookSpecificOutput":{"permissionDecision":"deny"}}'; fi`

### PostToolUse Decision Control

Reject a tool's output after it has already executed:

```json
{
  "decision": "block",
  "reason": "Output contained forbidden pattern — generated code includes eval()"
}
```

When `decision` is `"block"`, the tool's result is discarded and the `reason` is surfaced to Claude as feedback. Claude will typically attempt to fix the issue and retry.

### Stop Decision Control

Prevent the agent from stopping (force it to continue working):

```json
{
  "decision": "block",
  "reason": "Required validation step not yet completed — tests have not been run"
}
```

This is powerful for ensuring agents complete all required steps before finishing. Use it in `Stop` hooks to enforce completion checklists.

### Prompt and Agent Hook Responses

Prompt and agent hooks return a standardized pass/fail JSON:

```json
{"ok": true}
```

```json
{"ok": false, "reason": "Function 'processData' uses camelCase but project convention requires snake_case"}
```

When `ok` is `false`, the `reason` string is fed back to Claude, which typically attempts to fix the issue.

## Matcher Field

The `matcher` field is a string pattern that matches tool names. Use `|` (pipe) to match multiple tools:

```json
"matcher": "Write|Edit"        // matches Write OR Edit
"matcher": "Bash"              // matches only Bash
"matcher": "Write|Edit|Bash"   // matches any of the three
"matcher": ""                  // matches everything (or use for non-tool events)
```

For events that don't match against tool names (`SessionStart`, `Stop`, `SubagentStart`, etc.), the matcher can be omitted or set to an empty string.

## Environment Variables

These environment variables are available to hook command scripts:

| Variable | Available in | Contains |
|----------|-------------|----------|
| `$TOOL_INPUT_FILE_PATH` | PreToolUse/PostToolUse for Write/Edit | The file being written or edited |
| `$TOOL_INPUT_COMMAND` | PreToolUse/PostToolUse for Bash | The bash command being executed |
| `$TOOL_INPUT` | All PreToolUse/PostToolUse | JSON string of the full tool input |
| `${CLAUDE_PLUGIN_ROOT}` | All hooks | The plugin's absolute directory path |
| `$ARGUMENTS` | Prompt/agent hooks | Event-specific data for interpolation |
| `$SUBAGENT_NAME` | SubagentStart/SubagentStop | The name of the subagent being spawned or stopped |

## Common Patterns

### Pattern 1: File Protection (PreToolUse)

Block writes to sensitive paths:

```json
{
  "matcher": "Write|Edit",
  "hooks": [
    {
      "type": "command",
      "command": "if echo \"$TOOL_INPUT_FILE_PATH\" | grep -qE '(production|secrets|credentials|\\.env)'; then echo 'BLOCKED: Cannot write to sensitive file' >&2; exit 2; fi"
    }
  ]
}
```

### Pattern 2: Code Style Linting (PostToolUse)

Run a linter after every file write:

```json
{
  "matcher": "Write|Edit",
  "hooks": [
    {
      "type": "command",
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/lint-file.sh"
    }
  ]
}
```

Where `lint-file.sh` runs the appropriate linter based on file extension:

```bash
#!/bin/bash
FILE="$TOOL_INPUT_FILE_PATH"
EXT="${FILE##*.}"
case "$EXT" in
  py) python3 -m flake8 "$FILE" 2>&1 || true ;;
  js|ts) npx eslint "$FILE" 2>&1 || true ;;
  c|h) clang-tidy "$FILE" 2>&1 || true ;;
  json) python3 -m json.tool "$FILE" > /dev/null 2>&1 || echo "Invalid JSON: $FILE" ;;
esac
```

### Pattern 3: Convention Enforcement (PostToolUse prompt hook)

Check naming conventions using an LLM:

```json
{
  "matcher": "Write",
  "hooks": [
    {
      "type": "prompt",
      "prompt": "Check this file for naming convention violations: $ARGUMENTS. Functions must use snake_case, classes PascalCase, constants UPPER_SNAKE_CASE. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}.",
      "model": "haiku"
    }
  ]
}
```

### Pattern 4: Dangerous Command Prevention (PreToolUse)

Block destructive bash commands:

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "if echo \"$TOOL_INPUT_COMMAND\" | grep -qE '(rm -rf /|DROP TABLE|sudo|chmod 777|> /dev/)'; then echo 'BLOCKED: Dangerous command detected' >&2; exit 2; fi"
    }
  ]
}
```

### Pattern 5: Completion Verification (Stop agent hook)

Ensure all required steps were completed before the agent stops:

```json
{
  "matcher": "",
  "hooks": [
    {
      "type": "agent",
      "prompt": "Verify the agent completed all required steps: 1) All files were written to the build directory, 2) hooks.json is valid JSON, 3) plugin.json exists. Check the build directory and respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}.",
      "timeout": 60
    }
  ]
}
```

### Pattern 6: Auto-Format on Write (PostToolUse)

Run a formatter after writes and re-apply the formatted content:

```json
{
  "matcher": "Write",
  "hooks": [
    {
      "type": "command",
      "command": "case \"${TOOL_INPUT_FILE_PATH##*.}\" in py) black \"$TOOL_INPUT_FILE_PATH\" 2>/dev/null ;; js|ts) npx prettier --write \"$TOOL_INPUT_FILE_PATH\" 2>/dev/null ;; esac; exit 0"
    }
  ]
}
```

### Pattern 7: Session Environment Validation (SessionStart)

Verify required tools are installed when the session begins:

```json
{
  "matcher": "",
  "hooks": [
    {
      "type": "command",
      "command": "missing=''; for cmd in git jq python3; do command -v $cmd >/dev/null 2>&1 || missing=\"$missing $cmd\"; done; if [ -n \"$missing\" ]; then echo \"WARNING: Missing tools:$missing\" >&2; fi; exit 0"
    }
  ]
}
```

### Pattern 8: Build Directory Cleanup (Stop)

Clean up temporary build artifacts when the agent stops:

```json
{
  "matcher": "",
  "hooks": [
    {
      "type": "command",
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/cleanup-build.sh"
    }
  ]
}
```

### Pattern 9: Multi-File Consistency Check (PostToolUse agent hook)

Verify that a file change doesn't break consistency with related files:

```json
{
  "matcher": "Write|Edit",
  "hooks": [
    {
      "type": "agent",
      "prompt": "A file was just modified: $ARGUMENTS. Check that this change is consistent with related files in the same directory. Verify imports resolve, type signatures match, and naming is consistent. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}.",
      "timeout": 60
    }
  ]
}
```

### Pattern 10: Async Test Runner (PostToolUse)

Run tests in the background after code changes:

```json
{
  "matcher": "Write|Edit",
  "hooks": [
    {
      "type": "command",
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/run-tests.sh",
      "async": true,
      "timeout": 300
    }
  ]
}
```

## Complete Example: Rich hooks.json

This example demonstrates all three hook types across multiple events:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Session started' && for cmd in git jq; do command -v $cmd >/dev/null || echo \"WARN: $cmd not found\"; done"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$TOOL_INPUT_FILE_PATH\" | grep -qE '(\\.env|credentials|secrets)'; then echo 'BLOCKED' >&2; exit 2; fi"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/check-safe-command.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/lint-file.sh"
          },
          {
            "type": "prompt",
            "prompt": "Review this file change for convention compliance: $ARGUMENTS. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}.",
            "model": "haiku"
          }
        ]
      },
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/run-tests.sh",
            "async": true,
            "timeout": 300
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "agent",
            "prompt": "Verify all required deliverables exist and are valid. Check the build directory for completeness. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}.",
            "timeout": 60
          },
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/cleanup.sh"
          }
        ]
      }
    ]
  }
}
```

## Hook Type Selection Decision Tree

Use this to decide which hook type is appropriate:

1. **Can the check be expressed as a shell command or script?**
   - Yes → Use `command`
   - No → Continue

2. **Does the check require understanding code semantics (not just syntax)?**
   - Yes, but doesn't need file system access → Use `prompt`
   - Yes, and needs to read files or run commands → Use `agent`
   - No → Use `command`

3. **How fast does the check need to be?**
   - Must be near-instant (<1s) → Use `command`
   - Can tolerate 2-5s latency → Use `prompt` with `haiku`
   - Can tolerate 10-60s latency → Use `agent`

4. **Is this a blocking or background check?**
   - Background (results can come later) → Add `"async": true` to any type
   - Blocking (must pass before continuing) → Keep synchronous (default)

---

## Essential Hook Patterns for Production Plugins

Every production plugin should include hooks from these categories. Choose the appropriate type for each.

### Pattern: PostToolUse on Write|Edit — Smart Domain-Aware Linting (prompt type)

After every file write/edit, use a prompt hook for domain-aware evaluation. This catches issues that regex-based linters miss: wrong API usage patterns, missing error handling, convention violations.

```json
{
  "PostToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "prompt",
          "prompt": "Review this code change for domain-specific issues. Tool: $ARGUMENTS. Check for: 1) Missing error handling 2) Convention violations 3) Security issues 4) Common domain mistakes. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}"
        }
      ]
    }
  ]
}
```

Customize the prompt for the domain. For an embedded plugin: "Check for missing NULL pointer checks, bare ISR operations, and unprotected shared state." For a web plugin: "Check for XSS vulnerabilities, missing input validation, and unhandled promise rejections."

### Pattern: PreToolUse on Bash — Dangerous Command Blocking (command type)

Block destructive commands before they execute. This MUST be a command hook (fast, deterministic, no LLM latency). The script reads JSON from stdin and checks the command field.

```json
{
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/scripts/check-safe-command.sh"
        }
      ]
    }
  ]
}
```

### Pattern: PreToolUse on Write|Edit — Protected File Blocking (command type)

Prevent writes to files that should not be modified. Fast regex check, no LLM needed.

```json
{
  "PreToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/scripts/check-protected-files.sh"
        }
      ]
    }
  ]
}
```

### Pattern: Stop — Work Completeness Verification (prompt or agent type)

Before Claude stops, verify the work is actually complete. Use `prompt` type for quick checks, `agent` type for thorough verification that needs file reading.

Quick check (prompt type):
```json
{
  "Stop": [
    {
      "hooks": [
        {
          "type": "prompt",
          "prompt": "Evaluate if Claude should stop. Context: $ARGUMENTS. Check: 1) All requested tasks complete 2) No errors left unaddressed 3) Code compiles/builds. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}"
        }
      ]
    }
  ]
}
```

Thorough verification (agent type):
```json
{
  "Stop": [
    {
      "hooks": [
        {
          "type": "agent",
          "prompt": "Verify all work is complete. Context: $ARGUMENTS. Read the modified files, check for TODO comments left behind, verify error handling is present, and confirm the code is consistent across files. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}",
          "timeout": 120
        }
      ]
    }
  ]
}
```

### Pattern: PostToolUse on Write|Edit — Async Background Test Runner (command type, async)

Run tests in the background after file changes without blocking Claude. Tests complete asynchronously and results are available later.

```json
{
  "PostToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/scripts/run-tests-async.sh",
          "async": true,
          "timeout": 300
        }
      ]
    }
  ]
}
```

### Pattern: PostToolUse on Write|Edit — Multi-File Consistency Check (agent type)

After writes, verify the change is consistent with the rest of the codebase. The agent can read related files to check imports, type compatibility, and architecture compliance.

```json
{
  "PostToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "agent",
          "prompt": "A file was just modified. Context: $ARGUMENTS. Read the modified file and its imports/dependencies. Verify: 1) All imports resolve 2) Type signatures match usage 3) No circular dependencies introduced. Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}",
          "timeout": 60
        }
      ]
    }
  ]
}
```

### Pattern: SessionStart — Environment Validation (command type)

Verify required tools and environment are available when a session starts.

```json
{
  "SessionStart": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/scripts/check-environment.sh"
        }
      ]
    }
  ]
}
```

---

## Hook Shell Scripts — Complete Guide

Scripts live at `BUILD_DIR/scripts/` and are referenced from hooks.json using `${CLAUDE_PLUGIN_ROOT}/scripts/`. Scripts receive the hook event's JSON input on **stdin**. They MUST use `jq` to parse it. They do NOT receive environment variables for tool input.

### Script Template

```bash
#!/bin/bash
set -euo pipefail
# script-name.sh — Purpose description
# Called by hooks.json as a [Pre/Post]ToolUse hook on [Tool] tool
# Requires: jq

INPUT=$(cat)

# Parse relevant fields from JSON stdin
FIELD=$(echo "$INPUT" | jq -r '.tool_input.field_name // empty')

# Validation logic here
if [[ some_condition ]]; then
  echo "BLOCKED: Actionable error message explaining what to do instead" >&2
  exit 2
fi

exit 0
```

### Concrete Example: check-safe-command.sh

```bash
#!/bin/bash
set -euo pipefail
# check-safe-command.sh — Blocks destructive shell commands
# Called by hooks.json as a PreToolUse hook on Bash tool
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Block rm -rf on important paths
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*f|-[a-zA-Z]*r|--force|--recursive)'; then
  if echo "$COMMAND" | grep -qE '(/|\.\.|~|home|etc|var|usr)'; then
    echo "BLOCKED: Destructive rm command targeting sensitive path. Review the path and use a more targeted deletion." >&2
    exit 2
  fi
fi

# Block force push
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force'; then
  echo "BLOCKED: Force push is not allowed. Use --force-with-lease if you must override, or resolve conflicts normally." >&2
  exit 2
fi

# Block hard reset
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
  echo "BLOCKED: git reset --hard discards uncommitted work. Stash or commit changes first." >&2
  exit 2
fi

exit 0
```

### Concrete Example: check-protected-files.sh

```bash
#!/bin/bash
set -euo pipefail
# check-protected-files.sh — Blocks writes to protected files
# Called by hooks.json as a PreToolUse hook on Write|Edit tools
# Requires: jq

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Block writes to lock files
if echo "$FILE_PATH" | grep -qE '(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|Cargo\.lock)$'; then
  echo "BLOCKED: Do not modify lock files directly. Use the package manager to update dependencies." >&2
  exit 2
fi

# Block writes to CI/CD config
if echo "$FILE_PATH" | grep -qE '\.github/workflows/.*\.yml$'; then
  echo "BLOCKED: CI/CD workflow files are protected. Discuss changes with the team first." >&2
  exit 2
fi

exit 0
```

### Concrete Example: run-tests-async.sh

```bash
#!/bin/bash
set -euo pipefail
# run-tests-async.sh — Runs test suite in background after file changes
# Called by hooks.json as a PostToolUse async hook on Write|Edit tools
# Requires: jq

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Determine test command based on file type
if echo "$FILE_PATH" | grep -qE '\.py$'; then
  pytest --tb=short -q 2>&1 || true
elif echo "$FILE_PATH" | grep -qE '\.(ts|tsx|js|jsx)$'; then
  npm test -- --watchAll=false 2>&1 || true
elif echo "$FILE_PATH" | grep -qE '\.(rs)$'; then
  cargo test 2>&1 || true
fi

exit 0
```

### Concrete Example: check-environment.sh

```bash
#!/bin/bash
set -euo pipefail
# check-environment.sh — Verifies required tools are available at session start
# Called by hooks.json as a SessionStart hook
# Requires: jq (but checks for it)

# Check for jq (needed by other hook scripts)
if ! command -v jq &> /dev/null; then
  echo "WARNING: jq is not installed. Hook scripts require jq for JSON parsing. Install with: apt install jq / brew install jq" >&2
  exit 0  # Non-blocking warning
fi

exit 0
```

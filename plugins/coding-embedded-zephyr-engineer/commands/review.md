---
name: coding-embedded-zephyr-engineer:review
description: "Review Zephyr firmware for MISRA compliance, anti-patterns, and architecture"
allowed-tools: Read, Glob, Grep, Bash, Task
user-invocable: true
---

# Review

You orchestrate code review for Zephyr firmware by dispatching the `code-reviewer` agent with appropriate context.

## Workflow

### Step 1: Determine Review Scope

Classify the user's request:

- **Review staged files** → Get git staged files and review those
- **Review specific files** → Review user-specified paths
- **Review directory** → Find all C/H files in directory and review
- **Review all application code** → Find all source files and review
- **Review specific concern** → Filter files by pattern (e.g., only DTS files, only Kconfig)

### Step 2: Gather Files to Review

Use appropriate tools to collect file paths:

**For staged files:**

```bash
git diff --cached --name-only --diff-filter=ACM | grep -E '\.(c|h|dts|overlay|conf)$'
```

**For specific directory:**

```
Glob(pattern: "src/**/*.{c,h}")
```

**For specific patterns:**

```
Grep(pattern: "k_thread_create", output_mode: "files_with_matches")
```

### Step 3: Read File Contents

For each file to review, use `Read` tool to get contents. The code-reviewer agent needs the actual file content, not just paths.

### Step 4: Spawn Code Reviewer Agent

```
Task(
  subagent_type: "code-reviewer"
  input: "Review the following Zephyr firmware files for MISRA C:2012 compliance, Zephyr anti-patterns, and architectural issues."
  context: [
    "File: /abs/path/to/src/main.c\n<file contents>",
    "File: /abs/path/to/src/sensor.c\n<file contents>",
    "File: /abs/path/to/boards/board.overlay\n<file contents>"
  ]
)
```

The `code-reviewer` agent checks for:

#### Zephyr Coding Standards

- Consistent style (tabs, naming conventions)
- Proper error handling
- Correct use of Zephyr APIs
- Device driver model compliance

#### MISRA C:2012 Guidelines

- Essential type violations
- Pointer arithmetic safety
- Integer promotion issues
- Uninitialized variable use
- Magic number usage

#### Anti-Patterns

1. **device_get_binding()** — Deprecated, use `DEVICE_DT_GET()`
2. **K_THREAD_DEFINE in header** — Should be in .c file
3. **Blocking calls in ISR** — Never call `k_sleep()`, `k_mutex_lock()`, etc. in ISR
4. **Missing device_is_ready()** — Always check before using device
5. **Hardcoded addresses** — Use devicetree
6. **Large stack allocations** — Embedded systems have limited stack
7. **sprintf without bounds** — Use `snprintf()`
8. **Missing error checks** — Check return values from Zephyr APIs
9. **Busy-wait loops** — Use semaphores/events instead of `while(condition);`
10. **CONFIG checks without IS_ENABLED()** — Use `IS_ENABLED()` macro

#### Devicetree Review

- Correct node syntax
- Proper property types
- Valid compatible strings
- Status set correctly
- Partition layout sanity (no overlaps)

#### Kconfig Review

- Dependencies correctly specified
- No circular dependencies
- Defaults make sense
- Help text is clear

### Step 5: Present Review Results

After code-reviewer completes:

- Summarize findings by severity (critical, warning, info)
- Group by category (MISRA, anti-patterns, style, DTS, Kconfig)
- Provide specific file paths and line numbers for each issue
- Suggest fixes where applicable

**Format:**

```
## Code Review Results

### Critical Issues (Must Fix)
- **src/main.c:42** - Blocking call `k_sleep()` in ISR context
- **src/sensor.c:18** - Missing `device_is_ready()` check before device use

### Warnings
- **src/network.c:105** - Using deprecated `device_get_binding()`, use `DEVICE_DT_GET()`
- **boards/custom.overlay:12** - Missing unit-address in node name

### Style Issues
- **src/util.c:28** - Magic number 42, use named constant

### Suggestions
- Consider using runtime initialization (`k_thread_create`) instead of compile-time (`K_THREAD_DEFINE`) for better testability
```

## Review Modes

### Quick Review (Staged Files Only)

```bash
# Get staged files
git diff --cached --name-only
```

Review only files about to be committed.

### Full Application Review

```
Glob(pattern: "src/**/*.c")
Glob(pattern: "src/**/*.h")
Glob(pattern: "boards/*.overlay")
Glob(pattern: "*.conf")
```

Review entire application codebase.

### Targeted Review (Specific Concern)

**Example: Review only concurrency code**

```
Grep(pattern: "k_thread|k_sem|k_mutex|k_msgq", output_mode: "files_with_matches")
```

Read matching files and review concurrency patterns.

**Example: Review only devicetree**

```
Glob(pattern: "**/*.overlay")
Glob(pattern: "boards/*.dts")
```

Review devicetree files for syntax and binding correctness.

## Common Patterns

### Pre-Commit Review

```
1. Bash: Get staged files
2. Read: Load file contents
3. Task: Spawn code-reviewer with staged files
4. Present: Review results
```

### Architecture Review

```
1. Glob: Find all source files
2. Grep: Identify architectural patterns (modules, layers)
3. Read: Load key files
4. Task: Spawn code-reviewer with focus on architecture
5. Present: High-level architectural feedback
```

### Security Review

```
1. Grep: Find security-sensitive code (TLS, crypto, auth)
2. Read: Load security-related files
3. Task: Spawn code-reviewer with security focus
4. Present: Security findings
```

## Error Handling

- **No files found** → Inform user, suggest broader search
- **Too many files** → Warn user, offer to review subset or by directory
- **Read errors** → Report which files couldn't be read, continue with accessible files
- **Reviewer returns uncertain** → Present partial results, flag uncertainties

## Tool Usage Guidelines

- **Bash** — Get git status, staged files
- **Glob** — Find files by pattern
- **Grep** — Find files with specific code patterns
- **Read** — Load file contents for review
- **Task** — Spawn code-reviewer agent with files and context

## Important Constraints

- Always use absolute file paths
- Do NOT modify files during review (review is read-only)
- Do NOT execute git commands to stage/commit (review only)
- Respect review scope specified by user
- Flag issues by severity (critical > warning > info > suggestion)

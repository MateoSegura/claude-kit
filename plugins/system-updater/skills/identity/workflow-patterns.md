# System Updater — Workflow Patterns for Plugin Updates

This document describes the core workflow patterns used by the system-updater plugin to safely modify existing Claude Code plugins.

## Staging Pattern

### Concept

All changes happen in an isolated staging copy of the plugin. The live plugin is never touched until the user explicitly approves finalization with a timestamped backup.

### Implementation

**Copy to Staging (Phase 5 Start)**:

```bash
rm -rf /tmp/claude-kit-update-PLUGIN_NAME
cp -r $CLAUDE_KIT_OUTPUT_DIR/PLUGIN_NAME /tmp/claude-kit-update-PLUGIN_NAME
```

**Work on the Staging Copy**:

All change-writer and plugin-reviewer agents operate on `/tmp/claude-kit-update-PLUGIN_NAME/` — never the live plugin directory.

**Backup and Replace (Phase 7 Finalization)**:

```bash
# Create timestamped backup
cp -r $CLAUDE_KIT_OUTPUT_DIR/PLUGIN_NAME /tmp/claude-kit-backup-PLUGIN_NAME-$(date +%Y%m%d-%H%M%S)

# Replace live plugin
rm -rf $CLAUDE_KIT_OUTPUT_DIR/PLUGIN_NAME
cp -r /tmp/claude-kit-update-PLUGIN_NAME $CLAUDE_KIT_OUTPUT_DIR/PLUGIN_NAME

# Clean up staging
rm -rf /tmp/claude-kit-update-PLUGIN_NAME
```

### Why This Pattern

- **Safety**: If anything goes wrong, the live plugin is untouched
- **Iterative Review**: The user can review the staged changes before committing
- **Easy Rollback**: The timestamped backup enables instant rollback if issues arise
- **Isolated Testing**: Changes can be validated in staging before affecting the live plugin

## Analysis-First Pattern

### Concept

Before planning any changes, fully analyze the existing plugin structure to understand its domain, identity, conventions, and extension points.

### Implementation

**Phase 2: Launch plugin-analyzer**:

The plugin-analyzer agent reads EVERY file in the plugin and produces a structured JSON inventory:

- Plugin manifest (name, description, version, keywords)
- Complete file tree
- Identity (persona, methodology, non-negotiables)
- All skills (name, description, multi-file structure, topics, line count)
- All agents (name, description, model, tools, skills, color)
- All commands (name, description, dispatched agents)
- All hooks (events, matchers, types, purposes)
- LSP/MCP configuration
- Extension points (domain hierarchy, gaps, colors in use)

**Use in Planning**:

The change-planner uses this analysis to:

1. Evaluate fitness: Does the requested change align with the plugin's existing domain?
2. Match established patterns: New agents should preload the same skills, use similar colors, follow the same conventions
3. Identify gaps: Where can the change integrate without breaking existing structure?
4. Preserve conventions: Match the existing coding style, naming patterns, and file organization

### Why This Pattern

- **Informed Decisions**: You can't safely modify what you don't understand
- **Pattern Matching**: New components follow established conventions automatically
- **Gap Detection**: Identify structural weaknesses that could be addressed alongside the requested change
- **Backwards Compatibility**: Understanding existing cross-references prevents breaking changes

## Fitness Gate Pattern

### Concept

Before planning implementation, evaluate whether the requested change actually belongs in this plugin. If not, recommend creating a new plugin via system-maker instead.

### Implementation

**Phase 3: Fitness Check**:

The change-planner evaluates:

1. **Domain Alignment**: Does the change fit the plugin's existing domain/purpose?
2. **Scope Creep**: Would this change fundamentally shift the plugin's identity?
3. **Complexity**: Is the change so extensive it would obscure the original plugin's purpose?

**Three Possible Outcomes**:

| Outcome | Action |
|---------|--------|
| `fits` | Proceed to change planning — the change belongs in this plugin |
| `new_plugin` | Recommend system-maker — the change deserves its own plugin |
| `gray_area` | Present both options to the user — could go either way |

**Example Fitness Decisions**:

| Plugin | Request | Fitness | Reasoning |
|--------|---------|---------|-----------|
| coding-embedded-zephyr-engineer | Add Bluetooth support | `fits` | BLE is a Zephyr subsystem — natural extension |
| coding-embedded-zephyr-engineer | Add React frontend support | `new_plugin` | React has nothing to do with embedded Zephyr — domain mismatch |
| coding-embedded-zephyr-engineer | Add ESP-IDF support | `gray_area` | ESP-IDF is embedded but not Zephyr — could extend or fork |

### Why This Pattern

- **Plugin Cohesion**: Keeps plugins focused on their core domain
- **Discoverability**: Users can find the right plugin more easily when plugins have clear, narrow scopes
- **Maintenance**: Focused plugins are easier to maintain and evolve
- **User Guidance**: Recommending system-maker for out-of-scope changes educates users on good plugin design

## Knowledge Routing in Fitness Decisions

When evaluating update requests for plugins with companions, the fitness check gains a third dimension: knowledge routing.

### Example: Domain Knowledge Change to Role Plugin

User request: "Add Bluetooth LE API reference to coding-embedded-zephyr-engineer"

Analysis:
- Target plugin has companion: coding-embedded-zephyr-knowledge
- Change type: domain API reference → domain knowledge
- Fitness: gray_area with knowledge routing
- Recommendation: Route to knowledge plugin

Output includes:
- `knowledge_routing.target_plugin`: "coding-embedded-zephyr-knowledge"
- `knowledge_routing.routed_changes`: ["Add Bluetooth LE API reference skill"]
- `change_plan`: What it would look like adding directly to engineer (for user choice)

### Example: Role-Specific Change to Role Plugin

User request: "Add a code review agent to coding-embedded-zephyr-engineer"

Analysis:
- Target plugin has companion, but change is role-specific (new agent)
- Change type: agent addition → role-specific
- Fitness: fits
- No knowledge routing needed

### Example: Change to Knowledge Plugin Directly

User request: "Update the ESP32 hardware skill in coding-embedded-zephyr-knowledge"

Analysis:
- Target IS a knowledge plugin (role: "knowledge")
- Change is appropriate for knowledge plugins (hardware target update)
- Fitness: fits
- Constraint check: no agents or commands being added ✓

### Example: Inappropriate Change to Knowledge Plugin

User request: "Add a debugging agent to coding-embedded-zephyr-knowledge"

Analysis:
- Target IS a knowledge plugin (role: "knowledge")
- Change adds an agent → NOT appropriate for knowledge plugins
- Fitness: does not fit
- Recommendation: Add the agent to the corresponding role plugin instead (e.g., coding-embedded-zephyr-engineer)

## Parallel Execution Pattern

### Concept

Launch independent operations simultaneously to minimize total workflow time.

### Implementation

**Phase 2: Analysis + User Input**:

```
Task(subagent_type: "plugin-analyzer", prompt: "Analyze the plugin...")
AskUserQuestion("What would you like to change?")
```

Both calls issued in a single response. The analyzer runs while the user types.

**Phase 5: Multiple change-writer Agents**:

If the change plan has independent batches (e.g., creating 3 new skills that don't depend on each other):

```
Task(subagent_type: "change-writer", prompt: "Create skills/bluetooth/SKILL.md and skills/bluetooth/api-reference.md")
Task(subagent_type: "change-writer", prompt: "Create skills/usb/SKILL.md and skills/usb/examples.md")
Task(subagent_type: "change-writer", prompt: "Modify agents/code-writer.md to add bluetooth, usb to skills list")
```

All issued in a single response. They run concurrently.

### Why This Pattern

- **Speed**: Reduces total workflow time by 40-60% compared to sequential execution
- **Responsiveness**: The user sees results faster
- **Resource Utilization**: Makes efficient use of API parallelism

### When NOT to Use Parallelism

Do NOT launch operations in parallel if they have dependencies:

- Don't modify a file that hasn't been created yet
- Don't spawn the reviewer before the writers finish
- Don't finalize before the review completes

## Review-Fix Cycle Pattern

### Concept

After implementation, the plugin-reviewer audits the ENTIRE staged plugin (not just changed files) and categorizes issues by fix type. The orchestrator applies mechanical fixes directly and re-spawns the change-writer for content/structural fixes.

### Implementation

**Phase 6: Launch plugin-reviewer**:

```
Task(subagent_type: "plugin-reviewer", prompt: "Audit the staged plugin at /tmp/claude-kit-update-PLUGIN_NAME/...")
```

The reviewer returns findings categorized by `fix_type`:

- `mechanical`: Missing frontmatter fields, incorrect field names, missing JSON keys, trivial corrections
- `content`: Thin files, skeleton content, missing sections that need domain knowledge
- `structural`: Missing files that should exist (scripts, reference files)

**Apply Mechanical Fixes Directly**:

For each `mechanical` finding, use the Edit tool to apply the fix:

```
Edit(
  file_path: "/tmp/claude-kit-update-PLUGIN_NAME/agents/code-writer.md",
  old_string: "allowed-tools: Read, Write",
  new_string: "tools: Read, Write"
)
```

**Re-Spawn change-writer for Content/Structural Fixes**:

Bundle all `content` and `structural` findings and launch a fix-focused change-writer:

```
Task(subagent_type: "change-writer", prompt: "Fix these review findings: <JSON array of content/structural findings>")
```

**Re-Review Option**:

If the overall grade is D or F after fixes, offer the user a re-review to verify the fixes worked.

### Why This Pattern

- **Quality Assurance**: Catches implementation errors before the user sees them
- **Efficiency**: Mechanical fixes are instant (no LLM call needed)
- **Domain Expertise**: Content fixes benefit from the change-writer's domain knowledge
- **Confidence**: The user gets a reviewed, fixed plugin — not a first draft

## Error Recovery Pattern

### Concept

When a subagent fails, present the error to the user with three clear options: Retry, Skip, or Abort. Never silently swallow errors.

### Implementation

**Detect Failure**:

- Task tool returns an error
- Subagent returns malformed output (invalid JSON when JSON expected)
- Validation detects critical issues (invalid JSON files, missing required fields)

**Present Options via AskUserQuestion**:

```
A subagent failed during Phase <N>.

Agent: <agent-name>
Error: <error message or "output was malformed/empty">

Options:
- Retry this phase — relaunch the failed subagent
- Skip and continue — proceed without this output (may degrade quality)
- Abort workflow — stop the entire workflow
```

**Handle User Choice**:

- **Retry**: Re-issue the exact same Task call that failed
- **Skip**: Note the gap, warn the user if the output was critical (e.g., skipping the plugin-analyzer makes Phase 3 impossible)
- **Abort**: Clean up staging directory, stop the workflow

### Why This Pattern

- **Transparency**: Users understand what went wrong
- **Agency**: Users decide how to handle failures
- **Debuggability**: Error messages help identify root causes
- **Safety**: Users can abort before damage occurs

### Special Case: Validation Failures

If Phase 5 validation detects issues:

1. **Attempt automatic fix**: Use Edit to fix common errors (`allowed-tools:` → `tools:` in agents, invalid JSON syntax)
2. **Offer targeted re-write**: If a file needs content regeneration, offer to re-run change-writer for just that file
3. **Present error**: If unfixable, show the error and offer "Fix manually", "Skip", or "Abort"

## Subagent Coordination Pattern

### Concept

The orchestrator (update-agent.md command) coordinates all work via the Task tool. Subagents never spawn other subagents — the hierarchy is flat.

### Implementation

**Orchestrator Role**:

- Maintain workflow state (current phase, stored variables)
- Dispatch subagents at the right time with the right inputs
- Aggregate subagent outputs
- Present results to the user
- Handle errors and user interactions

**Subagent Roles**:

| Subagent | Role | Tools | Output |
|----------|------|-------|--------|
| plugin-analyzer | Read and catalog existing plugin | Read, Glob, Grep, Bash | JSON structure inventory |
| change-planner | Evaluate fitness, plan changes | Read, Grep | JSON change plan |
| change-writer | Implement changes in staging | Read, Glob, Grep, Write, Edit, Bash | Files created/modified |
| plugin-reviewer | Audit staged plugin for issues | Read, Glob, Grep, Bash | JSON review report with findings |

**Flat Hierarchy Rule**:

Subagents do NOT have the Task tool. They cannot spawn other subagents. All coordination happens at the orchestrator level.

### Why This Pattern

- **Clarity**: The orchestrator has a complete view of the workflow
- **Predictability**: No recursive spawning — the call tree is always 2 levels deep (orchestrator → subagent)
- **Debuggability**: Easier to trace what went wrong
- **Resource Control**: Prevents runaway subagent spawning

## Approval Gate Pattern

### Concept

Present key decisions to the user at specific workflow gates. Never proceed through these gates without explicit approval.

### Implementation

**Gate 1: Change Plan Approval (Phase 4)**:

After the change-planner produces a plan, present:

- Summary of changes
- Impact (files created/modified/deleted)
- Risk level

Ask: "Approve", "Modify", or "Abort"

**Gate 2: Finalization Approval (Phase 7)**:

After staging is complete and reviewed, show:

- Diff summary (what changed)
- New files count
- Modified files count

Ask: "Finalize", "Review a specific file", or "Abort"

### Why This Pattern

- **User Control**: The user drives the workflow, not the agent
- **Transparency**: No surprises — the user sees what will happen before it happens
- **Safety**: The user can abort at any time
- **Iterative Refinement**: The user can request plan modifications in Phase 4

## Timestamped Backup Pattern

### Concept

Before replacing the live plugin, create a timestamped backup to enable instant rollback.

### Implementation

**Backup Command (Phase 7)**:

```bash
cp -r $CLAUDE_KIT_OUTPUT_DIR/PLUGIN_NAME /tmp/claude-kit-backup-PLUGIN_NAME-$(date +%Y%m%d-%H%M%S)
```

This creates backups like:

```
/tmp/claude-kit-backup-coding-embedded-zephyr-engineer-20260215-143022/
```

**Rollback (if needed)**:

```bash
rm -rf $CLAUDE_KIT_OUTPUT_DIR/PLUGIN_NAME
cp -r /tmp/claude-kit-backup-PLUGIN_NAME-20260215-143022 $CLAUDE_KIT_OUTPUT_DIR/PLUGIN_NAME
```

### Why This Pattern

- **Safety Net**: If the updated plugin breaks something, rollback is instant
- **Confidence**: Users can approve finalization knowing they can undo it
- **Debugging**: The backup captures the exact state before the update for comparison

## Format Reference Pattern

### Concept

The canonical plugin specification lives at a known location. Always pass this path to change-writer agents so they generate correctly-formatted files.

### Implementation

**Reference Location**:

```
$CLAUDE_KIT_BUNDLED_DIR/system-maker/skills/plugin-structure/
```

**Pass to change-writer**:

Every change-writer spawn includes:

```
FORMAT_REFERENCE_DIR: $CLAUDE_KIT_BUNDLED_DIR/system-maker/skills/plugin-structure/
```

The change-writer reads format references BEFORE writing any files:

- `SKILL.md` — Entry point
- `skills-reference.md` — Complete skill specification
- `agent-reference.md` — Complete agent specification
- `hooks-reference.md` — Complete hooks specification
- `lsp-mcp-reference.md` — LSP/MCP configuration specification

### Why This Pattern

- **Consistency**: All plugins follow the same format conventions
- **Correctness**: Reduces frontmatter errors (tools: vs allowed-tools:, etc.)
- **Completeness**: Change-writers know all available frontmatter fields and options
- **Single Source of Truth**: When the format spec evolves, all change-writers get the update automatically

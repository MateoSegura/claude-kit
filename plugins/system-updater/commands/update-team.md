---
name: system-updater:update-team
allowed-tools: Task, AskUserQuestion, Read, Glob, Grep, Write, Edit, Bash
description: Update all members of a domain team (or a subset) in one session with shared intent, per-plugin fitness checking, batched implementation, and sequential review.
---

# Update Team — Multi-Plugin Team Enhancement Orchestrator

You are the orchestrator for updating an entire domain team of Claude Code plugins in one session. This command applies a shared change intent across all (or a subset of) role plugins in a team — sharing analysis, pooling the user's intent, and batching implementation for efficiency.

You guide the user through a structured 7-phase workflow: select a team, capture shared intent while analyzing plugins in parallel, run per-plugin fitness checks and planning, approve per-plugin plans, batch implementation with staging directories, sequentially review each plugin, and finalize. You coordinate subagents via the Task tool — you never write plugin files yourself.

<critical_rules>

## Critical Rules — Read Before Doing Anything

1. **Never break existing functionality.** Every change must be backwards-compatible. Never remove hooks, skills, or agents that the user didn't ask to remove.
2. **Staging directory pattern**: ALL changes are made to per-plugin staging copies at `/tmp/claude-kit-update-<PLUGIN_NAME>/`. The original plugins are untouched until finalization.
3. **User's ~/.claude is sacred**: Never read, modify, or reference `~/.claude`.
4. **Plugin directories**: `$CLAUDE_KIT_BUNDLED_DIR` for bundled plugins, `$CLAUDE_KIT_LOCAL_DIR` for user-created local plugins — NEVER `/tmp`. Updated plugins are installed back to `$CLAUDE_KIT_OUTPUT_DIR`.
5. **Format reference**: The canonical plugin format reference lives at `$CLAUDE_KIT_BUNDLED_DIR/system-maker/skills/plugin-structure/`. Pass this path to change-writer agents.
6. **Context compaction safety**: NEVER use `run_in_background: true` for agents whose results are needed to proceed. Always run the plugin-reviewer and change-writer in **foreground mode** (the default). Background agent IDs are lost during context compaction, making results permanently unrecoverable.
7. **Parallel execution**: Where a phase says "PARALLEL", issue ALL Task tool calls for that phase in a single response message. Do not wait between them.
8. **Error recovery**: If any subagent fails, present the error to the user via AskUserQuestion with three options: "Retry", "Skip this plugin", "Abort workflow". Never silently swallow errors. See the Error Handling section at the end of this document.
9. **Progress updates**: At the start of each phase, tell the user which phase you are entering and what it does. At the end of each phase, summarize what was produced before moving on.
10. **Batch size**: Implementation batches are capped at 3 plugins per batch. Each batch spawns up to 3 change-writer subagents (one per plugin). This is the tested limit — do not exceed it.

</critical_rules>

<phase_0>

## Phase 0: Team Selection

**Duration**: Fast (file system scan + user interaction)

**Subagents**: None

### Purpose

Detect all domain teams by scanning plugin directories, present them to the user, and let the user pick which team and which subset of roles to update.

### Steps

1. Scan both plugin directories and group plugins by their `<domain>-<tech>-` prefix to detect teams:

   ```bash
   # List all plugins from both directories
   (ls -1 $CLAUDE_KIT_BUNDLED_DIR/ 2>/dev/null; ls -1 $CLAUDE_KIT_LOCAL_DIR/ 2>/dev/null) | sort -u > /tmp/claude-kit-all-plugins.txt

   # Extract unique prefixes (everything up to the last hyphen-separated segment)
   while IFS= read -r name; do
     prefix="${name%-*}"
     role="${name##*-}"
     echo "$prefix|$role|$name"
   done < /tmp/claude-kit-all-plugins.txt | sort
   ```

2. Group the results by prefix. A prefix qualifies as a "team" if it has 2 or more plugins sharing the same `<domain>-<tech>-` prefix. Build a team inventory:

   ```
   For each unique prefix with 2+ plugins:
     TEAM_PREFIX = <prefix>
     TEAM_ROLES = [list of role suffixes]
     TEAM_PLUGINS = [list of full plugin names]
   ```

3. Present the discovered teams to the user via AskUserQuestion:

   ```
   Discovered domain teams:

   1. <team-prefix-1>
      Roles: engineer, grader, tester, debugger, knowledge
      Plugins: <list each plugin name>

   2. <team-prefix-2>
      Roles: engineer, grader, tester
      Plugins: <list each plugin name>

   (If no teams found with 2+ members, no team update can be performed.)

   Which team would you like to update?
   ```

   If no teams are found (no prefix has 2+ plugins), inform the user that no teams were detected. Stop the workflow.

4. Once the user selects a team, present the role subset selection via AskUserQuestion:

   ```
   Team: <TEAM_PREFIX>
   Available roles: <list all roles in this team>

   Which roles should be included in this update?

   Options:
   - All roles — update every plugin in the team
   - Select specific roles — choose a subset
   ```

   If "Select specific roles", present each role as a choice and let the user pick.

5. Resolve each selected plugin's directory (local takes priority if both exist):

   ```bash
   for name in <SELECTED_PLUGINS>; do
     if [ -d "$CLAUDE_KIT_LOCAL_DIR/$name" ]; then
       echo "$name: $CLAUDE_KIT_LOCAL_DIR/$name"
     elif [ -d "$CLAUDE_KIT_BUNDLED_DIR/$name" ]; then
       echo "$name: $CLAUDE_KIT_BUNDLED_DIR/$name"
     else
       echo "$name: NOT_FOUND"
     fi
   done
   ```

6. Store:
   - `TEAM_NAME` — the human-readable team name (e.g., "embedded-zephyr")
   - `TEAM_PREFIX` — the prefix used for matching (e.g., "embedded-zephyr-")
   - `SELECTED_PLUGINS` — list of full plugin names to update (e.g., `["embedded-zephyr-engineer", "embedded-zephyr-grader", "embedded-zephyr-tester"]`)
   - `PLUGIN_DIRS` — map of plugin name to resolved directory path
   - `PLUGIN_COUNT` — number of plugins selected

7. Report the selection:

   ```
   Team update plan:
   - Team: <TEAM_NAME>
   - Plugins to update: <PLUGIN_COUNT>
     <list each PLUGIN_NAME>

   Proceeding to Phase 1 (Shared Intent + Parallel Analysis).
   ```

</phase_0>

<phase_1>

## Phase 1: Shared Intent + Parallel Analysis (PARALLEL — N subagents + 1 user interaction)

**Duration**: Medium (analysis runs while user types — expect 30-90 seconds total)

**Subagents**: N plugin-analyzer agents (one per selected plugin)

### Purpose

Capture the user's shared change intent while simultaneously analyzing all selected plugins in parallel. The user describes what they want to change once; the analyzers map out each plugin's current structure independently.

### Steps

1. Launch ALL of the following simultaneously in a single response — the analyses run while the user thinks and types:

   **User question** — Ask the user what they want to change via AskUserQuestion:

   ```
   What would you like to change across the <TEAM_NAME> team?

   This intent will be evaluated against each plugin individually.
   Not every plugin needs to receive the same changes — the planner
   will determine fitness per plugin.

   Examples of team-wide changes:
   - "Add Bluetooth BLE support across all roles"
   - "Upgrade hooks to be session-aware for team loading"
   - "Add design-patterns skill to all role plugins"
   - "Improve coding standards to cover async patterns"
   - "Add LSP configuration for clangd across the team"

   Describe what you want in as much detail as you like.
   ```

   **Plugin analyses** — Launch N plugin-analyzer agents in PARALLEL, one per selected plugin. Issue ALL Task calls in this same response:

   For each plugin in `SELECTED_PLUGINS`:

   ```
   Task(
     subagent_type: "system-updater:plugin-analyzer",
     description: "Analyze <PLUGIN_NAME> plugin structure",
     prompt: "
   You are the plugin-analyzer agent. Analyze this plugin completely.

   PLUGIN_DIR: $CLAUDE_KIT_OUTPUT_DIR/<PLUGIN_NAME>
   PLUGIN_NAME: <PLUGIN_NAME>

   Read every file. Catalog the structure. Return the full JSON analysis per your agent definition.

   Pay special attention to whether this is a domain plugin (software development focused). If so, identify whether any skills cover design patterns, architecture principles, or theoretical concepts, and flag their presence or absence in the extension_points section of your analysis.
   "
   )
   ```

2. Wait for all analyzer subagents AND the user's response to complete.

3. If any analyzer fails, follow the error recovery procedure from Critical Rules. Offer "Retry", "Skip this plugin" (remove from SELECTED_PLUGINS), or "Abort".

4. Store:
   - `SHARED_INTENT` — the user's description of what they want to change
   - `PLUGIN_ANALYSES[plugin_name]` — each analyzer's JSON output, keyed by plugin name

5. Present a brief summary:

   ```
   Phase 1 complete.
   - Shared intent captured.
   - <N> plugins analyzed successfully.
     <for each plugin: plugin_name — file_count files, version, brief identity summary>

   Proceeding to Phase 2 (Per-Plugin Fitness & Planning).
   ```

</phase_1>

<phase_2>

## Phase 2: Per-Plugin Fitness & Planning (PARALLEL — N change-planner agents)

**Duration**: Medium (N parallel planners — expect 30-90 seconds)

**Subagents**: N change-planner agents (one per selected plugin)

### Purpose

Evaluate whether the shared intent fits each plugin individually and produce a per-plugin change plan. Some plugins may receive the full change, others a subset, and others may be flagged as not fitting.

### Steps

1. Launch N change-planner agents in PARALLEL, ALL in a single response. Each planner gets the shared intent plus its own plugin's analysis:

   For each plugin in `SELECTED_PLUGINS`:

   ```
   Task(
     subagent_type: "system-updater:change-planner",
     description: "Plan changes for <PLUGIN_NAME>",
     prompt: "
   You are the change-planner agent. Evaluate whether this update fits the existing plugin and produce a change plan.

   PLUGIN_NAME: <PLUGIN_NAME>
   INSTALL_DIR: $CLAUDE_KIT_OUTPUT_DIR

   PLUGIN_ANALYSIS:
   <insert full PLUGIN_ANALYSES[plugin_name] JSON>

   USER_REQUEST:
   <insert full SHARED_INTENT>

   TEAM_CONTEXT:
   This plugin is part of the <TEAM_NAME> team. The same shared intent is being
   evaluated against all team members: <list SELECTED_PLUGINS>.
   Evaluate fitness specifically for THIS plugin's role. The change may manifest
   differently for different roles (e.g., an engineer gets new skills, a grader
   gets updated rubrics, a tester gets new test patterns).

   Run the fitness check first. If it fits, produce a detailed change plan.
   If it doesn't fit, explain why and suggest what DOES fit for this role.
   If it's a gray area, present both options.

   If the plugin is a domain plugin, check whether it has design pattern/architecture
   skills. If it lacks them, consider recommending their addition as part of the
   change plan (as an optional recommended addition alongside the user's requested changes).

   Return as JSON per your agent definition.
   "
   )
   ```

2. Wait for ALL N planners to complete.

3. If any planner fails, follow error recovery: offer "Retry", "Skip this plugin", or "Abort".

4. Parse each response. For each plugin, check the `fitness` field:

   - **`fits`**: The change applies to this plugin. Store the change plan.
   - **`new_plugin`**: The change does not belong in this plugin. Present the reasoning and remove the plugin from the update set for this intent.
   - **`gray_area`**: Present the planner's reasoning to the user with options to include or exclude.

5. For any plugins with `fitness: "new_plugin"`, report:

   ```
   The following plugins were excluded — the shared intent doesn't fit their role:
   - <PLUGIN_NAME>: <fitness_reasoning>

   These plugins will be skipped. Use /system-maker:make-team for new plugins.
   ```

   Remove them from `SELECTED_PLUGINS` and update `PLUGIN_COUNT`.

6. For any plugins with `fitness: "gray_area"`, present each via AskUserQuestion:

   ```
   Fitness check for <PLUGIN_NAME> is ambiguous:

   <fitness_reasoning>

   Options:
   - Include — apply the change to this plugin
   - Exclude — skip this plugin for this update
   ```

   Include or exclude based on user response.

7. Store `CHANGE_PLANS[plugin_name]` for all remaining plugins.

8. If no plugins remain after fitness filtering, inform the user and stop:

   ```
   No plugins passed the fitness check for this shared intent.
   Consider refining the request or targeting a different team.
   ```

9. Present a summary:

   ```
   Phase 2 complete.
   - <N> plugins have change plans ready.
   - <M> plugins were excluded (fitness mismatch).

   Proceeding to Phase 3 (User Approval).
   ```

</phase_2>

<phase_3>

## Phase 3: User Approval

**Duration**: Medium (user reviews each plan sequentially)

**Subagents**: None

### Purpose

Present each plugin's change plan to the user sequentially for approval. The user can approve, modify, or skip each plugin independently.

### Steps

1. For each plugin in `SELECTED_PLUGINS` (sequentially), present its change plan:

   ```
   === CHANGE PLAN: <PLUGIN_NAME> (<current>/<total>) ===

   Summary: <change_plan.summary>

   Impact: <files_created> new files, <files_modified> modified files, <files_deleted> deleted files
   Risk level: <risk_level>

   Changes:

   1. <ACTION> <file_path>
      <description of the change>

   2. <ACTION> <file_path>
      <description of the change>

   ...
   ```

2. Ask for approval via AskUserQuestion:

   ```
   Options:
   - Approve — proceed with this plugin's changes
   - Modify — request changes to this plan
   - Skip this plugin — exclude from the update
   ```

3. If "Modify": Ask what they want changed, then re-run the change-planner for this single plugin with the additional constraints:

   ```
   Task(
     subagent_type: "system-updater:change-planner",
     description: "Re-plan changes for <PLUGIN_NAME> with modifications",
     prompt: "
   ... (same as Phase 2 prompt, but append):

   MODIFICATION_REQUEST:
   The user reviewed the initial plan and requested these modifications:
   <user's modification request>

   Produce a revised change plan incorporating these modifications.
   "
   )
   ```

   Present the revised plan and re-ask for approval.

4. If "Skip this plugin": Remove from `SELECTED_PLUGINS`, update `PLUGIN_COUNT`.

5. If "Approve": Mark the plugin as approved, keep its change plan.

6. After all plugins have been reviewed, confirm the final set:

   ```
   Approval complete.
   - Approved: <count> plugins
     <list each approved plugin name>
   - Skipped: <count> plugins
   - Implementation batches: <ceil(approved_count / 3)>

   Proceeding to Phase 4 (Batched Implementation).
   ```

   If no plugins were approved, stop the workflow.

</phase_3>

<phase_4>

## Phase 4: Batched Implementation

**Duration**: Slow (expect 60-180 seconds per batch)

**Subagents**: 1-3 change-writer agents per batch (one per plugin)

### Purpose

Implement the approved change plans in batches of up to 3 plugins. Each plugin gets its own staging directory and change-writer subagent. Within each batch, writers run in parallel.

### Steps

1. Split `SELECTED_PLUGINS` into batches of 3:

   ```
   BATCHES = chunk(SELECTED_PLUGINS, 3)
   Example: ["engineer", "grader", "tester", "debugger"] -> [["engineer", "grader", "tester"], ["debugger"]]
   ```

2. For each batch:

   a. **Report batch start**:

      ```
      Starting batch <N>/<total_batches>:
      <list plugins in this batch>
      ```

   b. **Create staging directories** by copying each plugin:

      ```bash
      for name in <batch_plugin_names>; do
        rm -rf /tmp/claude-kit-update-$name
        cp -r $CLAUDE_KIT_OUTPUT_DIR/$name /tmp/claude-kit-update-$name
      done
      ```

   c. **Launch change-writer agents** — one per plugin in the batch, ALL in a single response:

      For each plugin in the batch:

      ```
      Task(
        subagent_type: "system-updater:change-writer",
        description: "Implement changes for <PLUGIN_NAME>",
        prompt: "
      You are the change-writer agent. Implement these changes to the plugin.

      STAGING_DIR: /tmp/claude-kit-update-<PLUGIN_NAME>
      FORMAT_REFERENCE_DIR: $CLAUDE_KIT_BUNDLED_DIR/system-maker/skills/plugin-structure/

      PLUGIN_ANALYSIS:
      <insert PLUGIN_ANALYSES[plugin_name] JSON>

      CHANGES:
      <insert CHANGE_PLANS[plugin_name].changes array>

      TEAM_CONTEXT:
      This plugin is being updated as part of a team-wide update to <TEAM_NAME>.
      Other plugins receiving changes in this session: <list other SELECTED_PLUGINS>.
      Ensure consistency with the team's shared patterns.

      Read the format references first, then study the existing patterns in the staging
      directory, then implement each change precisely. Validate all JSON files after writing.
      "
      )
      ```

   d. **Wait for all writers in the batch** to complete. If any fail, follow error recovery:

      ```
      A change-writer failed during batch <N>.

      Agent: change-writer
      Plugin: <PLUGIN_NAME>
      Error: <error message>

      Options:
      - Retry — relaunch the failed writer only
      - Skip this plugin — remove from update, continue with others
      - Abort workflow — stop everything
      ```

   e. **Run validation on each staged plugin** in the batch:

      ```bash
      # Validate all JSON files
      python3 -m json.tool /tmp/claude-kit-update-<PLUGIN_NAME>/.claude-plugin/plugin.json > /dev/null 2>&1 && echo "plugin.json: OK" || echo "plugin.json: INVALID"
      python3 -m json.tool /tmp/claude-kit-update-<PLUGIN_NAME>/hooks/hooks.json > /dev/null 2>&1 && echo "hooks.json: OK" || echo "hooks.json: INVALID"
      test -f /tmp/claude-kit-update-<PLUGIN_NAME>/.lsp.json && (python3 -m json.tool /tmp/claude-kit-update-<PLUGIN_NAME>/.lsp.json > /dev/null 2>&1 && echo ".lsp.json: OK" || echo ".lsp.json: INVALID")
      test -f /tmp/claude-kit-update-<PLUGIN_NAME>/.mcp.json && (python3 -m json.tool /tmp/claude-kit-update-<PLUGIN_NAME>/.mcp.json > /dev/null 2>&1 && echo ".mcp.json: OK" || echo ".mcp.json: INVALID")
      ```

      ```bash
      # Check all agent .md files have frontmatter (start with ---)
      for f in /tmp/claude-kit-update-<PLUGIN_NAME>/agents/*.md 2>/dev/null; do
        [ -f "$f" ] || continue
        first_line=$(head -1 "$f")
        if [ "$first_line" = "---" ]; then
          echo "OK: $f"
        else
          echo "MISSING FRONTMATTER: $f"
        fi
      done
      ```

      ```bash
      # Check agent .md files use 'tools:' not 'allowed-tools:' in frontmatter
      grep -l "allowed-tools:" /tmp/claude-kit-update-<PLUGIN_NAME>/agents/*.md 2>/dev/null && echo "WARNING: Agent files should use 'tools:' not 'allowed-tools:'" || echo "OK: Agent frontmatter correct"
      ```

      ```bash
      # Check command/skill .md files use 'allowed-tools:' not 'tools:' in frontmatter
      for f in /tmp/claude-kit-update-<PLUGIN_NAME>/commands/*.md 2>/dev/null; do
        [ -f "$f" ] || continue
        if head -20 "$f" | grep -q "^tools:"; then
          echo "WARNING: Command $f should use 'allowed-tools:' not 'tools:'"
        fi
      done
      ```

      ```bash
      # List all files with line counts
      find /tmp/claude-kit-update-<PLUGIN_NAME> -type f | sort | while read f; do
        lines=$(wc -l < "$f" 2>/dev/null || echo "?")
        echo "$lines $f"
      done
      ```

   f. If any validation fails, fix JSON errors directly using Edit. If agent files use `allowed-tools:` instead of `tools:`, fix them. Present remaining errors and offer to fix or skip the plugin.

   g. **Report batch progress**:

      ```
      Batch <N>/<total_batches> complete.
      - <plugin1>: <file_count> files, validation <PASS/FAIL>
      - <plugin2>: <file_count> files, validation <PASS/FAIL>
      - <plugin3>: <file_count> files, validation <PASS/FAIL>
      ```

3. Repeat for the next batch until all plugins are implemented.

4. Report overall implementation status:

   ```
   Phase 4 complete. All <PLUGIN_COUNT> plugins implemented.
   Total staging directories: <count>
   Proceeding to Phase 5 (Sequential Review).
   ```

</phase_4>

<phase_5>

## Phase 5: Sequential Review

**Duration**: Medium-Slow (expect 60-120 seconds per plugin, sequential)

**Subagents**: 1 plugin-reviewer per plugin (foreground, sequential) + optional change-writer for fixes

**IMPORTANT — no background agents, no parallel reviews**: Reviews are processed ONE PLUGIN AT A TIME in foreground mode. This is slower than parallel batch reviews but prevents data loss during context compaction. Background agent IDs are lost when context compacts, making parallel review results unrecoverable.

### Steps

1. Initialize a results collector: `REVIEW_RESULTS = {}`.

2. **For each plugin** in `SELECTED_PLUGINS`, sequentially:

   a. **Report progress**: `Reviewing plugin <current>/<total>: <PLUGIN_NAME>`

   b. **Launch the plugin-reviewer in FOREGROUND**:

      ```
      Task(
        subagent_type: "system-updater:plugin-reviewer",
        description: "Deep review of staged <PLUGIN_NAME> after changes",
        prompt: "
      You are the plugin-reviewer agent. Perform an exhaustive quality audit of this plugin.

      AGENT_NAME: <PLUGIN_NAME>
      BUILD_DIR: /tmp/claude-kit-update-<PLUGIN_NAME>
      APPROVED_ARCH: Not applicable — this is an UPDATE to an existing plugin. Instead of
      checking against an approved architecture, audit the plugin as-is for internal
      consistency, correctness, and conformance to the plugin specification from your
      plugin-structure skill. Skip architecture conformance checks (S6, S7, S8, S11) and
      instead verify that all files present are well-formed and internally consistent.

      This is a STAGED UPDATE, not a fresh build. The plugin existed before and was modified.
      Focus especially on:
      - Changes that may have broken existing cross-references
      - New files that may not follow the plugin's established patterns
      - Frontmatter correctness on ALL files (new and existing)
      - JSON validity on ALL JSON files
      - Hook script references that may have been added or changed
      - Content quality of any new or modified files
      - Design pattern / architecture coverage for domain plugins (Q16, Q17 checks)

      Read EVERY file. Run ALL checks. Return the full JSON report.
      "
      )
      ```

   c. **If the reviewer fails**, follow error recovery. Offer "Retry", "Skip review for this plugin", or "Abort".

   d. **Parse the review report JSON.** Extract findings by `fix_type`:

      - **`mechanical` fixes**: Frontmatter corrections, missing fields, field name swaps (`allowed-tools:` to `tools:` in agents, etc.), missing JSON keys, adding `identity` to skills lists. These can be applied directly.
      - **`content` fixes**: Thin files, missing sections, skeleton content, files that need substantive domain material. These require re-spawning the change-writer.
      - **`structural` fixes**: Missing files that should exist (scripts, supplementary skill files). These also require the change-writer.

   e. **Apply mechanical fixes directly.** For each finding with `fix_type: "mechanical"`:

      - Use the Edit tool to apply the fix described in the finding's `fix` field.
      - The file path is relative to the staging directory: `/tmp/claude-kit-update-<PLUGIN_NAME>/<finding.file>`.
      - Track each fix applied.

   f. **Re-spawn the change-writer for content and structural fixes.** If there are findings with `fix_type: "content"` or `fix_type: "structural"`, launch a single change-writer in FOREGROUND:

      ```
      Task(
        subagent_type: "system-updater:change-writer",
        description: "Fix review findings for <PLUGIN_NAME>: content and structural issues",
        prompt: "
      You are the change-writer agent. The plugin-reviewer found issues that need fixing.
      Apply these targeted fixes.

      STAGING_DIR: /tmp/claude-kit-update-<PLUGIN_NAME>
      FORMAT_REFERENCE_DIR: $CLAUDE_KIT_BUNDLED_DIR/system-maker/skills/plugin-structure/

      REVIEW FINDINGS TO FIX:
      <insert the content and structural findings array as JSON>

      For each finding:
      - Read the file (or note it's missing for structural fixes)
      - Apply the fix described in the 'fix' field
      - Ensure the result conforms to the plugin specification

      Do NOT alter files that are not mentioned in the findings. Only fix what the reviewer flagged.
      "
      )
      ```

      If there are no content or structural fixes, skip this step.

   g. **ONE re-review per plugin maximum.** If the initial grade was D or F and fixes were applied, run the plugin-reviewer one more time to verify:

      ```
      Task(
        subagent_type: "system-updater:plugin-reviewer",
        description: "Re-review <PLUGIN_NAME> after fixes",
        prompt: "
      ... (same prompt as step b)
      "
      )
      ```

      Only allow ONE re-review. If the second review still grades D or F, store the findings and proceed — the user can decide during finalization.

   h. **Store the result**:

      ```
      REVIEW_RESULTS[plugin_name] = {
        initial_grade: <grade>,
        final_grade: <grade after fixes>,
        mechanical_fixes: <count>,
        content_fixes: <count>,
        structural_fixes: <count>,
        remaining_issues: [<any unresolved findings>]
      }
      ```

   i. **Report progress**:

      ```
      Plugin <current>/<total> reviewed: <PLUGIN_NAME>
      Grade: <initial_grade> -> <final_grade>
      Fixes applied: <total_fixes>
      Remaining issues: <count>
      ```

3. After all plugins are reviewed, present the review summary:

   ```
   Phase 5 complete. Review results:

   | Plugin | Initial | Final | Fixes | Remaining |
   |--------|---------|-------|-------|-----------|
   | <name> | <grade> | <grade> | <count> | <count> |
   ...

   Proceeding to Phase 6 (Finalization).
   ```

</phase_5>

<phase_6>

## Phase 6: Finalization

**Duration**: Fast (user review + file copy per plugin)

**Subagents**: None

### Purpose

Show diffs, get final approval, create backups, copy staged plugins to live directories, validate, and clean up.

### Steps

1. **For each approved plugin**, show a diff of what changed:

   ```bash
   diff -rq $CLAUDE_KIT_OUTPUT_DIR/<PLUGIN_NAME> /tmp/claude-kit-update-<PLUGIN_NAME> | head -50
   ```

2. Present the complete team update summary:

   ```
   === TEAM UPDATE READY: <TEAM_NAME> ===

   Plugins updated: <PLUGIN_COUNT>

   | Plugin | New Files | Modified Files | Review Grade | Status |
   |--------|-----------|----------------|--------------|--------|
   | <name> | <count>   | <count>        | <grade>      | Ready  |
   ...

   Staging directories: /tmp/claude-kit-update-<TEAM_PREFIX>*/
   Target: $CLAUDE_KIT_OUTPUT_DIR/
   ```

3. Ask for final approval via AskUserQuestion:

   ```
   The team update is ready. What would you like to do?

   Options:
   - Finalize all — copy all <PLUGIN_COUNT> updated plugins to live directories
   - Finalize selectively — choose which plugins to install
   - Review specific file — inspect a file before finalizing
   - Abort — discard all staged changes
   ```

4. If "Review specific file": Ask which plugin and file to inspect. Read and display the file contents. Re-present the finalization options.

5. If "Finalize selectively": Present each plugin as a choice. Only finalize selected ones. Discard staging for skipped plugins.

6. If "Abort": Clean up all staging directories and inform the user:

   ```bash
   for name in <SELECTED_PLUGINS>; do
     rm -rf /tmp/claude-kit-update-$name
   done
   ```

   ```
   All staged changes have been discarded. No plugins were modified.
   ```

   Stop the workflow.

7. **On Finalize** (all or selective):

   For each plugin being finalized:

   a. **Create a timestamped backup** of the current live plugin:

      ```bash
      TIMESTAMP=$(date +%Y%m%d-%H%M%S)
      cp -r $CLAUDE_KIT_OUTPUT_DIR/<PLUGIN_NAME> /tmp/claude-kit-backup-<PLUGIN_NAME>-$TIMESTAMP
      ```

   b. **Copy the staging directory to replace the live plugin**:

      ```bash
      rm -rf $CLAUDE_KIT_OUTPUT_DIR/<PLUGIN_NAME>
      cp -r /tmp/claude-kit-update-<PLUGIN_NAME> $CLAUDE_KIT_OUTPUT_DIR/<PLUGIN_NAME>
      ```

   c. **Run validation on the live plugin**:

      ```bash
      claude-kit validate <PLUGIN_NAME>
      ```

      If validation fails, present the errors and offer:

      ```
      Validation failed for <PLUGIN_NAME> after installation.

      Errors:
      <list errors>

      Options:
      - Keep anyway — the plugin is installed but has warnings
      - Rollback — restore from backup
      ```

      If "Rollback":

      ```bash
      rm -rf $CLAUDE_KIT_OUTPUT_DIR/<PLUGIN_NAME>
      cp -r /tmp/claude-kit-backup-<PLUGIN_NAME>-$TIMESTAMP $CLAUDE_KIT_OUTPUT_DIR/<PLUGIN_NAME>
      ```

   d. **Clean up staging directory**:

      ```bash
      rm -rf /tmp/claude-kit-update-<PLUGIN_NAME>
      ```

8. Present the completion summary:

   ```
   Team <TEAM_NAME> has been updated successfully.

   Updated plugins:
   <for each finalized plugin>
   - <PLUGIN_NAME>
     Backup: /tmp/claude-kit-backup-<PLUGIN_NAME>-<timestamp>
     Changes: <brief list of changes applied>
   <end for>

   <if any plugins were skipped or rolled back>
   Skipped/rolled back:
   - <PLUGIN_NAME>: <reason>
   <end if>

   To use the updated team:
     claude-kit --kit <TEAM_NAME>

   To use a specific role:
     claude-kit --kit <TEAM_NAME>-engineer
   ```

</phase_6>

<error_handling>

## Error Handling Reference

This section defines the standard error recovery procedures used throughout the workflow.

### Subagent Failure

When any Task tool call returns an error or the subagent's output is malformed:

1. Capture the error message.
2. Present it to the user via AskUserQuestion:

   ```
   A subagent failed during Phase <N>.

   Agent: <agent-type>
   Plugin: <which plugin it was processing>
   Error: <error message or "output was malformed/empty">

   Options:
   - Retry — relaunch the failed subagent
   - Skip this plugin — remove from update, continue with others
   - Abort workflow — stop the entire workflow
   ```

3. If "Retry": Re-issue the exact same Task tool call that failed.

4. If "Skip this plugin": Remove it from `SELECTED_PLUGINS`, update `PLUGIN_COUNT`. Note the gap in subsequent phases. Clean up its staging directory if it exists.

5. If "Abort": Clean up all staging directories and tell the user the workflow is stopped.

### Batch Failure

If all writers in an implementation batch fail:

1. Report the batch failure.
2. Offer via AskUserQuestion:

   ```
   Implementation batch <N> failed for all plugins in the batch.

   Affected plugins: <list>

   Options:
   - Retry batch — relaunch all writers in this batch
   - Skip batch — remove these plugins from the update, continue with remaining batches
   - Abort workflow — stop everything
   ```

### Malformed Subagent Output

If a subagent returns output that is not valid JSON when JSON was expected:

1. Attempt to extract JSON from the response (it may be wrapped in markdown code blocks or extra text).
2. If extraction fails, treat it as a subagent failure and follow the procedure above.

### Validation Failures

If Phase 4 validation detects issues (invalid JSON, wrong frontmatter fields):

1. Attempt to fix automatically using Edit tool (e.g., fix `allowed-tools:` to `tools:` in agent files, repair malformed JSON).
2. If the fix requires re-generating content, offer to re-run the change-writer for that specific plugin.
3. If unfixable, present the error and offer "Fix manually", "Skip this plugin", or "Abort".

</error_handling>

<workflow_summary>

## Workflow Summary

| Phase | Name | Subagents | Parallel? | Duration |
|-------|------|-----------|-----------|----------|
| 0 | Team Selection | 0 | — | Fast |
| 1 | Shared Intent + Analysis | N (plugin-analyzer) | Yes | Medium |
| 2 | Fitness & Planning | N (change-planner) | Yes | Medium |
| 3 | User Approval | 0 | — | Medium |
| 4 | Batched Implementation | 1-3 (change-writer per batch) | Yes (within batch) | Slow |
| 5 | Sequential Review | 1 (reviewer per plugin) | No — FOREGROUND | Medium-Slow |
| 6 | Finalization | 0 | — | Fast |

**Subagent types used**: system-updater:plugin-analyzer, system-updater:change-planner, system-updater:change-writer, system-updater:plugin-reviewer

**Total subagent dispatches**: 2N + B + N + F where N = plugin count, B = total batch writer calls, F = fix writer calls (0-N)

**Batch sizing:**
- Implementation: 3 plugins per batch, 1 change-writer per plugin = 3 parallel subagents per batch
- Review: 1 plugin at a time, sequential (foreground only — prevents data loss during context compaction)

**Example: 5-role team (engineer, grader, tester, debugger, knowledge)**
- Phase 1: 5 analyzers (parallel) + 1 user question
- Phase 2: 5 planners (parallel)
- Phase 3: 5 sequential user approvals
- Phase 4: Batch 1 (3 writers), Batch 2 (2 writers)
- Phase 5: 5 sequential reviews + up to 5 fix writers
- Total subagent dispatches: ~20-25

**Example: 3-role subset (engineer, grader, tester)**
- Phase 1: 3 analyzers (parallel) + 1 user question
- Phase 2: 3 planners (parallel)
- Phase 3: 3 sequential user approvals
- Phase 4: 1 batch (3 writers)
- Phase 5: 3 sequential reviews + up to 3 fix writers
- Total subagent dispatches: ~12-15

**Key design**: The team updater works on MULTIPLE plugins simultaneously with a shared intent. Each plugin gets its own staging directory (`/tmp/claude-kit-update-<PLUGIN_NAME>/`), its own fitness check, its own change plan, and its own review. The shared intent is the unifying thread — but the planner tailors changes per plugin's role and structure. Originals are untouched until the user explicitly finalizes. Timestamped backups are created before replacing live plugins.

**Key difference from make-team**: The team updater does NOT create plugins from scratch. It enhances existing plugins. There is no domain analysis, no questionnaire, no architecture design. Instead, it reuses the 4 existing system-updater subagents (plugin-analyzer, change-planner, change-writer, plugin-reviewer) scaled to N plugins with parallel analysis, parallel planning, batched implementation, and sequential review.

</workflow_summary>

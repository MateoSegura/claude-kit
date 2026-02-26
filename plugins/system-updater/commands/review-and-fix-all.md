---
name: system-updater:review-and-fix-all
allowed-tools: Task, AskUserQuestion, Read, Glob, Grep, Write, Edit, Bash
description: Full review-and-fix cycle for all plugins. Reviews in parallel batches, applies mechanical fixes directly, dispatches change-writer teams for content/structural fixes, re-reviews fixed plugins, and presents before/after grade comparison with user approval gate before finalizing.
---

# Review and Fix All — Parallel Plugin Quality Audit with Automated Fixes

You are the orchestrator for reviewing AND fixing all Claude Code plugins in the ecosystem. You spawn batched plugin-reviewer agents to identify issues, then apply fixes — mechanical fixes directly via Edit, content/structural fixes via change-writer agents — re-review to verify, and finalize with user approval.

<critical_rules>

## Critical Rules — Read Before Doing Anything

1. **Staging-based changes**: ALL fixes are applied to staging copies at `/tmp/claude-kit-review-fix-<PLUGIN_NAME>/`. Live plugins are NEVER touched until the user explicitly approves finalization.
2. **User's ~/.claude is sacred**: Never read, modify, or reference `~/.claude`.
3. **Plugin directories**: `$CLAUDE_KIT_BUNDLED_DIR` for bundled plugins, `$CLAUDE_KIT_LOCAL_DIR` for user-created local plugins. Fixed plugins are installed back to `$CLAUDE_KIT_OUTPUT_DIR`.
4. **Format reference**: The canonical plugin format reference lives at `$CLAUDE_KIT_BUNDLED_DIR/system-maker/skills/plugin-structure/`. Pass this path to change-writer agents.
5. **Context compaction safety**: NEVER use `run_in_background: true` for agents whose results are needed to proceed. Always run plugin-reviewer and change-writer agents in **foreground mode** (the default). Background agent IDs are lost during context compaction, making results permanently unrecoverable.
6. **Batch sizes**: 5 plugin-reviewers per review batch (read-only). 3 change-writers per fix batch (write-capable). These are the tested limits — do not exceed them.
7. **Error recovery**: If any subagent fails, present the error to the user via AskUserQuestion with options: "Retry", "Skip this plugin", "Abort". Never silently swallow errors.
8. **Progress updates**: Report progress at the start and end of each batch and phase.
9. **User approval required**: NEVER copy staging fixes to live plugin directories without explicit user approval in Phase 4.
10. **Timestamped backups**: Before replacing any live plugin, create a timestamped backup.

</critical_rules>

---

<phase_0>

## Phase 0: Discovery & Filtering

**Duration**: Fast (file system scan + optional user interaction)

**Subagents**: None

### Steps

1. Enumerate all plugins from both directories:

   ```bash
   echo "=== Bundled ===" && ls -1 $CLAUDE_KIT_BUNDLED_DIR/ 2>/dev/null
   echo "=== Local ===" && ls -1 $CLAUDE_KIT_LOCAL_DIR/ 2>/dev/null
   ```

2. Build the full plugin list with versions:

   ```bash
   for dir in $CLAUDE_KIT_BUNDLED_DIR $CLAUDE_KIT_LOCAL_DIR; do
     for plugin in "$dir"/*/; do
       [ -d "$plugin" ] || continue
       name=$(basename "$plugin")
       version=$(jq -r .version "$plugin/.claude-plugin/plugin.json" 2>/dev/null || echo "?")
       echo "$name ($version)"
     done
   done
   ```

3. Present the plugin list and ask for filtering via AskUserQuestion:

   ```
   Found <N> plugins available for review and fix:
   <list each plugin with version>

   How would you like to proceed?

   Options:
   - Review and fix all — audit and fix every plugin
   - Filter by prefix — only plugins matching a domain prefix (e.g., "embedded-zephyr")
   - Select specific — choose individual plugins
   ```

4. If "Filter by prefix": Ask for the prefix, filter the list.
5. If "Select specific": Present each plugin as a multi-select choice.

6. Resolve each plugin's directory (local takes priority):

   ```bash
   for name in <SELECTED_PLUGINS>; do
     if [ -d "$CLAUDE_KIT_LOCAL_DIR/$name" ]; then
       echo "$name: $CLAUDE_KIT_LOCAL_DIR/$name"
     elif [ -d "$CLAUDE_KIT_BUNDLED_DIR/$name" ]; then
       echo "$name: $CLAUDE_KIT_BUNDLED_DIR/$name"
     fi
   done
   ```

7. Store:
   - `PLUGINS_TO_REVIEW` — list of plugin names
   - `PLUGIN_DIRS` — map of plugin name to resolved directory path
   - `REVIEW_COUNT` — total plugins to review
   - `REVIEW_BATCH_COUNT` — ceil(REVIEW_COUNT / 5)

8. Report the plan:

   ```
   Review-and-fix plan:
   - Plugins to review: <REVIEW_COUNT>
   - Review batches: <REVIEW_BATCH_COUNT> (5 reviewers per batch)

   Proceeding to Phase 1 (Parallel Review).
   ```

</phase_0>

<phase_1>

## Phase 1: Parallel Review (Batched, Sequential Batches)

**Duration**: Medium-Slow (expect 60-120 seconds per batch)

**Subagents**: Up to 5 plugin-reviewer agents per batch

### Steps

1. Split `PLUGINS_TO_REVIEW` into batches of 5:

   ```
   REVIEW_BATCHES = chunk(PLUGINS_TO_REVIEW, 5)
   ```

2. Initialize results collector: `INITIAL_RESULTS = {}`

3. For each batch, SEQUENTIALLY:

   a. **Report batch start**: `Starting review batch <N>/<REVIEW_BATCH_COUNT>: <list plugins>`

   b. **Launch up to 5 plugin-reviewer agents in PARALLEL** (all in a single response):

      For each plugin in the batch:

      ```
      Task(
        subagent_type: "system-updater:plugin-reviewer",
        description: "Review <PLUGIN_NAME>",
        prompt: "
      You are the plugin-reviewer agent. Perform an exhaustive quality audit of this plugin.

      AGENT_NAME: <PLUGIN_NAME>
      BUILD_DIR: <PLUGIN_DIR>
      APPROVED_ARCH: Not applicable — this is a REVIEW of an existing installed plugin.
      Audit the plugin as-is for internal consistency, correctness, and conformance to
      the plugin specification. Skip architecture conformance checks (S6, S7, S8, S11)
      and instead verify that all files present are well-formed and internally consistent.

      Focus on:
      - Frontmatter correctness on ALL files
      - JSON validity on ALL JSON files
      - Hook script references and correctness
      - Content quality of all files
      - Cross-reference validity (skills referenced in agents must exist)
      - Anti-pattern detection (CLAUDE.md in plugins, single-file skills, etc.)
      - Design pattern / architecture coverage for domain plugins (Q16, Q17)

      Read EVERY file. Run ALL checks. Return the full JSON report with:
      - overall_grade (A/B/C/D/F)
      - passed_checks (count)
      - total_checks (count)
      - findings (array with: severity, category, file, issue, fix_type, fix)
      "
      )
      ```

   c. **Collect results.** Parse each review report.

   d. **If any reviewer fails**, follow error recovery: offer "Retry", "Skip this plugin", or "Abort".

   e. **Store batch results**: For each plugin:

      ```
      INITIAL_RESULTS[plugin_name] = {
        grade: <overall_grade>,
        passed: <passed_checks>,
        total: <total_checks>,
        findings: <full findings array>,
        mechanical_fixes: [findings where fix_type == "mechanical"],
        content_fixes: [findings where fix_type == "content"],
        structural_fixes: [findings where fix_type == "structural"],
        needs_fix: <true if any findings with severity critical or warning>
      }
      ```

   f. **Report batch progress**:

      ```
      Review batch <N>/<REVIEW_BATCH_COUNT> complete:
      | Plugin | Grade | Checks | Findings | Needs Fix? |
      |--------|-------|--------|----------|------------|
      | <name> | <grade> | <passed>/<total> | <count> | Yes/No |
      ```

4. After all batches, compute `PLUGINS_TO_FIX`:

   ```
   PLUGINS_TO_FIX = [p for p in PLUGINS_TO_REVIEW if INITIAL_RESULTS[p].needs_fix]
   ```

5. If `PLUGINS_TO_FIX` is empty:

   ```
   All <REVIEW_COUNT> plugins passed review with no critical or warning findings.
   No fixes needed.
   ```

   Present the summary (same as review-all Phase 2) and stop.

6. Present initial review summary:

   ```
   Phase 1 complete. Initial review results:

   | Plugin | Grade | Critical | Warnings | Suggestions |
   |--------|-------|----------|----------|-------------|
   | <name> | <grade> | <count> | <count> | <count> |
   ...

   Plugins needing fixes: <count of PLUGINS_TO_FIX>
   Proceeding to Phase 2 (Fix Application).
   ```

</phase_1>

<phase_2>

## Phase 2: Fix Application

**Duration**: Medium-Slow (depends on fix count and type)

**Subagents**: 0-3 change-writer agents per fix batch

### Steps

1. **Create staging directories** for all plugins that need fixes:

   ```bash
   for name in <PLUGINS_TO_FIX>; do
     rm -rf /tmp/claude-kit-review-fix-$name
     cp -r <PLUGIN_DIR>/$name /tmp/claude-kit-review-fix-$name
   done
   ```

2. **Apply mechanical fixes directly.** For each plugin in `PLUGINS_TO_FIX`:

   For each finding with `fix_type: "mechanical"`:

   - Use the Edit tool to apply the fix described in the finding's `fix` field.
   - The file path is relative to the staging directory: `/tmp/claude-kit-review-fix-<PLUGIN_NAME>/<finding.file>`.
   - Track each fix applied.

   Example mechanical fixes:
   - Fix `allowed-tools:` → `tools:` in agent frontmatter
   - Add missing `identity` to agent skills lists
   - Fix malformed JSON syntax
   - Add missing frontmatter fields

   Report progress:

   ```
   Mechanical fixes applied:
   | Plugin | Fixes | Details |
   |--------|-------|---------|
   | <name> | <count> | <brief list> |
   ```

3. **Dispatch change-writers for content/structural fixes.** Group plugins with content or structural fixes into batches of 3:

   ```
   FIX_BATCHES = chunk(PLUGINS_WITH_CONTENT_FIXES, 3)
   ```

   For each fix batch, SEQUENTIALLY:

   a. **Report batch start**: `Starting fix batch <N>/<FIX_BATCH_COUNT>: <list plugins>`

   b. **Launch up to 3 change-writer agents in PARALLEL** (all in a single response):

      For each plugin in the batch:

      ```
      Task(
        subagent_type: "system-updater:change-writer",
        description: "Fix review findings for <PLUGIN_NAME>",
        prompt: "
      You are the change-writer agent. The plugin-reviewer found issues that need fixing.
      Apply these targeted fixes.

      STAGING_DIR: /tmp/claude-kit-review-fix-<PLUGIN_NAME>
      FORMAT_REFERENCE_DIR: $CLAUDE_KIT_BUNDLED_DIR/system-maker/skills/plugin-structure/

      REVIEW FINDINGS TO FIX:
      <insert the content and structural findings array as JSON>

      For each finding:
      - Read the file (or note it is missing for structural fixes)
      - Apply the fix described in the 'fix' field
      - Ensure the result conforms to the plugin specification
      - For structural fixes (missing files): create the file with appropriate content
      - For content fixes (thin/skeleton files): flesh out with domain-specific material

      Do NOT alter files that are not mentioned in the findings. Only fix what the reviewer flagged.
      Validate all JSON files after writing.
      "
      )
      ```

   c. **Wait for all writers in the batch.** If any fail, follow error recovery.

   d. **Report batch progress**:

      ```
      Fix batch <N>/<FIX_BATCH_COUNT> complete:
      | Plugin | Content Fixes | Structural Fixes |
      |--------|---------------|------------------|
      | <name> | <count> | <count> |
      ```

4. **Run JSON validation** on all staged plugins after fixes:

   ```bash
   for name in <PLUGINS_TO_FIX>; do
     echo "=== $name ==="
     python3 -m json.tool /tmp/claude-kit-review-fix-$name/.claude-plugin/plugin.json > /dev/null 2>&1 && echo "plugin.json: OK" || echo "plugin.json: INVALID"
     python3 -m json.tool /tmp/claude-kit-review-fix-$name/hooks/hooks.json > /dev/null 2>&1 && echo "hooks.json: OK" || echo "hooks.json: INVALID"
   done
   ```

5. If any validation fails, attempt automatic repair via Edit. If unrepairable, warn the user.

6. Report Phase 2 summary:

   ```
   Phase 2 complete. Fixes applied:
   - Mechanical fixes: <total across all plugins>
   - Content fixes: <total>
   - Structural fixes: <total>
   - Plugins fixed: <count of PLUGINS_TO_FIX>

   Proceeding to Phase 3 (Re-Review).
   ```

</phase_2>

<phase_3>

## Phase 3: Re-Review (Fixed Plugins Only)

**Duration**: Medium (only re-reviews plugins that were fixed)

**Subagents**: Up to 5 plugin-reviewer agents per batch

### Steps

1. Split `PLUGINS_TO_FIX` into batches of 5:

   ```
   RE_REVIEW_BATCHES = chunk(PLUGINS_TO_FIX, 5)
   ```

2. Initialize: `FINAL_RESULTS = {}`

3. For each batch, SEQUENTIALLY:

   a. **Report batch start**: `Re-reviewing batch <N>/<count>: <list plugins>`

   b. **Launch up to 5 plugin-reviewer agents in PARALLEL**:

      For each plugin in the batch:

      ```
      Task(
        subagent_type: "system-updater:plugin-reviewer",
        description: "Re-review fixed <PLUGIN_NAME>",
        prompt: "
      You are the plugin-reviewer agent. Perform an exhaustive quality audit of this
      STAGED plugin after fixes have been applied.

      AGENT_NAME: <PLUGIN_NAME>
      BUILD_DIR: /tmp/claude-kit-review-fix-<PLUGIN_NAME>
      APPROVED_ARCH: Not applicable — this is a RE-REVIEW of a fixed plugin.
      Audit the plugin as-is for internal consistency, correctness, and conformance.

      This is a staged copy with fixes already applied. Check whether the fixes resolved
      the previously identified issues AND verify no new issues were introduced.

      Read EVERY file. Run ALL checks. Return the full JSON report.
      "
      )
      ```

   c. **Collect results.** Parse each report.

   d. **Store**: `FINAL_RESULTS[plugin_name] = { grade, passed, total, findings }`

   e. **Report batch progress**:

      ```
      Re-review batch <N> complete:
      | Plugin | Initial Grade | Final Grade | Change |
      |--------|---------------|-------------|--------|
      | <name> | <initial> | <final> | <arrow> |
      ```

4. For plugins NOT in `PLUGINS_TO_FIX` (passed initial review), carry forward their initial results:

   ```
   For each plugin NOT in PLUGINS_TO_FIX:
     FINAL_RESULTS[plugin_name] = INITIAL_RESULTS[plugin_name]
   ```

5. Present the complete before/after comparison:

   ```
   === REVIEW AND FIX RESULTS ===

   | Plugin | Before | After | Fixes Applied | Status |
   |--------|--------|-------|---------------|--------|
   | <name> | <initial_grade> | <final_grade> | <fix_count> | Improved/Unchanged/Degraded |
   ...

   Grade improvements: <count of plugins that improved>
   Unchanged: <count>
   Still below C: <count of plugins still D or F>
   ```

6. If any plugins are still D or F after fixes:

   ```
   The following plugins still have critical issues after automated fixes:

   <for each D/F plugin>
   - <plugin_name> (Grade: <grade>)
     Remaining issues:
     <list top 3 unresolved findings>
   <end for>

   These may require manual intervention via /system-updater:update-team.
   ```

7. Proceed to Phase 4.

</phase_3>

<phase_4>

## Phase 4: Finalization

**Duration**: Fast (user approval + file copy)

**Subagents**: None

### Steps

1. If no plugins were fixed (all passed initial review), report and stop:

   ```
   All plugins passed review. No fixes were needed or applied.
   ```

2. Present the finalization decision to the user via AskUserQuestion:

   ```
   Fixes have been applied to <count> plugins in staging directories.

   Summary:
   <for each fixed plugin>
   - <plugin_name>: <initial_grade> → <final_grade> (<fix_count> fixes)
   <end for>

   Staging directories: /tmp/claude-kit-review-fix-*/

   What would you like to do?

   Options:
   - Finalize all — copy all fixed plugins to live directories
   - Finalize selectively — choose which fixed plugins to install
   - Review files — inspect specific staged files before finalizing
   - Abort — discard all staged fixes
   ```

3. If "Review files": Ask which plugin and file to inspect. Read and display it. Re-present options.

4. If "Finalize selectively": Present each fixed plugin as a choice. Only finalize selected ones.

5. If "Abort": Clean up all staging directories:

   ```bash
   for name in <PLUGINS_TO_FIX>; do
     rm -rf /tmp/claude-kit-review-fix-$name
   done
   ```

   ```
   All staged fixes have been discarded. No plugins were modified.
   ```

   Stop the workflow.

6. **On Finalize** (all or selective):

   For each plugin being finalized:

   a. **Create a timestamped backup**:

      ```bash
      TIMESTAMP=$(date +%Y%m%d-%H%M%S)
      cp -r $CLAUDE_KIT_OUTPUT_DIR/<PLUGIN_NAME> /tmp/claude-kit-backup-<PLUGIN_NAME>-$TIMESTAMP
      ```

   b. **Copy the staged fix to replace the live plugin**:

      ```bash
      rm -rf $CLAUDE_KIT_OUTPUT_DIR/<PLUGIN_NAME>
      cp -r /tmp/claude-kit-review-fix-<PLUGIN_NAME> $CLAUDE_KIT_OUTPUT_DIR/<PLUGIN_NAME>
      ```

   c. **Run validation**:

      ```bash
      claude-kit validate <PLUGIN_NAME>
      ```

      If validation fails:

      ```
      Validation failed for <PLUGIN_NAME> after installation.

      Errors: <list>

      Options:
      - Keep anyway — the plugin is installed but has warnings
      - Rollback — restore from backup
      ```

      If "Rollback":

      ```bash
      rm -rf $CLAUDE_KIT_OUTPUT_DIR/<PLUGIN_NAME>
      cp -r /tmp/claude-kit-backup-<PLUGIN_NAME>-$TIMESTAMP $CLAUDE_KIT_OUTPUT_DIR/<PLUGIN_NAME>
      ```

   d. **Clean up staging**:

      ```bash
      rm -rf /tmp/claude-kit-review-fix-<PLUGIN_NAME>
      ```

7. Present the completion summary:

   ```
   Review-and-fix complete.

   Fixed and finalized:
   <for each finalized plugin>
   - <plugin_name>: <initial_grade> → <final_grade>
     Backup: /tmp/claude-kit-backup-<plugin_name>-<timestamp>
   <end for>

   <if any skipped or rolled back>
   Skipped/rolled back:
   - <plugin_name>: <reason>
   <end if>

   <if any staging dirs remain>
   Unfixed staging directories (not finalized):
   <list remaining /tmp/claude-kit-review-fix-* dirs>
   <end if>
   ```

</phase_4>

<error_handling>

## Error Handling Reference

### Reviewer Failure

When a plugin-reviewer Task call returns an error or malformed output:

1. Capture the error message.
2. Present it to the user via AskUserQuestion:

   ```
   A plugin-reviewer failed during Phase <N>, batch <M>.

   Plugin: <PLUGIN_NAME>
   Error: <error message or "output was malformed/empty">

   Options:
   - Retry — relaunch the reviewer for this plugin
   - Skip — exclude this plugin from fixes
   - Abort — stop the entire workflow
   ```

3. If "Retry": Re-issue the failed Task call only.
4. If "Skip": Remove the plugin from the batch, mark as "skipped" in results.
5. If "Abort": Clean up staging directories and stop.

### Change-Writer Failure

When a change-writer fails:

1. Present the error via AskUserQuestion:

   ```
   A change-writer failed during Phase 2, fix batch <M>.

   Plugin: <PLUGIN_NAME>
   Error: <error message>

   Options:
   - Retry — relaunch the writer for this plugin
   - Skip fixes — keep mechanical fixes only, skip content/structural
   - Abort — stop the entire workflow
   ```

2. If "Retry": Re-issue the failed Task call.
3. If "Skip fixes": The plugin proceeds with only mechanical fixes applied.
4. If "Abort": Clean up staging and stop.

### Malformed Output

If a subagent returns non-JSON output when JSON is expected:
1. Attempt to extract JSON from markdown code blocks.
2. If extraction fails, treat as a subagent failure.

### Validation Failures

If post-fix validation detects issues:
1. Attempt automatic repair via Edit (fix JSON syntax, frontmatter fields).
2. If unrepairable, present to the user with option to skip or abort.

</error_handling>

<workflow_summary>

## Workflow Summary

| Phase | Name | Subagents | Parallel? | Duration |
|-------|------|-----------|-----------|----------|
| 0 | Discovery & Filtering | 0 | — | Fast |
| 1 | Parallel Review | 5 per batch (sequential batches) | Yes (within batch) | Medium-Slow |
| 2 | Fix Application | 0 (mechanical) + 3 per batch (content/structural) | Yes (within batch) | Medium-Slow |
| 3 | Re-Review | 5 per batch (sequential batches) | Yes (within batch) | Medium |
| 4 | Finalization | 0 | — | Fast |

**Batch sizing:**
- Review: 5 plugin-reviewers per batch (read-only)
- Fix: 3 change-writers per batch (write-capable)
- Re-review: 5 plugin-reviewers per batch (read-only, fixed plugins only)

**Total subagent dispatches**: N (initial reviewers) + F (fix writers, 0 if all mechanical) + M (re-reviewers, only for fixed plugins)

**Example: 25 plugins, 10 need fixes, 5 need content fixes**
- Phase 0: scan and filter
- Phase 1: 5 review batches × 5 reviewers = 25 reviewer calls
- Phase 2: mechanical fixes (direct Edit) + 2 fix batches × 3 writers = 6 writer calls
- Phase 3: 2 re-review batches × 5 reviewers = 10 re-reviewer calls
- Phase 4: finalization
- Total subagent dispatches: ~41

**Staging directory pattern**: `/tmp/claude-kit-review-fix-<PLUGIN_NAME>/`

**Key difference from review-all**: This command FIXES issues. review-all is read-only.

**Key difference from update-team**: This command is driven by automated review findings, not user intent. update-team applies user-requested changes; review-and-fix-all applies quality fixes identified by the plugin-reviewer.

</workflow_summary>

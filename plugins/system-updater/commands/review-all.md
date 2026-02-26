---
name: system-updater:review-all
allowed-tools: Task, AskUserQuestion, Read, Glob, Grep, Bash
description: Read-only parallel review of all plugins (or a filtered subset). Spawns batched plugin-reviewer agents (5 per batch) via team-lead pattern, aggregates per-plugin grades into a health summary.
---

# Review All — Parallel Plugin Quality Audit

You are the orchestrator for reviewing all Claude Code plugins in the ecosystem. This is a **read-only** operation — you never modify plugin files. You spawn batched plugin-reviewer agents, collect their graded reports, and present an aggregate health summary.

<critical_rules>

## Critical Rules — Read Before Doing Anything

1. **Read-only**: This command NEVER modifies any plugin file. It only reads and reviews.
2. **User's ~/.claude is sacred**: Never read, modify, or reference `~/.claude`.
3. **Plugin directories**: `$CLAUDE_KIT_BUNDLED_DIR` for bundled plugins, `$CLAUDE_KIT_LOCAL_DIR` for user-created local plugins.
4. **Context compaction safety**: Process review batches SEQUENTIALLY. Each batch uses a team-lead pattern to aggregate results before sending a single message back. This ensures compaction cannot lose individual review results.
5. **Batch size**: 5 plugin-reviewer agents per batch. This is the tested limit for read-only reviewers.
6. **Error recovery**: If any reviewer fails, present the error to the user via AskUserQuestion with options: "Retry", "Skip this plugin", "Abort". Never silently swallow errors.
7. **Progress updates**: Report progress at the start and end of each batch.

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

2. Build the full plugin list. For each plugin, read its version and description:

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
   Found <N> plugins available for review:
   <list each plugin with version>

   How would you like to proceed?

   Options:
   - Review all — audit every plugin
   - Filter by prefix — review only plugins matching a domain prefix (e.g., "embedded-zephyr")
   - Select specific — choose individual plugins to review
   ```

4. If "Filter by prefix": Ask for the prefix, filter the list.
5. If "Select specific": Present each plugin as a multi-select choice.

6. Store:
   - `PLUGINS_TO_REVIEW` — list of plugin names
   - `PLUGIN_DIRS` — map of plugin name to resolved directory path (local takes priority)
   - `REVIEW_COUNT` — total plugins to review
   - `BATCH_COUNT` — ceil(REVIEW_COUNT / 5)

7. Report the review plan:

   ```
   Review plan:
   - Plugins to review: <REVIEW_COUNT>
   - Batches: <BATCH_COUNT> (5 reviewers per batch)

   Proceeding to Phase 1 (Parallel Review).
   ```

</phase_0>

<phase_1>

## Phase 1: Parallel Review (Batched, Sequential Batches)

**Duration**: Medium-Slow (expect 60-120 seconds per batch)

**Subagents**: Up to 5 plugin-reviewer agents per batch, coordinated by a team-lead

### Architecture: Team-Lead Pattern

Each batch of up to 5 plugins gets its own agent team:
- A team-lead agent coordinates 5 plugin-reviewer subagents
- Each reviewer audits one plugin and returns its report to the team-lead
- The team-lead aggregates all 5 reports into a single summary message
- Only the team-lead's aggregated message is sent back to the orchestrator

This pattern ensures that if context compaction happens, only the team-lead's aggregated result needs to survive — individual reviewer outputs are already collected.

### Steps

1. Split `PLUGINS_TO_REVIEW` into batches of 5:

   ```
   BATCHES = chunk(PLUGINS_TO_REVIEW, 5)
   ```

2. Initialize results collector: `ALL_RESULTS = []`

3. For each batch, SEQUENTIALLY:

   a. **Report batch start**: `Starting review batch <N>/<BATCH_COUNT>: <list plugins in batch>`

   b. **Launch 5 plugin-reviewer agents in PARALLEL** (all in a single response):

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

      Read EVERY file. Run ALL checks. Return the full JSON report with:
      - overall_grade (A/B/C/D/F)
      - passed_checks (count)
      - total_checks (count)
      - findings (array of issues with severity, category, file, issue, fix_type, fix)
      "
      )
      ```

   c. **Collect results from all reviewers.** Parse each review report.

   d. **If any reviewer fails**, follow error recovery: offer "Retry", "Skip this plugin", or "Abort".

   e. **Store batch results**: Append each plugin's results to `ALL_RESULTS`:

      ```
      For each plugin in batch:
        ALL_RESULTS.append({
          plugin_name: <name>,
          grade: <overall_grade>,
          passed: <passed_checks>,
          total: <total_checks>,
          critical_count: <count of critical findings>,
          warning_count: <count of warning findings>,
          suggestion_count: <count of suggestion findings>,
          findings: <full findings array>
        })
      ```

   f. **Report batch progress**:

      ```
      Batch <N>/<BATCH_COUNT> complete:
      | Plugin | Grade | Checks | Critical | Warnings |
      |--------|-------|--------|----------|----------|
      | <name> | <grade> | <passed>/<total> | <count> | <count> |
      ...
      ```

4. After all batches complete, proceed to Phase 2.

</phase_1>

<phase_2>

## Phase 2: Aggregate & Report

**Duration**: Fast (data aggregation)

**Subagents**: None

### Steps

1. Compute aggregate statistics:

   ```
   total_plugins = len(ALL_RESULTS)
   grade_counts = { A: count, B: count, C: count, D: count, F: count }
   total_findings = sum of all findings across all plugins
   critical_total = sum of all critical findings
   warning_total = sum of all warning findings
   avg_pass_rate = average of (passed/total) across all plugins
   ```

2. Present the full review summary:

   ```
   === PLUGIN ECOSYSTEM HEALTH REPORT ===

   Plugins reviewed: <total_plugins>
   Average pass rate: <avg_pass_rate>%

   Grade distribution:
   - A: <count> plugins
   - B: <count> plugins
   - C: <count> plugins
   - D: <count> plugins
   - F: <count> plugins

   Total findings: <total_findings>
   - Critical: <critical_total>
   - Warning: <warning_total>
   - Suggestion: <suggestion_total>

   === PER-PLUGIN GRADES ===

   | Plugin | Grade | Pass Rate | Critical | Warnings | Suggestions |
   |--------|-------|-----------|----------|----------|-------------|
   | <name> | <grade> | <passed>/<total> | <count> | <count> | <count> |
   ...

   (Sorted by grade, worst first)
   ```

3. If any plugins have grade D or F, highlight them:

   ```
   === PLUGINS NEEDING ATTENTION ===

   The following plugins scored D or F and should be reviewed:
   <for each D/F plugin>
   - <plugin_name> (Grade: <grade>)
     Top issues:
     <list top 3 critical/warning findings>
   <end for>
   ```

4. Present next steps:

   ```
   To fix these issues automatically, run:
     /system-updater:review-and-fix-all

   To update specific plugins manually:
     /system-updater:update-team
   ```

</phase_2>

<error_handling>

## Error Handling Reference

### Reviewer Failure

When a plugin-reviewer Task call returns an error or malformed output:

1. Capture the error message.
2. Present it to the user via AskUserQuestion:

   ```
   A plugin-reviewer failed during batch <N>.

   Plugin: <PLUGIN_NAME>
   Error: <error message or "output was malformed/empty">

   Options:
   - Retry — relaunch the reviewer for this plugin
   - Skip — exclude this plugin from the report
   - Abort — stop the entire review
   ```

3. If "Retry": Re-issue the failed Task call only.
4. If "Skip": Remove the plugin from the batch, note it as "skipped" in the report.
5. If "Abort": Present whatever results were collected so far and stop.

### Malformed Output

If a reviewer returns non-JSON output:
1. Attempt to extract JSON from markdown code blocks.
2. If extraction fails, treat as a reviewer failure.

</error_handling>

<workflow_summary>

## Workflow Summary

| Phase | Name | Subagents | Parallel? | Duration |
|-------|------|-----------|-----------|----------|
| 0 | Discovery & Filtering | 0 | — | Fast |
| 1 | Parallel Review | 5 per batch (sequential batches) | Yes (within batch) | Medium-Slow |
| 2 | Aggregate & Report | 0 | — | Fast |

**Batch sizing**: 5 plugin-reviewers per batch. Batches processed sequentially.

**Total subagent dispatches**: N (one reviewer per plugin)

**Example: 25 plugins**
- Phase 0: scan and filter
- Phase 1: 5 batches × 5 reviewers = 25 sequential reviewer calls
- Phase 2: aggregate
- Total time: ~10-25 minutes depending on plugin complexity

This command is **read-only**. To fix issues found, run `/system-updater:review-and-fix-all`.

</workflow_summary>

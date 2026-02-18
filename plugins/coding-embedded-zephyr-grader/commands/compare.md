---
allowed-tools: Task, AskUserQuestion, Read, Glob, Grep, Write, Bash
description: Perform blind A/B comparison of two Zephyr submissions with side-by-side scoring and winner analysis
---

# Compare Two Zephyr Submissions (A/B)

You orchestrate a blind A/B comparison of two Zephyr RTOS submissions by stripping identifying metadata, randomizing order, grading both independently, and generating a comparison report showing per-dimension deltas and overall winner.

## Input Parameters

Accept these parameters from the user (ask if not provided):

1. **submission_a_path** (required): Path to first submission
2. **submission_b_path** (required): Path to second submission
3. **board** (optional): Target board name
   - If not provided, use board from first submission or auto-detect
4. **weight_overrides** (optional): Custom dimension weights as JSON
5. **blind_mode** (optional): Randomize order before grading (default: true)
   - If true, submissions are graded as "Submission X" and "Submission Y", then mapped back
6. **output_formats** (optional): List of output formats (default: `["markdown", "json", "html"]`)

## Workflow

### Phase 1: Intake and Metadata Stripping

**Spawn:** `submission-intake` agent **twice in parallel**

**Input A:**
```json
{
  "submission_path": "<submission_a_path>",
  "board": "<board or null>",
  "strip_metadata": true
}
```

**Input B:**
```json
{
  "submission_path": "<submission_b_path>",
  "board": "<board or null>",
  "strip_metadata": true
}
```

**Metadata stripping:**
- Remove student name from comments
- Remove date/time stamps from headers
- Remove author fields from Kconfig
- Keep code identical otherwise

**Output:** Two intake results with metadata removed

---

### Phase 2: Order Randomization (if blind_mode)

If `blind_mode == true`:
1. Generate random bit (0 or 1)
2. If 0: X=A, Y=B
3. If 1: X=B, Y=A
4. Store mapping for later reversal
5. Grade as "Submission X" and "Submission Y"

If `blind_mode == false`:
- Grade as "Submission A" and "Submission B" directly

**Why blind?** Prevents bias in LLM reviews if reviewer sees submission names/metadata.

---

### Phase 3: Parallel Independent Grading

Grade both submissions **independently and in parallel** by spawning two complete grading pipelines.

**For Submission X:**
1. Spawn `compilability-checker`
2. Spawn `static-analyzer`
3. Spawn `metrics-collector`
4. Spawn `resource-analyzer`
5. Spawn `style-checker`
6. Spawn `zephyr-reviewer`
7. Spawn `architecture-reviewer`
8. Spawn `completeness-checker`
9. Spawn `score-aggregator`

**For Submission Y:**
1. (Same 9 agents as above)

**Run all 18 agents in parallel** (9 for X, 9 for Y) to maximize speed.

**Important:** Do NOT reveal Submission X vs Y identity to LLM review agents. They should grade blindly.

---

### Phase 4: Comparison Analysis

**Spawn:** `comparison-analyzer` agent

**Input:**
```json
{
  "submission_x": {
    "dimension_scores": {...},
    "aggregate_score": 87.75,
    "grade": "B+"
  },
  "submission_y": {
    "dimension_scores": {...},
    "aggregate_score": 68.30,
    "grade": "D+"
  },
  "mapping": {"X": "A", "Y": "B"} (if blind_mode)
}
```

**Output:**
```json
{
  "winner": "A",
  "aggregate_delta": 19.45,
  "dimension_deltas": {
    "compilability": {
      "a_score": 100,
      "b_score": 92,
      "delta": 8,
      "winner": "A"
    },
    ...
  },
  "largest_advantages": [
    {"dimension": "style", "delta": 52},
    {"dimension": "static_analysis", "delta": 43},
    {"dimension": "code_metrics", "delta": 16}
  ],
  "analysis": "Submission A is superior across all 9 dimensions..."
}
```

---

### Phase 5: Report Generation

**Spawn:** `comparison-report-generator` agent

**Input:**
```json
{
  "submission_a": <full scorecard>,
  "submission_b": <full scorecard>,
  "comparison_analysis": <from Phase 4>,
  "output_formats": ["markdown", "json", "html"]
}
```

**Output:**
```json
{
  "markdown_path": "/path/to/comparison.md",
  "json_path": "/path/to/comparison.json",
  "html_path": "/path/to/comparison.html"
}
```

**Report structure:**
1. **Summary table:** Aggregate scores, grades, KLOC side-by-side
2. **Dimension comparison table:** All 9 dimensions with deltas and winners
3. **Winner analysis:** Largest advantages, areas where loser is better (if any)
4. **Individual scorecards:** Full details for A and B separately
5. **Recommendations:** For each submission

---

### Phase 6: Present Results to User

Display a summary:

```
=== A/B Comparison Complete ===

Submission A: <path>
Submission B: <path>
Board: <board>

Aggregate Scores:
  A: <score> (<grade>)
  B: <score> (<grade>)

Winner: Submission <A/B> (+<delta> points)

Largest Advantages:
1. <dimension>: +<delta>
2. <dimension>: +<delta>
3. <dimension>: +<delta>

Reports Generated:
- Markdown: <path>
- JSON: <path>
- HTML: <path>
```

Offer to open comparison report.

---

## Comparison Modes

### Standard A/B Comparison

- Grade both submissions completely
- Generate side-by-side comparison
- Declare overall winner
- Show per-dimension winners

### Differential Analysis (Advanced)

If user requests, spawn `diff-analyzer` to:
- Compare source code line-by-line
- Identify algorithmic differences
- Highlight design pattern differences
- Show trade-offs between approaches

**Example use case:** "Why did A score higher on Resource Efficiency?"
Answer: "A uses k_mem_slab (O(1) allocation), B uses k_malloc (O(log N) with fragmentation)"

---

## Blind Mode Guarantees

When `blind_mode == true`:

1. **No metadata leakage:** Names, dates, authors stripped before grading
2. **Randomized labels:** Graded as X/Y, not A/B
3. **Independent reviews:** LLM agents don't know which is which
4. **Fair comparison:** Mapping revealed only in final report

**Why this matters:** Eliminates confirmation bias in LLM reviews.

---

## Edge Cases

### One Submission Fails to Build

If A builds but B doesn't:
- Grade A normally
- Grade B with Compilability failure and Resource Efficiency N/A
- Comparison still valid, but note build failure prominently

### Submissions Use Different Boards

If A is for nRF52840 and B is for ESP32:
- Warn user: "Comparing different boards, resource baselines differ"
- Use board-specific baselines for each
- Note in report that comparison is across different targets

### Identical Submissions

If A and B are identical (or nearly identical):
- Detect via file hash or diff
- Report: "Submissions are identical/very similar"
- Skip full grading, report tie

### Submissions of Very Different Size

If A is 500 LOC and B is 5000 LOC:
- Note size difference prominently
- Per-KLOC normalization ensures fair comparison
- Larger submission may score higher on Completeness if it has more features

---

## Comparison Table Format

### Dimension Comparison Table (Markdown)

```markdown
| Dimension | Submission A | Submission B | Delta | Winner |
|-----------|--------------|--------------|-------|--------|
| Compilability | 100 | 92 | +8 | **A** |
| Static Analysis | 88 | 45 | **+43** | **A** |
| Zephyr Correctness | 90 | 75 | +15 | **A** |
| Resource Efficiency | 65 | 52 | +13 | **A** |
| Architecture | 85 | 70 | +15 | **A** |
| Code Metrics | 78 | 62 | +16 | **A** |
| Style | 92 | 40 | **+52** | **A** |
| Completeness | 95 | 90 | +5 | **A** |
| Documentation | 80 | 65 | +15 | **A** |
| **Aggregate** | **87.75** | **68.30** | **+19.45** | **A** |
```

**Formatting rules:**
- Bold winner in last column
- Bold largest deltas (top 3)
- Use ± for deltas (+ means A is better, - means B is better)

---

## HTML Comparison Enhancements

For HTML output:
- Color-code winner cells (green for winner, light red for loser)
- Bar charts showing dimension scores side-by-side
- Expandable sections for detailed findings
- Diff view for source code (if requested)

**Example HTML snippet:**
```html
<table class="comparison-table">
  <tr class="winner">
    <td>Static Analysis</td>
    <td class="score">88</td>
    <td class="score loser">45</td>
    <td class="delta delta-positive">+43</td>
    <td class="winner-label">A</td>
  </tr>
</table>
```

---

## Statistical Analysis (Advanced)

If user requests statistical rigor:

### Confidence Intervals

For LLM-evaluated dimensions, run multiple passes and compute:
- Mean score
- Standard deviation
- 95% confidence interval

**Example:** "Architecture: A = 85 ± 3 (95% CI), B = 70 ± 4 (95% CI)"

### Significance Testing

If deltas are small, perform t-test to determine if difference is statistically significant.

**Example:** "Style delta of +5 is not statistically significant (p=0.12)"

---

## Recommendations Section

### For Submission A (Winner)

- Highlight strengths to maintain
- Note minor areas for improvement
- Suggest optimizations for even higher scores

### For Submission B (Loser)

- Prioritize fixes based on largest deltas
- Focus on failing dimensions first
- Provide concrete action items

**Example:**
```
Submission B Recommendations:

High Priority:
1. Fix style violations (currently 40/100, A has 92/100)
   - Run clang-format to auto-fix most issues
   - Estimated time: 1 hour

2. Address static analysis defects (currently 45/100, A has 88/100)
   - Fix memory leaks and uninitialized variables
   - Estimated time: 2 hours
```

---

## Output Files

### comparison.md
Full Markdown report with summary, tables, individual scorecards

### comparison.json
Machine-readable comparison with structured deltas:
```json
{
  "version": "1.0",
  "mode": "comparison",
  "submissions": {
    "a": {...},
    "b": {...}
  },
  "comparison": {
    "winner": "A",
    "aggregate_delta": 19.45,
    "dimension_deltas": {...}
  }
}
```

### comparison.html
Rich HTML with color-coded tables, charts, and expandable sections

---

## Example Invocation

User: "Compare student_123 and student_456 for nRF52840DK"

You:
1. Confirm paths and parameters
2. Spawn 2 intake agents in parallel (strip metadata)
3. Randomize order (X=?, Y=?)
4. Spawn 18 grading agents in parallel (9 for X, 9 for Y)
5. Wait for all to complete
6. Spawn comparison-analyzer
7. Spawn comparison-report-generator
8. Present winner with summary
9. Provide file paths to full reports

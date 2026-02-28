# Process Maturity Model

Five maturity levels describe how well a process is defined, measured, and
optimized. Each process document carries a `**Maturity:**` field set to one
of these levels.

## Levels

### Level 1: Initial

The process exists as a documented concept but execution is ad hoc.

- Process document has been written with all 15 sections
- Activities are described but may not be consistently followed
- No metrics are collected
- Quality gates may be informal

**Advancement criteria:** Evidence that the process has been executed at least
three times with consistent inputs and outputs.

### Level 2: Managed

The process is followed consistently within the project.

- Activities are executed as documented
- Entry and exit criteria are checked
- Quality gates are enforced (may be manual)
- Roles are assigned to real people or automation

**Advancement criteria:** Quality gates produce documented evidence. Metrics
collection has begun (even if not yet analyzed).

### Level 3: Defined

The process is standardized and instrumented.

- AI instrumentation enforces process compliance (hooks, rules)
- Templates are used consistently for all artifacts
- Metrics are collected automatically where possible
- The process is referenced by other processes in Related Processes sections

**Advancement criteria:** At least one quarter of metrics data exists. Process
has been tailored at least once based on retrospective feedback.

### Level 4: Measured

The process is quantitatively managed.

- Metrics are analyzed for trends (not just collected)
- Process performance baselines exist
- Deviations from baselines trigger investigation
- Quality gate effectiveness is measured (false positive/negative rates)

**Advancement criteria:** Process improvement actions have been taken based on
metrics analysis. Before/after comparisons show measurable improvement.

### Level 5: Optimizing

The process is continuously improved based on quantitative analysis.

- Improvement experiments are designed and executed
- Root cause analysis drives process changes
- Best practices are harvested and shared across processes
- The process contributes to organizational learning

**Advancement criteria:** Level 5 is sustained, not achieved. A process that
stops improving reverts to Level 4.

## Maturity and Status

Maturity level is independent of process status:

| Status | Maturity | Meaning |
|--------|----------|---------|
| `draft` | `initial` | Typical starting state |
| `active` | `initial` | Approved but still ad hoc |
| `active` | `managed` | Consistent execution |
| `active` | `defined` | Instrumented and standardized |
| `active` | `measured` | Quantitatively managed |
| `active` | `optimizing` | Continuously improving |
| `deprecated` | any | Process is being retired |

A process can be `active` at any maturity level. A `draft` process is
typically at `initial` maturity.

## Consistency Rules

The validation script (`validate-processes.sh`) enforces these consistency
rules between maturity level and section completeness:

| Maturity | Required Section Content |
|----------|------------------------|
| `initial` | All 15 sections present (may contain "TBD" placeholders) |
| `managed` | Sections 3, 7, 8 (Entry/Exit Criteria, Quality Gates) must be non-placeholder |
| `defined` | Section 10 (Metrics) must list at least one metric |
| `measured` | Section 10 must include baseline values |
| `optimizing` | Section 15 (Change History) must show improvement-driven changes |

## Assessment

Maturity assessment is performed per-process, not organization-wide. An
organization with 24 base processes might have:

- 8 processes at Level 3 (defined)
- 10 processes at Level 2 (managed)
- 6 processes at Level 1 (initial)

The overall maturity posture is reported by the `qms-process-status` command.

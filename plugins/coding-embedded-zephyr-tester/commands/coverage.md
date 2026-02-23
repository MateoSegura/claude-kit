---
name: coding-embedded-zephyr-tester:coverage
description: "Generate and analyze code coverage reports, identify untested paths"
allowed-tools: Read, Glob, Grep, Bash, Write
user-invocable: true
---

# Coverage

You generate code coverage reports, analyze gaps, and produce actionable improvement plans.

## Workflow

### Step 1: Determine Coverage Scope

Classify the user's request:

- **Full project coverage** -> Run all tests with `--coverage`
- **Module-specific coverage** -> Run module tests with `--coverage`
- **Analyze existing report** -> Read `twister-out/coverage/`
- **Coverage improvement plan** -> Analyze gaps and suggest tests

### Step 2: Generate Coverage Report

```bash
# Full project coverage
west twister -p native_sim -T tests/ --coverage --coverage-tool lcov

# Module-specific coverage
west twister -p native_sim -T tests/unit/sensor_mgr/ --coverage --coverage-tool lcov

# With pristine build (recommended for accurate results)
west twister -p native_sim -T tests/ --coverage --coverage-tool lcov -z
```

Coverage only works on native_sim (gcov instrumentation is host-only).

### Step 3: Parse Coverage Data

Read the coverage report:

```bash
# Summary statistics
lcov --summary twister-out/coverage/coverage.info

# Per-file breakdown
lcov --list twister-out/coverage/coverage.info
```

Use Grep to find low-coverage files:

```bash
# Find files below 80% line coverage in the lcov report
lcov --list twister-out/coverage/coverage.info | sort -t'|' -k2 -n
```

### Step 4: Identify Untested Paths

For each low-coverage file:

1. Read the source file
2. Read the coverage data to find uncovered line ranges
3. Classify uncovered code:
   - **Error paths**: High priority - these are where bugs hide
   - **Boundary conditions**: High priority - off-by-one errors
   - **Defensive checks**: Medium priority - NULL guards, range checks
   - **Platform-specific**: Low priority - may not be reachable on native_sim
   - **Debug/logging only**: Low priority - low risk

### Step 5: Generate Improvement Plan

For each coverage gap, produce a specific test recommendation:

```
## Coverage Improvement Plan

### Current Metrics
- Line coverage: 72% (target: 80%)
- Branch coverage: 58% (target: 70%)
- Function coverage: 90% (target: 95%)

### Priority 1: Error Handling Paths
| File | Lines | Gap | Recommended Test |
|------|-------|-----|-----------------|
| sensor_mgr.c | 45-48 | I2C read failure | test_read_handles_i2c_failure: set sensor_sample_fetch_fake.return_val = -EIO |
| sensor_mgr.c | 67-70 | NULL device ptr | test_init_returns_einval_for_null: pass NULL device |

### Priority 2: Branch Coverage
| File | Line | Branch | Recommended Test |
|------|------|--------|-----------------|
| filter.c | 23 | filter disabled | test_filter_bypassed_when_disabled: set CONFIG_APP_FILTER=n |
| filter.c | 45 | buffer full | test_filter_handles_full_buffer: fill buffer to capacity |

### Priority 3: Uncalled Functions
| File | Function | Recommended Test |
|------|----------|-----------------|
| storage.c | storage_erase() | test_erase_clears_all_data |
```

### Step 6: Optionally Write Tests

If the user asks, write the recommended tests following the unit test workflow from the identity skill. Create proper test files with ZTEST_SUITE, FFF mocks, and testcase.yaml.

## Presentation Format

```
## Coverage Report: <scope>

### Summary
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Line coverage | 72% | 80% | BELOW TARGET |
| Branch coverage | 58% | 70% | BELOW TARGET |
| Function coverage | 90% | 95% | BELOW TARGET |

### Per-Module Breakdown
| Module | Line % | Branch % | Function % | Priority |
|--------|--------|----------|------------|----------|
| sensor_mgr.c | 85% | 72% | 100% | Low |
| filter.c | 45% | 30% | 80% | HIGH |
| storage.c | 62% | 55% | 75% | Medium |

### Top 5 Coverage Gaps
[Ordered by risk * impact]

### Improvement Plan
[Specific test recommendations with code snippets]
```

## Error Handling

- **lcov not installed** -> Inform user: `apt install lcov`
- **No tests found** -> Suggest `/scaffold-tests` first
- **Coverage files empty** -> Check that tests actually ran (not just built)
- **Native_sim only** -> Coverage requires native_sim, cannot use QEMU or hardware

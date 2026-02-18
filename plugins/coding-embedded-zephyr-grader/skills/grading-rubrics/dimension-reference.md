# Dimension Reference

Complete specification of each grading dimension with detailed scoring criteria, edge cases, and evaluation protocols.

## 1. Compilability (20%, Automated)

**What it measures**: Whether the submission builds successfully with the Zephyr SDK and board configuration.

**Tools**: `west build`, `west build -t pristine`

**Scoring Criteria**:

### 100 points
- Builds successfully with zero warnings
- All configurations specified build without issues
- No deprecated API usage warnings

### 75 points
- Builds successfully with info-level warnings only (e.g., "note: ..." messages)
- Warnings are informational, not suppressible errors

### 50 points
- Builds successfully with warnings that could be suppressed
- Examples: unused variables, implicit declarations, sign comparison
- Code is functional but not clean

### 25 points
- Builds with errors that can be worked around (e.g., missing board overlay can be created)
- Requires manual intervention to build
- Core functionality is present

### 0 points
- Does not build
- Missing critical files (prj.conf, CMakeLists.txt, main.c)
- Syntax errors, undefined symbols, linker errors

**Edge Cases**:

| Situation | Handling |
|-----------|----------|
| No board specified | Try common boards (nrf52840dk_nrf52840, qemu_cortex_m3), use first successful |
| Multiple build configurations | Evaluate all, use average score weighted by importance |
| Board not available in SDK | Mark N/A if no alternative board available |
| Missing prj.conf | Score 0 — critical file |
| Overlay files present | Apply overlays automatically during build |

**Tool Commands**:

```bash
# Clean build attempt
west build -b <board> -p always <submission_path>

# Check for warnings in build log
grep -E "(warning|error):" build/build.log | wc -l

# Extract warning severity
grep -E "warning:" build/build.log | awk '{print $NF}' | sort | uniq -c
```

---

## 2. Static Analysis (15%, Automated)

**What it measures**: Code quality issues detected by static analyzers — bugs, memory leaks, undefined behavior, potential crashes.

**Tools**: `cppcheck`, `clang-tidy`

**Scoring Criteria**:

### 100 points
- Zero defects
- No errors, warnings, or style issues from analyzers

### 75 points
- <0.5 defects per KLOC
- Only low-severity informational messages
- No errors or warnings

### 50 points
- <1.0 defects per KLOC
- Some warnings but no errors
- Issues are mostly stylistic or minor

### 25 points
- <2.0 defects per KLOC
- Multiple warnings, possibly some errors
- Functional issues present but code runs

### 0 points
- ≥2.0 defects per KLOC
- Numerous errors indicating memory safety issues, undefined behavior, or logic bugs

**Defect Severity Weights**:

| Severity | Weight | Examples |
|----------|--------|----------|
| error | 10.0 | Memory leaks, null pointer dereferences, buffer overflows |
| warning | 3.0 | Uninitialized variables, unused code, suspicious constructs |
| style | 1.0 | Naming conventions, formatting |
| information | 0.5 | Performance suggestions, portability notes |
| note | 0.1 | Context information, related locations |

**Defect Density Formula**:

```
weighted_defects = Σ (count[severity] × weight[severity])
KLOC = lines_of_code / 1000
defect_density = weighted_defects / KLOC
score = max(0, 100 - (defect_density / 2.0 * 100))
```

**Edge Cases**:

| Situation | Handling |
|-----------|----------|
| Non-compiling code | Run best-effort analysis with available files, report N/A if insufficient |
| Analyzer crashes | Try alternative tool, mark N/A if both fail |
| False positives | Include suppression count in report but don't adjust score |
| Third-party code | Exclude vendor files from analysis (e.g., Zephyr SDK headers) |

**Tool Commands**:

```bash
# cppcheck with XML output
cppcheck --enable=all --inconclusive --xml --xml-version=2 \
  --suppress=missingIncludeSystem \
  -I <zephyr_include_dirs> \
  <submission_path> 2> cppcheck.xml

# clang-tidy on compilation database
clang-tidy -p build --checks='*' <source_files> > clang-tidy.log 2>&1

# Parse cppcheck XML
xmllint --xpath "//error/@severity" cppcheck.xml | grep -oP 'severity="\K[^"]+' | sort | uniq -c

# Parse clang-tidy output
grep -E "warning:|error:" clang-tidy.log | awk -F: '{print $4}' | sort | uniq -c
```

---

## 3. Zephyr Correctness (15%, LLM + Automated)

**What it measures**: Adherence to Zephyr RTOS patterns, correct API usage, threading model compliance, ISR safety, devicetree usage.

**Tools**: `grep`, LLM code review with pattern checklist

**Scoring Criteria**:

### 100 points
- All 25+ Zephyr patterns correctly applied
- Perfect ISR safety, threading model compliance
- Correct devicetree bindings and Kconfig usage
- No anti-patterns

### 75 points
- 1-2 minor issues (e.g., missing device_is_ready() check in non-critical path)
- No major issues
- Code is Zephyr-idiomatic

### 50 points
- 3-5 minor issues or 1 major issue (e.g., incorrect mutex usage)
- Code works but has technical debt
- Some non-idiomatic patterns

### 25 points
- 6+ minor issues or 2-3 major issues
- Multiple threading violations
- Code may have race conditions or deadlocks

### 0 points
- Critical anti-patterns (sleeping in ISR, unprotected shared state between ISR and threads)
- Fundamental misunderstanding of Zephyr architecture
- Code is unsafe

**Pattern Categories**:

| Category | Example Patterns | Count |
|----------|------------------|-------|
| Kernel | k_sleep vs k_msleep, k_yield usage, SYS_INIT ordering | 4 |
| Threading | k_thread_create params, stack size, priority, k_thread_join | 5 |
| ISR | k_is_in_isr(), no sleeping, k_sem_give vs k_sem_take | 4 |
| Devicetree | DEVICE_DT_GET, device_is_ready(), DT_ALIAS, DT_NODELABEL | 6 |
| Kconfig | CONFIG_ prefix, menuconfig types, dependencies | 3 |
| Synchronization | k_mutex vs k_sem, k_msgq usage, k_poll | 4 |
| Memory | k_malloc vs k_heap_alloc, stack allocation, k_mem_slab | 3 |
| Power | PM_DEVICE_DT_GET, pm_device_action_run | 2 |

**Edge Cases**:

| Situation | Handling |
|-----------|----------|
| No threading | Some patterns N/A (mutex, semaphore), adjust checklist |
| No devicetree | Acceptable for simple samples, reduce weight of DT patterns |
| Zephyr version mismatch | Use patterns for specified version, note if deprecated APIs used |
| Polling-based design | Check for k_poll usage vs busy-wait loops |

**Tool Commands**:

```bash
# ISR safety check
grep -rn "k_sleep\|k_msleep\|k_mutex_lock" --include="*.c" <submission_path> | \
  grep -B5 "ISR_DIRECT_DECLARE\|ISR_DIRECT_PM\|static void.*_isr"

# Device tree usage check
grep -rn "DEVICE_DT_GET\|device_is_ready" --include="*.c" <submission_path>

# Mutex without DEFINE check
grep -rn "k_mutex_init" --include="*.c" <submission_path> | \
  grep -v "K_MUTEX_DEFINE"
```

---

## 4. Resource Efficiency (15%, Automated)

**What it measures**: Flash (ROM) and RAM usage relative to a reference baseline for the same functionality.

**Tools**: `bloaty`, `arm-zephyr-eabi-size`, `west build -t ram_report`, `west build -t rom_report`

**Scoring Criteria**:

### 100 points
- <50% of reference baseline (exceptional optimization)
- Minimal unused code, efficient data structures

### 75 points
- 50-75% of reference baseline
- Good efficiency, standard Zephyr patterns

### 50 points
- 75-100% of reference baseline
- Acceptable resource usage, room for optimization

### 25 points
- 100-150% of reference baseline
- Wasteful patterns (large stack allocations, unused features)

### 0 points
- >150% of reference baseline
- Bloated binary, excessive memory usage

**Reference Baselines** (by board family):

| Board | Baseline Flash (KB) | Baseline RAM (KB) | Example |
|-------|---------------------|-------------------|---------|
| nRF52840 | 128 | 16 | Typical Bluetooth app |
| STM32F4 | 64 | 8 | Standard peripheral app |
| ESP32 | 256 | 32 | WiFi + BLE app |
| QEMU Cortex-M3 | 32 | 8 | Basic sample |

**Size Efficiency Formula**:

```
efficiency_ratio = submission_size / baseline_size
score = 100 - (efficiency_ratio - 0.5) * 200
score = clamp(score, 0, 100)
```

**Edge Cases**:

| Situation | Handling |
|-----------|----------|
| No baseline available | Use generic baseline for board family, note in report |
| Debug build | Compare debug-to-debug or strip symbols first |
| Extra features | Adjust baseline for feature delta |
| SDK version difference | Note if size changes due to SDK update |

**Tool Commands**:

```bash
# Overall size
arm-zephyr-eabi-size build/zephyr/zephyr.elf

# Detailed section breakdown
bloaty --csv -d sections build/zephyr/zephyr.elf > bloaty.csv

# RAM/ROM reports
west build -t ram_report > ram_report.txt
west build -t rom_report > rom_report.txt

# Parse sizes
awk '/text/ {print "Flash:", $1} /bss|data/ {ram+=$1} END {print "RAM:", ram}' \
  < <(arm-zephyr-eabi-size build/zephyr/zephyr.elf)
```

---

## 5. Architecture (10%, LLM)

**What it measures**: Code organization, separation of concerns, modularity, maintainability, design clarity.

**Scoring Criteria**:

### 100 points
- Clean layering with clear boundaries (HAL, driver, application)
- Excellent separation of concerns
- Minimal coupling, high cohesion
- Easy to understand and extend

### 75 points
- Good structure with minor coupling issues
- Clear module boundaries
- Some duplication or tight coupling in non-critical areas

### 50 points
- Acceptable but architectural debt present
- Some god objects or overly large modules
- Refactoring would improve clarity

### 25 points
- Poor separation, tight coupling throughout
- Business logic mixed with hardware access
- Difficult to understand or extend

### 0 points
- No discernible architecture
- All code in one file or module
- Impossible to maintain

**Evaluation Checklist**:

- [ ] Clear module boundaries (separate files for driver, app logic, config)
- [ ] Hardware abstraction layer present
- [ ] No circular dependencies
- [ ] Single Responsibility Principle followed
- [ ] Dependency Inversion (depends on abstractions, not concretions)
- [ ] Open/Closed Principle (extensible without modification)
- [ ] Clear data flow (no hidden global state mutations)
- [ ] Error handling abstracted and consistent

---

## 6. Code Metrics (10%, Automated)

**What it measures**: Cyclomatic complexity, function length, file length, code duplication, maintainability index.

**Tools**: `lizard`, `cloc`

**Scoring Criteria**:

### 100 points
- CCN <10 for all functions
- Functions <50 lines
- Files <500 lines
- No duplicated blocks >10 lines

### 75 points
- CCN <15 for all functions
- Functions <100 lines
- Files <1000 lines
- Minimal duplication

### 50 points
- CCN <20 for all functions
- Functions <150 lines
- Files <1500 lines
- Some duplication acceptable

### 25 points
- CCN <30 for some functions
- Functions <200 lines
- Large files present

### 0 points
- CCN ≥30 (extremely complex)
- Functions >200 lines
- Files >2000 lines

**Complexity Thresholds**:

| Metric | Excellent | Good | Acceptable | Poor | Critical |
|--------|-----------|------|------------|------|----------|
| CCN (avg) | <10 | <15 | <20 | <30 | ≥30 |
| CCN (max) | <15 | <20 | <30 | <40 | ≥40 |
| Function lines (avg) | <30 | <50 | <75 | <100 | ≥100 |
| Function lines (max) | <50 | <100 | <150 | <200 | ≥200 |
| File lines (avg) | <200 | <400 | <600 | <1000 | ≥1000 |
| File lines (max) | <500 | <1000 | <1500 | <2000 | ≥2000 |

**Tool Commands**:

```bash
# Lizard complexity analysis
lizard --csv -Ecpre <submission_path> > lizard.csv

# Count lines of code
cloc --json --by-file <submission_path> > cloc.json

# Parse lizard output
awk -F, 'NR>1 {ccn+=$3; funcs++} END {print "Avg CCN:", ccn/funcs}' lizard.csv
```

---

## 7. Style (5%, Automated)

**What it measures**: Linux kernel coding style compliance, naming conventions, indentation, line length.

**Tools**: `checkpatch.pl` (from Linux kernel scripts)

**Scoring Criteria**:

### 100 points
- Zero violations
- Perfect style compliance

### 75 points
- <1 violation per KLOC
- Minor issues only (whitespace, line length)

### 50 points
- <3 violations per KLOC
- Some naming or indentation issues

### 25 points
- <5 violations per KLOC
- Frequent style violations

### 0 points
- ≥5 violations per KLOC
- Pervasive style issues

**Tool Commands**:

```bash
# Run checkpatch on all C files
find <submission_path> -name "*.c" -exec \
  checkpatch.pl --no-tree --terse -f {} \; > checkpatch.log 2>&1

# Count violations
grep -c "WARNING:\|ERROR:" checkpatch.log

# Per-KLOC calculation
violations=$(grep -c "WARNING:\|ERROR:" checkpatch.log)
kloc=$(cloc --json <submission_path> | jq '.SUM.code / 1000')
echo "scale=2; $violations / $kloc" | bc
```

---

## 8. Completeness (5%, LLM)

**What it measures**: Whether all specified requirements are implemented, edge cases handled, functionality complete.

**Scoring Criteria**:

### 100 points
- All requirements implemented and tested
- Edge cases handled
- Error paths implemented

### 75 points
- All core requirements met
- Missing 1-2 edge cases (documented in code)

### 50 points
- Missing 1-2 secondary requirements
- Most functionality present

### 25 points
- Missing 3+ requirements
- Incomplete implementation of core features

### 0 points
- Barely started
- Most requirements not implemented

**Evaluation Checklist**:

- [ ] All functional requirements met
- [ ] Non-functional requirements met (performance, resource constraints)
- [ ] Error handling present
- [ ] Boundary conditions handled
- [ ] Test cases cover requirements
- [ ] Configuration options implemented

---

## 9. Documentation (5%, LLM)

**What it measures**: README quality, API documentation, inline comments, examples, setup instructions.

**Scoring Criteria**:

### 100 points
- Comprehensive README with quickstart, architecture, API reference
- All public functions documented with Doxygen/kernel-doc
- Inline comments explain why, not what
- Examples included

### 75 points
- Good README with setup and usage
- Most functions documented
- Key design decisions explained

### 50 points
- Basic README with build instructions
- Important functions documented
- Some inline comments

### 25 points
- Minimal README (one paragraph)
- Few comments
- Unclear how to use

### 0 points
- No README
- No comments
- Undocumented code

**Evaluation Checklist**:

- [ ] README exists with overview
- [ ] Build instructions present
- [ ] Usage examples included
- [ ] Architecture/design explained
- [ ] Public API documented
- [ ] Inline comments present
- [ ] Doxygen/kernel-doc format used
- [ ] Configuration options documented

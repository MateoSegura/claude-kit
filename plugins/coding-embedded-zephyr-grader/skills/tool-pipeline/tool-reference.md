# Tool Reference

Complete specification of each tool in the grading pipeline with command syntax, flags, version requirements, and troubleshooting.

## west build (Zephyr Build Tool)

### Purpose
Compile Zephyr RTOS application for target board.

### Command Syntax
```bash
west build -b <board> -p always <source_path>
```

### Flags

| Flag | Description | Required |
|------|-------------|----------|
| `-b <board>` | Target board name | Yes |
| `-p always` | Pristine build (clean first) | Recommended |
| `-d <dir>` | Build directory (default: `build`) | No |
| `-- -DCONFIG_X=y` | Pass Kconfig option | No |

### Example Invocations

**Basic build:**
```bash
west build -b nrf52840dk_nrf52840 -p always ble_peripheral/
```

**Build with custom Kconfig:**
```bash
west build -b nrf52840dk_nrf52840 -p always ble_peripheral/ -- -DCONFIG_DEBUG=y
```

**Build to specific directory:**
```bash
west build -b qemu_cortex_m3 -p always -d build_qemu sample_app/
```

### Output
- **STDOUT:** Build progress, warnings
- **STDERR:** Errors
- **Exit code:** 0 = success, non-zero = failure
- **Build artifacts:** `build/zephyr/zephyr.elf`, `build/zephyr.bin`, etc.

### Version Requirements
- Zephyr SDK 0.16.0+ (current SDK version as of 2026)
- west 1.0.0+

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Board not found | Check `west boards` for available boards |
| CMake error | Verify CMakeLists.txt exists and is valid |
| Missing prj.conf | Add prj.conf in source directory |
| Out of memory | Reduce CONFIG_HEAP_MEM_POOL_SIZE or similar |

---

## cppcheck (Static Analysis)

### Purpose
Detect bugs, memory leaks, undefined behavior in C/C++ code.

### Command Syntax
```bash
cppcheck --enable=all --inconclusive --xml --xml-version=2 \
         --suppress=missingIncludeSystem \
         -I <include_dirs> \
         <source_path> 2> cppcheck.xml
```

### Flags

| Flag | Description | Required |
|------|-------------|----------|
| `--enable=all` | Enable all checks (warning, style, performance, portability, information) | Yes |
| `--inconclusive` | Report inconclusive findings | Recommended |
| `--xml --xml-version=2` | Output in XML format (easier parsing) | Yes |
| `--suppress=<id>` | Suppress specific warning types | No |
| `-I <dir>` | Include directory for headers | Recommended |
| `--force` | Force checking even if includes are missing | For non-compiling code |
| `--inline-suppr` | Allow inline suppressions in code | No |

### Example Invocations

**Standard analysis:**
```bash
cppcheck --enable=all --inconclusive --xml --xml-version=2 \
         --suppress=missingIncludeSystem \
         -I /opt/zephyr-sdk/sysroots/arm-zephyr-eabi/usr/include \
         submission/ 2> cppcheck.xml
```

**Force analysis on non-compiling code:**
```bash
cppcheck --enable=all --force --xml --xml-version=2 \
         submission/ 2> cppcheck.xml
```

### Output
- **Format:** XML on STDERR (redirect with `2>`)
- **Schema:** `<results><error id="" severity="" msg="" file="" line=""/></results>`

### Version Requirements
- cppcheck 2.10+ (current version)

### Severity Levels
- `error` — Bugs, memory leaks, undefined behavior
- `warning` — Suspicious code, potential bugs
- `style` — Code quality, naming conventions
- `performance` — Optimization opportunities
- `portability` — Platform-specific code
- `information` — Informational messages

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Too many false positives | Add `--suppress=<id>` or inline `// cppcheck-suppress` |
| Missing includes | Add `-I` for Zephyr SDK includes |
| Slow analysis | Use `--jobs=4` for parallel analysis |

---

## clang-tidy (LLVM Static Analyzer)

### Purpose
LLVM-based static analysis with extensive checks for C/C++ code quality, modernization, and bugs.

### Command Syntax
```bash
clang-tidy -p build --checks='*' <source_files> > clang-tidy.log 2>&1
```

### Flags

| Flag | Description | Required |
|------|-------------|----------|
| `-p <build_dir>` | Compilation database directory (build/) | Yes |
| `--checks='*'` | Enable all checks (can filter with `-check1,-check2`) | Yes |
| `--format-style=file` | Use .clang-format for auto-fixes | No |
| `--fix` | Auto-fix issues (use with caution) | No |
| `--export-fixes=<file>` | Export fixes to YAML | No |

### Example Invocations

**Analyze with compilation database:**
```bash
clang-tidy -p build --checks='*' src/*.c > clang-tidy.log 2>&1
```

**Analyze specific check categories:**
```bash
clang-tidy -p build \
  --checks='clang-analyzer-*,bugprone-*,performance-*' \
  src/*.c
```

**Exclude certain checks:**
```bash
clang-tidy -p build \
  --checks='*,-readability-magic-numbers,-cppcoreguidelines-avoid-magic-numbers' \
  src/*.c
```

### Output
- **Format:** Text with file:line:column: severity: message
- **Example:** `main.c:23:5: warning: variable 'x' is uninitialized [clang-diagnostic-uninitialized]`

### Version Requirements
- clang-tidy 15.0+ (bundled with Zephyr SDK)
- Requires compilation database (build/compile_commands.json)

### Check Categories
- `clang-analyzer-*` — LLVM static analyzer checks
- `bugprone-*` — Bug-prone code patterns
- `cert-*` — CERT secure coding standards
- `cppcoreguidelines-*` — C++ Core Guidelines
- `performance-*` — Performance optimizations
- `readability-*` — Code readability
- `modernize-*` — Modern C++ features (less relevant for C)

### Troubleshooting

| Issue | Solution |
|-------|----------|
| No compilation database | Run `west build` first to generate `compile_commands.json` |
| Too many checks | Filter with `--checks='category-*'` |
| Slow analysis | Analyze fewer files at a time |
| Header file errors | Ensure headers are in include path |

---

## lizard (Cyclomatic Complexity)

### Purpose
Calculate cyclomatic complexity (CCN), function length, parameter count.

### Command Syntax
```bash
lizard --csv -Ecpre <source_path> > lizard.csv
```

### Flags

| Flag | Description | Required |
|------|-------------|----------|
| `--csv` | Output in CSV format | Yes |
| `-Ecpre` | Use preprocessor directives (better accuracy) | Recommended |
| `-l <language>` | Specify language (auto-detected if omitted) | No |
| `-w` | Ignore warnings | No |
| `-C <threshold>` | Only show functions with CCN > threshold | No |

### Example Invocations

**Standard analysis:**
```bash
lizard --csv -Ecpre submission/ > lizard.csv
```

**Filter high-complexity functions:**
```bash
lizard -C 15 submission/  # Show only CCN > 15
```

**Multiple languages:**
```bash
lizard --csv -Ecpre -l c -l cpp submission/ > lizard.csv
```

### Output
- **Format:** CSV with headers: NLOC, CCN, token, PARAM, length, location
- **Columns:**
  - `NLOC` — Lines of code (excluding blanks/comments)
  - `CCN` — Cyclomatic Complexity Number
  - `token` — Token count
  - `PARAM` — Parameter count
  - `length` — Function length in lines
  - `location` — File:function_name

### Version Requirements
- lizard 1.17+ (current version)

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Incorrect CCN for macros | Use `-Ecpre` to expand preprocessor |
| Missing functions | Check if file is recognized (lizard supports C, C++, Python, etc.) |
| Large files timeout | Increase timeout or analyze files individually |

---

## cloc (Count Lines of Code)

### Purpose
Count source lines of code, excluding comments and blanks.

### Command Syntax
```bash
cloc --json --by-file --exclude-dir=build,zephyr <source_path> > cloc.json
```

### Flags

| Flag | Description | Required |
|------|-------------|----------|
| `--json` | Output in JSON format | Yes |
| `--by-file` | Report per-file counts | Recommended |
| `--exclude-dir=<dirs>` | Exclude directories (comma-separated) | Recommended |
| `--exclude-ext=<exts>` | Exclude file extensions | No |
| `--quiet` | Suppress progress messages | No |

### Example Invocations

**Standard count:**
```bash
cloc --json --by-file --exclude-dir=build submission/ > cloc.json
```

**Count only C files:**
```bash
cloc --json --include-lang=C submission/ > cloc.json
```

### Output
- **Format:** JSON with keys: SUM, <filename>
- **Structure:**
  ```json
  {
    "SUM": {
      "blank": 120,
      "comment": 80,
      "code": 1500,
      "nFiles": 5
    },
    "src/main.c": {
      "blank": 30,
      "comment": 20,
      "code": 400
    }
  }
  ```

### Version Requirements
- cloc 1.90+ (current version)

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Incorrect language detection | Use `--force-lang=C,<file>` |
| Vendor code included | Add to `--exclude-dir` |
| Slow on large codebases | Use `--quiet` and `--exclude-dir` |

---

## checkpatch.pl (Linux Kernel Style Checker)

### Purpose
Validate code against Linux kernel coding style (adopted by Zephyr with modifications).

### Command Syntax
```bash
checkpatch.pl --no-tree --terse -f <source_file>
```

### Flags

| Flag | Description | Required |
|------|-------------|----------|
| `--no-tree` | Don't check against kernel source tree | Yes (for Zephyr) |
| `--terse` | One line per violation | Recommended |
| `-f <file>` | Check file (vs patch with default mode) | Yes |
| `--ignore=<types>` | Ignore specific violation types | No |
| `--max-line-length=<n>` | Custom line length (default 80) | No |

### Example Invocations

**Check single file:**
```bash
checkpatch.pl --no-tree --terse -f src/main.c
```

**Check all C files:**
```bash
find submission/ -name "*.c" -exec checkpatch.pl --no-tree --terse -f {} \; > checkpatch.log
```

**Ignore specific warnings:**
```bash
checkpatch.pl --no-tree --terse --ignore=LINE_LENGTH,CAMELCASE -f src/main.c
```

### Output
- **Format:** Text with FILE:LINE: SEVERITY: MESSAGE
- **Example:**
  ```
  main.c:23: ERROR: spaces required around that '=' (ctx:VxV)
  main.c:45: WARNING: line over 80 characters
  ```

### Version Requirements
- checkpatch.pl from Linux kernel 5.10+
- Available in Zephyr tree at `scripts/checkpatch.pl`

### Violation Types
- `ERROR` — Style violations that should be fixed
- `WARNING` — Style suggestions
- `CHECK` — Pedantic style checks

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Too strict | Use `--ignore=<types>` or `--max-line-length=100` |
| False positives on Zephyr APIs | Ignore CAMELCASE for Zephyr K_* macros |
| Script not found | Use Zephyr's copy: `$ZEPHYR_BASE/scripts/checkpatch.pl` |

---

## arm-zephyr-eabi-size (Binary Size Analysis)

### Purpose
Report flash (text) and RAM (data+bss) usage of compiled binary.

### Command Syntax
```bash
arm-zephyr-eabi-size build/zephyr/zephyr.elf
```

### Flags

| Flag | Description | Required |
|------|-------------|----------|
| `-A` | System V format (detailed sections) | No |
| `-B` | Berkeley format (default, text/data/bss) | No |
| `-t` | Total size | No |

### Example Invocations

**Berkeley format (default):**
```bash
arm-zephyr-eabi-size build/zephyr/zephyr.elf
```

**System V format (detailed):**
```bash
arm-zephyr-eabi-size -A build/zephyr/zephyr.elf
```

### Output
**Berkeley format:**
```
   text    data     bss     dec     hex filename
  98304    2048   10240  110592   1b000 build/zephyr/zephyr.elf
```

**Interpretation:**
- `text` — Flash usage (code + read-only data)
- `data` — Initialized RAM (copied from flash at boot)
- `bss` — Zero-initialized RAM
- Flash total = text + data
- RAM total = data + bss

### Version Requirements
- arm-zephyr-eabi-size (bundled with Zephyr SDK)

---

## west build -t ram_report / rom_report

### Purpose
Detailed RAM/ROM usage by symbol.

### Command Syntax
```bash
west build -t ram_report > ram_report.txt
west build -t rom_report > rom_report.txt
```

### Output
- **Format:** Text table with columns: address, size, symbol
- **Example:**
  ```
  ADDRESS      SIZE  SYMBOL
  0x20000000   1024  _main_stack
  0x20000400   256   _interrupt_stack
  0x20000500   4     variable_x
  ```

### Version Requirements
- Zephyr 3.0+ (these targets were added in Zephyr 3.x)

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Target not found | Update to Zephyr 3.0+, or use `arm-zephyr-eabi-nm` manually |
| Empty report | Ensure build succeeded first |

---

## bloaty (Binary Size Profiler)

### Purpose
Detailed binary size analysis with hierarchical breakdowns.

### Command Syntax
```bash
bloaty --csv -d sections build/zephyr/zephyr.elf > bloaty.csv
```

### Flags

| Flag | Description | Required |
|------|-------------|----------|
| `--csv` | Output in CSV format | Yes |
| `-d <dimension>` | Analysis dimension (sections, symbols, compileunits) | Yes |
| `-s <sort>` | Sort by (vm, file, both) | No |
| `-n <count>` | Show top N entries | No |

### Example Invocations

**Analyze by section:**
```bash
bloaty --csv -d sections build/zephyr/zephyr.elf > bloaty_sections.csv
```

**Analyze by symbol:**
```bash
bloaty --csv -d symbols build/zephyr/zephyr.elf > bloaty_symbols.csv
```

**Hierarchical (section -> symbol):**
```bash
bloaty --csv -d sections,symbols build/zephyr/zephyr.elf > bloaty_detailed.csv
```

### Output
- **Format:** CSV with columns: name, vmsize, filesize
- **Columns:**
  - `name` — Section/symbol name
  - `vmsize` — Size in memory (VM)
  - `filesize` — Size in binary file

### Version Requirements
- bloaty 1.1+ (install from GitHub or package manager)

### Installation
```bash
# Ubuntu/Debian
sudo apt install bloaty

# From source
git clone https://github.com/google/bloaty.git
cd bloaty
cmake -B build -G Ninja
cmake --build build
sudo cmake --build build --target install
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| bloaty not found | Install bloaty or mark tool as unavailable |
| Unsupported binary format | Ensure ELF format (not bin/hex) |
| Large output | Use `-n 50` to limit entries |

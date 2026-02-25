# Output Parsing

Parsing templates for each tool's output format with regex patterns, jq queries, XML/CSV parsing, and annotated example outputs.

## west build (Build Log Parsing)

### Output Format
Plain text build log with warnings/errors intermixed with progress messages.

### Parsing Strategy
Use regex to extract warnings and errors, classify by severity.

### Regex Patterns

**Extract warnings:**
```regex
^.*?:(\d+):(\d+):\s*warning:\s*(.+?)\s*\[(-W[^\]]+)\]
```
- Group 1: Line number
- Group 2: Column number
- Group 3: Warning message
- Group 4: Warning flag

**Extract errors:**
```regex
^.*?:(\d+):(\d+):\s*error:\s*(.+)$
```

**Extract notes:**
```regex
^.*?:(\d+):(\d+):\s*note:\s*(.+)$
```

### Example Output

```
[1/42] Building C object zephyr/CMakeFiles/zephyr.dir/lib/os/printk.c.obj
[2/42] Building C object zephyr/CMakeFiles/zephyr.dir/lib/os/rb.c.obj
/path/to/main.c:45:12: warning: implicit declaration of function 'k_msleep' [-Wimplicit-function-declaration]
    k_msleep(100);
    ^
/path/to/main.c:67:9: warning: unused variable 'ret' [-Wunused-variable]
    int ret = 0;
        ^
/path/to/main.c:45:12: note: 'k_msleep' declared here
[3/42] Building C object zephyr/CMakeFiles/zephyr.dir/lib/os/heap.c.obj
...
[42/42] Linking C executable zephyr/zephyr.elf
```

### Parsing Code (bash)

```bash
# Count warnings
grep -c "warning:" build.log

# Extract warning types
grep "warning:" build.log | sed -n 's/.*\[\(-W[^]]*\)\]/\1/p' | sort | uniq -c

# Extract errors
grep "error:" build.log
```

### Parsing Code (python)

```python
import re

def parse_build_log(log_text):
    warnings = []
    errors = []

    warning_pattern = re.compile(r'^(.*?):(\d+):(\d+):\s*warning:\s*(.+?)\s*\[(-W[^\]]+)\]', re.MULTILINE)
    error_pattern = re.compile(r'^(.*?):(\d+):(\d+):\s*error:\s*(.+)$', re.MULTILINE)

    for match in warning_pattern.finditer(log_text):
        warnings.append({
            'file': match.group(1),
            'line': int(match.group(2)),
            'column': int(match.group(3)),
            'message': match.group(4),
            'flag': match.group(5)
        })

    for match in error_pattern.finditer(log_text):
        errors.append({
            'file': match.group(1),
            'line': int(match.group(2)),
            'column': int(match.group(3)),
            'message': match.group(4)
        })

    return {'warnings': warnings, 'errors': errors}
```

---

## cppcheck XML Parsing

### Output Format
XML (version 2) on STDERR with `<results>` root element.

### Schema

```xml
<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
  <cppcheck version="2.10"/>
  <errors>
    <error id="uninitvar" severity="error" msg="Uninitialized variable: buffer" verbose="..." file="main.c" line="45" column="5"/>
    <error id="memleak" severity="error" msg="Memory leak: data" verbose="..." file="main.c" line="120"/>
    <error id="unusedVariable" severity="style" msg="Unused variable 'tmp'" file="main.c" line="33"/>
  </errors>
</results>
```

### Parsing with xmllint

```bash
# Extract all severities
xmllint --xpath "//error/@severity" cppcheck.xml | grep -oP 'severity="\K[^"]+'

# Count by severity
xmllint --xpath "//error/@severity" cppcheck.xml | \
  grep -oP 'severity="\K[^"]+' | sort | uniq -c

# Extract all error IDs
xmllint --xpath "//error/@id" cppcheck.xml | grep -oP 'id="\K[^"]+'

# Get errors only
xmllint --xpath "//error[@severity='error']/@msg" cppcheck.xml
```

### Parsing with python (ElementTree)

```python
import xml.etree.ElementTree as ET

def parse_cppcheck_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    defects = []
    for error in root.findall('.//error'):
        defects.append({
            'id': error.get('id'),
            'severity': error.get('severity'),
            'msg': error.get('msg'),
            'file': error.get('file', ''),
            'line': int(error.get('line', 0)),
            'column': int(error.get('column', 0))
        })

    return defects
```

### Severity Mapping

| cppcheck severity | Weight |
|-------------------|--------|
| error | 10.0 |
| warning | 3.0 |
| style | 1.0 |
| performance | 1.0 |
| portability | 0.5 |
| information | 0.5 |

---

## clang-tidy Output Parsing

### Output Format
Plain text with file:line:column: severity: message [check-name]

### Example Output

```
/path/to/main.c:23:5: warning: variable 'x' is uninitialized when used here [clang-diagnostic-uninitialized]
    return x + 1;
           ^
/path/to/main.c:20:9: note: initialize the variable 'x' to silence this warning
    int x;
        ^
          = 0
/path/to/service.c:67:12: error: use of undeclared identifier 'k_msleep' [clang-diagnostic-error]
    k_msleep(100);
    ^
2 warnings and 1 error generated.
```

### Regex Patterns

```regex
^([^:]+):(\d+):(\d+):\s+(warning|error|note):\s+(.+?)\s+\[([^\]]+)\]
```
- Group 1: File
- Group 2: Line
- Group 3: Column
- Group 4: Severity
- Group 5: Message
- Group 6: Check name

### Parsing Code (bash)

```bash
# Count warnings and errors
grep -E "^\S+:\d+:\d+:\s+(warning|error):" clang-tidy.log | wc -l

# Group by check name
grep -oP '\[.*?\]' clang-tidy.log | sort | uniq -c
```

### Parsing Code (python)

```python
import re

def parse_clang_tidy(log_text):
    pattern = re.compile(
        r'^([^:]+):(\d+):(\d+):\s+(warning|error|note):\s+(.+?)\s+\[([^\]]+)\]',
        re.MULTILINE
    )

    findings = []
    for match in pattern.finditer(log_text):
        findings.append({
            'file': match.group(1),
            'line': int(match.group(2)),
            'column': int(match.group(3)),
            'severity': match.group(4),
            'message': match.group(5),
            'check': match.group(6)
        })

    return findings
```

---

## lizard CSV Parsing

### Output Format
CSV with header row.

### Schema

```csv
NLOC,CCN,token,PARAM,length,location
45,8,234,2,50,main.c:process_data
67,22,445,3,75,main.c:handle_ble_event
23,6,145,1,28,service.c:init_service
```

### Column Definitions

| Column | Description |
|--------|-------------|
| NLOC | Lines of code (no comments/blanks) |
| CCN | Cyclomatic Complexity Number |
| token | Token count |
| PARAM | Parameter count |
| length | Function length in lines |
| location | file:function_name |

### Parsing with awk

```bash
# Average CCN
awk -F, 'NR>1 {sum+=$2; count++} END {print "Avg CCN:", sum/count}' lizard.csv

# Max CCN
awk -F, 'NR>1 {if($2>max) max=$2} END {print "Max CCN:", max}' lizard.csv

# Functions with CCN > 20
awk -F, 'NR>1 && $2>20 {print $6, "CCN:", $2}' lizard.csv
```

### Parsing Code (python)

```python
import csv

def parse_lizard_csv(csv_file):
    functions = []

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            functions.append({
                'nloc': int(row['NLOC']),
                'ccn': int(row['CCN']),
                'token': int(row['token']),
                'param': int(row['PARAM']),
                'length': int(row['length']),
                'location': row['location']
            })

    return functions

def calculate_ccn_stats(functions):
    ccns = [f['ccn'] for f in functions]
    return {
        'avg': sum(ccns) / len(ccns) if ccns else 0,
        'max': max(ccns) if ccns else 0,
        'total': sum(ccns)
    }
```

---

## cloc JSON Parsing

### Output Format
JSON with SUM key and per-file keys.

### Schema

```json
{
  "header": {
    "cloc_version": "1.90",
    "elapsed_seconds": 0.12,
    "n_files": 3,
    "n_lines": 2340
  },
  "SUM": {
    "blank": 180,
    "comment": 120,
    "code": 2040,
    "nFiles": 3
  },
  "src/main.c": {
    "blank": 60,
    "comment": 40,
    "code": 800,
    "language": "C"
  },
  "src/service.c": {
    "blank": 80,
    "comment": 50,
    "code": 900,
    "language": "C"
  },
  "include/config.h": {
    "blank": 40,
    "comment": 30,
    "code": 340,
    "language": "C Header"
  }
}
```

### Parsing with jq

```bash
# Total lines of code
jq '.SUM.code' cloc.json

# Total files
jq '.SUM.nFiles' cloc.json

# KLOC
jq '.SUM.code / 1000' cloc.json

# Per-file code counts
jq 'to_entries | map(select(.key != "SUM" and .key != "header")) | map({file: .key, code: .value.code})' cloc.json
```

### Parsing Code (python)

```python
import json

def parse_cloc_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    summary = data.get('SUM', {})

    return {
        'total_code': summary.get('code', 0),
        'total_blank': summary.get('blank', 0),
        'total_comment': summary.get('comment', 0),
        'total_files': summary.get('nFiles', 0),
        'kloc': summary.get('code', 0) / 1000.0
    }
```

---

## checkpatch Output Parsing

### Output Format
Plain text with FILE:LINE: SEVERITY: MESSAGE

### Example Output

```
main.c:23: ERROR: spaces required around that '=' (ctx:VxV)
main.c:45: WARNING: line over 80 characters
service.c:12: WARNING: Missing a blank line after declarations
service.c:67: ERROR: trailing whitespace
total: 2 errors, 2 warnings, 450 lines checked
```

### Regex Patterns

```regex
^([^:]+):(\d+):\s+(ERROR|WARNING|CHECK):\s+(.+)$
```
- Group 1: File
- Group 2: Line
- Group 3: Severity
- Group 4: Message

### Parsing Code (bash)

```bash
# Count errors
grep -c "ERROR:" checkpatch.log

# Count warnings
grep -c "WARNING:" checkpatch.log

# Total violations
grep -cE "(ERROR|WARNING):" checkpatch.log
```

### Parsing Code (python)

```python
import re

def parse_checkpatch(log_text):
    pattern = re.compile(r'^([^:]+):(\d+):\s+(ERROR|WARNING|CHECK):\s+(.+)$', re.MULTILINE)

    violations = []
    for match in pattern.finditer(log_text):
        violations.append({
            'file': match.group(1),
            'line': int(match.group(2)),
            'severity': match.group(3),
            'message': match.group(4)
        })

    return violations
```

---

## arm-zephyr-eabi-size Parsing

### Output Format (Berkeley)
Plain text table.

### Example Output

```
   text    data     bss     dec     hex filename
  98304    2048   10240  110592   1b000 build/zephyr/zephyr.elf
```

### Parsing Code (bash)

```bash
# Extract flash and RAM
arm-zephyr-eabi-size build/zephyr/zephyr.elf | awk 'NR==2 {
  flash = $1 + $2
  ram = $2 + $3
  print "Flash:", flash
  print "RAM:", ram
}'
```

### Parsing Code (python)

```python
import subprocess

def parse_size_output(elf_file):
    result = subprocess.run(
        ['arm-zephyr-eabi-size', elf_file],
        capture_output=True,
        text=True
    )

    lines = result.stdout.strip().split('\n')
    if len(lines) < 2:
        return None

    # Parse second line (data row)
    parts = lines[1].split()
    text = int(parts[0])
    data = int(parts[1])
    bss = int(parts[2])

    return {
        'flash': text + data,
        'ram': data + bss,
        'text': text,
        'data': data,
        'bss': bss
    }
```

---

## west build -t ram_report / rom_report Parsing

### Output Format
Plain text table with ADDRESS, SIZE, SYMBOL columns.

### Example Output

```
         ADDRESS      SIZE  SYMBOL
        0x20000000      1024  _main_stack
        0x20000400       256  _interrupt_stack
        0x20000500         4  variable_x
        0x20000504        64  buffer_y
        ...
Total: 8192 bytes
```

### Parsing Code (bash)

```bash
# Extract total
grep "^Total:" ram_report.txt | awk '{print $2}'

# Sum all symbols (if no total line)
awk 'NR>1 && /0x/ {sum+=$2} END {print sum}' ram_report.txt
```

### Parsing Code (python)

```python
import re

def parse_report(report_file):
    symbols = []
    total = 0

    with open(report_file, 'r') as f:
        for line in f:
            if line.startswith('Total:'):
                total = int(line.split()[1])
                continue

            # Parse symbol line: ADDRESS SIZE SYMBOL
            match = re.match(r'\s*(0x[0-9a-f]+)\s+(\d+)\s+(.+)', line, re.IGNORECASE)
            if match:
                symbols.append({
                    'address': match.group(1),
                    'size': int(match.group(2)),
                    'symbol': match.group(3)
                })

    if total == 0 and symbols:
        total = sum(s['size'] for s in symbols)

    return {'symbols': symbols, 'total': total}
```

---

## bloaty CSV Parsing

### Output Format
CSV with name, vmsize, filesize columns.

### Example Output

```csv
name,vmsize,filesize
.text,98304,98304
.data,2048,2048
.bss,10240,0
.rodata,8192,8192
```

### Parsing with awk

```bash
# Total VM size (memory)
awk -F, 'NR>1 {sum+=$2} END {print "Total VM:", sum}' bloaty.csv

# Total file size
awk -F, 'NR>1 {sum+=$3} END {print "Total File:", sum}' bloaty.csv
```

### Parsing Code (python)

```python
import csv

def parse_bloaty_csv(csv_file):
    sections = []

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sections.append({
                'name': row['name'],
                'vmsize': int(row['vmsize']),
                'filesize': int(row['filesize'])
            })

    return sections

def calculate_totals(sections):
    return {
        'total_vm': sum(s['vmsize'] for s in sections),
        'total_file': sum(s['filesize'] for s in sections)
    }
```

---

## Complete Example: Parsing All Tools

### Python Script

```python
#!/usr/bin/env python3

import json
import xml.etree.ElementTree as ET
import csv
import re

def parse_all_tool_outputs(submission_dir):
    results = {}

    # Parse cppcheck
    try:
        tree = ET.parse(f"{submission_dir}/cppcheck.xml")
        root = tree.getroot()
        defects = []
        for error in root.findall('.//error'):
            defects.append({
                'severity': error.get('severity'),
                'msg': error.get('msg'),
                'file': error.get('file', '')
            })
        results['cppcheck'] = defects
    except Exception as e:
        results['cppcheck'] = {'error': str(e)}

    # Parse lizard
    try:
        functions = []
        with open(f"{submission_dir}/lizard.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                functions.append({
                    'ccn': int(row['CCN']),
                    'location': row['location']
                })
        results['lizard'] = functions
    except Exception as e:
        results['lizard'] = {'error': str(e)}

    # Parse cloc
    try:
        with open(f"{submission_dir}/cloc.json", 'r') as f:
            data = json.load(f)
            results['cloc'] = {
                'code': data['SUM']['code'],
                'kloc': data['SUM']['code'] / 1000.0
            }
    except Exception as e:
        results['cloc'] = {'error': str(e)}

    return results

if __name__ == '__main__':
    import sys
    results = parse_all_tool_outputs(sys.argv[1])
    print(json.dumps(results, indent=2))
```

### Usage

```bash
python3 parse_tools.py /path/to/submission > results.json
```

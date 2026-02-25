# Coverage Strategy — Complete Reference

JSON report schema, coverage.py configuration details, exclusion patterns, per-module thresholds, and CI integration.

## coverage.json Schema

After running `pytest --cov-report=json:coverage.json`, the file has this structure:

```json
{
  "meta": {
    "version": "7.x",
    "timestamp": "2025-01-15T10:30:00",
    "branch_coverage": true,
    "show_contexts": false
  },
  "totals": {
    "covered_lines": 420,
    "num_statements": 500,
    "percent_covered": 84.0,
    "percent_covered_display": "84%",
    "missing_lines": 80,
    "excluded_lines": 15,
    "num_branches": 120,
    "num_partial_branches": 8,
    "covered_branches": 112
  },
  "files": {
    "src/services/user_service.py": {
      "executed_lines": [1, 5, 6, 10, 11],
      "summary": {
        "covered_lines": 45,
        "num_statements": 50,
        "percent_covered": 90.0,
        "percent_covered_display": "90%",
        "missing_lines": 5,
        "excluded_lines": 2,
        "num_branches": 18,
        "num_partial_branches": 1,
        "covered_branches": 17
      },
      "missing_lines": [34, 35, 60, 61, 62],
      "excluded_lines": [1, 2]
    }
  }
}
```

## JSON Report Analysis Script

```python
#!/usr/bin/env python3
"""
Parse coverage.json and report gaps. Run after pytest to identify where to
focus test-writing effort.

Usage:
    python scripts/analyze_coverage.py [--threshold 80] [--top 20]
"""
import json
import sys
import argparse


def analyze(report_path: str = "coverage.json", threshold: float = 80.0, top: int = 20):
    with open(report_path) as f:
        data = json.load(f)

    total = data["totals"]["percent_covered"]
    print(f"\nTotal coverage: {total:.1f}% (threshold: {threshold}%)")
    if total < threshold:
        print(f"  FAIL — {threshold - total:.1f}% below threshold")
    else:
        print(f"  PASS — {total - threshold:.1f}% above threshold")

    # Files below threshold
    files = [
        {
            "path": path,
            "pct": info["summary"]["percent_covered"],
            "missing": info["missing_lines"],
            "statements": info["summary"]["num_statements"],
        }
        for path, info in data["files"].items()
    ]
    files.sort(key=lambda x: x["pct"])

    print(f"\nLowest-coverage files (top {top}):")
    print(f"{'Coverage':>10}  {'Statements':>10}  {'Missing Lines':<30}  File")
    print("-" * 80)
    for f in files[:top]:
        missing_preview = str(f["missing"][:5])[1:-1]
        if len(f["missing"]) > 5:
            missing_preview += "..."
        print(f"{f['pct']:>9.1f}%  {f['statements']:>10}  {missing_preview:<30}  {f['path']}")

    # Lines that would push coverage over threshold
    if total < threshold:
        missing_total = data["totals"]["missing_lines"]
        statements_total = data["totals"]["num_statements"]
        lines_needed = int(
            threshold / 100 * statements_total - data["totals"]["covered_lines"]
        ) + 1
        print(f"\nLines needed to reach {threshold}%: ~{lines_needed} (out of {missing_total} missing)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=80.0)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--report", default="coverage.json")
    args = parser.parse_args()
    analyze(args.report, args.threshold, args.top)
```

## Per-Module Coverage Thresholds

coverage.py does not natively support per-file thresholds, but you can enforce them with a custom check:

```python
# scripts/check_module_coverage.py
import json
import sys

THRESHOLDS = {
    "src/services/": 90,     # Business logic — higher bar
    "src/repositories/": 85, # Data access — high bar
    "src/routers/": 80,      # API handlers — standard
    "src/utils/": 80,        # Utilities — standard
    "src/schemas/": 75,      # Schemas — lower (Pydantic handles most validation)
}

with open("coverage.json") as f:
    data = json.load(f)

failures = []
for path, info in data["files"].items():
    pct = info["summary"]["percent_covered"]
    for prefix, threshold in THRESHOLDS.items():
        if path.startswith(prefix) and pct < threshold:
            failures.append((path, pct, threshold))

if failures:
    print("Module coverage thresholds not met:")
    for path, pct, threshold in sorted(failures):
        print(f"  {pct:.1f}% < {threshold}%  {path}")
    sys.exit(1)
else:
    print("All module thresholds met.")
```

## Coverage Exclusion Patterns

Full list of safe exclusion patterns for `[tool.coverage.report]`:

```toml
[tool.coverage.report]
exclude_lines = [
    # Inline pragmas
    "pragma: no cover",

    # Type checking blocks
    "if TYPE_CHECKING:",

    # Main guard
    "if __name__ == .__main__.:",

    # Abstract methods
    "raise NotImplementedError",
    "@(abc\\.)?abstractmethod",

    # Ellipsis stubs
    "\\.\\.\\.",

    # Overload decorators (typing)
    "@(typing\\.)?overload",

    # Protocol methods
    "class .*\\bProtocol\\b",

    # Unreachable defensive code
    "assert False",
    "raise AssertionError",
]
```

## Coverage Configuration Options

### [tool.coverage.run]

| Option | Type | Description |
|--------|------|-------------|
| `branch` | bool | Measure branch coverage (always enable) |
| `source` | list | Packages/directories to measure |
| `omit` | list | Glob patterns to exclude from measurement |
| `include` | list | Only measure these files (alternative to `source`) |
| `parallel` | bool | Enable for pytest-xdist parallel runs |
| `data_file` | str | Path for .coverage data file (default: `.coverage`) |
| `concurrency` | list | `["thread", "greenlet"]` for async code |
| `dynamic_context` | str | `"test_function"` — tag coverage by test name |

### [tool.coverage.report]

| Option | Type | Description |
|--------|------|-------------|
| `fail_under` | float | Minimum total % (0–100) |
| `precision` | int | Decimal places in % display |
| `show_missing` | bool | Show uncovered line ranges |
| `skip_covered` | bool | Hide 100% files from report |
| `skip_empty` | bool | Hide files with no executable lines |
| `sort` | str | Sort by: `"Name"`, `"Stmts"`, `"Miss"`, `"Cover"` |
| `exclude_lines` | list | Regex patterns for lines to ignore |

## CI Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
- name: Run tests with coverage
  run: pytest --cov=src --cov-report=json:coverage.json --cov-fail-under=80

- name: Upload coverage report
  uses: actions/upload-artifact@v4
  with:
    name: coverage-report
    path: coverage.json

- name: Coverage badge (optional)
  uses: Schneegans/dynamic-badges-action@v1.7.0
  with:
    auth: ${{ secrets.GIST_SECRET }}
    gistID: your-gist-id
    filename: coverage.json
    label: Coverage
    message: ${{ steps.coverage.outputs.total }}%
    color: green
```

### Combining with diff-cover (PR coverage)

```bash
pip install diff-cover

# After running tests:
git diff origin/main...HEAD > diff.txt
diff-cover coverage.xml --diff-range-notation ... --compare-branch origin/main --fail-under 80
```

This fails if NEW lines introduced in the PR are less than 80% covered — regardless of existing legacy code.

## What NOT to Cover

These categories should be excluded, not forced to 100%:

| Category | Why to Exclude |
|----------|---------------|
| Migration files | Generated code, migration-tested separately |
| CLI entry points (`main.py`) | Tested via subprocess/integration, not unit |
| Abstract base classes | Subclasses cover the behavior |
| Type stubs / Protocol classes | No runtime behavior |
| Debug/development scripts | Not production code |
| Third-party adapter glue | Trust the library's own tests |

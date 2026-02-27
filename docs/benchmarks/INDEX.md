# benchmarks/ — Performance Benchmarks

Benchmarks measure system performance with reproducible methodology. Each
benchmark documents its methodology, baseline measurements, and results over
time.

## Subdirectories

| Directory | Contents |
|-----------|----------|
| `baselines/` | Baseline measurement records |
| `results/` | Benchmark run results |

## ID Convention

- Prefix: `BM-XXX` (zero-padded three digits)
- Filename: `BM-XXX-<short-description>.md`
- Example: `BM-001-baseline-raw-claude.md`

## Document Template

```markdown
# BM-XXX: <Title>

**Status:** active | superseded-by BM-YYY | retired
**Created:** YYYY-MM-DD
**Last Run:** YYYY-MM-DD

## Objective

What this benchmark measures and why it matters.

## Methodology

Exact steps to reproduce this benchmark. Must be deterministic enough
for any engineer to run independently.

## Environment

- Hardware/platform
- Software versions
- Configuration parameters

## Baseline

Initial measurement establishing the reference point.

## Results

| Date | Value | Notes |
|------|-------|-------|
| YYYY-MM-DD | ... | ... |

## Traces

- **From:** REQ-XXX or PLAN-XXX (what motivated this benchmark)
- **To:** ADR-XXX (decisions informed by benchmark results)
```

## Valid Status Values

| Status | Meaning |
|--------|---------|
| `active` | Currently tracked and periodically re-run |
| `superseded-by BM-YYY` | Replaced by a better benchmark |
| `retired` | No longer relevant |

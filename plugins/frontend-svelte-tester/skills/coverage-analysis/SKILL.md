---
name: frontend-svelte-tester:coverage-analysis
description: "Test coverage analysis for Svelte 5 / SvelteKit projects using Vitest's c8 (v8) and istanbul providers. Covers configuration, threshold enforcement, reading coverage reports, identifying gaps, branch coverage interpretation, and prioritizing what to test next."
user-invocable: false
---

# Coverage Analysis

Coverage tools measure how much of the source code is exercised by tests. Target: 80% across statements, branches, functions, and lines.

## Vitest Coverage Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      // v8 is default — faster, accurate as of Vitest 3.2
      provider: 'v8',       // or 'istanbul' for maximum compatibility

      // Report formats
      reporter: [
        'text',             // terminal summary
        'json-summary',     // machine-readable for CI thresholds
        'lcov',             // for coverage UI tools
        'html',             // browsable report at coverage/index.html
      ],

      // 80% minimum on all metrics
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },

      // What to include (even if not imported in tests)
      include: ['src/**/*.{ts,svelte}'],

      // What to exclude
      exclude: [
        'src/**/*.test.ts',
        'src/**/*.spec.ts',
        'src/**/*.svelte.test.ts',
        'src/**/+page.ts',          // SvelteKit loader types
        'src/**/+layout.ts',
        'src/**/+page.server.ts',   // covered by integration tests
        'src/app.d.ts',             // type declarations only
        'src/lib/index.ts',         // barrel exports only
        '**/node_modules/**',
      ],
    },
  },
});
```

## Running Coverage

```bash
# Run all tests with coverage
npx vitest run --coverage

# Run coverage for specific files
npx vitest run --coverage src/lib/utils

# Watch mode with coverage (updates as files change)
npx vitest --coverage

# Output JSON summary for CI parsing
npx vitest run --coverage --reporter=verbose
```

## Coverage Metrics Explained

| Metric | What It Measures | 80% Means |
|--------|-----------------|-----------|
| **Statements** | Individual executable statements | 8 of 10 statements run |
| **Branches** | All branch paths (if/else, ternary) | 8 of 10 branches taken |
| **Functions** | All function declarations called | 8 of 10 functions called |
| **Lines** | All physical lines executed | 8 of 10 lines run |

**Branch coverage is the most valuable metric** — it reveals untested conditional logic, error paths, and edge cases that statement coverage misses.

## Reading Coverage Output

### Terminal Summary

```
----------|---------|----------|---------|---------|-------------------
File      | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
----------|---------|----------|---------|---------|-------------------
All files |   87.3  |   74.2   |   91.0  |   87.1  |
 utils    |         |          |         |         |
  format.ts|  100   |   80.0   |  100   |  100    | 45-47
  validate.ts| 72.7 |  62.5   |  83.3  |  73.3   | 28-35, 62, 78
----------|---------|----------|---------|---------|-------------------
```

**Reading the table:**
- `validate.ts` line 28-35: a block of code that no test reaches
- `format.ts` line 45-47: branch condition not covered (the else branch)
- Branch coverage below statement coverage = untested conditional logic

## Per-File vs Aggregate Thresholds

```typescript
thresholds: {
  // Global threshold
  statements: 80,
  branches: 80,

  // Per-file overrides for files that warrant higher coverage
  perFile: true,

  // Or use glob-based thresholds (Vitest 2+)
  '**/*.svelte': {
    statements: 70,    // Components are harder to fully cover
    branches: 70,
  },
  '**/utils/**': {
    statements: 95,    // Utility functions should be thoroughly tested
    branches: 90,
  },
},
```

## Additional Resources

- **[reference.md](reference.md)** — Interpreting uncovered branches, gap prioritization heuristics, excluding generated code, generating coverage badges, json-summary format, integrating with CI

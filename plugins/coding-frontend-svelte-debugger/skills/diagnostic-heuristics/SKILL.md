---
name: coding-frontend-svelte-debugger:diagnostic-heuristics
description: "Failure domain classification and investigation heuristics for Svelte 5 / SvelteKit applications. Covers triage decision trees for compiler errors, reactivity bugs, SSR/hydration failures, build errors, and test failures. Used to route symptoms to the correct specialist diagnostic file."
user-invocable: false
---

# Diagnostic Heuristics — Svelte 5 / SvelteKit

Triage logic for classifying failures into domains. Load the domain-specific file once classification is complete.

## Failure Domain Classification

Use this decision tree from top to bottom. Stop at the first match.

```
Symptom received
│
├─ Contains "error TS" or svelte-check output?
│   └─ Domain: COMPILER → load compiler-errors.md
│
├─ Contains "hydration_mismatch" or "ERR_SVELTE_HYDRATION_MISMATCH"?
│   └─ Domain: SSR → load ssr-failures.md
│
├─ Contains "Cannot find module" / "Failed to resolve" / Vite stack trace?
│   └─ Domain: BUILD → load build-errors.md
│
├─ UI renders but data is wrong / stale / not updating?
│   └─ Domain: REACTIVITY → load reactivity-bugs.md
│
├─ Test output: FAIL / assertion mismatch / timeout?
│   └─ Domain: TEST → load test-failures.md
│
├─ Runtime error in browser console (not hydration)?
│   ├─ Stack includes "+page.server.ts" / "load"?
│   │   └─ Domain: SSR (load function) → load ssr-failures.md
│   └─ Stack includes component name?
│       └─ Domain: REACTIVITY or COMPONENT → load reactivity-bugs.md
│
└─ Symptoms span multiple domains?
    └─ Load ALL relevant domain files; flag cross-domain in report
```

## Eight Diagnostic Domains

| Domain | Key Indicators | Specialist File |
|--------|---------------|----------------|
| **Compiler** | `error TS`, `svelte-check`, rune compilation error, `.svelte` parse error | [compiler-errors.md](compiler-errors.md) |
| **Reactivity** | Stale UI, missed update, infinite loop, `$effect` running too often | [reactivity-bugs.md](reactivity-bugs.md) |
| **SSR / Hydration** | `hydration_mismatch`, `window is not defined`, prerender error, load fn error | [ssr-failures.md](ssr-failures.md) |
| **Build** | Vite plugin error, `Cannot find module`, adapter config error, circular dep | [build-errors.md](build-errors.md) |
| **Test** | Vitest `FAIL`, assertion mismatch, Playwright timeout, flaky test | [test-failures.md](test-failures.md) |
| **Component** | Context undefined, snippet render error, prop type mismatch | [compiler-errors.md](compiler-errors.md) + [reactivity-bugs.md](reactivity-bugs.md) |
| **Routing** | 404 on valid route, form action error, redirect loop | [ssr-failures.md](ssr-failures.md) |
| **Hardware IPC** | Device event leak, Tauri invoke rejection, listener after unmount | [reactivity-bugs.md](reactivity-bugs.md) (effect cleanup section) |

## Confidence Calibration

| Evidence Quality | Confidence Level | Action |
|-----------------|-----------------|--------|
| Error message + stack trace + reproduction steps | High (80-100%) | Single-cause diagnosis |
| Error message + partial stack | Medium (50-79%) | Multi-cause hypothesis, ask for stack |
| Symptom description only, no error text | Low (20-49%) | Request error output before diagnosing |
| Vague / second-hand description | Very low (<20%) | Clarification required; do not guess |

## Cross-Domain Indicators

These symptoms frequently involve multiple domains simultaneously:

- **Stale data after navigation** — could be SSR (load fn caching) OR reactivity (`$state` not reactive)
- **Component renders differently on server vs client** — SSR + Reactivity (accessing browser APIs)
- **Test passes locally, fails in CI** — Build (env vars) + Test (timing) + SSR (prerender config)
- **Form submits but UI doesn't update** — Reactivity + Routing (form action return value)

When cross-domain is suspected, load all relevant specialist files and flag the cross-cutting nature in the diagnostic report.

## Additional resources

- [compiler-errors.md](compiler-errors.md) — svelte-check error codes, TypeScript strict mode failures, rune compilation errors with symptom→cause→fix patterns
- [reactivity-bugs.md](reactivity-bugs.md) — `$state` mutation tracking failures, `$derived` staleness, `$effect` cleanup leaks, stale closure captures
- [ssr-failures.md](ssr-failures.md) — Hydration mismatch signatures, load function errors, prerender failures, adapter-specific gotchas
- [build-errors.md](build-errors.md) — Vite plugin ordering, adapter config mistakes, dependency resolution, circular dependencies
- [test-failures.md](test-failures.md) — Vitest component test lifecycle, Playwright timing, assertion mismatch categories

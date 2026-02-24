---
name: coding-frontend-svelte-debugger:output-format
description: "Structured diagnostic report format for Svelte 5 / SvelteKit debugging sessions. Defines the hybrid TL;DR + markdown output structure, confidence rating criteria, escalation format, and report templates for single-cause, multi-cause, low-confidence, and environment-issue diagnoses."
user-invocable: false
---

# Output Format — Diagnostic Reports

All diagnostic reports use a hybrid format: a one-line TL;DR followed by structured markdown sections. Load [templates.md](templates.md) for ready-to-fill report templates.

## Hybrid Format Spec

```
[DOMAIN] [CONFIDENCE] — One-sentence diagnosis.

### Root Cause
<concise explanation of what is wrong and why>

### Evidence
- `<file:line>` — <what this line shows>
- <stack frame or error code> — <what it means>

### Fix
<step-by-step corrective action>

### Verification
<how to confirm the fix worked>
```

The TL;DR line MUST contain:
1. Domain tag: `[COMPILER]`, `[REACTIVITY]`, `[SSR]`, `[BUILD]`, `[TEST]`, `[CROSS-DOMAIN]`
2. Confidence tag: `[HIGH]`, `[MEDIUM]`, `[LOW]`, `[INSUFFICIENT-EVIDENCE]`
3. One sentence summarizing the root cause

## Confidence Rating Criteria

| Tag | Threshold | Requirement |
|-----|-----------|-------------|
| `[HIGH]` | 80-100% | Error message + stack trace point to a single clear cause; fix is unambiguous |
| `[MEDIUM]` | 50-79% | Evidence is consistent with cause but alternative explanations exist; fix likely but verify |
| `[LOW]` | 20-49% | Symptoms match pattern but critical evidence is missing; fix is a hypothesis |
| `[INSUFFICIENT-EVIDENCE]` | <20% | Cannot make responsible diagnosis; escalate with clarification questions |

## Evidence Citation Format

Always cite file paths and line numbers when evidence is available:

```
- `src/routes/+page.svelte:14` — `$effect` contains `count = derived_val` (state sync anti-pattern)
- `src/lib/store.svelte.ts:8` — `$state` object destructured at call site (breaks reactivity)
- svelte-check: `error TS2345` at `src/lib/types.ts:23` — Argument type mismatch
```

When no file evidence is available, cite the symptom directly:

```
- Console error: `hydration_mismatch` — server HTML does not match client render
- Test output: `Expected: "connected" Received: "idle"` — state machine not transitioning
```

## Escalation Format

Use when diagnosis is impossible without more information:

```
[DOMAIN] [INSUFFICIENT-EVIDENCE] — Cannot diagnose without additional information.

### Information Needed
1. <specific artifact required> — <why this is needed>
2. <specific artifact required> — <why this is needed>

### How to Collect
<exact commands or steps to gather the required information>
```

## Multi-Cause Format

Use when symptoms involve more than one independent root cause:

```
[CROSS-DOMAIN] [MEDIUM] — Two independent issues contributing to failure.

### Cause 1: [DOMAIN]
<diagnosis for cause 1>

### Cause 2: [DOMAIN]
<diagnosis for cause 2>

### Fix Order
Fix Cause 1 first — it may resolve Cause 2 as a side effect.
(or: Fix independently — causes are unrelated)
```

## Constraints

- **Read-only**: Never propose to write or modify files. The diagnose command is strictly read-only.
- **No speculation beyond evidence**: If evidence is absent, use `[LOW]` or `[INSUFFICIENT-EVIDENCE]` rather than guessing.
- **Single fix path**: Present one primary fix, not a list of alternatives. Use "Alternative if primary fails:" for secondary options.
- **Reproducibility step**: Every `[HIGH]` and `[MEDIUM]` report must include a verification step.

## Additional resources

- [templates.md](templates.md) — Ready-to-fill report templates for: single-cause, multi-cause, low-confidence, performance escalation, and environment issue diagnoses

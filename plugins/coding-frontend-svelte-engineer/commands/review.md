---
allowed-tools: Task, Read, Glob, Grep, Bash, AskFollowupQuestion
description: "Performance-focused code review for Svelte/SvelteKit code. Analyzes bundle size, rendering strategy (SSR/CSR/prerender), code splitting, lazy loading, Core Web Vitals impact, reactive performance, image/font optimization, and accessibility compliance. Produces prioritized, actionable recommendations. Does NOT modify code."
---

# Review — Performance-Focused Code Analysis

You orchestrate a read-only performance review of SvelteKit code. Your job is to understand what the user wants reviewed, gather context, then dispatch the `performance-analyst` subagent to do the deep analysis. You synthesize and present the results clearly.

## Step 1: Determine Review Scope

Ask the user (or infer from context) what to review:

- **Entire project**: Review all routes, components, and build config
- **Specific route**: Review a single route and its load functions/components
- **Specific component**: Review a component for reactivity and rendering issues
- **Recent changes**: Review files modified in recent git commits
- **Pre-deploy audit**: Full audit before deploying

If scope is unclear, use AskFollowupQuestion: "What should I review — the whole project, a specific feature, or recent changes?"

## Step 2: Gather File Context

Before dispatching, collect relevant file paths:

```bash
# Get project overview
pnpm build 2>&1 | tail -20   # See current build output / chunk sizes
```

```
Glob: src/routes/**/*.{svelte,ts} — all route files
Glob: src/lib/components/**/*.svelte — all components
Read: svelte.config.js — adapter and prerender config
Read: vite.config.ts — build optimization config
Read: package.json — dependencies (heavy ones: d3, chart.js, monaco, etc.)
```

If reviewing specific files, read them first so you can provide accurate paths to the analyst.

## Step 3: Dispatch performance-analyst

Spawn a SINGLE `performance-analyst` subagent. This agent runs in plan mode (read-only).

```
Task(performance-analyst):

You are performing a performance audit of a SvelteKit application.

Scope: [specific scope from Step 1]

Files to analyze:
[list of relevant file paths gathered in Step 2]

Build output summary:
[paste pnpm build output showing chunk sizes]

Audit these dimensions in order of likely impact:

1. BUNDLE SIZE
   - Check each route's JS chunk size (target: < 100KB gzipped per route)
   - Identify heavy dependencies (chart.js, Monaco, PDF libs, icon libraries)
   - Look for barrel file imports that prevent tree-shaking
   - Identify vendor code that should be in a manual chunk

2. RENDERING STRATEGY
   - Verify each route has an explicit, correct SSR/prerender/CSR decision
   - Marketing/blog pages: should be prerendered (export const prerender = true)
   - Auth-gated pages: should SSR
   - Check for unnecessary ssr=false (disabling SSR for pages that could benefit)

3. CODE SPLITTING
   - Verify heavy components (editors, charts, maps) use dynamic import + {#await}
   - Check for large component files that should be split
   - Verify SvelteKit route-based splitting is being utilized (not all in one bundle)

4. REACTIVE PERFORMANCE
   - Find any $effect used where $derived would suffice (extra render cycles)
   - Find $state used on large arrays that should use $state.raw
   - Find {#each} without keys — potential O(n) reconciliation
   - Find deeply nested $state with unnecessary proxy overhead

5. DATA LOADING
   - Check for onMount fetch() that should be load functions (no SSR)
   - Verify parallel Promise.all in load functions (not sequential await chains)
   - Check for missing depends() keys that could enable selective invalidation
   - Look for streaming opportunities (slow API calls that block initial render)

6. IMAGES AND FONTS
   - Check for <img> tags without srcset or lazy loading
   - Verify @font-face declarations use font-display: swap
   - Look for large static images not using enhanced:img
   - Check for font loading that blocks LCP

7. CORE WEB VITALS IMPACT
   - Identify any render-blocking resources (scripts in <head> without defer/async)
   - Look for layout shift sources (images without dimensions, dynamic content insertion)
   - Check for long-running main-thread tasks (synchronous data processing in components)

8. ACCESSIBILITY COMPLIANCE
   - Verify interactive elements have aria labels (buttons, inputs, links)
   - Check for click handlers without keyboard equivalents
   - Verify form inputs have associated labels
   - Check color contrast in Tailwind classes (warn on low-contrast combinations)

For each issue found, provide:
- FILE and LINE reference
- SEVERITY: Critical (blocks deploy) / High (fix before shipping) / Medium (fix this sprint) / Low (optimization opportunity)
- IMPACT: Which Core Web Vital or metric is affected, estimated magnitude
- RECOMMENDATION: Specific fix with code example

Format your output as a structured report with sections per dimension. Include an EXECUTIVE SUMMARY at the top listing the top 5 highest-impact issues.
```

## Step 4: Present Results

After the performance-analyst completes:

1. Display the executive summary prominently.
2. Present the full report organized by severity.
3. Add a recommended action order based on effort vs impact:
   - **Quick wins** (< 30 min, high impact): List first
   - **This sprint** (hours, medium-high impact): List second
   - **Backlog** (significant effort, lower urgency): List last

4. Offer to dispatch specific fixes:
   - "I found 3 high-priority issues. Would you like me to run `/develop` to fix the bundle splitting issue, or would you prefer to review the full report first?"

## Step 5: Error Handling

If the analyst cannot access files (path errors, permission issues):
- Report which files were inaccessible
- Provide the partial analysis from accessible files
- Note what was skipped and why

If no issues are found:
- Report the clean bill of health with specifics: "Routes are correctly configured for SSR/prerender. No heavy unoptimized dependencies found. All images use appropriate optimization."
- Suggest running Lighthouse in CI for runtime CWV measurement that static analysis cannot detect.

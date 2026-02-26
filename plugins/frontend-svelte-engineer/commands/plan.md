---
name: frontend-svelte-engineer:plan
description: "Architecture planning for SvelteKit applications — route design, component hierarchy, state management strategy, data flow patterns, and rendering strategy decisions"
allowed-tools: Task, Read, Glob, Grep, Bash, AskUserQuestion, WebSearch
user-invocable: true
---

# Plan — SvelteKit Architecture Orchestrator

You orchestrate architecture planning for SvelteKit projects by analyzing the user's design challenge and dispatching the `architect` agent to produce a detailed architecture plan. This is a read-only workflow — no code is written or modified.

## Step 1: Classify the Design Challenge

Read the user's request and classify it:

| Category | Signals | Architect Focus |
|----------|---------|----------------|
| New application architecture | "plan app", "design system", "architect project", "new application" | Full architecture: routes, components, state, data flow |
| Feature architecture | "plan feature", "design this feature", "how should I structure" | Feature-scoped: affected routes, new components, data flow changes |
| Route structure design | "organize routes", "plan navigation", "route hierarchy" | Route groups, layouts, rendering strategy per route |
| State management design | "state strategy", "manage data", "where to store" | State scope analysis, reactive patterns, server/client split |
| Refactoring plan | "refactor", "restructure", "improve architecture" | Current state analysis, target state, migration steps |
| Technology selection | "which approach", "should I use", "compare options" | Trade-off analysis for specific architectural choices |

## Step 2: Gather Context

Before dispatching, collect relevant project information:

```
Glob: src/routes/**/*.{svelte,ts} — existing route structure
Glob: src/lib/components/**/*.svelte — component library
Read: svelte.config.js — adapter and SSR/prerender config
Read: package.json — dependencies and deployment target
Read: vite.config.ts — build configuration
```

If reviewing an existing project, also check:

```
Glob: src/lib/stores/**/*.ts — existing state management
Glob: src/lib/server/**/*.ts — server-side utilities
Bash: du -sh node_modules/.vite 2>/dev/null — build cache status
```

## Step 3: Clarify Requirements

If the request is ambiguous, use `AskUserQuestion` to clarify:

- **Deployment target**: "What deployment target? (Vercel, Cloudflare, Tauri 2, Electron, static, Node.js)"
- **Scale**: "How many routes/pages do you expect? Any complex interactive features?"
- **Data sources**: "What are the data sources? (REST API, GraphQL, database, local storage)"
- **Auth**: "Does this need authentication? (Cookies, OAuth, JWT, none)"

Do NOT ask if the request already has enough information to dispatch.

## Step 4: Dispatch Architect

Spawn a SINGLE `architect` subagent:

```
Task(architect):
  Input: <full design challenge description>
  Context:
    - User request: [verbatim]
    - Deployment target: [from svelte.config.js or user input]
    - Existing routes: [route list from Glob]
    - Existing components: [component inventory]
    - Dependencies: [relevant packages from package.json]
    - Constraints: [performance budget, accessibility, browser support]
```

The `architect` agent has these skills preloaded:
- `performance` — Core Web Vitals, bundle optimization
- `state-management` — reactive patterns, Svelte 5 runes
- `build-deploy` — Vite, adapters, deployment strategies
- `design-patterns` — frontend architecture patterns
- `svelte5-runes` — Svelte 5 reactivity model
- `sveltekit-patterns` — SvelteKit routing and data loading
- `component-patterns` — component composition patterns

## Step 5: Present the Architecture Plan

After the architect completes:

1. Present the full architecture plan organized by section
2. Highlight the rendering strategy decisions (SSR/CSR/prerender per route)
3. Flag any assumptions about deployment target or data sources
4. Call out performance budget implications

Offer follow-up actions:

- "Ready to implement? Run `/frontend-svelte-engineer:develop` with this architecture."
- "Want a performance analysis? Run `/frontend-svelte-engineer:review` after implementation."
- "Need to adjust the plan? Tell me which aspect to refine."

## Common Patterns

### New Application Architecture

```
1. Gather: Deployment target, auth needs, data sources, page inventory
2. Clarify: Performance budget, accessibility level, browser support
3. Architect: Full route hierarchy, component tree, state management, data flow
```

### Feature Addition Planning

```
1. Read: Current route structure, existing components, state patterns
2. Architect: How the feature fits — new routes, components, load functions, state
3. Present: Integration points, shared component reuse, rendering strategy
```

### Performance-Driven Refactoring

```
1. Analyze: Current bundle size, rendering strategy, component structure
2. Architect: Optimized structure with code splitting, lazy loading, improved SSR
3. Present: Before/after comparison, migration phases, expected CWV improvement
```

## Error Handling

- **Ambiguous scope** → Use `AskUserQuestion` to narrow the design challenge
- **No existing project** → Architecture plan assumes greenfield SvelteKit setup
- **Conflicting requirements** → Present trade-offs, let user decide priority
- **Architect returns incomplete** → Report gaps, offer to re-run with more context

## Important Constraints

- This command produces READ-ONLY architecture plans — no files are modified
- Always pass sufficient context to the architect (routes, components, config)
- Use absolute file paths in context and results
- Do NOT execute git commands unless explicitly requested
- The architect CANNOT spawn other agents — keep hierarchy flat

# coding-frontend-svelte-engineer

> **Role:** Engineer · **Version:** 0.0.2

Svelte 5 / SvelteKit frontend development agent — writes code, builds features, fixes bugs with runes-only patterns, TypeScript strict mode, Tailwind CSS, proactive performance management, WCAG 2.2 AA accessibility, and desktop targets (Tauri/Electron).

```bash
claude-kit --kit coding-frontend-svelte-engineer
# or load the full team:
claude-kit --kit coding-frontend-svelte
```

**Companion auto-loaded:** `coding-frontend-svelte-knowledge` (Svelte 5 runes, SvelteKit patterns, CSS architecture, accessibility, hardware communication)

---

## Agents

| Agent | Description |
|-------|-------------|
| `component-writer` | Svelte 5 component specialist for building isolated, reusable UI components with runes-only reactivity, typed props, scoped styling, and WCAG 2.2 AA accessibility. Use when the user needs to create or refactor individual components, design prop interfaces, or build component libraries. |
| `feature-builder` | Full-stack SvelteKit feature implementation specialist. Use when the user needs to build a complete feature spanning routes, components, load functions, server endpoints, API integrations, or any multi-file vertical slice through the SvelteKit stack. |
| `scaffold-writer` | SvelteKit project and route scaffolding specialist. Use when the user needs to create a new project skeleton, add routes with correct file conventions, set up layouts, configure adapters, initialize TypeScript/Tailwind/tooling, or scaffold module structures. |
| `style-engineer` | Styling, theming, and animation specialist for Svelte 5 applications. Use when the user needs to implement design systems, create theme configurations, build responsive layouts, add Svelte transitions or CSS animations, set up dark/light mode theming, or resolve visual/CSS issues. |
| `performance-analyst` | Read-only performance analysis agent for Svelte 5 / SvelteKit applications. Use when the user needs a performance audit, bundle size analysis, SSR/CSR rendering strategy review, Core Web Vitals assessment, lazy loading evaluation, or optimization recommendations. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/coding-frontend-svelte-engineer:develop` | Primary entry point for all Svelte/SvelteKit development work. Routes feature builds, component creation, styling, and project scaffolding to the appropriate specialist subagent. Handles bugs and refactors as well as new features. |
| `/coding-frontend-svelte-engineer:review` | Performance-focused code review for Svelte/SvelteKit code. Analyzes bundle size, rendering strategy (SSR/CSR/prerender), code splitting, lazy loading, Core Web Vitals impact, reactive performance, and accessibility compliance. Does NOT modify code. |

# coding-frontend-svelte-debugger

> **Role:** Debugger · **Version:** 0.0.5

Svelte 5 / SvelteKit frontend debugger — diagnoses compiler errors, reactivity bugs, SSR failures, styling issues, accessibility violations, Tauri hardware integration failures, build errors, and test failure root causes with structured evidence-based diagnostic reports.

```bash
claude-kit --kit coding-frontend-svelte-debugger
# or load the full team:
claude-kit --kit coding-frontend-svelte
```

**Companion auto-loaded:** `coding-frontend-svelte-knowledge` (runes, SvelteKit patterns, CSS architecture, accessibility, hardware communication, desktop targets)

---

## Agents

| Agent | Description |
|-------|-------------|
| `triage` | Classifies incoming Svelte 5 / SvelteKit error reports into failure domains: compiler/TS, reactivity, SSR/routing, styling/layout, accessibility, hardware/IPC, build/bundle, or test failure. Asks one clarifying question if critical context is missing, then dispatches to specialist agents. Can dispatch multiple specialists in parallel for cross-domain symptoms. |
| `compiler-ts-analyst` | Diagnoses Svelte compiler errors and TypeScript type errors. Analyzes svelte-check output, tsc diagnostics, Vite transform errors, and Svelte 5 runes compilation failures. Identifies root cause in .svelte, .ts, or .svelte.ts files. |
| `reactivity-analyst` | Diagnoses Svelte 5 reactivity bugs — $state mutation tracking failures, $derived dependency staleness, $effect cleanup leaks, $effect.pre timing issues, nested $state proxy traps, context-shared $state serialization problems, and stale closure captures. |
| `routing-ssr-analyst` | Diagnoses SvelteKit routing failures, SSR hydration mismatches, load function errors, form action failures, hook execution order issues, adapter configuration problems (adapter-node, adapter-static), and prerendering errors. |
| `styling-layout-analyst` | Diagnoses CSS/Tailwind v4 styling failures, layout issues, Svelte scoped style leakage, :global() misuse, design token resolution failures, CSS layer conflicts, container query breakpoints, View Transitions API problems, and responsive design regressions. |
| `accessibility-analyst` | Diagnoses accessibility violations against WCAG 2.2 AA criteria. Analyzes axe-core output, ARIA attribute usage, keyboard navigation paths, focus management, color contrast ratios, and screen reader compatibility. Invoked on-demand when user reports a11y symptoms. |
| `hardware-ipc-analyst` | Diagnoses hardware integration failures through Tauri 2 IPC — USB/Serial/HID connection drops, BLE GATT characteristic errors, LAN/mDNS discovery failures, Audio/MIDI device enumeration problems. Reads and interprets Tauri Rust backend panic traces and IPC invoke/listen/emit event flow. Does NOT modify Rust code. |
| `build-bundle-analyst` | Diagnoses Vite build failures, SvelteKit adapter errors (adapter-node, adapter-static), bundling issues (tree-shaking failures, circular dependencies, missing exports), npm/pnpm dependency resolution problems, and Svelte preprocessing pipeline errors. |
| `test-failure-analyst` | Diagnoses Vitest unit test and Playwright E2E test failures. Performs root-cause analysis distinguishing between test bugs (wrong assertion) and application bugs (correct test, broken code). Understands Svelte component testing patterns and Playwright timing issues. |

---

## Commands

| Command | What it does |
|---------|-------------|
| `/coding-frontend-svelte-debugger:diagnose` | Triage and diagnose failures in Svelte 5 / SvelteKit applications. Classifies symptoms into failure domains, routes to specialist agents, and delivers structured diagnostic reports. Read-only — never writes or modifies code. |

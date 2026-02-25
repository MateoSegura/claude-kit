# core-frontend

> **Role:** Knowledge companion · **Version:** 0.0.1

Framework-agnostic frontend development — accessibility, CSS architecture, UX design, component patterns, state management, and web performance.

This plugin is **auto-loaded as a companion** by any plugin with `"domain": "frontend"`. Do not launch it directly.

---

## Skills Inventory

| Skill | Domain Coverage |
|-------|----------------|
| `accessibility` | WCAG 2.2 AA compliance, ARIA roles/states/properties, semantic HTML, keyboard navigation, focus management, screen reader testing |
| `css-architecture` | Design tokens, CSS custom properties, @layer cascade control, container queries, :has() selector, fluid typography, oklch color, View Transitions |
| `human-centered-design` | Spacing systems, visual hierarchy, Gestalt principles, progressive disclosure, optimistic UI, skeleton loading, micro-interactions, cognitive load |
| `component-architecture` | Composition (slots/children/render props), compound components, headless components, controlled vs uncontrolled, prop drilling vs context |
| `state-management` | Local vs global state, derived/computed state, state machines, optimistic updates, server state vs client state |
| `web-performance` | Core Web Vitals (LCP, INP, CLS), lazy loading, code splitting, image optimization, bundle analysis, critical rendering path, caching strategies |

---

## Auto-Loading

This plugin is automatically loaded as a companion by any plugin whose `ctl.json` declares `"domain": "frontend"`, including:

- `frontend-svelte-engineer`
- `frontend-svelte-tester`
- `frontend-svelte-grader`

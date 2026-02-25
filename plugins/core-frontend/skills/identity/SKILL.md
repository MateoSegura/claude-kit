---
name: core-frontend:identity
description: "Framework-agnostic frontend development knowledge — accessibility, CSS architecture, human-centered design, component patterns, state management, and web performance."
user-invocable: false
---

# Frontend Development — Core Domain Knowledge

This plugin provides framework-agnostic frontend development reference material. It is a **knowledge companion** — loaded alongside framework-specific plugins to provide consistent domain expertise that applies regardless of which framework (React, Svelte, Vue, Angular, etc.) the team uses.

## Domain Scope

- **Accessibility**: WCAG 2.2 AA compliance, ARIA roles/states/properties, semantic HTML, keyboard navigation, focus management, screen reader testing
- **CSS Architecture**: Design tokens, CSS custom properties, @layer cascade control, container queries, :has() selector, fluid typography, responsive patterns
- **Human-Centered Design**: Spacing systems, visual hierarchy, Gestalt principles, progressive disclosure, optimistic UI, skeleton loading, micro-interactions, cognitive load
- **Component Architecture**: Composition patterns (slots/children/render props), compound components, headless components, controlled vs uncontrolled, prop drilling vs context
- **State Management**: Local vs global state, derived/computed state, state machines, optimistic updates, server state vs client state
- **Web Performance**: Core Web Vitals (LCP, FID, CLS), lazy loading, code splitting, image optimization, bundle analysis, critical rendering path, caching strategies

## What This Plugin Contains

Six domain skill directories, each with a SKILL.md entry point and a detailed reference file:

- **accessibility** — WCAG 2.2 AA patterns, ARIA, keyboard navigation, focus management, testing tools
- **css-architecture** — Design tokens, cascade layers, container queries, fluid typography, modern CSS features
- **human-centered-design** — Spacing systems, visual hierarchy, Gestalt principles, interaction design, cognitive load
- **component-architecture** — Composition patterns, compound components, headless components, API design
- **state-management** — Local/global state, derived state, state machines, server state patterns
- **web-performance** — Core Web Vitals, lazy loading, code splitting, image optimization, caching

Each skill directory contains:
- `SKILL.md` — Entry point with overview and quick-reference (auto-loaded by Claude)
- Reference files — Detailed patterns, examples, and checklists (loaded on demand via Read)

## What This Plugin Does NOT Contain

- No agents (role plugins provide those)
- No commands (role plugins provide those)
- No framework-specific patterns (framework knowledge plugins provide those)
- No role-specific identity or persona

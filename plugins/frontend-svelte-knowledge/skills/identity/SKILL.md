---
name: frontend-svelte-knowledge:identity
description: "Domain overview for Svelte 5 and SvelteKit frontend development knowledge base. Covers runes, component patterns, SvelteKit routing, Svelte-specific CSS/a11y/UX patterns, desktop deployment targets, and hardware communication (USB, BLE, LAN, audio/MIDI, IoT)."
user-invocable: false
---

# Svelte 5 / SvelteKit Frontend Development — Domain Knowledge

This plugin provides **Svelte-specific** domain reference material for modern Svelte 5 frontend development with SvelteKit. It is a **knowledge companion** — loaded alongside role-specific plugins (engineer, grader, tester) to provide consistent Svelte expertise across the entire development team.

> **Framework-agnostic frontend patterns** (WCAG 2.2, CSS architecture, UX design, component patterns, state management, web performance) are provided by the `core-frontend` plugin, which is auto-loaded via the `"domain": "frontend"` field. This plugin provides the Svelte-specific layer on top of those foundations.

## Domain Scope

- **Framework**: Svelte 5 with runes (`$state`, `$derived`, `$effect`, `$props`, `$bindable`, `$inspect`) — Svelte 4 patterns are explicitly rejected
- **Meta-framework**: SvelteKit for routing, SSR/CSR, load functions, form actions, hooks, adapters
- **Component model**: Snippet blocks (`{#snippet}`/`{@render}`), `$props()` destructuring, event attributes (`onclick`), component composition
- **State management**: Fine-grained reactivity via runes, shared state with exported `$state`, stores only for Svelte 4 interop
- **Styling**: Svelte scoped CSS, `--style-props`, `:global()` escape hatch, SvelteKit View Transitions
- **Accessibility**: Svelte compiler a11y warnings, SvelteKit route announcements, Bits UI headless components
- **UX Implementation**: Svelte transitions, spring physics, `prefersReducedMotion`, optimistic UI with runes
- **TypeScript**: `strict: true` as the default, `lang="ts"` in all script blocks
- **Testing**: Vitest for unit/integration, Svelte Testing Library for components, Playwright for E2E
- **Desktop targets**: Tauri and Electron deployment considerations — IPC, native menus, file system access, window management
- **Hardware communication**: USB/serial/HID device access, Bluetooth Low Energy scanning and GATT interaction, LAN/mDNS device discovery, audio/MIDI I/O — all via Rust crates wrapped in Tauri commands

## Expertise Areas

This knowledge base covers Svelte-specific implementation details that go beyond what generic frontend references provide. Key expertise areas include:

- **Runes reactivity model**: Deep understanding of the Svelte 5 compiler's reactivity transformation — when `$state` creates proxies vs. primitives, how `$derived` tracks dependencies, `$effect` cleanup semantics, and the difference between `$state.raw` and `$state` for performance-sensitive data
- **SvelteKit full-stack patterns**: Server-only load functions vs. universal load, form actions with progressive enhancement, hooks for auth/middleware, adapter selection for deployment targets, and streaming with `resolve({ filterSerializedResponseHeaders })`
- **Component composition**: Snippet blocks as the Svelte 5 replacement for slots, `$props()` rest/spread patterns, event attributes vs. `createEventDispatcher` (Svelte 4), and `svelte:boundary` for error isolation
- **Desktop-native integration**: Tauri v2 command bridge for accessing Rust crates from Svelte components, IPC patterns for hardware communication, window management, and cross-platform permission models
- **Hardware communication layer**: USB/serial/HID, BLE GATT, LAN/mDNS discovery, and audio/MIDI device access — all bridged through Tauri commands wrapping Rust crates, with Svelte reactive state managing device connection lifecycle

## Skill Reference Map

Twelve domain skill directories, each with multi-file structure. Each contains a `SKILL.md` entry point (auto-loaded by Claude) and supplemental reference files (loaded on demand via Read).

| Skill | What It Provides |
|-------|-----------------|
| `svelte5-runes` | `$state`, `$derived`, `$effect`, `$props`, `$bindable`, `$inspect` — full runes API, anti-patterns, `.svelte.ts` shared reactive logic |
| `sveltekit-patterns` | Routing, load functions, form actions, server endpoints, layouts, error boundaries, hooks, adapters |
| `component-patterns` | Snippet blocks, prop patterns, event handling, composition, reusable UI, typed props |
| `css-architecture` | Svelte scoped styles, `--style-props`, `:global()`, container queries in scoped context, SvelteKit View Transitions |
| `human-centered-design` | Svelte transitions, spring animations, `prefersReducedMotion`, optimistic UI with runes, skeleton loading |
| `accessibility` | Compiler a11y warnings, SvelteKit route announcements, `afterNavigate` focus management, Bits UI, `svelte:boundary` |
| `desktop-targets` | Tauri v2 / Electron integration, platform APIs, packaging, cross-platform considerations |
| `usb-serial-hid` | Serial port, raw USB, HID device communication via Rust crates and Tauri plugins |
| `ble-communication` | BLE scanning, GATT services, btleplug and tauri-plugin-blec |
| `lan-discovery` | TCP/UDP sockets, mDNS/DNS-SD service discovery, local network device communication |
| `audio-midi-devices` | Audio I/O via cpal, MIDI via midir, real-time audio streaming patterns |
| `hardware-abstraction` | Tauri command patterns for hardware, async device streams, IoT protocols, cross-platform permissions |

## Core Companion Plugins

Framework-agnostic frontend knowledge has been extracted into core plugins. Svelte-specific content remains here. Core plugins that complement this domain knowledge:

- `core-frontend` — WCAG 2.2, CSS architecture, UX design principles, component architecture theory, state management patterns, web performance
- `core-architecture` — Design pattern theory, SOLID, component composition principles
- `core-testing` — Test philosophy, test doubles, coverage strategy
- `core-security` — Content Security Policy, XSS prevention, dependency scanning
- `core-git` — Git workflow, branching strategies, commit conventions

When a role plugin (engineer, grader, tester, debugger) references a concept covered by a core plugin, this knowledge plugin provides the Svelte-specific implementation while the core plugin supplies the underlying theory. For example, `core-frontend` covers generic component composition patterns; this plugin's `component-patterns` skill covers Svelte 5 snippet blocks, `$props()` destructuring, and event attributes.

## What This Plugin Does NOT Contain

- No agents — role plugins (engineer, grader, tester, debugger) provide those
- No commands — role plugins provide workflow orchestration commands
- No framework-agnostic patterns — those belong in `core-frontend`
- No role-specific identity or persona — each role plugin defines its own
- No Svelte 4 legacy patterns — all content targets Svelte 5 runes syntax exclusively
- No backend/API patterns — those belong in `core-backend` or team-specific backend plugins

## Additional resources

- For Svelte 5 coding conventions shared across the team, see [coding-standards.md](coding-standards.md)
- For how companion plugins consume this knowledge, see [workflow-patterns.md](workflow-patterns.md)

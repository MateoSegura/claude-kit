---
name: coding-frontend-svelte-knowledge:identity
description: "Domain overview for Svelte 5 and SvelteKit frontend development knowledge base. Covers runes, component patterns, SvelteKit routing, CSS architecture, accessibility, human-centered design, desktop deployment targets, and hardware communication (USB, BLE, LAN, audio/MIDI, IoT)."
user-invocable: false
---

# Svelte 5 / SvelteKit Frontend Development — Domain Knowledge

This plugin provides shared domain reference material for modern Svelte 5 frontend development with SvelteKit. It is a **knowledge companion** — loaded alongside role-specific plugins (engineer, grader, tester) to provide consistent domain expertise across the entire development team.

## Domain Scope

- **Framework**: Svelte 5 with runes (`$state`, `$derived`, `$effect`, `$props`, `$bindable`, `$inspect`) — Svelte 4 patterns are explicitly rejected
- **Meta-framework**: SvelteKit for routing, SSR/CSR, load functions, form actions, hooks, adapters
- **Component model**: Snippet blocks (`{#snippet}`/`{@render}`), `$props()` destructuring, event attributes (`onclick`), component composition
- **State management**: Fine-grained reactivity via runes, shared state with exported `$state`, stores only for Svelte 4 interop
- **Styling**: Tailwind CSS + CSS custom properties for design tokens, theming, fluid typography, container queries, `:has()`, `@layer`
- **Accessibility**: WCAG 2.2 AA as baseline — ARIA patterns, keyboard navigation, focus management, screen reader semantics
- **Human-centered design**: Visual hierarchy, consistent spacing scales, fluid typography, natural transitions, predictable interaction patterns
- **TypeScript**: `strict: true` as the default, `lang="ts"` in all script blocks
- **Testing**: Vitest for unit/integration, Svelte Testing Library for components, Playwright for E2E
- **Desktop targets**: Tauri and Electron deployment considerations — IPC, native menus, file system access, window management
- **Hardware communication**: USB/serial/HID device access, Bluetooth Low Energy scanning and GATT interaction, LAN/mDNS device discovery, audio/MIDI I/O — all via Rust crates wrapped in Tauri commands

## What This Plugin Contains

Twelve domain skill directories, each with multi-file structure:

- **svelte5-runes** — Rune API reference, reactivity model, migration patterns from Svelte 4
- **sveltekit-patterns** — Routing, load functions, form actions, hooks, adapters, SSR/CSR strategies
- **component-patterns** — Composition, snippet blocks, prop patterns, event handling, lifecycle
- **css-architecture** — Design tokens, Tailwind configuration, fluid scales, theming, modern CSS features
- **human-centered-design** — Spacing systems, typography scales, transitions, visual hierarchy, interaction design
- **accessibility** — WCAG 2.2 AA patterns, ARIA, keyboard navigation, focus management, testing tools
- **desktop-targets** — Tauri/Electron integration, platform APIs, packaging, cross-platform considerations
- **usb-serial-hid** — Serial port, raw USB, and HID device communication via Rust crates (serialport, nusb, hidapi) and Tauri plugins
- **ble-communication** — Bluetooth Low Energy scanning, GATT services, btleplug and tauri-plugin-blec
- **lan-discovery** — TCP/UDP sockets, mDNS/DNS-SD service discovery, local network device communication
- **audio-midi-devices** — Audio I/O via cpal, MIDI via midir, real-time audio streaming patterns
- **hardware-abstraction** — Tauri command patterns for hardware, async device streams, IoT protocols, cross-platform permissions

Each skill directory contains:
- `SKILL.md` — Entry point with overview and quick-reference (auto-loaded by Claude)
- Reference files — Detailed API docs, pattern catalogs, examples (loaded on demand via Read)

## What This Plugin Does NOT Contain

- No agents (role plugins provide those)
- No commands (role plugins provide those)
- No role-specific identity or persona (each role plugin defines its own)
- No role-specific hooks

## Additional resources
- For Svelte 5 coding conventions shared across the team, see [coding-standards.md](coding-standards.md)
- For how companion plugins consume this knowledge, see [workflow-patterns.md](workflow-patterns.md)

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

## What This Plugin Contains

Twelve domain skill directories, each with multi-file structure:

- **svelte5-runes** — Rune API reference, reactivity model, migration patterns from Svelte 4
- **sveltekit-patterns** — Routing, load functions, form actions, hooks, adapters, SSR/CSR strategies
- **component-patterns** — Composition, snippet blocks, prop patterns, event handling, lifecycle
- **css-architecture** — Svelte scoped styles, --style-props, :global(), container queries in scoped context, SvelteKit View Transitions
- **human-centered-design** — Svelte transitions, spring animations, prefersReducedMotion, optimistic UI with runes, skeleton loading
- **accessibility** — Svelte compiler a11y warnings, SvelteKit route announcements, afterNavigate focus management, Bits UI, svelte:boundary
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
- No framework-agnostic patterns (provided by `core-frontend`)
- No role-specific identity or persona (each role plugin defines its own)

## Additional resources
- For Svelte 5 coding conventions shared across the team, see [coding-standards.md](coding-standards.md)
- For how companion plugins consume this knowledge, see [workflow-patterns.md](workflow-patterns.md)

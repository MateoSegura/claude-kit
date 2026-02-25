# frontend-svelte-knowledge

> **Role:** Knowledge companion · **Version:** 0.1.1

Svelte 5 / SvelteKit-specific frontend knowledge — runes, component patterns, scoped CSS, a11y compiler warnings, SvelteKit routing, desktop targets, and hardware communication (USB, BLE, LAN, audio/MIDI, IoT).

Framework-agnostic frontend patterns (WCAG 2.2, CSS architecture, UX design, component architecture, state management, web performance) are provided by the `core-frontend` plugin, which is auto-loaded via the `"domain": "frontend"` field.

This plugin is **auto-loaded as a companion** by the engineer, tester, grader, and debugger plugins. Do not launch it directly.

---

## Skills Inventory

| Skill | Domain Coverage |
|-------|----------------|
| `svelte5-runes` | `$state`, `$derived`, `$effect`, `$props`, `$bindable`, `$inspect` — full runes API reference |
| `sveltekit-patterns` | Routing, load functions, form actions, server endpoints, layouts, error boundaries |
| `component-patterns` | Composition, snippets, slot patterns, event forwarding, typed props, reusable UI |
| `css-architecture` | Svelte scoped styles, --style-props, :global(), container queries in scoped context, SvelteKit View Transitions |
| `human-centered-design` | Svelte transitions, spring animations, prefersReducedMotion, optimistic UI with runes, skeleton loading |
| `accessibility` | Svelte compiler a11y warnings, SvelteKit route announcements, afterNavigate focus, Bits UI, svelte:boundary |
| `desktop-targets` | Tauri v2, Electron, native OS APIs, window management, system tray, auto-update |
| `usb-serial-hid` | WebUSB, Web Serial API, HID protocol, device enumeration, data framing |
| `ble-communication` | Web Bluetooth API, GATT profiles, service/characteristic discovery, pairing flows |
| `lan-discovery` | mDNS, Zeroconf, WebSocket servers, local network device discovery |
| `audio-midi-devices` | Web Audio API, Web MIDI API, audio worklets, device selection, latency tuning |
| `hardware-abstraction` | HAL patterns for bridging browser APIs to physical devices across protocols |

---

## Auto-Loading

The following plugins declare this plugin as a companion and automatically inject all its skills into their agent context at launch:

- `frontend-svelte-engineer`
- `frontend-svelte-tester`
- `frontend-svelte-grader`
- `frontend-svelte-debugger`

# coding-frontend-svelte-knowledge

> **Role:** Knowledge companion · **Version:** 0.0.3

Shared domain reference for Svelte 5 / SvelteKit frontend development — runes, component patterns, CSS architecture, accessibility, human-centered design, desktop targets, and hardware communication (USB, BLE, LAN, audio/MIDI, IoT).

This plugin is **auto-loaded as a companion** by the engineer and tester plugins. Do not launch it directly.

---

## Skills Inventory

| Skill | Domain Coverage |
|-------|----------------|
| `svelte5-runes` | `$state`, `$derived`, `$effect`, `$props`, `$bindable`, `$inspect` — full runes API reference |
| `sveltekit-patterns` | Routing, load functions, form actions, server endpoints, layouts, error boundaries |
| `component-patterns` | Composition, snippets, slot patterns, event forwarding, typed props, reusable UI |
| `css-architecture` | Tailwind utility-first, custom properties, design tokens, scoped styles, responsive design |
| `human-centered-design` | UX principles: affordances, feedback loops, progressive disclosure, cognitive load |
| `accessibility` | WCAG 2.2 AA, ARIA patterns, keyboard navigation, focus management, screen reader testing |
| `desktop-targets` | Tauri v2, Electron, native OS APIs, window management, system tray, auto-update |
| `usb-serial-hid` | WebUSB, Web Serial API, HID protocol, device enumeration, data framing |
| `ble-communication` | Web Bluetooth API, GATT profiles, service/characteristic discovery, pairing flows |
| `lan-discovery` | mDNS, Zeroconf, WebSocket servers, local network device discovery |
| `audio-midi-devices` | Web Audio API, Web MIDI API, audio worklets, device selection, latency tuning |
| `hardware-abstraction` | HAL patterns for bridging browser APIs to physical devices across protocols |

---

## Auto-Loading

The following plugins declare this plugin as a companion and automatically inject all its skills into their agent context at launch:

- `coding-frontend-svelte-engineer`
- `coding-frontend-svelte-tester`
- `coding-frontend-svelte-grader`

# Workflow Patterns -- Svelte 5 / SvelteKit

Step-by-step workflows for the most common development tasks. Each workflow reflects the Analyze -> Design -> Implement -> Verify Perf -> Test A11y methodology.

## 1. Feature Implementation Workflow

Use when: adding a new feature that spans routes, components, data loading, and styling.

### Step 1: Understand Route Structure

1. Read `src/routes/` to map the existing route tree.
2. Identify which layout(s) the new feature falls under.
3. Check `svelte.config.js` for the adapter and any route-level `prerender` or `ssr` overrides.
4. Determine the rendering strategy for the new route:
   - **Prerendered** if the content is static or changes infrequently.
   - **SSR** if the content depends on the request (auth, personalized data, fresh API data).
   - **CSR-only** if the content requires browser-only APIs (WebGL, device sensors) or is behind authentication and SEO is irrelevant.

### Step 2: Design Data Loading

1. List the data the page needs to render.
2. For each data source, decide the load location:
   - `+page.server.ts` -- needs secrets, database access, or must never run on client.
   - `+page.ts` -- runs on both server and client, good for public API calls.
   - Client-side fetch in component -- only for non-critical, lazily loaded data.
3. If multiple independent data sources exist, use `Promise.all` in the load function to avoid waterfalls.
4. For slow data sources, consider SvelteKit streaming (return a nested promise and await it in the template with `{#await}`).

### Step 3: Implement Server Logic

1. Create the `+page.server.ts` or `+page.ts` file with a typed load function.
2. Add explicit return type annotation.
3. Validate external data with Zod at the boundary.
4. Handle errors with SvelteKit's `error()` function.
5. If the feature includes mutations, implement form actions in `+page.server.ts`.

### Step 4: Build Components

1. Identify the component decomposition: which pieces are reusable, which are page-specific.
2. Create reusable components in `$lib/components/` with well-defined `Props` interfaces.
3. Create page-specific components colocated near the route.
4. Use `$state` for local mutable state, `$derived` for computed values, `$effect` only for side effects.
5. Pass data from load functions through page props: `let { data }: Props = $props()`.
6. Wire event handlers with `onclick`, `oninput`, etc. (not `on:click`).
7. Use `{#snippet}` / `{@render}` for content projection (not `<slot>`).

### Step 5: Add Styling

1. Apply Tailwind utility classes directly in the template.
2. Use CSS custom properties for any values that change with theme.
3. Ensure responsive design: start mobile-first, add breakpoint modifiers.
4. Add Svelte transitions for mount/unmount animations where they improve UX.

### Step 6: Verify Performance

1. Check that the new route is code-split (no barrel imports pulling in unrelated modules).
2. Verify heavy dependencies are dynamically imported.
3. Confirm images have explicit `width`/`height` or `aspect-ratio`.
4. Estimate the JS cost of new dependencies: `npx bundlephobia <package>` or check bundlephobia.com.
5. If adding a new third-party library, verify it is tree-shakeable.

### Step 7: Test Accessibility

1. Tab through all new interactive elements -- verify visible focus indicators.
2. Verify all buttons/links have accessible names.
3. Check that dynamic content changes are announced (use `aria-live` regions for toast notifications, status updates).
4. Verify form inputs have associated labels.
5. Test color contrast of new text/background combinations.
6. Verify modal/dialog focus trapping and Escape-to-close behavior.

---

## 2. Bug Fix Workflow

Use when: investigating and fixing a reported bug.

### Step 1: Reproduce

1. Identify the exact route/component where the bug manifests.
2. Find the minimal interaction sequence that triggers the bug.
3. Check if the bug is SSR-specific, CSR-specific, or both (test with `ssr: false` toggle if ambiguous).
4. Check the browser console and terminal for errors or warnings.

### Step 2: Isolate the Reactive Chain

1. Identify the `$state` variable(s) involved in the buggy behavior.
2. Trace forward through all `$derived` values that depend on that state.
3. Trace all `$effect` blocks that reference those values.
4. Look for these common runes bugs:
   - `$effect` used where `$derived` should be (unnecessary intermediate state).
   - Missing `$effect` cleanup (stale event listeners, timers).
   - Mutating `$derived` values (they are read-only; mutations silently fail).
   - Reading and writing the same `$state` inside one `$effect` (infinite loop).
   - Object/array identity: replacing a `$state` object loses fine-grained tracking on nested properties.

### Step 3: Fix at the Source

1. Apply the fix at the root cause, not at the symptom.
2. If the bug was a `$effect`-for-derived mistake, replace with `$derived`.
3. If the bug was a missing cleanup, add the cleanup return to the `$effect`.
4. If the bug was a type error caught late, tighten the type to prevent recurrence.
5. Run `npx svelte-check` to verify no new type errors were introduced.

### Step 4: Verify No Regressions

1. Check components that share the same state or derived values.
2. Test the fix in both SSR and CSR contexts if applicable.
3. Verify the fix does not break keyboard navigation or screen reader behavior.
4. Run the existing test suite if available: `npx vitest run` for unit tests, `npx playwright test` for e2e.

---

## 3. Component Creation Workflow

Use when: creating a new reusable Svelte 5 component.

### Step 1: Define the Props Interface

1. List all inputs the component needs.
2. Classify each as required or optional (with default value).
3. Identify which props need two-way binding (`$bindable`).
4. Identify content projection needs (use `Snippet` type for render props).
5. Define event callback props with the `on` prefix convention.

```typescript
interface Props {
  label: string;                           // required
  variant?: 'primary' | 'secondary';       // optional with default
  disabled?: boolean;                       // optional
  value?: string;                           // bindable for form use
  children: Snippet;                        // required content
  onclick?: (event: MouseEvent) => void;   // optional callback
}
```

### Step 2: Implement Structure

1. Create the `.svelte` file with PascalCase naming in the appropriate `$lib/components/` subdirectory.
2. Write the `<script lang="ts">` block following the component structure order: imports, props, state, derived, effects, handlers.
3. Destructure props with defaults: `let { label, variant = 'primary', disabled = false, value = $bindable(''), children, onclick }: Props = $props()`.
4. Write the template using semantic HTML elements.

### Step 3: Add Reactivity

1. Declare local `$state` for internal component state (toggle, hover, focus tracking).
2. Add `$derived` for computed display values.
3. Add `$effect` only for DOM interactions, timers, or external subscriptions -- always with cleanup.

### Step 4: Style with Tailwind

1. Apply utility classes directly in the template.
2. Use CSS custom properties for theme-dependent values.
3. Keep component-specific styles in a `<style>` block for anything Tailwind cannot express.
4. Ensure the component is responsive (test at mobile, tablet, desktop widths).

### Step 5: Add Accessibility Attributes

1. Use semantic HTML: `<button>` for actions, `<a>` for navigation, `<input>` for data entry.
2. Add `aria-label` or `aria-labelledby` if the visible text is insufficient.
3. Add `aria-expanded`, `aria-controls`, `aria-selected` as appropriate for interactive patterns.
4. Set `role` attributes for custom interactive elements.
5. Ensure `tabindex` is correct: `0` for focusable, `-1` for programmatically focusable only, never positive values.

### Step 6: Verify Keyboard Navigation

1. Tab to the component -- focus indicator must be visible.
2. Activate the component with Enter and/or Space as appropriate.
3. If the component is a composite widget (dropdown, listbox, tabs), verify arrow key navigation within it.
4. If the component opens an overlay (modal, popover), verify focus trapping and Escape-to-close.
5. Verify Tab order is logical (follows visual/reading order).

---

## 4. Performance Audit Workflow

Use when: proactively auditing or reactively investigating performance issues.

### Step 1: Check Bundle Size

1. Run `npx vite-bundle-visualizer` to generate the bundle treemap.
2. Identify the largest chunks and their contents.
3. Look for:
   - Barrel file imports pulling in entire libraries (`import { x } from 'huge-lib'` where `x` is 2KB but the barrel import includes 200KB).
   - Duplicate dependencies (same library bundled twice at different versions).
   - Node.js polyfills accidentally included in client bundles.
4. Compare total JS size against the 200KB budget.

### Step 2: Analyze Code Splitting

1. Check that each route loads only the code it needs.
2. Look for shared module imports that defeat route-level splitting.
3. Verify that heavy components (charts, rich text editors, map widgets) use dynamic `import()`.
4. Check `svelte.config.js` and `vite.config.ts` for `manualChunks` configuration.

```typescript
// GOOD: lazy-loaded heavy component
{#await import('$lib/components/Chart.svelte') then { default: Chart }}
  <Chart {data} />
{/await}

// BAD: statically imported heavy component on every page
import Chart from '$lib/components/Chart.svelte';
```

### Step 3: Review SSR/CSR Decisions

For each route, verify the rendering strategy is appropriate:

| Route characteristic | Recommended strategy |
|----------------------|----------------------|
| Public content, SEO matters | Prerender (`export const prerender = true`) |
| User-specific data, SEO matters | SSR (default SvelteKit behavior) |
| Authenticated dashboard, no SEO | CSR (`export const ssr = false` in layout) |
| Mostly static with some dynamic | Hybrid (prerender pages, SSR API routes) |

Flag routes where the current strategy is suboptimal.

### Step 4: Audit Images and Fonts

1. Images: Verify `width`/`height` attributes or CSS `aspect-ratio` (prevents CLS).
2. Images: Check for modern formats (WebP/AVIF) with `<picture>` fallbacks.
3. Images: Verify below-the-fold images use `loading="lazy"`.
4. Fonts: Check for `font-display: swap` in `@font-face` declarations.
5. Fonts: Verify critical fonts are preloaded in `<svelte:head>` or the HTML template.
6. Fonts: Consider variable fonts to reduce total font file count.

### Step 5: Measure Core Web Vitals Impact

1. If browser tools are available, run a Lighthouse audit on the affected routes.
2. Check LCP: is the largest element loading within 2.5s? If not, identify the bottleneck (slow server response, render-blocking resources, large images).
3. Check CLS: are there layout shifts? Common causes: images without dimensions, dynamic content injection above the fold, font swap causing reflow.
4. Check INP: are interactions responsive? Common causes: long-running `$effect` chains, synchronous heavy computation in event handlers, blocking the main thread with data processing.
5. Document findings with specific metrics, root causes, and recommended fixes ranked by estimated impact.

---

## 5. Route Scaffolding Workflow

Use when: adding a new route or route group to an existing SvelteKit project.

### Step 1: Determine Route Type

- **Static page**: `+page.svelte` only, possibly with `export const prerender = true`.
- **Dynamic data page**: `+page.svelte` + `+page.server.ts` (or `+page.ts` for universal load).
- **API endpoint**: `+server.ts` with GET/POST/PUT/DELETE handlers.
- **Layout boundary**: `+layout.svelte` + optional `+layout.server.ts`.
- **Error boundary**: `+error.svelte` for the route group.

### Step 2: Create Directory Structure

```bash
# Example: new authenticated dashboard section
mkdir -p src/routes/(dashboard)/analytics
```

### Step 3: Create Files in Order

1. `+layout.svelte` and `+layout.server.ts` (if new layout boundary needed).
2. `+page.server.ts` or `+page.ts` (data loading).
3. `+page.svelte` (page component).
4. `+error.svelte` (error boundary for the group).
5. Supporting components in `$lib/components/`.

### Step 4: Wire Up Navigation

1. Add links to the new route from relevant navigation components.
2. Use `data-sveltekit-preload-data="hover"` on links for preloading.
3. Verify the route works with both direct navigation (SSR) and client-side navigation (CSR).

### Step 5: Verify

1. Run `npx svelte-check` -- no type errors.
2. Navigate to the route in the browser -- verify SSR and CSR both work.
3. Check that the route appears correctly in the layout hierarchy.
4. Verify the route is code-split (check network tab for separate chunk).

---

## 6. Desktop App Feature Workflow (Tauri 2)

Use when: building a feature that requires native hardware access (USB, BLE, serial, LAN, audio, MIDI) in a Tauri 2 desktop application.

### Step 1: Identify the Hardware Interface

1. Determine the communication protocol: USB (bulk/HID), BLE (GATT), serial (UART), LAN (TCP/UDP/mDNS), audio (capture/playback), MIDI (note/CC/SysEx).
2. Choose the Rust crate: `nusb` (USB), `btleplug` (BLE), `serialport`/`tokio-serial` (serial), `tokio::net` + `mdns-sd` (LAN), `cpal` (audio), `midir` (MIDI).
3. Decide the IPC pattern: synchronous `invoke` for one-shot commands, Tauri events for streaming data.

### Step 2: Implement the Rust Backend

1. Create a Rust module under `src-tauri/src/` for the hardware domain (e.g., `src-tauri/src/ble.rs`).
2. Define Tauri commands with `#[tauri::command]`:
   - Device discovery/enumeration command
   - Connect/disconnect commands
   - Read/write/subscribe commands
3. Wrap device handles in `tauri::State<Arc<Mutex<DeviceHandle>>>` for thread-safe shared access.
4. Use `tauri::Emitter` to push streaming data (sensor telemetry, BLE notifications, audio buffers) to the frontend via events.
5. Implement proper error types with `thiserror` — return `Result<T, String>` from commands (Tauri serializes errors as strings).
6. Register commands in `src-tauri/src/main.rs` with `.invoke_handler(tauri::generate_handler![...])`.

### Step 3: Build the Svelte Frontend

1. Create a `.svelte.ts` rune store for device state management:
   ```typescript
   // src/lib/stores/device.svelte.ts
   let devices = $state<Device[]>([]);
   let connected = $state<Device | null>(null);
   let status = $state<'idle' | 'scanning' | 'connecting' | 'connected' | 'error'>('idle');
   ```
2. Import `@tauri-apps/api/core` (for `invoke`) and `@tauri-apps/api/event` (for `listen`) inside `browser` guards or `onMount`.
3. Build UI components for device listing, connection status, and data visualization.
4. Use `$effect` with cleanup for event listeners:
   ```typescript
   $effect(() => {
     const unlisten = listen('sensor-data', (event) => { /* update state */ });
     return () => { unlisten.then(fn => fn()); };
   });
   ```

### Step 4: Handle Cross-Platform Permissions

1. **Linux**: Create udev rules for USB/serial device access. Document in README.
2. **macOS**: Add `Info.plist` entries for Bluetooth (`NSBluetoothAlwaysUsageDescription`), microphone, camera as needed. Add local network permission description for LAN.
3. **Windows**: Handle driver requirements (WinUSB for raw USB, signed drivers for serial).
4. Configure Tauri capabilities in `src-tauri/capabilities/` for required permissions.

### Step 5: Add Error Handling and Reconnection

1. Implement disconnect detection (device removal, link loss, timeout).
2. Add automatic reconnection with exponential backoff.
3. Show connection status in the UI with clear user feedback (connecting spinner, error messages, retry buttons).
4. Handle permission denial gracefully — show instructions for granting access.

### Step 6: Verify

1. Test on each target platform (Linux, macOS, Windows) for platform-specific quirks.
2. Verify device hot-plug: connect/disconnect/reconnect while the app is running.
3. Verify error states: device not found, permission denied, device busy, communication timeout.
4. Check that background event listeners are cleaned up when components unmount.

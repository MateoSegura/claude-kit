# Diagnostic Workflow Patterns

Step-by-step workflows for the 7 most common diagnostic domains. Each workflow follows the 5-phase methodology (Symptom Capture, Triage, Investigation, Root Cause, Recommendation) with domain-specific detail.

---

## 1. Compiler / TypeScript Error Diagnosis

### Entry Point
User reports red squiggles, `svelte-check` failures, or TypeScript errors during build.

### Investigation Steps

1. **Capture the full error output.**
   - Run `npx svelte-check --output machine` (if Bash is available in read-only mode) or read the provided error log.
   - Note every error code, file path, and line number.

2. **Classify the error type:**
   - `svelte(...)` -- Svelte compiler error (template syntax, rune misuse, a11y)
   - `ts(...)` -- TypeScript error (type mismatch, missing import, strict mode violation)
   - `vite(...)` -- Build-time resolution error (missing module, plugin failure)

3. **Read the offending file at the reported line.**
   - Check 10 lines above and below for context.
   - Look for: incorrect rune syntax, Svelte 4 patterns (`export let`, `$:`, `on:click`), missing type annotations.

4. **Check `tsconfig.json` and `svelte.config.js`.**
   - Verify `"extends": "./.svelte-kit/tsconfig.json"` is present.
   - Verify `compilerOptions.strict` is `true`.
   - Check for `moduleResolution` mismatches (`bundler` is standard for SvelteKit).

5. **Check `$lib` alias resolution.**
   - Verify `$lib` maps to `src/lib` in `svelte.config.js` via `kit.alias` or default.
   - Check for circular imports within `$lib`.

### Common Root Causes
- Svelte 4 syntax in runes-mode component (`export let` instead of `$props()`)
- Missing or incorrect generic type on `$state<T>()`
- `tsconfig.json` not extending SvelteKit's generated config
- Import path using `.svelte` extension when `moduleResolution` is set to `node` instead of `bundler`

### Verification
- `npx svelte-check --output machine` reports 0 errors after fix
- `npx tsc --noEmit` passes (if project uses separate TS checking)

---

## 2. Reactivity Bug Diagnosis ($state / $derived / $effect)

### Entry Point
User reports UI not updating, stale values, infinite loops, or unexpected re-renders.

### Investigation Steps

1. **Identify the reactive variable in question.**
   - Which component? Which variable? What is its declaration (`$state`, `$derived`, `let`, plain `const`)?

2. **Trace the reactive dependency graph manually.**
   - For `$derived(expr)`: list every reactive variable referenced in `expr`. Are they all `$state` or `$derived` themselves?
   - For `$effect(() => { ... })`: list every reactive variable read inside the effect body. Check for writes to `$state` variables within the same effect.

3. **Check for the 5 reactivity anti-patterns:**
   - **Missing `$state`**: Variable declared with plain `let` -- invisible to Svelte's reactivity system.
   - **Effect-derived loop**: `$effect` writes to a `$state` that the same effect reads.
   - **Stale closure**: Reactive value captured in a callback or `setTimeout` that does not re-run when the value changes.
   - **Deep mutation without `$state`**: Mutating a nested property on a plain object (not wrapped in `$state`).
   - **`$derived` with side effects**: `$derived` body performs I/O, DOM manipulation, or state writes.

4. **Check for `$inspect()` output if available.**
   - `$inspect(variable)` logs every time the variable changes. If it never fires, the variable is not reactive.

5. **Check component boundaries.**
   - Props passed from parent to child: does the parent use `$state`? Does the child destructure with `$props()`?
   - Are any props passed through a store or context that strips reactivity?

### Common Root Causes
- Plain `let` instead of `$state` (most frequent)
- `$effect` writing to its own dependency (infinite loop)
- Destructuring `$props()` into local variables without `$derived` (snapshot, not reactive binding)
- Array/object mutation via methods (`.push()`, `.splice()`) on non-`$state` references

### Verification
- Add `$inspect(variable)` temporarily to confirm reactivity is restored
- `npx svelte-check` clean
- Visual confirmation that UI updates when state changes

---

## 3. SSR / Hydration Mismatch Diagnosis

### Entry Point
User reports hydration warnings in browser console, content flash on page load, or `500` errors during SSR.

### Investigation Steps

1. **Capture the hydration warning verbatim.**
   - Browser console typically shows: `"Hydration failed because the initial UI does not match what was rendered on the server"`
   - Note which DOM element is mismatched.

2. **Identify server vs. client divergence points.**
   - Check for browser-only APIs used during SSR: `window`, `document`, `localStorage`, `navigator`.
   - Check for conditional rendering based on `typeof window !== 'undefined'` or `browser` import from `$app/environment`.

3. **Inspect load functions.**
   - `+page.server.ts`: runs only on server. Data returned here is available in `$page.data`.
   - `+page.ts`: runs on both server and client. If it accesses browser APIs, it will fail during SSR.
   - Check: does the load function return different data on server vs. client?

4. **Check for dynamic imports or lazy components.**
   - Components imported with `import()` may not resolve identically on server and client.
   - `onMount` callbacks run only on client -- content dependent on `onMount` data will mismatch during hydration.

5. **Check `+layout.ts` / `+layout.server.ts` chain.**
   - Data flows from layout load functions to child pages. A layout returning inconsistent data can cause hydration mismatches in any child route.

6. **Check for date/time rendering.**
   - `new Date()` on server vs. client produces different timestamps. This is the single most common SSR mismatch cause.

### Common Root Causes
- Browser API (`window`, `localStorage`) accessed during SSR without guard
- Date/time rendered without consistent formatting between server and client
- `+page.ts` load function with side effects that differ between environments
- Third-party library that accesses `document` at import time

### Verification
- `npm run build && npm run preview` -- no hydration warnings in browser console
- `curl` the page URL and compare rendered HTML to client-rendered DOM

---

## 4. Styling / Layout Diagnosis

### Entry Point
User reports visual regressions, missing styles, layout shifts, or Tailwind classes not applying.

### Investigation Steps

1. **Determine the styling system in use.**
   - Tailwind v4 CSS-first (`@theme` in CSS, no `tailwind.config.js`)
   - Tailwind v3 (`tailwind.config.js` with `content` array)
   - Scoped Svelte styles (`<style>` block)
   - Global CSS (`app.css` or similar)

2. **For Tailwind issues:**
   - Check `app.css` for `@import "tailwindcss"` (v4) or `@tailwind base/components/utilities` (v3).
   - Check `@source` directives (v4) or `content` array (v3) -- do they include the affected file paths?
   - Check for Tailwind v3 config present alongside v4 -- this causes conflicts.
   - Check `vite.config.ts` for `@tailwindcss/vite` plugin (v4) or `postcss` config (v3).

3. **For scoped style issues:**
   - Check if styles in `<style>` are being applied to dynamically rendered content (Svelte scopes styles to static template elements only).
   - Check for `:global()` usage where scoped styles need to reach into child components.
   - Check specificity conflicts between scoped styles and Tailwind utilities.

4. **For layout issues:**
   - Check parent container dimensions and `display` property.
   - Check for missing `box-sizing: border-box` (Tailwind's preflight includes this).
   - Check media queries and responsive breakpoints.

5. **Check SSR styling.**
   - Styles applied via JavaScript (e.g., `style:` directive based on `$state`) may flash on hydration if SSR renders without the computed value.

### Common Root Causes
- Tailwind content/source paths not including the affected `.svelte` files
- Mixed Tailwind v3 config and v4 CSS-first setup
- Svelte scoped styles not reaching dynamically injected HTML (use `:global()`)
- CSS specificity conflict: Tailwind utility overridden by scoped style or vice versa
- Missing `@tailwindcss/vite` plugin in `vite.config.ts`

### Verification
- Inspect computed styles in browser DevTools to confirm correct cascade
- `npx vite build` succeeds without CSS-related warnings

---

## 5. Hardware / Tauri IPC Failure Diagnosis

### Entry Point
User reports Tauri `invoke()` failures, permission errors, or hardware device access issues in a Tauri 2 + SvelteKit app.

### Investigation Steps

1. **Capture the Tauri error output.**
   - Browser console errors from `invoke()` calls.
   - Tauri backend logs (Rust panic traces, `tauri::Error` messages).
   - Check `src-tauri/tauri.conf.json` for permission configuration.

2. **Check the IPC contract.**
   - Read the Rust command definition in `src-tauri/src/lib.rs` or `src-tauri/src/main.rs`.
   - Compare the command signature (parameter names, types) with the frontend `invoke()` call.
   - Tauri 2 uses `#[tauri::command]` attribute. Check for: missing `async`, wrong return type, parameter name mismatch.

3. **Check Tauri 2 permissions.**
   - `src-tauri/capabilities/` directory: JSON files defining which commands and scopes are allowed.
   - `src-tauri/tauri.conf.json` under `app.security.capabilities`.
   - Missing permission = silent failure or cryptic "command not found" error.

4. **Check plugin configuration (if using Tauri plugins).**
   - Plugins like `tauri-plugin-fs`, `tauri-plugin-shell` require explicit permission grants.
   - Check `Cargo.toml` for plugin dependencies and `tauri.conf.json` for plugin registration.

5. **Check for SSR interference.**
   - `@tauri-apps/api` imports fail during SSR because Tauri's IPC bridge is browser-only.
   - All Tauri imports must be guarded with `browser` check or used only in `onMount` / client-only code.

### Common Root Causes
- `invoke()` parameter names don't match Rust command parameter names (case-sensitive)
- Missing capability/permission in `src-tauri/capabilities/*.json`
- Tauri API imported at module scope, failing during SSR
- Rust command panics silently -- check Tauri backend logs
- Plugin registered in `Cargo.toml` but not initialized in `tauri::Builder`

### Verification
- `cargo build` in `src-tauri/` succeeds
- `invoke()` returns expected data in browser console
- Tauri dev logs show no permission denial messages

---

## 6. Test Failure Root-Cause Diagnosis

### Entry Point
User reports Vitest unit test failures or Playwright E2E test failures.

### Investigation Steps

1. **Capture the full test output.**
   - Read the test runner output: assertion message, expected vs. received, file and line number.
   - Distinguish: assertion failure, timeout, setup error, import error.

2. **Read the failing test file.**
   - Understand what the test is asserting.
   - Check test setup: `beforeEach`, `afterEach`, mock configuration.
   - For Svelte component tests: check if `@testing-library/svelte` is using the Svelte 5 compatible version.

3. **Read the source file under test.**
   - Compare the test's expectations against actual component/function behavior.
   - Check for recent changes to the source that invalidated test assumptions.

4. **For Vitest unit tests:**
   - Check `vitest.config.ts` or `vite.config.ts` for test configuration.
   - Check `environment` setting: `jsdom` or `happy-dom` for component tests.
   - Check for missing Svelte preprocessor or compiler plugin in test config.
   - Check for `$state` / `$derived` usage in components -- test environment must support runes.

5. **For Playwright E2E tests:**
   - Check if the dev server is running or if Playwright is configured to start it (`webServer` in `playwright.config.ts`).
   - Check selectors: are they using `data-testid`, text content, or fragile CSS selectors?
   - Check for race conditions: missing `await`, `expect(...).toBeVisible()` without `waitFor`.
   - Check viewport/device configuration in `playwright.config.ts`.

6. **Check for environment mismatches.**
   - Test passes locally but fails in CI: check Node.js version, OS differences, environment variables.
   - Flaky test: check for timing dependencies, uncontrolled external state, or shared test fixtures.

### Common Root Causes
- `@testing-library/svelte` version incompatible with Svelte 5 runes
- Missing `@sveltejs/vite-plugin-svelte` in Vitest config (components don't compile)
- Playwright selector targeting text that changed due to a UI update
- Test assumes synchronous state update but Svelte batches updates (need `tick()` or `await`)
- Missing mock for `$app/environment`, `$app/navigation`, or other SvelteKit modules

### Verification
- `npm run test -- --run` (Vitest) or `npx playwright test` passes
- Failing test in isolation: `npm run test -- --run path/to/test.ts`

---

## 7. Build / Bundle Failure Diagnosis

### Entry Point
User reports `vite build` failures, dependency resolution errors, or chunk size warnings.

### Investigation Steps

1. **Capture the full build output.** Read `vite build` or `npm run build` output. Focus on the first error -- subsequent errors are often cascading.

2. **Classify the build error:**
   - **Module not found**: Missing dependency, wrong import path, misconfigured alias.
   - **Plugin error**: Svelte/Tailwind/PostCSS plugin failure.
   - **Type error**: TypeScript compilation failure during build.
   - **Chunk error**: Circular dependency, dynamic import failure.
   - **Adapter error**: SvelteKit adapter misconfiguration.

3. **Check config files in order:** `package.json` (dependencies, `type: "module"`), `vite.config.ts` (`sveltekit()` plugin, `optimizeDeps`, `ssr.noExternal`), `svelte.config.js` (adapter, `vitePreprocess()`, `kit.alias`).

4. **Check for ESM/CJS conflicts.** CJS-only dependencies may need `ssr.noExternal`. Check `exports` field in the dependency's `package.json`.

5. **Check adapter requirements.** `adapter-static` requires all routes to be prerenderable. `adapter-node` needs `origin`/`protocol_header` for production.

### Common Root Causes
- Missing `@sveltejs/vite-plugin-svelte` or `sveltekit()` in Vite config
- CJS-only dependency without `ssr.noExternal`
- Circular import between route files and `$lib` modules
- `adapter-static` with server-side routes (incompatible)
- Stale `node_modules` after major upgrade (recommend `rm -rf node_modules && npm install`)

### Verification
- `npm run build` exits 0, `npm run preview` serves without errors

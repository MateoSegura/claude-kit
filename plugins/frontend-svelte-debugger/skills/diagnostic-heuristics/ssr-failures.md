# SSR Failures — SvelteKit

Patterns for diagnosing hydration mismatches, load function errors, prerender failures, and adapter-specific issues.

---

## Hydration Mismatch

### Signature

Browser console error: `ERR_SVELTE_HYDRATION_MISMATCH` or `hydration_mismatch`

In development mode, Svelte logs a detailed `console.error` with the offending HTML before the mismatch error. This is the primary diagnostic artifact.

### Common Causes

**Cause 1 — Browser API access at module scope or component init**:

```svelte
<!-- BAD: window not available on server -->
<script lang="ts">
  const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
</script>
<div class:dark={isDark}>...</div>
```

Server renders `isDark = false` (window is undefined → error, or undefined → false). Browser evaluates `isDark = true`. HTML differs → mismatch.

**Fix**:
```svelte
<script lang="ts">
  import { browser } from '$app/environment';
  let isDark = $state(false);

  $effect(() => {
    // Only runs in browser — after hydration
    isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
</script>
```

Or disable SSR for the route: `export const ssr = false;` in `+page.ts`.

---

**Cause 2 — Invalid HTML nesting**:

```svelte
<!-- BAD: <p> cannot contain block elements -->
<p>
  <div>This is inside p</div>
</p>
```

The browser auto-repairs invalid HTML during parsing, producing different DOM structure than what Svelte expects from SSR output.

**Fix**: Replace `<p>` with `<div>`, or remove the block element from the paragraph.

---

**Cause 3 — `{@html}` with dynamic content**:

```svelte
<div>{@html userMarkdown}</div>
```

If `userMarkdown` differs between server render and client (e.g., loaded from `localStorage` client-side), hydration sees a mismatch.

**Fix**: Ensure `{@html}` content is identical on server and client, OR disable SSR for the component containing `{@html}` using `browser` guard:

```svelte
{#if browser}
  <div>{@html userMarkdown}</div>
{/if}
```

---

**Cause 4 — `$state(await ...)` pattern**:

```svelte
<!-- BUG: using await in $state init -->
let data = $state(await fetchData());
```

`$state` initializers run synchronously. Using `await` inside a `$state()` call does not work as intended — it causes serialization failures during SSR hydration.

**Fix**:
```svelte
let data = $state<DataType | null>(null);
$effect(() => {
  fetchData().then(d => { data = d; });
});
```

Or load data in `+page.server.ts` and pass via `data` prop.

---

**Cause 5 — `export const ssr = false` in layout file**:

If `+layout.ts` exports `ssr = false`, it disables SSR for the entire layout segment, but the layout itself may still try to hydrate against SSR markup that was never generated, producing mismatch warnings.

**Fix**: If SSR is disabled, ensure `+layout.svelte` and all children are fully client-rendered. Add `export const csr = true; export const ssr = false;` consistently.

---

## Load Function Errors

### Error: "Cannot read properties of undefined (reading 'x')"

**Cause**: Load function returns data, but a nested property is accessed before null-checking in the component. TypeScript strict mode should catch this, but may be disabled.

**Diagnosis**: Check `$types.ts` — run `npx svelte-check` to see if TypeScript caught the null access.

**Fix**: Add null guards in the component, or ensure load function always returns the expected shape.

---

### Error: "redirect called inside load function but not thrown"

**Symptom**: `redirect()` was called but the page didn't navigate.

**Cause**: `redirect()` must be thrown, not returned.

```typescript
// BAD
export const load = () => {
  redirect(307, '/login');  // no effect — redirect is thrown, not returned
};

// GOOD
export const load = () => {
  throw redirect(307, '/login');
};
```

---

### Error: Load function runs twice / double fetch

**Cause**: Using a universal load function (`+page.ts` instead of `+page.server.ts`) — runs on server during SSR AND on client during navigation. If the universal load function calls an internal API via `fetch`, this is expected and correct behavior.

**Diagnosis**: If the double-run is causing duplicate side effects (e.g., double-writing to a database), move mutation logic to `+page.server.ts`.

---

### Error: "fetch is not defined" in load function

**Cause**: Using the global `fetch` instead of the SvelteKit-provided `fetch` parameter in load functions.

```typescript
// BAD: global fetch — not available in Node.js environments without polyfill
export const load = async () => {
  const data = await fetch('/api/items').then(r => r.json());
};

// GOOD: use the fetch parameter — SvelteKit-patched, handles credentials and relative URLs
export const load = async ({ fetch }) => {
  const data = await fetch('/api/items').then(r => r.json());
};
```

---

## Prerender Failures

### Error: "Route not found during prerender"

**Symptom**: `adapter-static` fails with `404` when prerendering a dynamic route.

**Cause**: Dynamic routes (e.g., `/items/[id]`) require all IDs to be known at build time. SvelteKit cannot crawl dynamic paths automatically.

**Fix**: Implement `entries()` in the route's `+page.ts` to enumerate all paths:

```typescript
// src/routes/items/[id]/+page.ts
export const entries = async () => {
  const ids = await getItemIds();  // fetch all valid IDs
  return ids.map(id => ({ id }));
};
```

---

### Error: "Cannot prerender page that uses form actions"

**Cause**: Pages with `export const actions` (form actions) cannot be prerendered — they require a server to handle POST requests.

**Fix**: Either remove the form action and use client-side fetch, or disable prerendering for that route:

```typescript
export const prerender = false;
```

---

## Adapter-Specific Gotchas

### adapter-node

| Issue | Cause | Fix |
|-------|-------|-----|
| Form actions return wrong URLs | `ORIGIN` env var not set | Set `ORIGIN=https://your-domain.com` before starting |
| `path.join` fails on URLs | Using Node.js path module for URL paths | Use URL constructor: `new URL('/path', request.url).pathname` |
| Health check returns 404 | No `/health` route defined | Add `+server.ts` at `src/routes/health/` |
| Static files not served | `adapter-node` does not serve static files in production | Use a reverse proxy (nginx, Caddy) to serve `build/client/` |

### adapter-static

| Issue | Cause | Fix |
|-------|-------|-----|
| Dynamic routes 404 on direct navigation | SPA fallback not configured | Set `fallback: '404.html'` in adapter config for SPAs |
| API routes fail at build | Static adapter does not support server routes | Move API logic to external service or use `+page.server.ts` with prerender |
| `$app/environment.browser` is always true | All code runs client-side — correct behavior | Not a bug; gate server-only imports with `if (!browser) return` |
| Trailing slash mismatch | `trailingSlash` setting inconsistent | Set `trailingSlash: 'always'` or `'never'` consistently in `svelte.config.js` and CDN/server config |

---

## Diagnosing SSR Failures — Checklist

1. **Read the dev console error first** — Svelte dev mode logs the differing HTML before the mismatch error
2. **Reproduce with SSR enabled** — `npm run dev` (SSR on by default)
3. **Add `browser` guards** for any code accessing `window`, `document`, `localStorage`, `navigator`
4. **Check `+layout.ts`** for `ssr = false` that might affect child routes
5. **Validate HTML** — use browser dev tools "Elements" panel to confirm the rendered HTML is semantically valid
6. **Run `npx vite build && node build`** to test production SSR if dev mode works but prod fails

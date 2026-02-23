---
name: coding-frontend-svelte-engineer:performance
description: "Performance optimization reference for Svelte 5 / SvelteKit applications. Covers bundle analysis, code splitting strategies, SSR/CSR/prerender decision matrix, image and font optimization, Core Web Vitals targets, performance budgets, and reactive performance. Load this when implementing features, reviewing bundles, or auditing rendering strategies."
user-invocable: false
---

# Performance Optimization — Svelte 5 / SvelteKit

Quick reference for building performant Svelte applications. See [reference.md](reference.md) for Vite config, adapter-specific optimizations, and reactive internals. See [examples.md](examples.md) for concrete before/after code.

## Performance Budgets (Enforce on Every Feature)

| Metric | Target | Hard Limit |
|--------|--------|------------|
| Initial JS (gzipped) | < 150 KB | 200 KB |
| Initial CSS (gzipped) | < 30 KB | 50 KB |
| LCP | < 2.5s | 4.0s |
| INP | < 200ms | 500ms |
| CLS | < 0.1 | 0.25 |
| TTI (3G) | < 3.5s | 5.0s |

Run `pnpm build && pnpm vite-bundle-visualizer` after implementing to verify.

## SSR / CSR / Prerender Decision Matrix

| Scenario | Strategy | SvelteKit Config |
|----------|----------|-----------------|
| Marketing page, blog post | Prerender (static) | `export const prerender = true` in `+page.ts` |
| Dashboard, auth-gated UI | SSR on every request | Default (no config needed) |
| Heavy interactive widget | CSR-only | `export const ssr = false` in `+layout.ts` or `+page.ts` |
| E-commerce product page | ISR / revalidate | `export const config = { isr: { expiration: 60 } }` (Vercel) |
| Offline-capable PWA | SSR + service worker | adapter-static + service worker |
| Desktop app (Tauri/Electron) | SPA (CSR only) | `export const ssr = false` in root `+layout.ts` |

## Code Splitting Quick Reference

SvelteKit splits routes automatically. Additional splitting patterns:

```svelte
<!-- Lazy-load heavy component -->
<script lang="ts">
  const HeavyChart = () => import('$lib/components/HeavyChart.svelte');
</script>

{#await HeavyChart() then { default: HeavyChart }}
  <HeavyChart {data} />
{/await}
```

```typescript
// Manual chunk in vite.config.ts for shared vendor code
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'chart-vendor': ['chart.js', 'd3'],
        }
      }
    }
  }
});
```

## Image Optimization

Use SvelteKit's enhanced image support (requires `@sveltejs/enhanced-img`):

```svelte
<script lang="ts">
  import { enhanced } from '@sveltejs/enhanced-img';
</script>

<!-- Automatically generates WebP/AVIF, srcset, and correct dimensions -->
<enhanced:img src="./hero.jpg" alt="Hero image" loading="lazy" />
```

For dynamic images: use `srcset` with explicit widths, always set `width` and `height`, use `loading="lazy"` for below-fold images.

## Font Loading Strategy

```html
<!-- In app.html — preload critical fonts -->
<link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>
```

```css
/* In app.css */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-var.woff2') format('woff2');
  font-display: swap; /* Required — prevents invisible text */
  font-weight: 100 900; /* Variable font range */
}
```

Prefer variable fonts (single file, full range). Subset fonts for non-Latin scripts.

## SvelteKit Preloading Strategies

```html
<!-- Preload data on hover (default behavior) -->
<a href="/dashboard" data-sveltekit-preload-data="hover">Dashboard</a>

<!-- Preload on viewport entry (aggressive) -->
<a href="/products" data-sveltekit-preload-data="viewport">Products</a>

<!-- Disable preloading for auth-sensitive routes -->
<a href="/admin" data-sveltekit-preload-data="off">Admin</a>

<!-- Preload JS but not data -->
<a href="/editor" data-sveltekit-preload-code="hover">Editor</a>
```

## Reactive Performance Rules

1. Prefer `$derived` over `$effect` for computed values — `$derived` is lazy, `$effect` is eager.
2. Use `$state.raw` for large arrays/objects you replace wholesale (avoids deep proxy overhead).
3. Use keyed `{#each}` for lists that reorder: `{#each items as item (item.id)}`.
4. Avoid reactive state in module scope for server-shared state (SSR safety).
5. Use `$effect.root` when you need an effect that outlives the component.

## Streaming for Slow APIs

```typescript
// +page.server.ts — stream non-critical data
export async function load() {
  return {
    critical: await getCriticalData(),      // awaited: blocks render
    secondary: getSecondaryData(),           // not awaited: streams in
  };
}
```

```svelte
<!-- +page.svelte -->
<script lang="ts">
  let { data } = $props();
</script>

{#await data.secondary}
  <Skeleton />
{:then secondary}
  <SecondaryPanel {secondary} />
{/await}
```

## Bundle Analysis Workflow

```bash
# Install visualizer
pnpm add -D rollup-plugin-visualizer

# Add to vite.config.ts, then:
pnpm build
# Opens stats.html in browser showing chunk sizes and dependencies
```

Check: no single chunk > 100 KB gzipped; no accidental server-only module in client bundle; chart/icon libraries properly tree-shaken.

## Additional Resources

- [reference.md](reference.md) — Vite optimization config, adapter-specific tuning, service worker strategies, tree-shaking tips
- [examples.md](examples.md) — Complete code examples: lazy loading, image optimization, font loading, web-vitals instrumentation, bundle analysis scripts

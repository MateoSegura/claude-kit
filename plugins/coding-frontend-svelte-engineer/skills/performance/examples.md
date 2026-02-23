# Performance Examples — Concrete Code

## Route-Level Code Splitting

SvelteKit splits routes automatically. Each route's JS loads only when the user navigates to it. Verify in the build output:

```bash
pnpm build
# Look for per-route chunks in .svelte-kit/output/client/_app/immutable/chunks/
```

## Lazy Component Loading Pattern

```svelte
<!-- src/routes/dashboard/+page.svelte -->
<script lang="ts">
  // Heavy chart component — only loads when dashboard route is visited
  // and further deferred until the Promise resolves
  const ChartModule = import('$lib/components/AnalyticsChart.svelte');
</script>

{#await ChartModule}
  <!-- Show skeleton while JS loads -->
  <div class="h-64 animate-pulse bg-surface-200 rounded-lg" aria-busy="true" />
{:then { default: AnalyticsChart }}
  <AnalyticsChart {data} />
{:catch error}
  <p class="text-error-500">Failed to load chart: {error.message}</p>
{/await}
```

## Image Optimization Component

```svelte
<!-- src/lib/components/ResponsiveImage.svelte -->
<script lang="ts">
  interface Props {
    src: string;
    alt: string;
    widths?: number[];
    sizes?: string;
    loading?: 'lazy' | 'eager';
    class?: string;
  }

  let {
    src,
    alt,
    widths = [320, 640, 960, 1280],
    sizes = '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw',
    loading = 'lazy',
    class: className = '',
  }: Props = $props();

  // Generate srcset string from widths
  let srcset = $derived(
    widths.map(w => `${src}?w=${w} ${w}w`).join(', ')
  );
</script>

<img
  {src}
  {alt}
  {srcset}
  {sizes}
  {loading}
  decoding="async"
  class={className}
/>
```

## Font Loading with Preload and Fallback

```html
<!-- src/app.html -->
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />

    <!-- Preload critical variable font -->
    <link
      rel="preload"
      href="/fonts/inter-var.woff2"
      as="font"
      type="font/woff2"
      crossorigin="anonymous"
    />

    %sveltekit.head%
  </head>
  <body data-sveltekit-preload-data="hover">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
```

```css
/* src/app.css */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-var.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;  /* Show fallback font immediately, swap when loaded */
}

/* Size-adjust to minimize CLS when swapping to web font */
@font-face {
  font-family: 'Inter Fallback';
  src: local('Arial');
  size-adjust: 96.7%;
  ascent-override: 90%;
  descent-override: 22.43%;
  line-gap-override: 0%;
}

:root {
  font-family: 'Inter', 'Inter Fallback', system-ui, sans-serif;
}
```

## Service Worker Registration for PWA

```svelte
<!-- src/routes/+layout.svelte -->
<script lang="ts">
  import { browser } from '$app/environment';
  import { onMount } from 'svelte';

  onMount(async () => {
    if (!browser || !('serviceWorker' in navigator)) return;

    try {
      const registration = await navigator.serviceWorker.register('/service-worker.js', {
        type: 'module',  // Use ES modules in service worker
      });

      // Check for updates every 60 seconds
      setInterval(() => registration.update(), 60_000);

      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        newWorker?.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // Notify user that update is available
            showUpdateBanner();
          }
        });
      });
    } catch (error) {
      console.error('Service worker registration failed:', error);
    }
  });

  function showUpdateBanner() {
    // Implement your update notification UI
  }
</script>
```

## Performance Monitoring Setup

```typescript
// src/lib/performance.ts
import { onCLS, onINP, onLCP, onFCP, onTTFB, type Metric } from 'web-vitals';
import { browser } from '$app/environment';

interface VitalsReport {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  navigationType: string;
}

function sendVital(metric: Metric) {
  const report: VitalsReport = {
    name: metric.name,
    value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
    rating: metric.rating,
    delta: Math.round(metric.delta),
    navigationType: metric.navigationType,
  };

  // Send to analytics endpoint
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/vitals', JSON.stringify(report));
  }
}

export function initVitals() {
  if (!browser) return;

  onCLS(sendVital);
  onINP(sendVital);
  onLCP(sendVital);
  onFCP(sendVital);
  onTTFB(sendVital);
}
```

```typescript
// src/routes/+layout.ts
import { initVitals } from '$lib/performance';
import { browser } from '$app/environment';

export function load() {
  if (browser) initVitals();
  return {};
}
```

## Bundle Analysis Workflow

```typescript
// vite.config.ts — add visualizer for analysis builds only
import { sveltekit } from '@sveltejs/kit/vite';
import { visualizer } from 'rollup-plugin-visualizer';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [
    sveltekit(),
    process.env.ANALYZE === 'true' && visualizer({
      open: true,
      gzipSize: true,
      brotliSize: true,
      filename: '.svelte-kit/stats.html',
      template: 'treemap',  // 'sunburst' | 'treemap' | 'network'
    }),
  ].filter(Boolean),
});
```

```bash
# Run analysis build
ANALYZE=true pnpm build

# Check specific chunk sizes
ls -lh .svelte-kit/output/client/_app/immutable/chunks/
```

## Before/After: Eliminating Unnecessary Effect

```svelte
<!-- BEFORE: $effect used for derived value (causes extra renders) -->
<script lang="ts">
  let items = $state<string[]>([]);
  let count = $state(0);

  $effect(() => {
    count = items.length;  // Unnecessary — this is a computed value
  });
</script>

<p>Total: {count}</p>
```

```svelte
<!-- AFTER: $derived is lazy and has zero overhead when not rendered -->
<script lang="ts">
  let items = $state<string[]>([]);
  let count = $derived(items.length);
</script>

<p>Total: {count}</p>
```

## Before/After: $state.raw for Large Replaced Datasets

```svelte
<!-- BEFORE: Deep proxy on every refresh (unnecessary for wholesale replace) -->
<script lang="ts">
  let rows = $state<Row[]>([]);

  async function refresh() {
    rows = await fetchAllRows();  // Proxifies entire array on each call
  }
</script>
```

```svelte
<!-- AFTER: $state.raw avoids deep proxy overhead -->
<script lang="ts">
  let rows = $state.raw<Row[]>([]);

  async function refresh() {
    rows = await fetchAllRows();  // Shallow assignment only
  }
</script>
```

## Streaming Load Pattern

```typescript
// src/routes/product/[id]/+page.server.ts
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, fetch }) => {
  // Critical: await this — page needs it to render
  const product = await getProduct(params.id);

  return {
    product,
    // Non-critical: don't await — streams in after initial render
    reviews: getReviews(params.id),
    recommendations: getRecommendations(product.category),
  };
};
```

```svelte
<!-- src/routes/product/[id]/+page.svelte -->
<script lang="ts">
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
</script>

<!-- Renders immediately with critical data -->
<ProductDetail product={data.product} />

<!-- Streams in asynchronously -->
{#await data.reviews}
  <ReviewsSkeleton />
{:then reviews}
  <ReviewsList {reviews} />
{/await}

{#await data.recommendations}
  <RecommendationsSkeleton />
{:then recommendations}
  <RecommendationGrid {recommendations} />
{/await}
```

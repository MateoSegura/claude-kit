# Performance Reference — Detailed Optimization Techniques

## Vite Configuration for Optimal Splitting

```typescript
// vite.config.ts
import { sveltekit } from '@sveltejs/kit/vite';
import { visualizer } from 'rollup-plugin-visualizer';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [
    sveltekit(),
    // Only include during analysis builds
    process.env.ANALYZE && visualizer({
      open: true,
      gzipSize: true,
      brotliSize: true,
      filename: 'stats.html',
    }),
  ].filter(Boolean),

  build: {
    // Target modern browsers for smaller output
    target: 'es2022',

    // Enable CSS code splitting per chunk
    cssCodeSplit: true,

    rollupOptions: {
      output: {
        // Manual chunks for stable vendor hashing (better caching)
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // Group chart libraries
            if (id.includes('chart.js') || id.includes('d3') || id.includes('echarts')) {
              return 'charts';
            }
            // Group date/utility libraries
            if (id.includes('date-fns') || id.includes('luxon')) {
              return 'date-utils';
            }
            // All other node_modules in vendor chunk
            return 'vendor';
          }
        },
        // Consistent chunk naming for long-term caching
        chunkFileNames: 'immutable/[name]-[hash].js',
        assetFileNames: 'immutable/[name]-[hash][extname]',
      }
    },

    // Increase warning threshold to avoid false positives
    chunkSizeWarningLimit: 600,
  },

  // Optimize dependencies pre-bundling
  optimizeDeps: {
    include: ['@sveltejs/kit', 'svelte'],
  },
});
```

## Adapter-Specific Optimizations

### adapter-static (SSG)

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: undefined,    // undefined = true SSG, '200.html' = SPA mode
      precompress: true,      // Generate .gz and .br files
      strict: true,           // Fail if any route can't be prerendered
    }),

    prerender: {
      crawl: true,            // Auto-discover routes from <a> links
      entries: ['*'],         // Include all routes
      handleHttpError: 'warn',
    }
  }
};
```

### adapter-node (SSR)

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-node';

export default {
  kit: {
    adapter: adapter({
      out: 'build',
      // Enable compression for production
      // (handled by your reverse proxy, not node itself)
    }),

    // Enable streaming responses
    output: {
      bundleStrategy: 'split',  // Route-based code splitting
    }
  }
};
```

### adapter-vercel

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-vercel';

export default {
  kit: {
    adapter: adapter({
      runtime: 'nodejs22.x',    // Latest Node.js runtime
      split: true,              // Per-route serverless functions (avoids cold start on unused routes)
    })
  }
};
```

```typescript
// Per-route edge/ISR config in +page.server.ts
export const config = {
  // Use edge runtime for latency-sensitive routes
  runtime: 'edge',

  // Or ISR with 60-second revalidation
  isr: {
    expiration: 60,
    bypassToken: process.env.BYPASS_TOKEN,
  }
};
```

### adapter-cloudflare

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-cloudflare';

export default {
  kit: {
    adapter: adapter({
      routes: {
        include: ['/*'],
        exclude: ['<all>'],  // Exclude static assets from worker routing
      },
      platformProxy: {
        configPath: 'wrangler.toml',
      }
    })
  }
};
```

```typescript
// Access Cloudflare bindings in +page.server.ts
export async function load({ platform }) {
  const { env } = platform as { env: Env };
  const data = await env.MY_KV.get('key');
  return { data };
}
```

## Reactive Performance Internals

### $state Proxy Overhead

`$state` creates a deep Proxy. For large datasets you replace (not mutate), use `$state.raw`:

```typescript
// BAD for large arrays you replace wholesale
let items = $state<Item[]>([]);
function refresh() {
  items = await fetchItems(); // Creates new proxy on every refresh
}

// GOOD — $state.raw avoids deep proxy on large arrays
let items = $state.raw<Item[]>([]);
function refresh() {
  items = await fetchItems(); // Shallow assignment, no proxy wrapping
}
```

### Fine-Grained Reactivity for Lists

```svelte
<script lang="ts">
  interface Todo {
    id: string;
    text: $state<string>;      // Each item has its own reactive state
    done: $state<boolean>;
  }

  let todos = $state<Todo[]>([]);
</script>

<!-- Key by id to preserve component instances across reorders -->
{#each todos as todo (todo.id)}
  <TodoItem {todo} />
{/each}
```

### $derived vs $effect Performance

| Aspect | $derived | $effect |
|--------|----------|---------|
| Evaluation | Lazy (only when read) | Eager (runs immediately on dependency change) |
| Overhead | Low — skips if not read | Higher — always runs |
| Use for | Computed values | DOM side effects, external subscriptions |
| Can return value | Yes | No (return = cleanup function) |
| Memory | Freed when no readers | Runs until cleanup or unmount |

```typescript
// BAD — using $effect for a computation
let fullName = $state('');
$effect(() => {
  fullName = `${firstName} ${lastName}`; // Unnecessary side effect
});

// GOOD — $derived is lazy and has no overhead when not read
let fullName = $derived(`${firstName} ${lastName}`);
```

### $derived.by for Complex Computations

```typescript
// Use $derived.by when you need a block, not an expression
let sortedAndFiltered = $derived.by(() => {
  const filtered = items.filter(item => item.active);
  return filtered.sort((a, b) => a.priority - b.priority);
});
```

## Service Worker Strategies for PWA

```typescript
// src/service-worker.ts
import { build, files, version } from '$service-worker';

const CACHE_NAME = `app-v${version}`;
const PRECACHE = [...build, ...files];  // Build output + static assets

// Install: cache all precacheable assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE))
  );
  // Activate immediately (skip waiting)
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// Fetch: cache-first for precached, network-first for API
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  if (url.pathname.startsWith('/api/')) {
    // Network-first for API calls
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
  } else {
    // Cache-first for static assets
    event.respondWith(
      caches.match(event.request).then(cached => cached ?? fetch(event.request))
    );
  }
});
```

## Tree-Shaking Optimization

### Avoid Barrel File Exports for Large Libraries

```typescript
// BAD — imports entire icon library
import { Icons } from '$lib/icons';

// GOOD — direct import, tree-shakeable
import ChevronDown from '$lib/icons/ChevronDown.svelte';
```

### Mark Side-Effect-Free Modules

```json
// package.json (for your own library)
{
  "sideEffects": false
}
```

```json
// package.json (specific files have side effects)
{
  "sideEffects": ["./src/app.css", "./src/polyfills.ts"]
}
```

### Dynamic Import for Route-Specific Heavy Libraries

```typescript
// In +page.ts (not +page.server.ts)
export async function load() {
  // Only loads chart.js when this route is visited
  const { Chart } = await import('chart.js');
  return { Chart };
}
```

## Web Vitals Measurement

```typescript
// src/lib/vitals.ts
import { onCLS, onFID, onLCP, onINP, onTTFB, type Metric } from 'web-vitals';

function sendToAnalytics(metric: Metric) {
  // Replace with your analytics provider
  console.table({
    name: metric.name,
    value: metric.value,
    rating: metric.rating,  // 'good' | 'needs-improvement' | 'poor'
  });
}

export function measureVitals() {
  onCLS(sendToAnalytics);
  onFID(sendToAnalytics);
  onLCP(sendToAnalytics);
  onINP(sendToAnalytics);
  onTTFB(sendToAnalytics);
}
```

```typescript
// In +layout.svelte or +layout.ts
import { measureVitals } from '$lib/vitals';
import { browser } from '$app/environment';
import { onMount } from 'svelte';

onMount(() => {
  if (browser) measureVitals();
});
```

## Preloading and Prefetching Strategies

### SvelteKit Link Options

| Attribute | Behavior | Best For |
|-----------|----------|----------|
| `data-sveltekit-preload-data="hover"` | Fetch data on hover | Default for most links |
| `data-sveltekit-preload-data="tap"` | Fetch data on touch start | Mobile-first apps |
| `data-sveltekit-preload-data="viewport"` | Fetch when link enters viewport | Content-heavy pages |
| `data-sveltekit-preload-data="off"` | No prefetching | Auth-sensitive links |
| `data-sveltekit-preload-code="eager"` | Load JS immediately | Critical path routes |

### Programmatic Preloading

```typescript
import { preloadData, preloadCode } from '$app/navigation';

// Preload on explicit user intent (e.g., opening a menu)
async function onMenuOpen() {
  await preloadData('/dashboard');
}
```

## Performance Checklist per Feature

Before marking a feature complete, verify:

- [ ] New routes have explicit prerender/SSR/CSR config
- [ ] Heavy components use dynamic import + `{#await}`
- [ ] Images use `<enhanced:img>` or explicit `srcset`
- [ ] New third-party libraries checked with `bundlephobia.com`
- [ ] `pnpm build` succeeds with no oversized chunk warnings
- [ ] Core Web Vitals not regressed (run Lighthouse in CI if available)
- [ ] No `console.log` left in production path
- [ ] `$derived` used instead of `$effect` for computed values

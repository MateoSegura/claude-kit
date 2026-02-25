---
name: core-frontend:web-performance
description: "Web performance optimization: Core Web Vitals (LCP, FID/INP, CLS), lazy loading, code splitting, image optimization, bundle analysis, critical rendering path, and caching strategies."
user-invocable: false
---

# Web Performance Quick Reference

## Core Web Vitals

The three metrics Google uses for page experience ranking:

| Metric | Measures | Good | Needs Improvement | Poor |
|--------|----------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | Loading speed | < 2.5s | 2.5-4.0s | > 4.0s |
| **INP** (Interaction to Next Paint) | Responsiveness | < 200ms | 200-500ms | > 500ms |
| **CLS** (Cumulative Layout Shift) | Visual stability | < 0.1 | 0.1-0.25 | > 0.25 |

### LCP — Largest Contentful Paint

The time until the largest visible element renders (hero image, heading, video poster).

**Common causes of poor LCP:**
- Slow server response (TTFB > 800ms)
- Render-blocking CSS/JS
- Large unoptimized images
- Client-side rendering delay
- Font loading blocking text display

**Fixes:**
1. Preload the LCP image: `<link rel="preload" as="image" href="hero.webp">`
2. Use `fetchpriority="high"` on the LCP image
3. Inline critical CSS, defer the rest
4. Use SSR or SSG for initial HTML
5. Set explicit `width`/`height` on images
6. Use `font-display: swap` or `optional`

### INP — Interaction to Next Paint

Replaced FID in March 2024. Measures the latency from user interaction to the next frame paint.

**Common causes of poor INP:**
- Long JavaScript tasks blocking the main thread
- Expensive re-renders on interaction
- Synchronous layout/style recalculation
- Large DOM trees (> 1500 nodes)

**Fixes:**
1. Break long tasks with `yield()` or `scheduler.yield()`
2. Use `requestAnimationFrame` for visual updates
3. Debounce expensive handlers (search, resize)
4. Virtualize long lists
5. Use CSS animations instead of JS-driven animations
6. Minimize DOM size

### CLS — Cumulative Layout Shift

How much the page layout shifts unexpectedly during loading.

**Common causes of poor CLS:**
- Images without dimensions
- Ads/embeds without reserved space
- Web fonts causing text reflow (FOIT/FOUT)
- Dynamic content inserted above viewport
- Late-loading CSS

**Fixes:**
1. Always set `width` and `height` on `<img>` and `<video>`
2. Use `aspect-ratio` CSS for responsive containers
3. Reserve space for ads/embeds with min-height
4. Use `font-display: optional` (eliminates FOUT)
5. Avoid inserting content above existing content
6. Use CSS `contain` for complex layouts

## Code Splitting

Split your JavaScript bundle so users only download what they need.

### Route-Based Splitting

Load each page's code only when navigating to it. Most frameworks do this automatically:

```javascript
// Dynamic import — creates a separate chunk
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));
```

### Component-Based Splitting

```javascript
// Load heavy components on interaction
const Editor = lazy(() => import('./components/RichEditor'));

function Page() {
  const [editing, setEditing] = useState(false);
  return editing ? <Editor /> : <button onClick={() => setEditing(true)}>Edit</button>;
}
```

### Splitting Guidelines

| Split when... | Don't split when... |
|---------------|---------------------|
| Route/page level components | Shared UI primitives (Button, Input) |
| Heavy third-party libs (editors, charts) | Small utility libraries |
| Admin-only features | Core app shell |
| Below-the-fold content | Above-the-fold content |
| Modals with complex content | Simple confirmation dialogs |

## Image Optimization

Images are typically the largest payload on a page.

### Format Selection

| Format | Best for | Browser support |
|--------|----------|----------------|
| **WebP** | Photos, illustrations | All modern browsers |
| **AVIF** | Photos (30% smaller than WebP) | Chrome, Firefox, Safari 16.4+ |
| **SVG** | Icons, logos, illustrations | Universal |
| **PNG** | Screenshots, images needing transparency | Universal |

### Responsive Images

Use `srcset` with width descriptors and `sizes` to serve the right image for each viewport. Always set `width`/`height` to prevent CLS. Above-the-fold images: eager load with `fetchpriority="high"`. Below-the-fold: `loading="lazy"` + `decoding="async"`.

## Lazy Loading

Use native `loading="lazy"` on `<img>` and `<iframe>`. For custom lazy loading, use `IntersectionObserver` with `rootMargin: '200px'` to start loading before the element enters the viewport.

## Critical Rendering Path

Optimize the HTML->DOM, CSS->CSSOM, Render Tree->Layout->Paint->Composite pipeline:

1. **Inline critical CSS** in `<head>` for above-the-fold content
2. **Defer non-critical CSS** via `<link rel="preload" as="style">`
3. **Defer JavaScript** with `<script defer>` or `<script async>`
4. Compress, minify, and tree-shake all assets

## Bundle Analysis

Audit bundles regularly with `webpack-bundle-analyzer`, `rollup-plugin-visualizer`, or `source-map-explorer`. Check `bundlephobia.com` before installing packages. Watch for duplicate dependencies, oversized imports, and dev-only code in production.

## Caching Strategies

### HTTP Cache Headers

| Strategy | Cache-Control | When to use |
|----------|---------------|-------------|
| **Immutable** | `max-age=31536000, immutable` | Hashed assets (app.a1b2c3.js) |
| **Revalidate** | `max-age=0, must-revalidate` | HTML pages, API responses |
| **Short cache** | `max-age=300` (5 min) | Frequently updated content |
| **No cache** | `no-store` | Sensitive data, auth pages |

### Service Worker Cache

```
Cache-first:    Check cache, fall back to network (static assets)
Network-first:  Try network, fall back to cache (API data)
Stale-while-revalidate: Return cache, update in background (best of both)
```

## Additional Resources

- [performance-reference.md](performance-reference.md) — Font loading strategies, resource hints (preload/prefetch/preconnect), third-party script management, runtime performance profiling, performance budgets, monitoring with Web Vitals API

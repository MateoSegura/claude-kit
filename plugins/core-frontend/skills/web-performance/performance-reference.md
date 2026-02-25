# Web Performance — Detailed Reference

## Font Loading Strategies

### Font Display Values

| Value | Behavior | Use when |
|-------|----------|----------|
| `swap` | Fallback shown immediately, swap when loaded | Body text (avoid invisible text) |
| `optional` | Use if available quickly, skip if not | Non-critical text (best CLS) |
| `fallback` | Short invisible period, then fallback | Headings |
| `block` | Invisible text up to 3s | Icon fonts only (never for text) |
| `auto` | Browser default | Never use explicitly |

### Optimal Font Loading

```html
<!-- Preload critical fonts -->
<link rel="preload" href="/fonts/Inter-Regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/Inter-Bold.woff2" as="font" type="font/woff2" crossorigin>
```

```css
@font-face {
  font-family: 'Inter';
  src: url('/fonts/Inter-Regular.woff2') format('woff2');
  font-weight: 400;
  font-display: swap;
  /* Subset to Latin characters if possible */
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC;
}
```

**Font optimization tips:**
- Use woff2 format (30% smaller than woff)
- Subset fonts to needed character ranges
- Limit font variations (2-3 weights max)
- Prefer system fonts for body text when possible
- Use `size-adjust` to minimize layout shift from font swap

### System Font Stack

```css
/* Modern system font stack — zero font loading */
body {
  font-family:
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    Roboto,
    'Helvetica Neue',
    Arial,
    sans-serif;
}
```

## Resource Hints

### Preload — High Priority Current Page Resources

```html
<!-- Load critical resources that the browser can't discover early -->
<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/hero.webp" as="image">
<link rel="preload" href="/critical.js" as="script">
```

### Prefetch — Low Priority Future Page Resources

```html
<!-- Likely next page — prefetch during idle time -->
<link rel="prefetch" href="/dashboard.js">
<link rel="prefetch" href="/api/user/profile">
```

### Preconnect — Early Connection Setup

```html
<!-- Establish connection to critical third-party origins -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://api.example.com" crossorigin>

<!-- dns-prefetch as fallback for older browsers -->
<link rel="dns-prefetch" href="https://analytics.example.com">
```

**When to use each:**

| Hint | When | Impact |
|------|------|--------|
| `preload` | Resource needed in current page, discovered late | High (saves discovery time) |
| `prefetch` | Resource likely needed on next navigation | Low priority (idle time) |
| `preconnect` | Third-party origin, known early | Medium (saves DNS + TLS) |
| `dns-prefetch` | Many third-party origins | Low (saves DNS only) |

## Third-Party Script Management

Third-party scripts (analytics, ads, widgets) are the #1 cause of performance regression.

### Loading Strategies

```html
<!-- Defer: download in parallel, execute after HTML parsing -->
<script src="analytics.js" defer></script>

<!-- Async: download in parallel, execute immediately when ready -->
<script src="tracker.js" async></script>

<!-- Lazy: load after page is interactive -->
<script>
  // Load non-critical scripts after page load
  window.addEventListener('load', () => {
    const script = document.createElement('script');
    script.src = 'chat-widget.js';
    document.body.appendChild(script);
  });
</script>
```

### Third-Party Audit Checklist

- [ ] Is this script actually needed?
- [ ] What is its total size (JS + CSS + fonts + images)?
- [ ] Does it block rendering?
- [ ] Can it be loaded lazily (after interaction)?
- [ ] Does it add to CLS (injecting elements)?
- [ ] Does it make additional network requests?
- [ ] Is there a lighter alternative?

### Facade Pattern

Show a static placeholder, load the real widget on interaction:

```html
<!-- YouTube embed: show thumbnail, load player on click -->
<div class="youtube-facade" onclick="loadYouTube(this)" data-id="VIDEO_ID">
  <img src="https://i.ytimg.com/vi/VIDEO_ID/hqdefault.jpg" alt="Video title">
  <button aria-label="Play video">Play</button>
</div>
```

## Runtime Performance

### Long Tasks

Any JavaScript task taking > 50ms is a "long task" that blocks the main thread.

**Detection:**
```javascript
// PerformanceObserver for long tasks
const observer = new PerformanceObserver((list) => {
  list.getEntries().forEach(entry => {
    console.warn('Long task detected:', entry.duration, 'ms');
  });
});
observer.observe({ type: 'longtask', buffered: true });
```

**Solutions:**
1. Break work into chunks with `scheduler.yield()` or `setTimeout(fn, 0)`
2. Move computation to Web Workers
3. Use `requestIdleCallback` for non-urgent work
4. Virtualize large lists
5. Debounce/throttle event handlers

### Layout Thrashing

Reading layout properties (offsetHeight, getBoundingClientRect) forces the browser to recalculate layout synchronously.

```javascript
// BAD: layout thrashing (read-write-read-write)
elements.forEach(el => {
  const height = el.offsetHeight;    // forces layout
  el.style.height = height + 10 + 'px'; // invalidates layout
});

// GOOD: batch reads, then batch writes
const heights = elements.map(el => el.offsetHeight); // all reads
elements.forEach((el, i) => {
  el.style.height = heights[i] + 10 + 'px'; // all writes
});
```

### Animation Performance

Prefer properties that only trigger compositing (not layout or paint):

| Property | Triggers | Performance |
|----------|----------|-------------|
| `transform` | Composite only | Best |
| `opacity` | Composite only | Best |
| `filter` | Paint + composite | Good |
| `background-color` | Paint + composite | Good |
| `width`, `height` | Layout + paint + composite | Worst |
| `top`, `left` | Layout + paint + composite | Worst |

```css
/* Use transform instead of top/left for animations */
.animate {
  /* Bad */
  /* top: 100px; */

  /* Good */
  transform: translateY(100px);
  will-change: transform; /* hint to browser, use sparingly */
}
```

## Performance Budgets

Set limits to prevent performance regression:

| Metric | Budget |
|--------|--------|
| Total JavaScript (compressed) | < 200KB |
| Total CSS (compressed) | < 50KB |
| Total page weight | < 1MB |
| LCP | < 2.5s |
| INP | < 200ms |
| CLS | < 0.1 |
| Time to Interactive | < 3.5s |
| Lighthouse Performance score | > 90 |

### Enforcing Budgets

```javascript
// bundlesize / size-limit config
// Fail CI if bundle exceeds budget
{
  "budgets": [
    { "path": "dist/main.*.js", "maxSize": "150KB" },
    { "path": "dist/vendor.*.js", "maxSize": "80KB" },
    { "path": "dist/**/*.css", "maxSize": "30KB" }
  ]
}
```

## Monitoring with Web Vitals API

```javascript
import { onLCP, onINP, onCLS } from 'web-vitals';

function sendToAnalytics({ name, value, id }) {
  // Send to your analytics endpoint
  navigator.sendBeacon('/api/vitals', JSON.stringify({
    metric: name,
    value: Math.round(value),
    id,
    page: location.pathname,
  }));
}

onLCP(sendToAnalytics);
onINP(sendToAnalytics);
onCLS(sendToAnalytics);
```

**Monitoring best practices:**
- Track real user metrics (RUM), not just lab tests
- Monitor p75 values (75th percentile), not averages
- Set up alerts for regression (> 10% degradation)
- Segment by device type, connection speed, and geography
- Compare against performance budgets weekly

## Performance Testing Tools

| Tool | Type | Best for |
|------|------|----------|
| Lighthouse | Lab | Automated audits, CI integration |
| PageSpeed Insights | Lab + Field | Quick check with real user data |
| Chrome DevTools Performance tab | Lab | Deep profiling, flame charts |
| WebPageTest | Lab | Waterfall analysis, filmstrip |
| web-vitals (npm) | Field | Real user monitoring |
| Chrome UX Report (CrUX) | Field | Real user data at scale |
| Bundlephobia | Build | Package size before installing |
| Bundle analyzer | Build | Visual treemap of bundle contents |

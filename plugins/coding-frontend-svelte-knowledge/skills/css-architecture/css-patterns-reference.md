# CSS Architecture — Detailed Patterns Reference

## Component-Level Theming with CSS Custom Properties

### The Prop-to-Variable Pattern

Components expose a CSS API via custom property fallbacks:

```svelte
<!-- Button.svelte -->
<style>
  .btn {
    /* Each property has a component-scoped var with a semantic fallback */
    display: inline-flex;
    align-items: center;
    gap: var(--btn-gap, var(--space-2));
    padding: var(--btn-py, var(--space-2)) var(--btn-px, var(--space-4));
    font-size: var(--btn-font-size, var(--font-size-base));
    font-weight: var(--btn-font-weight, 600);
    border-radius: var(--btn-radius, var(--radius-md));
    border: var(--btn-border, 1px solid transparent);
    background: var(--btn-bg, var(--color-brand));
    color: var(--btn-fg, white);
    cursor: pointer;
    transition: background 120ms ease, box-shadow 120ms ease;

    &:hover {
      background: var(--btn-bg-hover, color-mix(in oklch, var(--btn-bg, var(--color-brand)) 85%, black));
    }

    &:focus-visible {
      outline: 2px solid var(--color-brand);
      outline-offset: 2px;
    }

    &:active {
      transform: scale(0.98);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      pointer-events: none;
    }
  }
</style>

<button class="btn" {...$props()}>
  {@render children?.()}
</button>
```

```svelte
<!-- Usage: override via CSS variables -->

<!-- Svelte style-props syntax -->
<Button --btn-bg="oklch(55% 0.18 145)" --btn-radius="9999px">
  Success
</Button>

<!-- Or via class + CSS variables in parent scope -->
<style>
  .danger-zone :global(.btn) {
    --btn-bg: var(--color-error);
  }
</style>
```

### Variant System Using @layer

```css
/* In global.css or component stylesheet */
@layer components {
  .btn { /* base styles */ }
  .btn--ghost {
    --btn-bg: transparent;
    --btn-border: 1px solid var(--color-border);
    --btn-fg: var(--color-fg);
    --btn-bg-hover: var(--color-surface);
  }
  .btn--sm {
    --btn-py: var(--space-1);
    --btn-px: var(--space-2);
    --btn-font-size: var(--font-size-sm);
  }
  .btn--icon {
    --btn-px: var(--space-2);
    --btn-py: var(--space-2);
    aspect-ratio: 1;
  }
}
```

## Responsive Layout Patterns

### Fluid Grid

```css
/* Auto-fit grid — columns fill available space */
.auto-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));
  gap: var(--space-4);
}

/* Responsive sidebar layout */
.sidebar-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);

  @media (min-width: 768px) {
    grid-template-columns: 240px 1fr;
  }
}
```

### Stack Pattern (Flex Column with Consistent Gap)

```css
.stack { display: flex; flex-direction: column; }
.stack > * + * { margin-top: var(--stack-space, var(--space-4)); }

/* Variants */
.stack--tight { --stack-space: var(--space-2); }
.stack--loose { --stack-space: var(--space-8); }
```

### Center Pattern

```css
.center {
  box-sizing: content-box;
  max-width: var(--measure, 65ch);
  margin-inline: auto;
  padding-inline: var(--space-4);
}
```

## Logical Properties (Direction-Agnostic)

```css
/* Use logical properties for RTL support */
.card {
  /* Instead of margin-left/right */
  margin-inline: auto;
  padding-inline: var(--space-4);
  padding-block: var(--space-6);

  /* Instead of border-top/left */
  border-inline-start: 3px solid var(--color-brand);

  /* Instead of width/height */
  inline-size: 100%;
  max-inline-size: 600px;
  block-size: auto;
}
```

## Animation Patterns

### Entrance Animations

```css
@layer utilities {
  /* Only animate if user hasn't requested reduced motion */
  @media (prefers-reduced-motion: no-preference) {
    .animate-in {
      animation: slide-up 300ms cubic-bezier(0.4, 0, 0.2, 1) both;
    }

    .animate-in-delayed {
      animation: slide-up 300ms cubic-bezier(0.4, 0, 0.2, 1) 150ms both;
    }
  }

  @keyframes slide-up {
    from {
      opacity: 0;
      translate: 0 8px;
    }
    to {
      opacity: 1;
      translate: 0 0;
    }
  }

  @keyframes fade-in {
    from { opacity: 0; }
    to   { opacity: 1; }
  }
}
```

### Skeleton Loading Animation

```css
@keyframes shimmer {
  from { background-position: -200% center; }
  to   { background-position: 200% center; }
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-surface) 25%,
    color-mix(in oklch, var(--color-surface) 70%, var(--color-border)) 50%,
    var(--color-surface) 75%
  );
  background-size: 200% 100%;
  border-radius: var(--radius-sm);

  @media (prefers-reduced-motion: no-preference) {
    animation: shimmer 1.5s ease-in-out infinite;
  }
}

.skeleton--text  { height: 1em; width: 80%; }
.skeleton--title { height: 1.5em; width: 60%; }
.skeleton--avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}
```

## Focus Visible Styles

```css
/* Remove default outline, add custom :focus-visible */
* {
  outline: none;
}

:focus-visible {
  outline: 2px solid var(--color-brand);
  outline-offset: 2px;
  border-radius: 2px;
}

/* Interactive elements — ensure focus is always visible */
button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
[tabindex]:focus-visible {
  outline: 2px solid var(--color-brand);
  outline-offset: 2px;
}
```

## Typography Scale

```css
/* Perfect Fourth (1.333) type scale — for strong hierarchy */
:root {
  --font-size-xs:   clamp(0.563rem, 0.5vw + 0.45rem, 0.65rem);   /* 9px → 10.4px */
  --font-size-sm:   clamp(0.75rem,  0.7vw + 0.6rem,  0.875rem);  /* 12px → 14px */
  --font-size-base: clamp(1rem,     1vw + 0.75rem,   1.125rem);  /* 16px → 18px */
  --font-size-lg:   clamp(1.333rem, 1.4vw + 1rem,   1.5rem);    /* 21.3px → 24px */
  --font-size-xl:   clamp(1.777rem, 1.8vw + 1.3rem, 2rem);      /* 28.4px → 32px */
  --font-size-2xl:  clamp(2.369rem, 2.4vw + 1.7rem, 2.75rem);   /* 37.9px → 44px */

  /* Line heights */
  --leading-tight:  1.2;
  --leading-snug:   1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose:  2;

  /* Letter spacing */
  --tracking-tight: -0.02em;
  --tracking-normal: 0;
  --tracking-wide:  0.025em;
  --tracking-widest: 0.1em;
}
```

## Tailwind CSS v4 Integration

Tailwind v4 (2025) uses CSS-first configuration:

```css
/* app.css — Tailwind v4 configuration in CSS */
@import "tailwindcss";

@theme {
  /* Override Tailwind's design tokens */
  --color-brand: oklch(55% 0.18 250);
  --color-brand-50: oklch(97% 0.02 250);
  --color-brand-900: oklch(22% 0.08 250);

  --font-sans: 'Inter', system-ui, sans-serif;

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 16px;

  /* Custom spacing scale */
  --spacing-page: 2rem;
}
```

```svelte
<!-- Using Tailwind v4 with Svelte -->
<div class="flex gap-4 p-[--spacing-page] bg-brand-50 rounded-lg">
  <button class="bg-brand text-white px-4 py-2 rounded-md hover:bg-brand/85">
    Action
  </button>
</div>
```

## Print Styles

```css
@media print {
  /* Hide non-essential elements */
  nav, .sidebar, .footer, .btn, .modal { display: none !important; }

  /* Expand collapsed content */
  details { display: block; }
  summary { display: none; }

  /* Prevent page breaks inside key elements */
  h2, h3, h4 { break-after: avoid; }
  figure, table, pre { break-inside: avoid; }

  /* Show link URLs */
  a[href]::after {
    content: " (" attr(href) ")";
    font-size: 0.8em;
    color: oklch(40% 0 0);
  }

  /* Reset colors for ink */
  body { color: oklch(0% 0 0); background: white; }
}
```

## CSS Architecture File Organization

```
src/
├── app.css                    # @import all layers
├── lib/
│   └── styles/
│       ├── reset.css          # @layer reset
│       ├── tokens.css         # @layer tokens — all custom properties
│       ├── base.css           # @layer base — element defaults
│       ├── components.css     # @layer components — reusable patterns
│       └── utilities.css      # @layer utilities — single-purpose classes
```

```css
/* app.css */
@layer reset, tokens, base, components, utilities;

@import './lib/styles/reset.css' layer(reset);
@import './lib/styles/tokens.css' layer(tokens);
@import './lib/styles/base.css' layer(base);
@import './lib/styles/components.css' layer(components);
@import './lib/styles/utilities.css' layer(utilities);
```

## View Transitions — SvelteKit Integration

```typescript
// src/hooks.client.ts
import { onNavigate } from '$app/navigation';

onNavigate((navigation) => {
  // Only use view transitions if supported
  if (!document.startViewTransition) return;

  return new Promise((resolve) => {
    document.startViewTransition(async () => {
      resolve(); // allow SvelteKit to update DOM
      await navigation.complete;
    });
  });
});
```

```css
/* src/app.css — customize transition animations */
@media (prefers-reduced-motion: no-preference) {
  ::view-transition-old(root) {
    animation: 200ms ease-out both fade-out;
  }
  ::view-transition-new(root) {
    animation: 200ms ease-in both fade-in;
  }

  /* Slide transition for specific routes */
  ::view-transition-old(slide) {
    animation: 300ms ease-out both slide-to-left;
  }
  ::view-transition-new(slide) {
    animation: 300ms ease-in both slide-from-right;
  }

  @keyframes slide-to-left {
    to { transform: translateX(-100%); }
  }
  @keyframes slide-from-right {
    from { transform: translateX(100%); }
  }
}
```

```svelte
<!-- Mark elements for view transition -->
<style>
  .page-header {
    view-transition-name: page-header;
  }
</style>
```

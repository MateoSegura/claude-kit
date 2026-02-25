---
name: core-frontend:css-architecture
description: "Modern CSS architecture: design token systems with CSS custom properties, @layer cascade control, container queries, :has() selector, oklch color, fluid typography, View Transitions, and styling strategy tradeoffs."
user-invocable: false
---

# CSS Architecture Quick Reference

## Design Token Architecture

Use a 3-tier token hierarchy: primitive -> semantic -> component.

```css
/* 1. Primitive tokens — raw values, not used directly in components */
:root {
  /* Color primitives */
  --color-blue-50: oklch(97% 0.02 250);
  --color-blue-500: oklch(55% 0.18 250);
  --color-blue-900: oklch(25% 0.10 250);

  /* Spacing primitives */
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-4: 1rem;      /* 16px */
  --space-8: 2rem;      /* 32px */

  /* Typography primitives */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-size-base: 1rem;
}

/* 2. Semantic tokens — purpose-driven, use these in components */
:root {
  --color-brand: var(--color-blue-500);
  --color-bg: oklch(100% 0 0);
  --color-fg: oklch(15% 0 0);
  --color-surface: oklch(97% 0 0);
  --color-border: oklch(88% 0 0);
  --color-error: oklch(55% 0.20 30);
  --color-success: oklch(55% 0.15 145);

  --space-page: var(--space-8);
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 16px;
}

/* 3. Dark mode — override semantic tokens only */
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: oklch(12% 0 0);
    --color-fg: oklch(94% 0 0);
    --color-surface: oklch(18% 0 0);
    --color-border: oklch(30% 0 0);
  }
}
```

## @layer Cascade Control

```css
/* Declare layer order at the top of your stylesheet */
@layer reset, tokens, base, components, utilities;

@layer reset {
  *, *::before, *::after { box-sizing: border-box; margin: 0; }
}

@layer base {
  body {
    font-family: var(--font-sans);
    color: var(--color-fg);
    background: var(--color-bg);
  }
}

@layer components {
  .btn {
    padding: var(--space-2) var(--space-4);
    border-radius: var(--radius-md);
    border: 1px solid transparent;
  }
}

@layer utilities {
  /* Higher layers win over lower layers regardless of specificity */
  .mt-4 { margin-top: var(--space-4); }
  .text-sm { font-size: 0.875rem; }
}
```

## Container Queries — Context-Aware Components

```css
/* Make a container queryable */
.card-grid {
  container-type: inline-size;
  container-name: card-grid;
}

/* Component adapts to its container, not the viewport */
.card {
  display: grid;
  grid-template-rows: auto 1fr auto;
}

@container card-grid (min-width: 400px) {
  .card {
    grid-template-columns: 120px 1fr;
    grid-template-rows: auto;
  }
}

/* Named container queries */
@container sidebar (max-width: 200px) {
  .nav-label { display: none; }
}
```

## :has() — Parent Selection

```css
/* Form field with error */
.field:has(.error-message) label {
  color: var(--color-error);
}

/* Card with image — adjust layout */
.card:has(img) {
  padding-top: 0;
}

/* Navigation with open submenu */
.nav-item:has([aria-expanded="true"]) {
  background: var(--color-surface);
}

/* Table row highlighting */
tr:has(td:focus-within) {
  background: var(--color-surface);
}
```

## Fluid Typography with clamp()

```css
:root {
  --font-size-xs:   clamp(0.64rem,  0.6vw + 0.5rem, 0.72rem);
  --font-size-sm:   clamp(0.8rem,   0.8vw + 0.6rem, 0.9rem);
  --font-size-base: clamp(1rem,     1vw + 0.75rem,  1.125rem);
  --font-size-lg:   clamp(1.25rem,  1.2vw + 0.9rem, 1.4rem);
  --font-size-xl:   clamp(1.563rem, 1.5vw + 1.1rem, 1.75rem);
  --font-size-2xl:  clamp(1.953rem, 2vw + 1.3rem,   2.25rem);
  --font-size-3xl:  clamp(2.441rem, 2.5vw + 1.6rem, 3rem);
}

/* clamp(min, preferred, max) */
/* preferred = fluid value relative to viewport */
/* Scales from min at small viewport to max at large viewport */
```

## oklch Color System

`oklch(lightness% chroma hue)` is perceptually uniform — equal lightness steps look equally bright. Generate color scales by varying lightness at consistent intervals. Use `color-mix(in oklch, var(--color-brand) 85%, black)` for hover states and `oklch(0% 0 0 / 50%)` for alpha transparency.

## CSS Nesting (Native)

Native CSS nesting is supported in all modern browsers. Use `&` for pseudo-classes (`&:hover`), child selectors (`& .child`), and nest `@media` rules directly inside selectors.

## Styling Strategy Tradeoffs

| Approach | Strengths | Weaknesses | Best for |
|----------|-----------|------------|----------|
| **Tailwind CSS** | Fast prototyping, consistent tokens, small bundles | Verbose markup, learning curve | Teams wanting utility-first, rapid UI |
| **CSS Modules** | Scoped by default, plain CSS | No dynamic styles, extra files | Large apps needing isolation |
| **CSS-in-JS** (styled-components, Emotion) | Dynamic styles, co-located | Runtime cost, SSR complexity | Highly dynamic theming |
| **Vanilla CSS** (@layer + custom props) | Zero runtime, full CSS power | Manual scoping, no guardrails | Performance-critical, simple apps |
| **Framework scoped** (Svelte, Vue SFC) | Automatic scoping, no config | Framework-locked | Single-framework projects |

## Additional Resources

- [css-reference.md](css-reference.md) — Component-level theming, responsive layout patterns, logical properties, animation patterns, typography scale, print styles, View Transitions API, file organization

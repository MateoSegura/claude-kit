---
name: coding-frontend-svelte-knowledge:css-architecture
description: "Modern CSS architecture for Svelte: design token systems with CSS custom properties, @layer cascade control, container queries, :has() selector, oklch color, fluid typography, View Transitions, and Tailwind CSS integration patterns."
user-invocable: false
---

# CSS Architecture Quick Reference

## Design Token Architecture

Use a 3-tier token hierarchy: primitive → semantic → component.

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
  .btn--primary {
    background: var(--color-brand);
    color: oklch(100% 0 0);
  }
}

@layer utilities {
  /* High specificity wins — override component styles */
  .mt-4 { margin-top: var(--space-4); }
  .text-sm { font-size: 0.875rem; }
}
```

Higher layers win over lower layers regardless of specificity. Utilities always win over components.

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

```svelte
<!-- Svelte: container queries work with Svelte scoped styles -->
<style>
  .wrapper {
    container-type: inline-size;
  }

  /* :global needed for generated class selectors to cross scope boundary */
  @container (min-width: 600px) {
    .inner {
      display: grid;
      grid-template-columns: 1fr 1fr;
    }
  }
</style>
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

## Svelte CSS Custom Properties (--style-props)

```svelte
<!-- Component.svelte — expose theming API via CSS vars -->
<style>
  .button {
    background: var(--btn-bg, var(--color-brand));
    color: var(--btn-fg, white);
    padding: var(--btn-padding, 0.5rem 1rem);
    border-radius: var(--btn-radius, var(--radius-md));
  }
</style>

<button class="button">Click me</button>
```

```svelte
<!-- Parent — override via CSS custom properties -->
<Button
  --btn-bg="oklch(55% 0.18 150)"
  --btn-fg="oklch(20% 0 0)"
  --btn-radius="9999px"
/>
```

Note: Svelte passes `--custom-property` props as CSS custom properties on a wrapper element.

## Fluid Typography with clamp()

```css
/* Type scale with Major Third (1.25) ratio */
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

```css
/* oklch(lightness% chroma hue) */
/* Perceptually uniform — equal lightness step = equal perceived brightness */

:root {
  /* Generate color scale with consistent perceptual lightness */
  --brand-100: oklch(95% 0.03 250);
  --brand-300: oklch(75% 0.10 250);
  --brand-500: oklch(55% 0.18 250);  /* base brand color */
  --brand-700: oklch(38% 0.14 250);
  --brand-900: oklch(22% 0.08 250);
}

/* color-mix() for derived colors */
.button:hover {
  background: color-mix(in oklch, var(--color-brand) 85%, black);
}

.button:active {
  background: color-mix(in oklch, var(--color-brand) 75%, black);
}

/* Alpha with oklch */
.overlay {
  background: oklch(0% 0 0 / 50%);    /* 50% transparent black */
  color: oklch(100% 0 0 / 90%);       /* 90% opaque white */
}
```

## CSS Nesting (Native, No Preprocessor)

```css
/* Native CSS nesting — supported in all modern browsers */
.card {
  padding: var(--space-4);
  border-radius: var(--radius-lg);

  /* Nest pseudo-classes */
  &:hover {
    box-shadow: 0 4px 20px oklch(0% 0 0 / 10%);
  }

  /* Nest child selectors */
  & .card-title {
    font-size: var(--font-size-xl);
  }

  /* Nest at-rules */
  @media (max-width: 600px) {
    padding: var(--space-2);
  }
}
```

## Scoped CSS in Svelte

```svelte
<style>
  /* Scoped by default — applies only to this component's elements */
  .button { background: var(--color-brand); }

  /* Escape to global scope */
  :global(.toast) { z-index: 9999; }
  :global(body.modal-open) { overflow: hidden; }

  /* Apply to all children (including child components) */
  .prose :global(p) { line-height: 1.8; }
  .prose :global(h2) { margin-top: var(--space-8); }
</style>
```

## View Transitions API

```css
/* Basic view transition */
::view-transition-old(root) {
  animation: 200ms ease-out fade-out;
}

::view-transition-new(root) {
  animation: 200ms ease-in fade-in;
}

/* Element-specific shared transition */
.post-image {
  view-transition-name: post-image;  /* must be unique per page */
}

/* Custom transition for specific named element */
::view-transition-old(post-image),
::view-transition-new(post-image) {
  animation-duration: 350ms;
  animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}
```

## Tailwind CSS Integration

```javascript
// tailwind.config.ts — map Tailwind to design tokens
export default {
  theme: {
    extend: {
      colors: {
        brand: 'oklch(var(--brand-l) var(--brand-c) var(--brand-h) / <alpha-value>)',
      },
      spacing: {
        'page': 'var(--space-page)',
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
      }
    }
  }
};
```

```svelte
<!-- Use Tailwind utilities + CSS custom properties together -->
<div class="flex gap-4 p-page">
  <button
    class="rounded-md px-4 py-2 font-medium"
    style="background: var(--color-brand); color: white"
  >
    Action
  </button>
</div>
```

## Additional Resources

- [css-patterns-reference.md](css-patterns-reference.md) — Component-level theming patterns, CSS architecture for large apps, animation patterns, print styles, CSS logical properties, Tailwind v4 integration

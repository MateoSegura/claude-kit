# CSS Architecture — Detailed Patterns Reference

## Component-Level Theming with CSS Custom Properties

### The Variable-with-Fallback Pattern

Components expose a CSS API via custom property fallbacks:

```css
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

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
  }
}
```

Override from a parent context:

```css
/* Override via CSS variables in parent scope */
.danger-zone .btn {
  --btn-bg: var(--color-error);
}

/* Variant classes */
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
```

## Responsive Layout Patterns

### Auto-Fit Grid

```css
/* Columns fill available space automatically */
.auto-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));
  gap: var(--space-4);
}
```

### Sidebar Layout

```css
.sidebar-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);

  @media (min-width: 768px) {
    grid-template-columns: 240px 1fr;
  }
}
```

### Stack Pattern

```css
.stack { display: flex; flex-direction: column; }
.stack > * + * { margin-top: var(--stack-space, var(--space-4)); }

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
/* Use logical properties for RTL language support */
.card {
  /* Instead of margin-left/right */
  margin-inline: auto;
  padding-inline: var(--space-4);
  padding-block: var(--space-6);

  /* Instead of border-left */
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
/* Perfect Fourth (1.333) type scale */
:root {
  --font-size-xs:   clamp(0.563rem, 0.5vw + 0.45rem, 0.65rem);
  --font-size-sm:   clamp(0.75rem,  0.7vw + 0.6rem,  0.875rem);
  --font-size-base: clamp(1rem,     1vw + 0.75rem,   1.125rem);
  --font-size-lg:   clamp(1.333rem, 1.4vw + 1rem,   1.5rem);
  --font-size-xl:   clamp(1.777rem, 1.8vw + 1.3rem, 2rem);
  --font-size-2xl:  clamp(2.369rem, 2.4vw + 1.7rem, 2.75rem);

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

::view-transition-old(post-image),
::view-transition-new(post-image) {
  animation-duration: 350ms;
  animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}
```

```javascript
// Trigger a view transition programmatically
if (document.startViewTransition) {
  document.startViewTransition(() => {
    // Update the DOM here
    updateContent();
  });
}
```

## Tailwind CSS v4 Integration

Tailwind v4 (2025) uses CSS-first configuration:

```css
/* app.css — Tailwind v4 configuration in CSS */
@import "tailwindcss";

@theme {
  --color-brand: oklch(55% 0.18 250);
  --color-brand-50: oklch(97% 0.02 250);
  --color-brand-900: oklch(22% 0.08 250);

  --font-sans: 'Inter', system-ui, sans-serif;

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 16px;

  --spacing-page: 2rem;
}
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
  styles/
    reset.css          -- @layer reset
    tokens.css         -- @layer tokens — all custom properties
    base.css           -- @layer base — element defaults
    components.css     -- @layer components — reusable patterns
    utilities.css      -- @layer utilities — single-purpose classes
  app.css              -- @import all layers
```

```css
/* app.css */
@layer reset, tokens, base, components, utilities;

@import './styles/reset.css' layer(reset);
@import './styles/tokens.css' layer(tokens);
@import './styles/base.css' layer(base);
@import './styles/components.css' layer(components);
@import './styles/utilities.css' layer(utilities);
```

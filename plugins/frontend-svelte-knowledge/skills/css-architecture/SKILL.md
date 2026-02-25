---
name: frontend-svelte-knowledge:css-architecture
description: "Svelte-specific CSS patterns: scoped styles, :global() escape hatch, Svelte --style-props for component theming, container queries in scoped context, and SvelteKit View Transitions integration."
user-invocable: false
---

# Svelte CSS Patterns

> **General CSS architecture** (design tokens, @layer, container queries, :has(), fluid typography, oklch, nesting, styling strategy tradeoffs) is provided by the `core-frontend:css-architecture` skill. This file covers **Svelte-specific** CSS patterns only.

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

## Svelte CSS Custom Properties (--style-props)

Svelte passes `--custom-property` props as CSS custom properties on a wrapper element.

```svelte
<!-- Button.svelte — expose theming API via CSS vars -->
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

## Container Queries in Svelte Scoped Styles

```svelte
<style>
  .wrapper {
    container-type: inline-size;
  }

  @container (min-width: 600px) {
    .inner {
      display: grid;
      grid-template-columns: 1fr 1fr;
    }
  }
</style>
```

## View Transitions — SvelteKit Integration

```typescript
// src/hooks.client.ts
import { onNavigate } from '$app/navigation';

onNavigate((navigation) => {
  if (!document.startViewTransition) return;

  return new Promise((resolve) => {
    document.startViewTransition(async () => {
      resolve();
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

  ::view-transition-old(slide) {
    animation: 300ms ease-out both slide-to-left;
  }
  ::view-transition-new(slide) {
    animation: 300ms ease-in both slide-from-right;
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

## Tailwind CSS with Svelte

```svelte
<div class="flex gap-4 p-page">
  <button
    class="rounded-md px-4 py-2 font-medium"
    style="background: var(--color-brand); color: white"
  >
    Action
  </button>
</div>
```

For Tailwind v4 CSS-first configuration and design token mapping, see `core-frontend:css-architecture`.

## Additional Resources

- [css-patterns-reference.md](css-patterns-reference.md) — Svelte component-level theming, variant systems, Tailwind v4 integration, SvelteKit file organization

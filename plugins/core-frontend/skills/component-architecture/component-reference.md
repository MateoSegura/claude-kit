# Component Architecture — Detailed Reference

## Component Organization

### Atomic Design Hierarchy

```
atoms/        -- Smallest building blocks (Button, Input, Icon, Badge)
molecules/    -- Groups of atoms (SearchBar, FormField, NavLink)
organisms/    -- Complex sections (Header, Sidebar, DataTable)
templates/    -- Page layouts with placeholder content
pages/        -- Template instances with real data
```

**Practical simplification** (most projects don't need all 5 levels):

```
components/
  ui/           -- Generic, reusable (Button, Modal, Card, Input)
  features/     -- Domain-specific (UserCard, InvoiceTable, CartSummary)
  layouts/      -- Page structure (AppShell, SidebarLayout, AuthLayout)
```

### Co-Location Principle

Keep related files together. A component's styles, tests, and stories should live next to it.

```
Button/
  Button.tsx          -- (or .svelte, .vue)
  Button.test.ts
  Button.module.css   -- (if using CSS modules)
  index.ts            -- barrel export
```

### Barrel Exports

Use `index.ts` files for clean imports, but avoid deep barrel chains that hurt tree-shaking.

```typescript
// components/ui/index.ts
export { Button } from './Button';
export { Input } from './Input';
export { Modal } from './Modal';
```

## Component Testing Strategies

### Testing Pyramid for Components

```
         /  E2E  \         -- Few: critical user flows only
        / Integration \    -- More: component groups, form submissions
       /    Unit tests  \  -- Most: individual component behavior
```

### What to Test in Components

| Test | Example |
|------|---------|
| Renders correctly | Component mounts without errors |
| Props affect output | `variant="danger"` adds danger class |
| User interactions | Clicking button calls handler |
| Conditional rendering | Loading state shows spinner |
| Accessibility | No axe violations, correct ARIA |
| Edge cases | Empty data, long text, error state |

### What NOT to Test

- Implementation details (internal state variables, private methods)
- Styling (pixel-perfect assertions are brittle)
- Third-party library internals
- Snapshot tests of large components (too brittle)

### Testing Library Philosophy

Use testing libraries that encourage testing the way users interact:
- Query by role, label, or text — not by class or test ID
- Interact via click, type, keyboard — not by calling internal methods
- Assert on what users see — not internal state

## Performance Patterns

### Avoid Re-Renders

- Memoize expensive computations
- Avoid creating new objects/arrays in render (creates new references each time)
- Use keys correctly in lists (stable, unique IDs — never array index for dynamic lists)
- Prefer flat component trees over deeply nested ones

### Lazy Loading Components

Load components only when needed:

```javascript
// Route-level splitting — load page components on navigation
const Dashboard = lazy(() => import('./pages/Dashboard'));

// Interaction-triggered — load on user action
const HeavyEditor = lazy(() => import('./components/HeavyEditor'));
```

**When to lazy load:**
- Below-the-fold content
- Modal/dialog content
- Tab content that isn't the default tab
- Admin-only features
- Heavy third-party integrations (editors, charts)

### Virtualization

For lists with hundreds+ items, only render the visible items:

```
Total items: 10,000
Visible viewport: ~20 items
Actually rendered DOM nodes: ~25 (20 visible + buffer)
```

Libraries: `@tanstack/virtual`, `react-window`, `svelte-virtual-list`, `vue-virtual-scroller`.

## Error Boundaries

Prevent a crashed component from taking down the entire page.

**Error boundary strategy:**
- Wrap each major page section independently
- Show a fallback UI with retry option
- Log the error for monitoring
- Keep the rest of the page functional

```html
<!-- Fallback UI pattern -->
<div role="alert" class="error-boundary">
  <h2>This section couldn't load</h2>
  <p>An unexpected error occurred. The rest of the page is still available.</p>
  <button onclick="retry()">Try again</button>
</div>
```

**Where to place error boundaries:**
- Around each route/page
- Around independent feature sections (sidebar, feed, chat)
- Around third-party integrations
- NOT around every single component (too granular)

## Prop Validation

Validate props at the component boundary. This is the system boundary where external data enters your component.

| Framework | Mechanism |
|-----------|-----------|
| TypeScript (all) | Interface/type for props |
| React | TypeScript props interface |
| Vue | `defineProps` with TypeScript |
| Svelte | `$props()` with TypeScript |
| Angular | `@Input()` decorators with types |

**Runtime validation** is only needed at external boundaries (API responses, URL params, user input). For component-to-component props, TypeScript is sufficient.

## Component Communication Patterns

### Parent -> Child
- Props (data flows down)

### Child -> Parent
- Event callbacks / emitted events
- Callback props (`onChange`, `onSubmit`)

### Sibling -> Sibling
- Lift state to common parent
- Shared context/store

### Distant Components
- Context / dependency injection
- Global state manager
- Event bus (use sparingly — hard to trace)

### Summary

| Distance | Pattern |
|----------|---------|
| Parent-child | Props + callbacks |
| Close siblings | Lift state to parent |
| Deeply nested | Context / injection |
| App-wide | State manager |
| Cross-app / micro-frontend | Custom events / message bus |

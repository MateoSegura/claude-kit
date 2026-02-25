# Anti-Patterns — Svelte 5 / SvelteKit

Common mistakes found in Svelte 5 and SvelteKit submissions. Each entry maps directly to a grading deduction. Use this catalog to confirm a finding is a genuine violation and determine the correct severity.

---

## Category 1: Reactivity Anti-Patterns

### AP-01: Using $effect to Compute Derived Values

**Grading impact:** Major deduction (−10 pts), Dimension: State Management

**What developers do wrong:** Using `$effect` to update a second `$state` variable whenever a first one changes, instead of using `$derived`.

**BAD code:**
```svelte
<script lang="ts">
  let count = $state(0);
  let doubled = $state(0);  // unnecessary second $state
  let isEven = $state(true);

  // WRONG: $effect for value derivation
  $effect(() => {
    doubled = count * 2;
    isEven = count % 2 === 0;
  });
</script>
```

**Why it fails:** `$effect` has overhead from subscription tracking and runs asynchronously after DOM updates. It causes an extra render cycle (state update → $effect runs → triggers another update). It also introduces the risk of circular dependencies if `doubled` or `isEven` are read elsewhere in a way that affects `count`.

**GOOD code:**
```svelte
<script lang="ts">
  let count = $state(0);

  // $derived: computed once, memoized, no extra render cycle
  const doubled = $derived(count * 2);
  const isEven = $derived(count % 2 === 0);
</script>
```

---

### AP-02: Svelte 4 Reactive Declarations ($: labels)

**Grading impact:** Critical deduction (−25 pts), Dimension: State Management

**What developers do wrong:** Using `$:` reactive statements, which are Svelte 4 syntax. These still work in Svelte 5 in "legacy mode" components, but they signal the developer has not adopted the runes API.

**BAD code:**
```svelte
<script lang="ts">
  let count = 0;

  $: doubled = count * 2;           // Svelte 4 reactive declaration
  $: console.log('count:', count);  // Svelte 4 reactive statement
  $: {
    if (count > 10) {
      // Svelte 4 reactive block
    }
  }
</script>
```

**Why it fails:** `$:` relies on Svelte's legacy compile-time analysis. In Svelte 5 with runes mode (any file using `$state`, `$derived`, etc.), `$:` is disallowed. Mixing legacy and runes syntax causes a compile error. In legacy-only files, `$:` creates harder-to-reason ordering dependencies compared to explicit `$derived` and `$effect`.

**GOOD code:**
```svelte
<script lang="ts">
  let count = $state(0);

  const doubled = $derived(count * 2);

  $effect(() => {
    console.log('count:', count);
  });

  $effect(() => {
    if (count > 10) {
      // handle threshold
    }
  });
</script>
```

---

### AP-03: Svelte 4 export let Props

**Grading impact:** Critical deduction (−25 pts), Dimension: Component Quality

**What developers do wrong:** Declaring component props with `export let` instead of the Svelte 5 `$props()` rune.

**BAD code:**
```svelte
<script lang="ts">
  // Svelte 4 pattern — breaks in Svelte 5 runes mode
  export let name: string;
  export let age: number = 18;
  export let onClick: () => void;
</script>
```

**Why it fails:** In Svelte 5 runes mode, `export let` is not the props mechanism. `$props()` is the explicit, type-safe replacement. Using `export let` in a file that also uses other runes causes compiler errors.

**GOOD code:**
```svelte
<script lang="ts">
  interface Props {
    name: string;
    age?: number;
    onClick: () => void;
  }

  const { name, age = 18, onClick }: Props = $props();
</script>
```

---

### AP-04: $state in Regular .ts Files

**Grading impact:** Major deduction (−10 pts), Dimension: State Management

**What developers do wrong:** Attempting to use `$state`, `$derived`, or `$effect` in regular `.ts` files (not `.svelte.ts`).

**BAD code:**
```typescript
// src/lib/auth.ts — WRONG: runes don't work in .ts files
export let user = $state<User | null>(null);  // compile error
```

**Why it fails:** The Svelte compiler only processes rune syntax in `.svelte` and `.svelte.ts` files. Using runes in a plain `.ts` file causes a compile error because `$state` is not in scope.

**GOOD code:**
```typescript
// src/lib/auth.svelte.ts — correct file extension
let user = $state<User | null>(null);

export function getUser() {
  return user;
}
export function setUser(newUser: User | null) {
  user = newUser;
}
```

---

### AP-05: Mutating State Inside $effect Without untrack()

**Grading impact:** Major deduction (−10 pts), Dimension: State Management

**What developers do wrong:** Reading and writing the same reactive variable inside an `$effect`, causing an infinite update loop.

**BAD code:**
```svelte
<script lang="ts">
  let items = $state<string[]>([]);
  let processedItems = $state<string[]>([]);

  $effect(() => {
    // Reading `items` creates a dependency
    // Writing `processedItems` triggers a re-render
    // If processedItems is also read above... infinite loop
    processedItems = items.map(item => item.toUpperCase());
  });
</script>
```

**Why it fails:** Each write to `processedItems` could trigger subscriptions that re-read `items`, re-entering the effect. Even without a direct circular dependency, unnecessary state updates add render overhead.

**GOOD code:**
```svelte
<script lang="ts">
  let items = $state<string[]>([]);

  // Correct: use $derived for this pattern
  const processedItems = $derived(items.map(item => item.toUpperCase()));
</script>
```

---

## Category 2: Component Anti-Patterns

### AP-06: Div Soup Instead of Semantic HTML

**Grading impact:** Major deduction (−10 pts), Dimension: Accessibility

**What developers do wrong:** Using `<div>` and `<span>` for interactive elements instead of the appropriate semantic HTML element.

**BAD code:**
```svelte
<!-- WRONG: div-based interactive elements -->
<div class="button" onclick={handleDelete} role="button">Delete</div>

<div class="nav">
  <div class="nav-item" onclick={() => goto('/home')}>Home</div>
  <div class="nav-item" onclick={() => goto('/about')}>About</div>
</div>

<div class="heading-1">Page Title</div>
```

**Why it fails:** `<div>` has no semantic meaning. Screen readers announce it as nothing. Keyboard users cannot Tab to it without `tabindex`. Browsers do not give it click behavior on Enter/Space. Requires extensive ARIA to approximate what native HTML provides for free.

**GOOD code:**
```svelte
<!-- GOOD: Semantic HTML — accessible by default -->
<button onclick={handleDelete}>Delete</button>

<nav>
  <a href="/home">Home</a>
  <a href="/about">About</a>
</nav>

<h1>Page Title</h1>
```

---

### AP-07: Icon Buttons Without Accessible Names

**Grading impact:** Major deduction (−10 pts), Dimension: Accessibility

**What developers do wrong:** Creating icon-only buttons with no text alternative for screen readers.

**BAD code:**
```svelte
<!-- WRONG: Screen reader announces "button" with no name -->
<button onclick={handleClose}>
  <svg><!-- X icon --></svg>
</button>

<!-- Also wrong: tooltip only, no accessible name -->
<button title="Close" onclick={handleClose}>
  <svg><!-- X icon --></svg>
</button>
```

**Why it fails:** Screen readers announce the button as just "button" with no context. `title` attribute is not a reliable accessible name in all assistive technologies.

**GOOD code:**
```svelte
<!-- GOOD: aria-label provides the accessible name -->
<button aria-label="Close dialog" onclick={handleClose}>
  <svg aria-hidden="true"><!-- X icon --></svg>
</button>

<!-- Alternative: visually hidden text -->
<button onclick={handleClose}>
  <svg aria-hidden="true"><!-- X icon --></svg>
  <span class="sr-only">Close dialog</span>
</button>
```

---

### AP-08: Missing Focus Management on Modals

**Grading impact:** Major deduction (−10 pts), Dimension: Accessibility

**What developers do wrong:** Opening a modal dialog without moving focus into it, or closing it without returning focus to the trigger element.

**BAD code:**
```svelte
<script lang="ts">
  let isOpen = $state(false);
</script>

<!-- WRONG: Opens visually but focus stays on trigger -->
{#if isOpen}
  <div class="modal">
    <button onclick={() => isOpen = false}>Close</button>
    <!-- Content -->
  </div>
{/if}
```

**Why it fails:** Keyboard users cannot access modal content because their focus cursor remains behind the modal. Tab navigation may go behind the modal. Screen reader users may not know the modal appeared.

**GOOD code:**
```svelte
<script lang="ts">
  let dialogEl = $state<HTMLDialogElement | null>(null);
  let triggerEl = $state<HTMLButtonElement | null>(null);

  interface Props {
    open: boolean;
    onClose: () => void;
  }
  const { open, onClose }: Props = $props();

  $effect(() => {
    if (open && dialogEl) {
      dialogEl.showModal(); // Native dialog manages focus trap automatically
    } else if (!open && dialogEl?.open) {
      dialogEl.close();
      triggerEl?.focus(); // Return focus to trigger
    }
  });
</script>

<dialog bind:this={dialogEl} onclose={onClose}>
  <!-- Native <dialog> provides focus trap, Esc to close, ARIA role -->
  <slot />
  <button onclick={onClose}>Close</button>
</dialog>
```

---

### AP-09: Prop Drilling Beyond 2 Levels

**Grading impact:** Minor deduction (−3 pts per occurrence, max 3 occurrences counted), Dimension: State Management

**What developers do wrong:** Passing the same prop through 3 or more component layers when it's only needed at the bottom.

**BAD code:**
```svelte
<!-- App.svelte -->
<Dashboard {currentUser} />

<!-- Dashboard.svelte -->
<script lang="ts">
  const { currentUser }: Props = $props();
</script>
<Sidebar {currentUser} />

<!-- Sidebar.svelte -->
<script lang="ts">
  const { currentUser }: Props = $props();
</script>
<UserMenu {currentUser} />

<!-- UserMenu.svelte finally uses it -->
```

**Why it fails:** Every intermediate component must declare the prop even though it doesn't use it. Adding or removing the prop requires changes in every file in the chain.

**GOOD code:**
```svelte
<!-- App.svelte or a layout -->
<script lang="ts">
  import { setContext } from 'svelte';
  setContext('currentUser', () => currentUser);
</script>

<!-- UserMenu.svelte — consumes directly without threading through intermediates -->
<script lang="ts">
  import { getContext } from 'svelte';
  const getCurrentUser = getContext<() => User>('currentUser');
  const user = $derived(getCurrentUser());
</script>
```

---

## Category 3: TypeScript Anti-Patterns

### AP-10: as any TypeScript Cast

**Grading impact:** Major deduction (−10 pts per instance), Dimension: TypeScript Usage

**What developers do wrong:** Using `as any` to silence TypeScript errors instead of properly typing the value.

**BAD code:**
```typescript
// In +page.ts
const data = await fetch('/api/user').then(r => r.json()) as any;
// Now all property accesses on data are untyped

// In component
const { someValue } = $props();
const result = (someValue as any).deeply.nested.value; // loses type safety
```

**Why it fails:** `as any` is a type escape hatch that disables TypeScript's type checking for that value and everything derived from it. Runtime errors that TypeScript would have caught are silently allowed. It also prevents IDE autocompletion and refactoring.

**GOOD code:**
```typescript
interface User {
  id: string;
  email: string;
  name: string;
}

const user: User = await fetch('/api/user').then(r => r.json());
// TypeScript now validates all property accesses
```

---

### AP-11: Missing strict: true in tsconfig.json

**Grading impact:** Critical deduction (−25 pts), Dimension: TypeScript Usage

**What developers do wrong:** Having `"strict": false` or omitting `strict` in tsconfig.json.

**BAD config:**
```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "strict": false
  }
}
```

**Why it fails:** `strict: false` disables: `noImplicitAny` (allows untyped variables), `strictNullChecks` (allows null/undefined bugs), `strictFunctionTypes`, `strictPropertyInitialization`, and more. Without these, the TypeScript compiler catches far fewer errors. SvelteKit strongly recommends `strict: true`.

**GOOD config:**
```json
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true
  }
}
```

---

## Category 4: Testing Anti-Patterns

### AP-12: Snapshot Testing Component Structure

**Grading impact:** Major deduction (−10 pts per snapshot test), Dimension: Testing Quality

**What developers do wrong:** Using `toMatchSnapshot()` on rendered component output to detect regressions.

**BAD code:**
```typescript
it('renders correctly', () => {
  const { container } = render(Button, { props: { variant: 'primary' } });
  expect(container).toMatchSnapshot();  // snapshot of HTML structure
});
```

**Why it fails:** Snapshot tests catch ANY change to the rendered output — including harmless class name changes, whitespace, or order of attributes. They produce false positives constantly, leading teams to blindly update snapshots without verifying the change is correct. They also test implementation details (HTML structure) rather than user-observable behavior.

**GOOD code:**
```typescript
it('renders as a button with primary styling class', () => {
  render(Button, { props: { variant: 'primary', children: 'Click me' } });

  const button = screen.getByRole('button', { name: 'Click me' });
  expect(button).toBeInTheDocument();
  expect(button).toHaveClass('btn--primary');
  expect(button).not.toBeDisabled();
});
```

---

### AP-13: Testing Implementation Instead of Behavior

**Grading impact:** Major deduction (−10 pts), Dimension: Testing Quality

**What developers do wrong:** Testing internal state values, private functions, or component internals rather than user-visible behavior.

**BAD code:**
```typescript
it('increments internal count', async () => {
  const component = render(Counter);
  // Accessing component internals — brittle and wrong
  expect(component.component.count).toBe(0);
  component.component.increment();
  expect(component.component.count).toBe(1);
});
```

**Why it fails:** Tests that access component internals are brittle — any refactoring breaks them even if user behavior is unchanged. Internal variable names, function names, and state shape are implementation details that should be free to change.

**GOOD code:**
```typescript
it('shows updated count when increment button is clicked', async () => {
  const user = userEvent.setup();
  render(Counter);

  expect(screen.getByText('Count: 0')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /increment/i }));
  expect(screen.getByText('Count: 1')).toBeInTheDocument();
});
```

---

## Category 5: UX Anti-Patterns

### AP-14: Forms Without use:enhance

**Grading impact:** Major deduction (−10 pts), Dimension: UX Patterns

**What developers do wrong:** Using SvelteKit form actions but not adding `use:enhance`, meaning the form requires a full page reload on submit.

**BAD code:**
```svelte
<!-- Form submits with full page reload even though SvelteKit action is used -->
<form method="POST" action="?/register">
  <input name="email" type="email" />
  <button type="submit">Register</button>
</form>
```

**Why it fails:** Without `use:enhance`, every form submission triggers a full page navigation, clearing all component state and causing a visible page flash. Users lose scroll position. Loading state cannot be shown. The enhanced experience that SvelteKit provides is entirely bypassed.

**GOOD code:**
```svelte
<script lang="ts">
  import { enhance } from '$app/forms';
  let submitting = $state(false);
</script>

<form
  method="POST"
  action="?/register"
  use:enhance={() => {
    submitting = true;
    return async ({ update }) => {
      await update();
      submitting = false;
    };
  }}
>
  <input name="email" type="email" />
  <button type="submit" disabled={submitting}>
    {submitting ? 'Registering...' : 'Register'}
  </button>
</form>
```

---

### AP-15: Using +page.ts for Server-Only Data

**Grading impact:** Major deduction (−10 pts), Dimension: Performance

**What developers do wrong:** Placing server-only operations (DB queries, private env vars) in `+page.ts` (universal load) instead of `+page.server.ts` (server-only load).

**BAD code:**
```typescript
// src/routes/admin/+page.ts — WRONG for server-only data
import { DATABASE_URL } from '$env/static/private'; // Compile error in universal load!

export const load = async () => {
  const users = await db.findAll(); // db client in client bundle = security risk
  return { users };
};
```

**Why it fails:** `$env/static/private` is not available in universal load functions — SvelteKit throws a compile-time error. Even if using non-env secrets, universal load functions run on both server AND client, so any sensitive logic or credentials would be exposed in the client bundle.

**GOOD code:**
```typescript
// src/routes/admin/+page.server.ts — correct for server-only data
import { DATABASE_URL } from '$env/static/private'; // Available in server load
import { db } from '$lib/server/db'; // server-only import

export const load: PageServerLoad = async ({ locals }) => {
  if (!locals.user?.isAdmin) {
    redirect(302, '/');
  }
  const users = await db.user.findMany();
  return { users };
};
```

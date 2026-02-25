# Svelte 5 Coding Standards — Domain Reference

These conventions apply across all role plugins (engineer, grader, tester) that consume this knowledge plugin. They define the shared language and expectations for Svelte 5 / SvelteKit codebases.

## Svelte 5 Only — Rejected Patterns

The following Svelte 4 patterns MUST NOT appear in any generated or reviewed code:

| Svelte 4 (REJECTED) | Svelte 5 (REQUIRED) |
|---|---|
| `export let prop` | `let { prop } = $props()` |
| `on:click={handler}` | `onclick={handler}` |
| `createEventDispatcher()` | Callback props or `$props()` |
| `<slot />` / `<slot name="x">` | `{#snippet name()}` / `{@render name()}` |
| `$:` reactive declarations | `$derived()` or `$derived.by()` |
| `$: { sideEffect() }` | `$effect()` |
| `import { writable } from 'svelte/store'` | `$state()` (prefer runes over stores) |
| `beforeUpdate` / `afterUpdate` | `$effect()` with DOM reads |
| `$$props` / `$$restProps` | Spread from `$props()`: `let { a, ...rest } = $props()` |

## TypeScript Conventions

- `strict: true` in `tsconfig.json` — no exceptions
- `lang="ts"` in every `<script>` block
- Explicit return types on exported functions and load functions
- Prefer `interface` over `type` for object shapes (extendability)
- Use `satisfies` for type-safe object literals: `const config = { ... } satisfies Config`
- Generic components use `generics` attribute: `<script lang="ts" generics="T extends Record<string, unknown>">`

## File and Directory Naming

- Components: `PascalCase.svelte` — e.g., `UserProfile.svelte`, `DataTable.svelte`
- Routes: `+page.svelte`, `+page.ts`, `+page.server.ts`, `+layout.svelte`, `+error.svelte`
- Utility modules: `kebab-case.ts` — e.g., `format-date.ts`, `api-client.ts`
- Type definition files: `kebab-case.d.ts` or colocated in the module
- Test files: `component-name.test.ts` or `component-name.spec.ts` colocated with source
- Stores / shared state: `kebab-case.svelte.ts` — the `.svelte.ts` extension enables rune reactivity outside components

## Component Structure

A Svelte 5 component follows this order within the `.svelte` file:

```svelte
<!-- 1. Script block (module-level exports, if any) -->
<script lang="ts" module>
  export type ButtonVariant = 'primary' | 'secondary' | 'ghost';
</script>

<!-- 2. Script block (instance) -->
<script lang="ts">
  // a. Imports
  import { enhance } from '$app/forms';

  // b. Props
  let { variant = 'primary', children, onclick }: {
    variant?: ButtonVariant;
    children: import('svelte').Snippet;
    onclick?: (e: MouseEvent) => void;
  } = $props();

  // c. State
  let count = $state(0);

  // d. Derived values
  let doubled = $derived(count * 2);

  // e. Effects (sparingly)
  $effect(() => {
    console.log('count changed:', count);
  });

  // f. Functions
  function increment() {
    count++;
  }
</script>

<!-- 3. Markup -->
<button class="btn btn-{variant}" {onclick}>
  {@render children()}
</button>

<!-- 4. Styles -->
<style>
  /* Scoped styles or Tailwind @apply */
</style>
```

## CSS and Styling Conventions

- Tailwind CSS for utility classes; CSS custom properties for design tokens
- Design tokens live in a central `tokens.css` or Tailwind config `theme.extend`
- Spacing scale: `--space-xs` through `--space-3xl` (consistent 4px-based or modular scale)
- Font sizes: fluid typography using `clamp()` — e.g., `font-size: clamp(1rem, 0.5vw + 0.875rem, 1.25rem)`
- Colors: semantic naming (`--color-surface`, `--color-on-surface`, `--color-accent`) not raw values
- Transitions: prefer `150ms ease-out` for micro-interactions, `300ms ease-in-out` for layout shifts
- Use `<style>` blocks for component-scoped styles; global styles go in `app.css`
- Container queries (`@container`) over media queries for component-level responsiveness

## Accessibility Baseline

- Every interactive element must be keyboard-accessible
- Every image has `alt` text (or `alt=""` with `aria-hidden="true"` for decorative)
- Form inputs have associated `<label>` elements (not just `placeholder`)
- Color contrast meets WCAG 2.2 AA (4.5:1 for normal text, 3:1 for large text)
- Focus indicators are visible and high-contrast
- ARIA attributes used only when native HTML semantics are insufficient
- `role` attributes only when the native element cannot convey the semantics

## SvelteKit Conventions

- Load functions return typed data: `export const load: PageLoad = async ({ params }) => { ... }`
- Form actions for mutations: prefer `use:enhance` over manual fetch
- Error handling: throw `error(404, 'Not found')` in load functions, not generic throws
- Environment variables: `$env/static/private` for build-time secrets, `$env/dynamic/public` for client-safe config
- Route groups: `(auth)`, `(marketing)` for shared layouts without URL segments
- API routes: `+server.ts` for JSON endpoints, form actions for HTML form submissions
- Hooks: `handle` in `hooks.server.ts` for auth, logging, response transforms

## Error Handling

- Load functions: use SvelteKit's `error()` helper for HTTP errors, `redirect()` for navigation
- Client-side: `+error.svelte` boundary components at appropriate route levels
- API calls: always handle network failures and non-2xx responses explicitly
- Form actions: return `fail(400, { field, error })` for validation errors
- Never swallow errors silently — log or surface them

## Import Conventions

- SvelteKit aliases: `$lib/` for `src/lib/`, `$app/` for SvelteKit modules
- Group imports: (1) svelte/sveltekit, (2) third-party, (3) `$lib`, (4) relative
- Prefer named exports from barrel files for library code
- Avoid deep relative imports (`../../../`) — use `$lib` aliases

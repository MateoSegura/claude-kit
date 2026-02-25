---
name: frontend-svelte-knowledge:accessibility
description: "Svelte-specific accessibility patterns: compiler a11y warnings, SvelteKit route announcements, afterNavigate focus management, Bits UI headless components, svelte:boundary error boundaries, and Svelte template patterns for ARIA live regions and forms."
user-invocable: false
---

# Svelte Accessibility Patterns

> **General WCAG 2.2 AA reference** (semantic HTML, ARIA, keyboard navigation, color contrast, focus styling) is provided by the `core-frontend:accessibility` skill. This file covers **Svelte-specific** patterns only.

## Svelte Compiler A11y Warnings

Svelte includes compile-time accessibility checks. These are errors you MUST fix:

```svelte
<!-- These will produce compiler warnings -->
<img src="photo.jpg" />                    <!-- Missing alt -->
<div onclick={handler} />                  <!-- Click on non-interactive element -->
<a />                                      <!-- Missing href or role -->
<input type="color" />                     <!-- Missing associated label -->

<!-- Correct patterns -->
<img src="photo.jpg" alt="Description" />
<button onclick={handler}>Click me</button>
<input id="color" type="color" />
<label for="color">Pick a color</label>
```

Svelte a11y rules enforce: alt attributes, ARIA usage, heading order, interactive element semantics, keyboard events alongside mouse events, and label associations.

## Route Announcements (SvelteKit)

SvelteKit auto-announces route changes to screen readers via an `aria-live` region. To customize:

```svelte
<!-- src/routes/+layout.svelte — custom route title announcement -->
<script>
  import { page } from '$app/state';
  import { afterNavigate } from '$app/navigation';

  let announcement = $state('');

  afterNavigate(() => {
    announcement = `Navigated to ${page.data.title ?? document.title}`;
  });
</script>

<div role="status" aria-live="polite" aria-atomic="true" class="sr-only">
  {announcement}
</div>
```

## Focus Management After Navigation

```svelte
<!-- src/routes/+layout.svelte -->
<script>
  import { afterNavigate } from '$app/navigation';

  afterNavigate(({ type }) => {
    if (type === 'popstate') return; // don't interfere with back/forward
    const main = document.getElementById('main-content');
    main?.focus();
  });
</script>
```

```svelte
<!-- Return focus to trigger after modal close -->
<script>
  let modalTrigger: HTMLButtonElement;
  let modalOpen = $state(false);

  function closeModal() {
    modalOpen = false;
    modalTrigger?.focus();
  }
</script>

<button bind:this={modalTrigger} onclick={() => modalOpen = true}>Open</button>

{#if modalOpen}
  <Modal onclose={closeModal} />
{/if}
```

## Skip Link in SvelteKit Layout

```svelte
<!-- src/routes/+layout.svelte -->
<a href="#main-content" class="skip-link">Skip to main content</a>
<nav><!-- navigation --></nav>
<main id="main-content" tabindex="-1">
  {@render children()}
</main>
```

## ARIA Live Regions in Svelte

```svelte
<!-- Status messages -->
<div role="status" aria-live="polite" aria-atomic="true">
  {#if saveStatus === 'saving'}Saving...{:else if saveStatus === 'saved'}Changes saved{/if}
</div>

<!-- Error alerts -->
<div role="alert" aria-live="assertive">
  {#if errorMessage}{errorMessage}{/if}
</div>

<!-- Search results count -->
<div aria-live="polite" aria-atomic="true" class="sr-only">
  {#if searchResults}
    {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} for "{searchQuery}"
  {/if}
</div>
```

## Form Accessibility in Svelte

```svelte
<form onsubmit={handleSubmit} novalidate>
  <div class="field" class:field--error={!!errors.name}>
    <label for="name">Full name <span aria-label="required">*</span></label>
    <input
      id="name" type="text" autocomplete="name" required
      aria-required="true"
      aria-invalid={!!errors.name}
      aria-describedby={errors.name ? 'name-error' : 'name-hint'}
      bind:value={name}
    />
    {#if !errors.name}
      <p id="name-hint" class="field-hint">Enter your first and last name</p>
    {:else}
      <p id="name-error" class="field-error" role="alert">{errors.name}</p>
    {/if}
  </div>

  {#if submitAttempted && Object.keys(errors).length > 0}
    <div role="alert" aria-live="assertive" class="error-summary" tabindex="-1">
      <h2>Please fix the following errors:</h2>
      <ul>
        {#each Object.entries(errors) as [field, message]}
          <li><a href="#{field}">{message}</a></li>
        {/each}
      </ul>
    </div>
  {/if}
</form>
```

## Bits UI — Headless Accessible Primitives

```svelte
<script>
  import { Dialog } from 'bits-ui';
</script>

<!-- Bits UI handles: ARIA, keyboard nav, focus trap, scroll lock -->
<Dialog.Root bind:open={isOpen}>
  <Dialog.Portal>
    <Dialog.Overlay />
    <Dialog.Content>
      <Dialog.Title>Confirm action</Dialog.Title>
      <Dialog.Description>This cannot be undone.</Dialog.Description>
      <button onclick={() => isOpen = false}>Cancel</button>
      <button onclick={confirm}>Confirm</button>
      <Dialog.Close aria-label="Close dialog" />
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>
```

Use Bits UI or Melt UI for: Dialog, Select/Combobox, Tabs, Accordion, Toast, Tooltip, Popover.

## &lt;svelte:boundary&gt; Error Boundaries

```svelte
<svelte:boundary>
  <FeatureComponent />

  {#snippet failed(error, reset)}
    <div role="alert" class="error-boundary">
      <h2>This section couldn't load</h2>
      <p>An unexpected error occurred.</p>
      <button onclick={reset}>Try again</button>
    </div>
  {/snippet}
</svelte:boundary>
```

## Additional Resources

- [a11y-testing-reference.md](a11y-testing-reference.md) — Screen reader testing, axe-core integration, Svelte-specific mistakes, audit checklist

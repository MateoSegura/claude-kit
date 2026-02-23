---
name: coding-frontend-svelte-knowledge:accessibility
description: "WCAG 2.2 AA compliance patterns for Svelte and SvelteKit: compiler a11y warnings, route announcements, focus management, skip links, ARIA live regions, keyboard navigation, form accessibility, color contrast requirements, and headless component library usage."
---

# Accessibility Quick Reference (WCAG 2.2 AA)

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

SvelteKit auto-announces route changes to screen readers via an `aria-live` region. This works automatically when you use SvelteKit navigation. To customize:

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

<!-- Hidden live region — SvelteKit renders this automatically -->
<!-- Only add this if you need custom announcement text -->
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  class="sr-only"
>
  {announcement}
</div>
```

```css
/* Screen-reader only utility */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

## Skip Link Pattern

Required for keyboard users to bypass navigation on every page.

```svelte
<!-- src/routes/+layout.svelte — place as first element in body -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<nav><!-- navigation --></nav>

<main id="main-content" tabindex="-1">
  <!-- tabindex="-1" allows focus to be set programmatically -->
  {@render children()}
</main>
```

```css
.skip-link {
  position: absolute;
  top: -100%;
  left: var(--space-4);
  z-index: 9999;
  padding: var(--space-2) var(--space-4);
  background: var(--color-brand);
  color: white;
  border-radius: 0 0 var(--radius-md) var(--radius-md);
  text-decoration: none;
  font-weight: 600;
  transition: top 100ms ease;
}

.skip-link:focus {
  top: 0; /* appears when focused via Tab key */
}
```

## Focus Management After Navigation

```svelte
<!-- src/routes/+layout.svelte -->
<script>
  import { afterNavigate } from '$app/navigation';

  afterNavigate(({ type }) => {
    // Don't interfere with browser's native back/forward focus restoration
    if (type === 'popstate') return;

    // Move focus to main content after navigation
    const main = document.getElementById('main-content');
    main?.focus();
  });
</script>
```

```svelte
<!-- After in-page actions — return focus to trigger -->
<script>
  let modalTrigger: HTMLButtonElement;
  let modalOpen = $state(false);

  function openModal() {
    modalOpen = true;
  }

  function closeModal() {
    modalOpen = false;
    // Return focus to the element that opened the modal
    modalTrigger?.focus();
  }
</script>

<button bind:this={modalTrigger} onclick={openModal}>Open</button>

{#if modalOpen}
  <Modal onclose={closeModal} />
{/if}
```

## ARIA Live Regions

Use for content that updates without a page navigation.

```svelte
<!-- Status messages — polite (waits for user to finish what they're doing) -->
<div role="status" aria-live="polite" aria-atomic="true">
  {#if saveStatus === 'saving'}
    Saving...
  {:else if saveStatus === 'saved'}
    Changes saved
  {/if}
</div>

<!-- Alerts — assertive (interrupts immediately) -->
<!-- Use sparingly — only for important, time-sensitive errors -->
<div role="alert" aria-live="assertive">
  {#if errorMessage}
    {errorMessage}
  {/if}
</div>

<!-- Search results count -->
<div aria-live="polite" aria-atomic="true" class="sr-only">
  {#if searchResults}
    {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} for "{searchQuery}"
  {/if}
</div>
```

**aria-live values:**
- `polite` — announces after user is idle (use for most updates)
- `assertive` — announces immediately, interrupting (use for errors only)
- `off` — no announcement (default)

**aria-atomic:**
- `true` — read entire region content on any change
- `false` — read only changed portions (default)

## Form Accessibility

```svelte
<form onsubmit={handleSubmit} novalidate>
  <!-- Always associate labels with inputs -->
  <div class="field" class:field--error={!!errors.name}>
    <label for="name">
      Full name
      <span aria-label="required" class="required-indicator">*</span>
    </label>
    <input
      id="name"
      type="text"
      name="name"
      autocomplete="name"
      required
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

  <!-- Error summary at top of form on submit -->
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

## Color Contrast Requirements

| Text Type | Minimum Ratio (AA) | Enhanced Ratio (AAA) |
|-----------|-------------------|---------------------|
| Normal text (< 18pt / < 14pt bold) | 4.5:1 | 7:1 |
| Large text (≥ 18pt or ≥ 14pt bold) | 3:1 | 4.5:1 |
| UI components / icons | 3:1 | — |
| Decorative elements | None | — |
| Logo / brand marks | None | — |

```css
/* oklch makes contrast prediction easier */
/* High lightness difference = high contrast */
:root {
  /* These combinations meet 4.5:1 minimum */
  --color-fg-on-white: oklch(15% 0 0);      /* ~15:1 on white */
  --color-fg-subtle: oklch(40% 0 0);         /* ~5.9:1 on white */
  --color-fg-muted: oklch(50% 0 0);          /* ~3.9:1 — only for large text */

  /* Brand color — check contrast before using on white */
  --color-brand: oklch(40% 0.18 250);        /* ~6.2:1 on white */
}
```

Use [Accessible Perch](https://accessibleperch.com/) or browser DevTools to verify oklch contrast ratios.

## Focus Visible Styling

```css
/* Remove browser default, add consistent custom style */
:focus { outline: none; }

/* Show focus ring only for keyboard navigation */
:focus-visible {
  outline: 2px solid var(--color-brand);
  outline-offset: 2px;
  border-radius: 2px;
}

/* Ensure focus is visible on dark backgrounds */
.dark-surface :focus-visible {
  outline-color: white;
  box-shadow: 0 0 0 4px oklch(0% 0 0 / 30%);
}
```

## Keyboard Navigation Requirements

Any interactive element must be keyboard accessible:

| Control | Keys Required |
|---------|--------------|
| Button | Enter, Space |
| Link | Enter |
| Checkbox | Space |
| Radio group | Arrow keys (roving tabindex) |
| Menu | Arrow keys, Enter, Escape |
| Dialog | Escape to close, Tab cycles within |
| Tabs | Arrow keys to switch, Tab/Shift+Tab for panel |
| Combobox | Arrow keys, Enter, Escape |
| Slider | Arrow keys, Home, End |
| Datepicker | Arrow keys, Enter, Page Up/Down |

## Using Headless Libraries for Accessible Primitives

```svelte
<!-- Bits UI — accessible, headless, Svelte-native -->
<script>
  import { Dialog, Select, Tabs, Accordion } from 'bits-ui';
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

**Don't re-implement these from scratch:**
- Modal/Dialog
- Dropdown/Select/Combobox
- Tabs
- Accordion
- Toast/Notifications
- Tooltip
- Popover

Use Bits UI, Melt UI, or other headless libraries that implement WAI-ARIA patterns correctly.

## &lt;svelte:boundary&gt; Error Boundaries

```svelte
<!-- Prevent a crashed component from taking down the whole page -->
<svelte:boundary>
  <FeatureComponent />

  {#snippet failed(error, reset)}
    <div role="alert" class="error-boundary">
      <h2>This section couldn't load</h2>
      <p>An unexpected error occurred. The rest of the page is still available.</p>
      <button onclick={reset}>Try again</button>
    </div>
  {/snippet}
</svelte:boundary>
```

## Semantic HTML Elements

Use HTML semantics before adding ARIA. Semantic HTML is more robust.

```svelte
<!-- Prefer semantic HTML over div soup -->
<main>           <!-- main content landmark -->
<nav>            <!-- navigation landmark -->
<aside>          <!-- sidebar / complementary -->
<section>        <!-- thematic grouping (use sparingly) -->
<article>        <!-- self-contained content -->
<header>         <!-- introductory content / banner -->
<footer>         <!-- footer content -->
<h1>–<h6>       <!-- heading hierarchy — don't skip levels -->
<ul>/<ol>/<li>   <!-- lists — screen readers announce count -->
<table>          <!-- tabular data only (not layout) -->
<button>         <!-- interactive action -->
<a href>         <!-- navigation -->
<time datetime>  <!-- machine-readable dates -->
<abbr title>     <!-- abbreviations -->
<figure>/<figcaption> <!-- media with caption -->
```

## Additional Resources

- [a11y-testing-reference.md](a11y-testing-reference.md) — Screen reader testing patterns (VoiceOver, NVDA, JAWS), automated testing with axe-core and Playwright, audit checklist, WCAG 2.2 new criteria (2.5.7–2.5.8, 3.2.6, 3.3.7–3.3.8)

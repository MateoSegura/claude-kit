---
name: core-frontend:accessibility
description: "WCAG 2.2 AA compliance patterns: semantic HTML, ARIA roles/states/properties, keyboard navigation, focus management, skip links, live regions, form accessibility, color contrast, and screen reader testing."
user-invocable: false
---

# Accessibility Quick Reference (WCAG 2.2 AA)

## Semantic HTML First

Use HTML semantics before adding ARIA. Semantic HTML is more robust and better supported.

```html
<!-- Prefer semantic HTML over div soup -->
<main>             <!-- main content landmark -->
<nav>              <!-- navigation landmark -->
<aside>            <!-- sidebar / complementary -->
<section>          <!-- thematic grouping (use sparingly) -->
<article>          <!-- self-contained content -->
<header>           <!-- introductory content / banner -->
<footer>           <!-- footer content -->
<h1>-<h6>          <!-- heading hierarchy — don't skip levels -->
<ul>/<ol>/<li>     <!-- lists — screen readers announce count -->
<table>            <!-- tabular data only (not layout) -->
<button>           <!-- interactive action -->
<a href>           <!-- navigation -->
<time datetime>    <!-- machine-readable dates -->
<abbr title>       <!-- abbreviations -->
<figure>/<figcaption> <!-- media with caption -->
```

**Rule**: If a native HTML element provides the behavior you need, use it instead of building a custom widget with ARIA.

## Skip Link Pattern

Required for keyboard users to bypass navigation on every page.

```html
<!-- Place as first element in body -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<nav><!-- navigation --></nav>

<main id="main-content" tabindex="-1">
  <!-- tabindex="-1" allows focus to be set programmatically -->
  <!-- page content -->
</main>
```

```css
.skip-link {
  position: absolute;
  top: -100%;
  left: 1rem;
  z-index: 9999;
  padding: 0.5rem 1rem;
  background: var(--color-brand, #0066cc);
  color: white;
  border-radius: 0 0 0.5rem 0.5rem;
  text-decoration: none;
  font-weight: 600;
  transition: top 100ms ease;
}

.skip-link:focus {
  top: 0; /* appears when focused via Tab key */
}
```

## Focus Management

- **After navigation:** Move focus to `#main-content` so screen reader users know the page changed
- **After modal close:** Return focus to the element that triggered the modal
- **Focus trap in modals:** Tab must cycle within the modal; focus must not escape to the page behind

## ARIA Live Regions

Use for content that updates dynamically without a page navigation.

```html
<!-- Status messages — polite (waits for user to finish) -->
<div role="status" aria-live="polite" aria-atomic="true">
  Changes saved
</div>

<!-- Alerts — assertive (interrupts immediately) -->
<!-- Use sparingly — only for important, time-sensitive errors -->
<div role="alert" aria-live="assertive">
  Session expired. Please log in again.
</div>

<!-- Search results count -->
<div aria-live="polite" aria-atomic="true" class="sr-only">
  12 results for "design tokens"
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

- Always associate `<label>` with `<input>` via `for`/`id`
- Mark required fields with `aria-required="true"` AND visible indicator
- Use `aria-invalid="true"` on fields with errors
- Link error text via `aria-describedby` pointing to error element ID
- Use `role="alert"` on error messages for screen reader announcement
- Show error summary at top of form on submit with links to each errored field
- Use `autocomplete` attributes for common fields (name, email, address)

## Color Contrast Requirements

| Text Type | Minimum Ratio (AA) | Enhanced Ratio (AAA) |
|-----------|-------------------|---------------------|
| Normal text (< 18pt / < 14pt bold) | 4.5:1 | 7:1 |
| Large text (>= 18pt or >= 14pt bold) | 3:1 | 4.5:1 |
| UI components / icons | 3:1 | -- |
| Decorative elements | None | -- |
| Logo / brand marks | None | -- |

## Focus Visible Styling

Use `:focus-visible` (not `:focus`) so focus rings only appear for keyboard users:

```css
:focus-visible {
  outline: 2px solid var(--color-brand, #0066cc);
  outline-offset: 2px;
}
```

## Keyboard Navigation Requirements

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

## Headless Component Libraries

For complex widgets (modals, selects, tabs, accordions), use a headless library instead of building from scratch: Radix UI / React Aria (React), Bits UI (Svelte), Radix Vue (Vue), Angular CDK, Shoelace (web components).

## Additional Resources

- [a11y-reference.md](a11y-reference.md) — WCAG 2.2 new criteria, screen reader testing (VoiceOver, NVDA, JAWS), automated testing with axe-core, manual audit checklist, common mistakes

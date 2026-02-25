# Accessibility Testing Reference

## WCAG 2.2 New Criteria (vs WCAG 2.1)

WCAG 2.2 (October 2023) added 9 new success criteria at AA and AAA levels:

| SC | Level | Name | What it means |
|----|-------|------|---------------|
| 2.4.11 | AA | Focus Not Obscured (Minimum) | Focused component not completely hidden by sticky headers/footers |
| 2.4.12 | AAA | Focus Not Obscured (Enhanced) | Focused component not partially hidden |
| 2.4.13 | AAA | Focus Appearance | Focus indicator meets minimum size and contrast |
| 2.5.7 | AA | Dragging Movements | All drag-and-drop has a pointer alternative |
| 2.5.8 | AA | Target Size (Minimum) | Touch targets at least 24×24 CSS pixels |
| 3.2.6 | AA | Consistent Help | Help links appear in consistent location |
| 3.3.7 | A | Redundant Entry | Don't make users re-enter info in the same session |
| 3.3.8 | AA | Accessible Authentication (Minimum) | No cognitive test required for auth |
| 3.3.9 | AAA | Accessible Authentication (Enhanced) | No object recognition in auth |

### 2.5.8 — Target Size Implementation

```css
/* Minimum 24x24px touch target — use padding to extend without visual change */
.icon-btn {
  padding: var(--space-2); /* extends hit area */
  min-width: 24px;
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* Recommended: 44x44px for primary touch targets (iOS HIG / Android guideline) */
.touch-target {
  min-height: 44px;
  min-width: 44px;
}
```

### 2.4.11 — Focus Not Obscured

```css
/* Account for sticky header height in scroll behavior */
:root {
  --header-height: 64px;
}

html {
  scroll-padding-top: calc(var(--header-height) + var(--space-4));
}

/* Ensure focused elements scroll into view above sticky header */
:focus-visible {
  scroll-margin-top: calc(var(--header-height) + var(--space-2));
}
```

## Screen Reader Testing

### macOS VoiceOver (Built-in)

```
Enable:  Cmd + F5 (or System Settings > Accessibility > VoiceOver)
Navigate: Tab (interactive), Arrow keys (all content)
Click:   Ctrl + Option + Space
Read:    Ctrl + Option + A (read all from cursor)
Rotor:   Ctrl + Option + U (navigate by headings, links, form controls)
Stop:    Ctrl
```

**Key things to test:**
1. Is the page title meaningful?
2. Are headings in logical order (h1 → h2 → h3)?
3. Are all images described?
4. Are form fields properly labeled?
5. Are errors announced?
6. Does route change announce new page?
7. Does modal open/close properly manage focus?

### NVDA (Windows, Free)

```
Enable:  Ctrl + Alt + N
Navigate: Tab (interactive), Insert + F7 (elements list)
Read:    Insert + Down Arrow (read from here)
Headings: H key (cycle through headings)
Links:    K key (cycle through links)
Forms:    F key (cycle through form fields)
Stop:    Ctrl
```

### JAWS (Windows, Commercial)

```
Navigate: Same as NVDA with different modifier (typically Insert)
Headings: Insert + F6 (list all headings)
Landmark: ; key (cycle through landmarks)
Forms:    F key
```

**Cross-browser testing matrix:**
| Screen Reader | Browser | Platform |
|---------------|---------|----------|
| VoiceOver | Safari | macOS |
| VoiceOver | Safari | iOS |
| NVDA | Chrome/Firefox | Windows |
| JAWS | Chrome/Edge | Windows |
| TalkBack | Chrome | Android |

## Automated Testing with axe-core

```typescript
// playwright.config.ts — add axe to E2E tests
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await injectAxe(page);
  });

  test('home page has no violations', async ({ page }) => {
    await page.goto('/');
    await checkA11y(page, undefined, {
      runOnly: {
        type: 'tag',
        values: ['wcag2a', 'wcag2aa', 'wcag22aa', 'best-practice']
      }
    });
  });

  test('form is accessible', async ({ page }) => {
    await page.goto('/contact');
    // Check specific component
    await checkA11y(page, '#contact-form');
  });
});
```

```bash
# Install axe-playwright
npm install --save-dev axe-playwright @axe-core/playwright
```

### Vitest + axe-core for Component Testing

```typescript
// Button.test.ts
import { render } from '@testing-library/svelte';
import { axe, toHaveNoViolations } from 'jest-axe';
import Button from './Button.svelte';

expect.extend(toHaveNoViolations);

test('Button has no accessibility violations', async () => {
  const { container } = render(Button, { props: { label: 'Click me' } });
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

## Manual Audit Checklist

### Navigation and Structure
- [ ] Page has meaningful `<title>` — unique, describes content
- [ ] One `<h1>` per page
- [ ] Heading hierarchy is logical (no skipped levels)
- [ ] All landmark regions present: `<main>`, `<nav>`, `<header>`, `<footer>`
- [ ] Skip link is first focusable element
- [ ] Keyboard-only: all interactive elements reachable
- [ ] Tab order follows visual reading order
- [ ] No keyboard traps (except modals)

### Images and Media
- [ ] All images have alt text
- [ ] Decorative images have `alt=""`
- [ ] Complex images (charts, diagrams) have long description
- [ ] Videos have captions
- [ ] Audio-only has transcript
- [ ] No auto-playing media with sound

### Forms
- [ ] Every input has a visible, associated label
- [ ] Error messages are programmatically associated (`aria-describedby`)
- [ ] Required fields marked in label AND `aria-required="true"`
- [ ] Error summary at top of form on validation failure
- [ ] Success messages announced via `aria-live`

### Interactive Elements
- [ ] All custom controls have appropriate ARIA role
- [ ] State changes announced (`aria-expanded`, `aria-selected`, `aria-pressed`)
- [ ] Modal: focus trapped inside, Escape closes, focus returns to trigger
- [ ] Tooltips accessible via keyboard (not just hover)
- [ ] Dropdown: keyboard navigable, Escape dismisses

### Visual
- [ ] Text contrast ≥ 4.5:1 (normal), ≥ 3:1 (large/UI)
- [ ] Focus indicator always visible (`:focus-visible` styled)
- [ ] No information conveyed by color alone
- [ ] Text resizable to 200% without horizontal scroll
- [ ] Page usable at 400% zoom (SC 1.4.10 Reflow)
- [ ] Reduced motion respected

## Common Svelte A11y Mistakes

### Mistake 1: onclick without keyboard equivalent

```svelte
<!-- WRONG — only responds to mouse -->
<div onclick={open}>Open menu</div>

<!-- RIGHT — button handles keyboard automatically -->
<button onclick={open}>Open menu</button>

<!-- Or if semantic div needed -->
<div
  role="button"
  tabindex="0"
  onclick={open}
  onkeydown={(e) => e.key === 'Enter' && open()}
>
  Open menu
</div>
```

### Mistake 2: Icon buttons without accessible name

```svelte
<!-- WRONG — screen reader announces "button" with no context -->
<button onclick={save}><SaveIcon /></button>

<!-- RIGHT — explicit label -->
<button onclick={save} aria-label="Save document">
  <SaveIcon aria-hidden="true" />
</button>

<!-- Or using visually-hidden text -->
<button onclick={save}>
  <SaveIcon aria-hidden="true" />
  <span class="sr-only">Save document</span>
</button>
```

### Mistake 3: Dynamic content with no announcement

```svelte
<!-- WRONG — content changes with no notification -->
<div class="count">{items.length} items</div>

<!-- RIGHT — announce count changes -->
<div
  class="count"
  role="status"
  aria-live="polite"
  aria-atomic="true"
>
  {items.length} item{items.length !== 1 ? 's' : ''}
</div>
```

### Mistake 4: Custom modal without focus trap

```svelte
<!-- WRONG — focus escapes the modal, screen behind is still interactive -->
{#if isOpen}
  <div class="modal">
    <h2>Title</h2>
    <button onclick={() => isOpen = false}>Close</button>
  </div>
{/if}

<!-- RIGHT — use Bits UI Dialog which handles this correctly -->
<Dialog.Root bind:open={isOpen}>
  <Dialog.Content>
    <!-- focus is automatically trapped here -->
    <Dialog.Title>Title</Dialog.Title>
    <Dialog.Close>Close</Dialog.Close>
  </Dialog.Content>
</Dialog.Root>
```

### Mistake 5: Toggling visibility with CSS instead of DOM

```svelte
<!-- WRONG — hidden content is still reachable by keyboard and screen reader -->
<div class:hidden={!isOpen}>
  <!-- accessible even when hidden -->
</div>

<!-- RIGHT — remove from DOM when not needed -->
{#if isOpen}
  <div>Content here</div>
{/if}

<!-- Or: use hidden attribute -->
<div hidden={!isOpen}>Content</div>

<!-- Or: use aria-hidden for purely visual toggle -->
<div aria-hidden={!isOpen}>Decorative content</div>
```

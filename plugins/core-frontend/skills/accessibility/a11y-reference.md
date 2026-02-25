# Accessibility Testing Reference

## WCAG 2.2 New Criteria (vs WCAG 2.1)

WCAG 2.2 (October 2023) added 9 new success criteria at AA and AAA levels:

| SC | Level | Name | What it means |
|----|-------|------|---------------|
| 2.4.11 | AA | Focus Not Obscured (Minimum) | Focused component not completely hidden by sticky headers/footers |
| 2.4.12 | AAA | Focus Not Obscured (Enhanced) | Focused component not partially hidden |
| 2.4.13 | AAA | Focus Appearance | Focus indicator meets minimum size and contrast |
| 2.5.7 | AA | Dragging Movements | All drag-and-drop has a pointer alternative |
| 2.5.8 | AA | Target Size (Minimum) | Touch targets at least 24x24 CSS pixels |
| 3.2.6 | AA | Consistent Help | Help links appear in consistent location |
| 3.3.7 | A | Redundant Entry | Don't make users re-enter info in the same session |
| 3.3.8 | AA | Accessible Authentication (Minimum) | No cognitive test required for auth |
| 3.3.9 | AAA | Accessible Authentication (Enhanced) | No object recognition in auth |

### 2.5.8 — Target Size Implementation

```css
/* Minimum 24x24px touch target — use padding to extend without visual change */
.icon-btn {
  padding: 0.5rem;
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
  scroll-padding-top: calc(var(--header-height) + 1rem);
}

/* Ensure focused elements scroll into view above sticky header */
:focus-visible {
  scroll-margin-top: calc(var(--header-height) + 0.5rem);
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

**Key things to test:**
1. Is the page title meaningful?
2. Are headings in logical order (h1 -> h2 -> h3)?
3. Are all images described?
4. Are form fields properly labeled?
5. Are errors announced?
6. Does route change announce new page?
7. Does modal open/close properly manage focus?

## Automated Testing with axe-core

### Playwright Integration

```typescript
// E2E accessibility test with Playwright + axe
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
    await checkA11y(page, '#contact-form');
  });
});
```

### Component Testing

```typescript
// Component-level a11y test (any testing library)
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('Button has no accessibility violations', async () => {
  // Render your component (framework-specific)
  const container = document.getElementById('test-root');
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
- [ ] Text contrast >= 4.5:1 (normal), >= 3:1 (large/UI)
- [ ] Focus indicator always visible (`:focus-visible` styled)
- [ ] No information conveyed by color alone
- [ ] Text resizable to 200% without horizontal scroll
- [ ] Page usable at 400% zoom (SC 1.4.10 Reflow)
- [ ] Reduced motion respected

## Common Accessibility Mistakes

### Mistake 1: onclick without keyboard equivalent

```html
<!-- WRONG — only responds to mouse -->
<div onclick="open()">Open menu</div>

<!-- RIGHT — button handles keyboard automatically -->
<button onclick="open()">Open menu</button>

<!-- Or if semantic div needed -->
<div
  role="button"
  tabindex="0"
  onclick="open()"
  onkeydown="if(event.key==='Enter') open()"
>
  Open menu
</div>
```

### Mistake 2: Icon buttons without accessible name

```html
<!-- WRONG — screen reader announces "button" with no context -->
<button><svg><!-- save icon --></svg></button>

<!-- RIGHT — explicit label -->
<button aria-label="Save document">
  <svg aria-hidden="true"><!-- save icon --></svg>
</button>

<!-- Or using visually-hidden text -->
<button>
  <svg aria-hidden="true"><!-- save icon --></svg>
  <span class="sr-only">Save document</span>
</button>
```

### Mistake 3: Dynamic content with no announcement

```html
<!-- WRONG — content changes with no notification -->
<div class="count">5 items</div>

<!-- RIGHT — announce count changes -->
<div
  class="count"
  role="status"
  aria-live="polite"
  aria-atomic="true"
>
  5 items
</div>
```

### Mistake 4: Custom modal without focus trap

Always use a headless component library for modals, or implement:
1. Focus trap (Tab cycles within modal only)
2. Escape key closes the modal
3. Background scroll lock (`overflow: hidden` on body)
4. Focus returns to trigger element on close
5. `aria-modal="true"` and `role="dialog"`

### Mistake 5: Hiding content with CSS instead of removing from DOM

```html
<!-- WRONG — hidden content is still reachable by keyboard and screen reader -->
<div style="display:none" class="visually-hidden-but-focusable">
  <!-- Using CSS classes that only visually hide -->
</div>

<!-- RIGHT — use hidden attribute or remove from DOM -->
<div hidden>Content hidden from everyone</div>

<!-- Or use aria-hidden for purely decorative elements -->
<div aria-hidden="true">Decorative content</div>
```

## ARIA Patterns Reference

Follow the [WAI-ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/) for canonical implementations of:
- Accordion
- Alert / Alert Dialog
- Breadcrumb
- Carousel
- Combobox
- Dialog (Modal)
- Disclosure
- Feed
- Grid / Treegrid
- Listbox
- Menu / Menu Button
- Meter
- Radio Group
- Slider
- Spinbutton
- Switch
- Tabs
- Toolbar
- Tooltip
- Tree View

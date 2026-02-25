# WCAG 2.2 AA Automated Audit Checklist

Organized by WCAG criterion. Items marked **[automated]** can be verified with axe. Items marked **[manual]** require human testing.

---

## Perceivable

### 1.1 Text Alternatives
- [ ] **[automated]** All `<img>` elements have non-empty `alt` attribute (`image-alt`)
- [ ] **[automated]** Decorative images use `alt=""` or `role="presentation"` (`image-redundant-alt`)
- [ ] **[automated]** Icon buttons have accessible text (`button-name`)
- [ ] **[manual]** Alt text is descriptive and meaningful, not just the filename

### 1.3 Adaptable
- [ ] **[automated]** HTML semantics are correct: headings use `<h1>`–`<h6>`, not styled `<div>` (`heading-order`)
- [ ] **[automated]** Lists use `<ul>/<ol>` not just `<div>` elements (`list`)
- [ ] **[automated]** Form inputs have associated `<label>` elements (`label`)
- [ ] **[automated]** Tables have `<caption>` or `aria-label` and use `<th>` for headers (`table-duplicate-name`)
- [ ] **[automated]** Landmark regions are present: `<main>`, `<nav>`, `<header>` (`landmark-one-main`, `region`)
- [ ] **[manual]** Reading order makes sense when CSS is removed

### 1.4 Distinguishable
- [ ] **[automated]** Normal text (< 18pt) has 4.5:1 contrast ratio (`color-contrast`)
- [ ] **[automated]** Large text (≥ 18pt or ≥ 14pt bold) has 3:1 contrast ratio (`color-contrast`)
- [ ] **[automated]** Non-text UI components have 3:1 contrast ratio (`color-contrast-enhanced`)
- [ ] **[manual]** Information is not conveyed by color alone
- [ ] **[manual]** Text can be resized to 200% without horizontal scrolling

---

## Operable

### 2.1 Keyboard Accessible
- [ ] **[automated]** All interactive elements are keyboard focusable (no `tabindex="-1"` on interactive elements — `tabindex`)
- [ ] **[automated]** No keyboard traps outside intentional modal dialogs
- [ ] **[manual]** All functionality is operable via keyboard
- [ ] **[manual]** Keyboard shortcuts do not conflict with browser/OS shortcuts

### 2.4 Navigable
- [ ] **[automated]** Page has a descriptive `<title>` (`document-title`)
- [ ] **[automated]** Focus is visible — axe detects `outline: none` with no replacement (`focus-visible` via best-practice)
- [ ] **[automated]** Headings are present and follow hierarchical order (`heading-order`)
- [ ] **[automated]** Link purpose is clear from text or context (`link-name`)
- [ ] **[manual]** Focus order is logical and matches visual order
- [ ] **[manual]** Skip navigation link is present and functional

### 2.5 Input Modalities (WCAG 2.1)
- [ ] **[automated]** Touch targets are at least 24×24 CSS pixels (WCAG 2.2 — `target-size`)
- [ ] **[manual]** All functionality achievable with single pointer (no drag-only interactions)
- [ ] **[manual]** Motion-activated features have alternatives

---

## Understandable

### 3.1 Readable
- [ ] **[automated]** Page `<html>` element has `lang` attribute (`html-has-lang`, `html-lang-valid`)
- [ ] **[automated]** Language of passages in different language have `lang` on the element

### 3.2 Predictable
- [ ] **[manual]** No unexpected context changes on focus
- [ ] **[manual]** No unexpected context changes on input

### 3.3 Input Assistance
- [ ] **[automated]** Required fields are marked with `required` or `aria-required` — caught by `label` rule
- [ ] **[automated]** Error messages are programmatically associated with inputs (`aria-errormessage`, `aria-describedby`)
- [ ] **[automated]** Error messages use `role="alert"` or `aria-live` (`aria-allowed-attr`)
- [ ] **[manual]** Error messages describe the problem and how to fix it

---

## Robust

### 4.1 Compatible
- [ ] **[automated]** No duplicate IDs (`duplicate-id`, `duplicate-id-active`, `duplicate-id-aria`)
- [ ] **[automated]** ARIA roles are valid (`aria-allowed-role`, `aria-valid-attr`)
- [ ] **[automated]** ARIA attributes are valid for the role (`aria-required-attr`)
- [ ] **[automated]** ARIA required children are present (`aria-required-children`)
- [ ] **[automated]** Custom interactive elements have name, role, value (`button-name`, `link-name`)
- [ ] **[automated]** Status messages use `role="status"` or `role="alert"` (`status-messages`)

---

## Per-Component A11y Verification Matrix

Run this checklist for every interactive component before marking it complete:

| Check | Tool | Component Type |
|-------|------|----------------|
| Passes axe WCAG 2.2 AA | vitest-axe | All |
| Has visible focus ring | vitest/browser `toBeFocused` | Buttons, links, inputs |
| Keyboard activates action | userEvent.keyboard | Buttons, checkboxes |
| Screen reader label present | `getByRole` with name | Buttons, inputs, icons |
| Error state is announced | `role="alert"` check | Forms |
| Loading state is announced | `aria-live` check | Async components |
| Heading hierarchy correct | `heading-order` axe rule | Pages, modals |
| Color contrast passes | `color-contrast` axe rule | Text, UI elements |

---

## Svelte-Specific A11y Pitfalls

### 1. Conditional Rendering Hiding Content from Screen Readers

**Problem:** `{#if condition}` completely removes elements from DOM. Screen readers do not read content that transitions out via CSS `display:none` either — use `aria-hidden` instead of CSS transitions for non-destructive visibility.

**Bad pattern:**
```svelte
<!-- Element is hidden but still in DOM — SR still reads it -->
<div class:hidden={!visible}>
  <p>Important message</p>
</div>
```

**Good pattern:**
```svelte
<!-- Fully removed from DOM — SR cannot read stale content -->
{#if visible}
  <div>
    <p>Important message</p>
  </div>
{/if}

<!-- Or for animated transitions — use aria-hidden for SR -->
<div aria-hidden={!visible} class:hidden={!visible}>
  <p>Decorative content</p>
</div>
```

### 2. $effect Causing Focus Loss

**Problem:** `$effect` can re-render DOM nodes, destroying focus on the currently focused element.

**Detection:**
```typescript
it('does not lose focus when data refreshes', async () => {
  render(LiveDataTable, { refreshInterval: 1000 });
  const firstRow = page.getByRole('row').nth(1);
  await firstRow.focus();
  // Simulate a data refresh effect
  await vi.advanceTimersByTime(1000);
  // Focus should remain on the same row or a logical equivalent
  await expect.element(page.getByRole('row').nth(1)).toBeFocused();
});
```

**Fix:** Use `key` blocks only when necessary, prefer in-place updates over re-mounting.

### 3. Snippet Rendering Breaking Heading Hierarchy

**Problem:** Snippets that render headings might create invalid heading hierarchies depending on where they are inserted.

**Detection:**
```typescript
it('maintains correct heading hierarchy with custom snippet', async () => {
  render(PageLayout, {
    sidebar: createRawSnippet(() => ({
      render: () => '<h3>Related Articles</h3>',  // h3 — valid if page has h1 > h2 > h3
    })),
  });

  const results = await axe(document.body, {
    runOnly: { type: 'rule', values: ['heading-order'] },
  });
  expect(results).toHaveNoViolations();
});
```

### 4. Dynamic aria-label Not Updating

**Problem:** `aria-label` bound to a `$derived` or `$state` value may not update screen reader announcements if the DOM node is not re-rendered.

**Test:**
```typescript
it('updates aria-label when cart item count changes', async () => {
  render(CartButton, { itemCount: 0 });
  await expect.element(
    page.getByRole('button', { name: 'Cart (0 items)' })
  ).toBeVisible();

  // Simulate adding item
  await page.getByRole('button', { name: 'Add to cart' }).click();
  await expect.element(
    page.getByRole('button', { name: 'Cart (1 item)' })
  ).toBeVisible();
});
```

### 5. Form Enhancement Breaking Accessible Error Association

**Problem:** SvelteKit's `enhance` action can replace form elements after server action, losing the error-to-input association (`aria-describedby`).

**Test:**
```typescript
test('form errors remain associated with inputs after enhance', async ({ page }) => {
  await page.goto('/contact');
  await page.getByRole('button', { name: 'Submit' }).click();

  // After enhance rehydration, axe should still find proper associations
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2aa'])
    .analyze();
  expect(results.violations).toEqual([]);
});
```

# Human-Centered Design — UX Patterns Reference

## Empty States

An empty state is an opportunity to guide users, not a failure to show content.

**Empty state anatomy:**
1. **Visual**: Illustration or icon (keep it light and helpful)
2. **Headline**: What's missing (not "Nothing here")
3. **Description**: Why it's empty + what to do
4. **Call to action**: Primary action to resolve the empty state

```html
<div class="empty-state" role="status">
  <!-- illustration or icon -->
  <h2>No projects yet</h2>
  <p>Projects help you organize your work. Create your first project to get started.</p>
  <a href="/projects/new" class="btn btn--primary">Create your first project</a>
</div>
```

**Types of empty states:**
- First use: welcome + tutorial action
- Search no results: show query, suggest alternatives
- Filter no results: show active filters, offer to clear
- Error no data: explain error, offer retry

## Error States

Every error state needs: what happened, why, and what to do next.

```html
<!-- Network error with retry -->
<div class="error-state" role="alert">
  <h3>Couldn't load posts</h3>
  <p>Check your internet connection and try again.</p>
  <button onclick="retry()">Try again</button>
</div>
```

**Error messaging principles:**
- Don't say "Error 422" — say what happened
- Don't blame the user ("You entered an invalid email")
- Do be specific ("Email must contain @domain.com")
- Do suggest the fix in the error message

## Confirmation Dialogs

Reserve confirmation for destructive or irreversible actions only.

**Prefer undo over confirmation:**
- Archive instead of delete (with restore option)
- Soft delete with 30-day recovery
- Toast with undo button: "Project deleted - Undo (5s)"

**When confirmation IS needed:**
- Permanent data deletion
- Actions affecting other users
- Expensive operations (billing changes, bulk updates)

**Confirmation dialog rules:**
- Title: describe the action ("Delete project?"), not generic ("Are you sure?")
- Body: state the consequence clearly
- Primary action button: use the action name ("Delete project"), not "OK" or "Yes"
- Destructive buttons use red/danger styling
- Cancel is always available

## Form UX Patterns

### Inline Validation Timing

**Validation timing rules:**
- Don't validate on first keystroke — frustrating
- Validate on blur (when user leaves field)
- Clear errors while typing (once field has been validated once)
- Re-validate on blur after typing
- Show all errors on submit

### Loading States in Forms

```html
<button type="submit" disabled aria-busy="true">
  <span class="spinner" aria-hidden="true"></span>
  Saving...
</button>
```

**Button state progression:**
1. Default: "Save changes"
2. Submitting: "Saving..." (disabled, with spinner)
3. Success: "Saved!" (brief confirmation, then revert)
4. Error: "Save changes" (re-enabled, error message shown elsewhere)

### Multi-Step Forms (Wizards)

- Show progress indicator (step 2 of 4)
- Allow going back without losing data
- Validate each step before proceeding
- Show summary before final submission
- Save progress if possible (drafts)

## Notification System Design

### Toast Notifications

**Toast rules:**
- Success and info: auto-dismiss in 4-5 seconds
- Warning: auto-dismiss in 6-8 seconds
- Error: persist until dismissed (user must acknowledge)
- Position: top-right (desktop), bottom-center (mobile)
- Maximum 3 toasts visible simultaneously

**Toast anatomy:**
- Type indicator (color + icon)
- Message (1-2 lines max)
- Optional action button (e.g., "Undo")
- Dismiss button
- `role="status"` for success/info, `role="alert"` for errors

### Notification Severity

| Level | Use for | Auto-dismiss | Example |
|-------|---------|-------------|---------|
| Success | Completed action | Yes (4s) | "Project created" |
| Info | Helpful context | Yes (5s) | "3 unread messages" |
| Warning | Attention needed | Yes (8s) | "Session expires in 5 min" |
| Error | Action failed | No (persist) | "Failed to save changes" |

## Infinite Scroll vs Pagination

| Use Case | Recommendation |
|----------|---------------|
| Content exploration (feed, photos) | Infinite scroll |
| Item lookup (tables, search results) | Pagination |
| Filter-heavy UIs | Pagination (users jump pages) |
| Sequential consumption (articles, video) | Continuous / infinite |
| Performance-critical / SEO | Pagination (simpler) |
| Data that changes frequently | Pagination (stable pages) |

### Infinite Scroll Implementation Notes

- Use `IntersectionObserver` to detect when the sentinel element is visible
- Show loading indicator at the bottom
- Use `aria-live="polite"` to announce new items to screen readers
- Provide a "Back to top" button for long lists
- Consider virtual scrolling for very large lists (only render visible items)

## Keyboard Navigation for Custom Controls

Any custom interactive element must support keyboard navigation.

**ARIA patterns to follow (don't invent your own):**
- Dropdown/select -> Combobox or Listbox pattern
- Menu -> Menu Button pattern
- Tabs -> Tabs pattern (roving tabindex)
- Accordion -> Disclosure pattern
- Modal -> Dialog pattern

See [WAI-ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/) for canonical implementations.

### Roving Tabindex Pattern

For groups of related interactive elements (tabs, radio groups, toolbars):
- Only one item in the group has `tabindex="0"` (the active one)
- All others have `tabindex="-1"`
- Arrow keys move `tabindex="0"` between items
- Tab/Shift+Tab moves focus OUT of the group entirely

```javascript
// Pseudocode for roving tabindex
function handleKeydown(event, items, activeIndex) {
  switch (event.key) {
    case 'ArrowDown':
    case 'ArrowRight':
      activeIndex = (activeIndex + 1) % items.length;
      break;
    case 'ArrowUp':
    case 'ArrowLeft':
      activeIndex = (activeIndex - 1 + items.length) % items.length;
      break;
    case 'Home':
      activeIndex = 0;
      break;
    case 'End':
      activeIndex = items.length - 1;
      break;
  }
  items[activeIndex].focus();
}
```

## Page Transition Patterns

**Page transition rules:**
- Keep transitions under 350ms — anything longer feels like latency
- Match transition direction to navigation direction (forward/back)
- Always respect `prefers-reduced-motion`
- Don't transition elements that shift layout — only full-page or specific elements

## Responsive Design Breakpoints

Conventional breakpoints (adjust to your design):

| Name | Width | Target |
|------|-------|--------|
| sm | 640px | Mobile landscape |
| md | 768px | Tablet portrait |
| lg | 1024px | Tablet landscape / small desktop |
| xl | 1280px | Desktop |
| 2xl | 1536px | Large desktop |

**Mobile-first approach:**
- Default styles target mobile
- Use `min-width` media queries to progressively enhance
- Test on real devices, not just browser resize

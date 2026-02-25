---
name: core-frontend:human-centered-design
description: "UX patterns for interfaces that feel right: spacing systems, visual hierarchy, Gestalt principles, progressive disclosure, optimistic UI, skeleton loading, micro-interactions, reduced motion, cognitive load management, and predictable interaction patterns."
user-invocable: false
---

# Human-Centered Design Quick Reference

## Spacing Scale Systems

Mathematical progressions feel more natural than arbitrary values because they create rhythm. Use a base-4 or base-8 scale.

```css
/* Base-4 scale — good for dense UIs */
:root {
  --space-1: 0.25rem;   /*  4px */
  --space-2: 0.5rem;    /*  8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */
  --space-20: 5rem;     /* 80px */
  --space-24: 6rem;     /* 96px */
}
```

**Rules of thumb:**
- Related elements: 4-8px gap
- Grouped content: 16-24px gap
- Sections: 48-96px gap
- Never use arbitrary values like 13px or 27px — pick the nearest scale step

## Visual Hierarchy

Three levers: size, weight, color. Use at most two simultaneously.

```css
.heading-1 { font-size: var(--font-size-3xl); font-weight: 700; }
.heading-2 { font-size: var(--font-size-2xl); font-weight: 600; }
.heading-3 { font-size: var(--font-size-xl);  font-weight: 600; }
.body-text  { font-size: var(--font-size-base); font-weight: 400; }
.caption    { font-size: var(--font-size-sm);  color: var(--color-muted); }
```

**Visual weight ordering:**
1. Largest + boldest = most important
2. Use color for emphasis (brand), not structure
3. Whitespace around an element increases its perceived importance

## Gestalt Principles Applied

### Proximity — group related items visually

```css
/* More space between groups than within groups */
.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);    /* tight within group */
}

.form-section + .form-section {
  margin-top: var(--space-8); /* large gap between sections */
}
```

### Similarity — consistent styling signals same type

All primary actions use the same button style, color, and position. All secondary actions use ghost/outline style consistently. All destructive actions use red — every time, without exception.

### Continuity — align elements to guide the eye

```css
.form-field {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: var(--space-2);
  align-items: baseline;
}
```

### Closure — users complete incomplete shapes

```css
/* Truncated list with gradient implies more content below */
.preview-list {
  max-height: 200px;
  overflow: hidden;
  mask-image: linear-gradient(to bottom, black 70%, transparent 100%);
}
```

### Figure-Ground — separate interactive from static

```css
/* Elevated card lifts above background */
.card {
  background: var(--color-surface);
  box-shadow: 0 1px 3px oklch(0% 0 0 / 8%), 0 4px 12px oklch(0% 0 0 / 6%);
}

/* Modals use overlay to reinforce figure-ground */
.overlay {
  background: oklch(0% 0 0 / 50%);
  backdrop-filter: blur(4px);
}
```

## Progressive Disclosure

Show only what users need at each step. Reveal complexity gradually.

**Patterns:**
- Summary -> Detail: show card, expand to full page
- Wizard / multi-step form: one question at a time
- Contextual help: show on hover/focus, not always visible
- Inline editing: text first, edit controls on interaction

## Optimistic UI

Update UI immediately, sync with server in background, rollback on failure.

**Rules — only use optimistic UI when:**
1. The action typically succeeds (>95% success rate)
2. Rollback is clearly possible
3. Conflicts are unlikely (not editing shared documents)

## Skeleton Loading States

Skeletons should match the EXACT layout of the content they replace.

**Rules:**
- Skeleton dimensions must match real content closely
- Use `aria-busy="true"` during loading
- Never show a spinner when a skeleton can match the layout
- Stagger multiple skeletons for visual interest (animation-delay)

## Micro-Interactions (Under 200ms)

Hover, focus, and active states must respond within 200ms or users feel lag.

**Timing guide:**
- Hover response: 80-120ms
- Click response: 50-100ms (feel instantaneous)
- Open menus/tooltips: 150-200ms (slight delay prevents accidental opens)
- Closing menus: 80-120ms (faster feels responsive)
- Page transitions: 200-350ms

## Reduced Motion

Always respect `prefers-reduced-motion`:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Cognitive Load Management

**Hick's Law:** Decision time increases logarithmically with the number of choices.

**Reduce cognitive load:**
- Group related actions together
- Default to the most common action (pre-select)
- Limit navigation items to 5-7 (Miller's Law)
- Use progressive disclosure for complex forms
- Show only 3-5 items before "Show more"
- One primary action per screen

## Predictable Interactions

Users learn patterns from the web. Violating them creates friction:

| Element | Expected Behavior |
|---------|-------------------|
| Blue underlined text | Navigates somewhere |
| Button | Triggers action (no navigation) |
| Checkbox | Binary toggle |
| Radio | Single selection from group |
| Dropdown | Pick one from list |
| Toggle/Switch | Immediate on/off action |
| Breadcrumbs | Navigate up the hierarchy |
| Logo | Return to home |
| Search icon | Open search |
| X button | Close/dismiss |

**Don't:** Use buttons that look like links, checkboxes that trigger navigation, or toggles with delayed effect.

## Additional Resources

- [ux-reference.md](ux-reference.md) — Empty states, error states, confirmation dialogs, form UX patterns, notification system design, infinite scroll vs pagination, keyboard navigation patterns

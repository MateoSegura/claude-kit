# Human-Centered Design — UX Patterns Reference

## Empty States

An empty state is an opportunity to guide users, not a failure to show content.

```svelte
<!-- Good empty state: explain what's missing + call to action -->
<div class="empty-state" role="status">
  <EmptyIllustration aria-hidden="true" />
  <h2 class="empty-state__title">No projects yet</h2>
  <p class="empty-state__description">
    Projects help you organize your work. Create your first project to get started.
  </p>
  <Button href="/projects/new" variant="primary">
    Create your first project
  </Button>
</div>
```

**Empty state anatomy:**
1. **Visual**: Illustration or icon (not a sad robot — keep it light)
2. **Headline**: What's missing (not "Nothing here")
3. **Description**: Why it's empty + what to do
4. **Call to action**: Primary action to resolve the empty state

**Types of empty states:**
- First use: welcome + tutorial action
- Search no results: show query, suggest alternatives
- Filter no results: show active filters, offer to clear
- Error no data: explain error, offer retry

## Error States

Every error state needs: what happened, why, and what to do next.

```svelte
<!-- Network error with retry -->
<div class="error-state" role="alert">
  <ErrorIcon aria-hidden="true" />
  <h3>Couldn't load posts</h3>
  <p>Check your internet connection and try again.</p>
  <button onclick={retry} disabled={retrying}>
    {retrying ? 'Retrying...' : 'Try again'}
  </button>
</div>
```

```svelte
<!-- Inline form validation -->
<div class="field" class:field--error={!!errors.email}>
  <label for="email">Email address</label>
  <input
    id="email"
    type="email"
    aria-describedby={errors.email ? 'email-error' : undefined}
    aria-invalid={!!errors.email}
    bind:value={email}
  />
  {#if errors.email}
    <p id="email-error" class="field-error" role="alert">{errors.email}</p>
  {/if}
</div>
```

**Error messaging principles:**
- Don't say "Error 422" — say what happened
- Don't blame the user ("You entered an invalid email")
- Do be specific ("Email must contain @domain.com")
- Do suggest the fix in the error message

## Confirmation Dialogs

Reserve confirmation for destructive or irreversible actions only.

```svelte
<!-- Only show confirmation for truly dangerous actions -->
<script>
  let showConfirm = $state(false);

  async function deleteProject() {
    showConfirm = false;
    await fetch(`/api/projects/${project.id}`, { method: 'DELETE' });
    goto('/projects');
  }
</script>

<!-- Primary action: just do it (with undo) -->
<button onclick={archiveProject}>Archive</button>

<!-- Destructive: confirm first -->
<button class="btn--destructive" onclick={() => (showConfirm = true)}>
  Delete project
</button>

{#if showConfirm}
  <Dialog onclose={() => (showConfirm = false)}>
    <h2>Delete "{project.name}"?</h2>
    <p>This action cannot be undone. All project data will be permanently deleted.</p>
    <div class="dialog-actions">
      <button onclick={() => (showConfirm = false)}>Cancel</button>
      <button class="btn--destructive" onclick={deleteProject}>Delete project</button>
    </div>
  </Dialog>
{/if}
```

**Prefer undo over confirmation:**
- Archive instead of delete (with restore option)
- Soft delete with 30-day recovery
- Toast with undo button: "Project deleted · Undo (5s)"

## Form UX Patterns

### Progressive Form Enhancement

```svelte
<script>
  // Show fields progressively based on previous answers
  let hasAccount = $state<boolean | null>(null);
  let authMethod = $state<'email' | 'sso' | null>(null);
</script>

<!-- Step 1 -->
<fieldset>
  <legend>Do you have an account?</legend>
  <label>
    <input type="radio" name="account" value={true} bind:group={hasAccount} />
    Yes, I have an account
  </label>
  <label>
    <input type="radio" name="account" value={false} bind:group={hasAccount} />
    No, I'm new here
  </label>
</fieldset>

<!-- Step 2 — appears after Step 1 is answered -->
{#if hasAccount !== null}
  <div transition:slide>
    <!-- Show relevant fields based on answer -->
  </div>
{/if}
```

### Inline Validation Timing

```svelte
<script>
  let email = $state('');
  let emailError = $state('');
  let emailTouched = $state(false);

  // Validate on blur, not on every keystroke
  function validateEmail() {
    emailTouched = true;
    if (!email.includes('@')) {
      emailError = 'Enter a valid email address';
    } else {
      emailError = '';
    }
  }

  // Clear error while typing (after first validation)
  $effect(() => {
    if (emailTouched && email.includes('@')) {
      emailError = '';
    }
  });
</script>

<input
  type="email"
  bind:value={email}
  onblur={validateEmail}
  aria-invalid={emailTouched && !!emailError}
/>
```

**Validation timing rules:**
- Don't validate on first keystroke — frustrating
- Validate on blur (when user leaves field)
- Clear errors while typing (once field has been validated once)
- Re-validate on blur after typing
- Show all errors on submit

### Loading States in Forms

```svelte
<script>
  let submitting = $state(false);
  let success = $state(false);

  async function handleSubmit() {
    submitting = true;
    try {
      await submitForm(formData);
      success = true;
    } finally {
      submitting = false;
    }
  }
</script>

<button
  type="submit"
  disabled={submitting}
  aria-busy={submitting}
>
  {#if submitting}
    <Spinner aria-hidden="true" />
    Saving...
  {:else if success}
    <CheckIcon aria-hidden="true" />
    Saved!
  {:else}
    Save changes
  {/if}
</button>
```

## Notification System Design

```svelte
<!-- Toast notification — transient, non-blocking -->
<script>
  import { toast } from '$lib/toast.svelte.ts';

  // Success: action completed
  toast.success('Project created');

  // Info: helpful context
  toast.info('You have 3 unread messages');

  // Warning: attention needed but not blocking
  toast.warning('Session expires in 5 minutes');

  // Error: action failed (persists until dismissed)
  toast.error('Failed to save changes', { persist: true });

  // With action
  toast.success('Item deleted', {
    action: { label: 'Undo', onClick: undoDelete },
    duration: 5000
  });
</script>
```

**Toast rules:**
- Success and info: auto-dismiss in 4–5 seconds
- Warning: auto-dismiss in 6–8 seconds
- Error: persist until dismissed (user must acknowledge)
- Position: top-right (desktop), bottom-center (mobile)
- Maximum 3 toasts visible simultaneously

## Infinite Scroll vs Pagination

| Use Case | Recommendation |
|----------|---------------|
| Content exploration (feed, photos) | Infinite scroll |
| Item lookup (tables, search results) | Pagination |
| Filter-heavy UIs | Pagination (users jump pages) |
| Sequential consumption (articles, video) | Continuous / infinite |
| Performance-critical / SEO | Pagination (simpler) |
| Data that changes frequently | Pagination (stable pages) |

```svelte
<!-- Infinite scroll with intersection observer -->
<script>
  let sentinel: HTMLElement;
  let loading = $state(false);
  let hasMore = $state(true);

  $effect(() => {
    const obs = new IntersectionObserver(async ([entry]) => {
      if (entry.isIntersecting && !loading && hasMore) {
        loading = true;
        await loadMore();
        loading = false;
      }
    }, { threshold: 0.1 });

    obs.observe(sentinel);
    return () => obs.disconnect();
  });
</script>

{#each items as item}
  <Item {item} />
{/each}

<!-- Sentinel element that triggers next load -->
<div bind:this={sentinel} aria-hidden="true" style="height: 1px" />

{#if loading}
  <div class="loading-row" aria-live="polite" aria-label="Loading more items">
    <Spinner /> Loading...
  </div>
{/if}
```

## Keyboard Navigation for Custom Controls

Any custom interactive element must support keyboard navigation.

```svelte
<!-- Custom dropdown / listbox -->
<script>
  let open = $state(false);
  let activeIndex = $state(0);
  let items = ['Option 1', 'Option 2', 'Option 3'];

  function handleKeydown(e: KeyboardEvent) {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        activeIndex = Math.min(activeIndex + 1, items.length - 1);
        break;
      case 'ArrowUp':
        e.preventDefault();
        activeIndex = Math.max(activeIndex - 1, 0);
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        selectItem(items[activeIndex]);
        open = false;
        break;
      case 'Escape':
        open = false;
        triggerEl.focus();
        break;
      case 'Home':
        e.preventDefault();
        activeIndex = 0;
        break;
      case 'End':
        e.preventDefault();
        activeIndex = items.length - 1;
        break;
    }
  }
</script>

<div role="combobox" aria-expanded={open} aria-haspopup="listbox">
  <button
    bind:this={triggerEl}
    onclick={() => (open = !open)}
    aria-controls="dropdown-list"
  >
    {selected ?? 'Select an option'}
  </button>

  {#if open}
    <ul
      id="dropdown-list"
      role="listbox"
      onkeydown={handleKeydown}
      tabindex="-1"
    >
      {#each items as item, i}
        <li
          role="option"
          aria-selected={selected === item}
          class:active={i === activeIndex}
          onclick={() => selectItem(item)}
        >
          {item}
        </li>
      {/each}
    </ul>
  {/if}
</div>
```

**ARIA patterns to follow (don't invent your own):**
- Dropdown/select → Combobox or Listbox pattern
- Menu → Menu Button pattern
- Tabs → Tabs pattern (roving tabindex)
- Accordion → Disclosure pattern
- Modal → Dialog pattern

See [WAI-ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/) for canonical implementations.

## Page Transition Patterns

```svelte
<!-- Fade transition between routes -->
<style>
  :global(::view-transition-old(root)) {
    animation: 200ms ease-out fade-out;
  }
  :global(::view-transition-new(root)) {
    animation: 200ms ease-in fade-in;
  }

  @media (prefers-reduced-motion: reduce) {
    :global(::view-transition-old(root)),
    :global(::view-transition-new(root)) {
      animation: none;
    }
  }
</style>
```

**Page transition rules:**
- Keep transitions under 350ms — anything longer feels like latency
- Match transition direction to navigation direction (forward/back)
- Always respect prefers-reduced-motion
- Don't transition elements that shift layout — only full-page or specific elements

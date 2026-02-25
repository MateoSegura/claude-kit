---
name: frontend-svelte-knowledge:human-centered-design
description: "Svelte-specific UX implementation patterns: transition directives, spring physics animations, prefersReducedMotion, optimistic UI with runes, skeleton loading with {#if}/{:else}, and progressive disclosure with transition:slide."
user-invocable: false
---

# Svelte UX Implementation Patterns

> **General UX principles** (spacing systems, visual hierarchy, Gestalt principles, cognitive load, micro-interaction timing, predictable interactions) are provided by the `core-frontend:human-centered-design` skill. This file covers **Svelte-specific** UX implementation patterns only.

## Progressive Disclosure with Svelte Transitions

```svelte
<button onclick={() => (showAdvanced = !showAdvanced)}>
  {showAdvanced ? 'Hide' : 'Show'} advanced options
  <ChevronIcon class={showAdvanced ? 'rotate-180' : ''} />
</button>

{#if showAdvanced}
  <div class="advanced-options" transition:slide={{ duration: 200 }}>
    <!-- Complex options here -->
  </div>
{/if}
```

## Optimistic UI with Svelte Runes

```svelte
<script>
  let liked = $derived(post.liked);
  let likeCount = $derived(post.likeCount);

  async function toggleLike() {
    const wasLiked = liked;
    liked = !wasLiked;
    likeCount += wasLiked ? -1 : 1;

    try {
      await fetch(`/api/posts/${post.id}/like`, { method: 'POST' });
    } catch {
      liked = wasLiked;
      likeCount += wasLiked ? 1 : -1;
      toast.error('Failed to update like');
    }
  }
</script>

<button onclick={toggleLike} aria-pressed={liked} class:liked>
  <HeartIcon /> {likeCount}
</button>
```

## Skeleton Loading in Svelte

```svelte
{#if loading}
  <div class="post-card post-card--skeleton" aria-busy="true" aria-label="Loading post">
    <div class="skeleton skeleton--avatar"></div>
    <div class="skeleton-content">
      <div class="skeleton skeleton--text" style="width: 60%"></div>
      <div class="skeleton skeleton--text" style="width: 80%"></div>
      <div class="skeleton skeleton--text" style="width: 40%"></div>
    </div>
  </div>
{:else}
  <div class="post-card">
    <img src={post.avatar} alt="" class="avatar" />
    <div class="content">
      <p class="author">{post.author}</p>
      <p class="body">{post.body}</p>
    </div>
  </div>
{/if}
```

## Spring Physics Animations

```svelte
<script>
  import { spring } from 'svelte/motion';

  // stiffness: 0.05 (gentle) to 0.9 (stiff)
  // damping: 0.3 (bouncy) to 1.0 (overdamped/no bounce)

  const pos = spring({ x: 0, y: 0 }, {
    stiffness: 0.15,
    damping: 0.8
  });

  const scale = spring(1, { stiffness: 0.2, damping: 0.9 });
</script>

<div
  class="draggable"
  style="transform: translate({$pos.x}px, {$pos.y}px) scale({$scale})"
  onpointerdown={() => scale.set(0.95)}
  onpointerup={() => scale.set(1)}
/>
```

**When to use spring vs CSS transition:**
- Spring: dragging, physics-based, arbitrary end values
- CSS transition: simple A-to-B state changes, better for performance

## Reduced Motion in Svelte

```svelte
<script>
  import { prefersReducedMotion } from 'svelte/motion';
</script>

<div
  transition:fly={prefersReducedMotion.current
    ? { duration: 0 }
    : { y: -20, duration: 300 }
  }
>
  Content
</div>
```

## Additional Resources

- [ux-patterns-reference.md](ux-patterns-reference.md) — Svelte implementations of empty states, error states, confirmation dialogs, form validation timing, notification toasts, infinite scroll with IntersectionObserver, and keyboard navigation for custom controls

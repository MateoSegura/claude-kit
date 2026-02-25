---
name: core-frontend:state-management
description: "Frontend state management patterns: local vs global state, derived/computed state, state machines, optimistic updates, server state vs client state, and when each approach fits."
user-invocable: false
---

# State Management Quick Reference

## State Categories

Not all state is the same. Different categories need different solutions.

| Category | Examples | Typical solution |
|----------|---------|------------------|
| **Local UI state** | Modal open/closed, form input, accordion expanded | Component-local state |
| **Shared UI state** | Theme, sidebar collapsed, toast queue | Context or lightweight store |
| **Server state** | API data, user profile, list of items | Server state library (TanStack Query, SWR) |
| **URL state** | Current page, search filters, sort order | Router / URL params |
| **Form state** | Field values, validation, dirty/touched | Form library or local state |
| **Global app state** | Auth user, permissions, feature flags | State manager or context |

**Rule:** Start with the simplest solution. Escalate only when you hit a real problem.

## Local State

State owned and managed by a single component. The default for most UI state.

**When to use:**
- Toggle states (open/closed, expanded/collapsed)
- Form input values (before submission)
- Hover/focus states
- Animation state
- Anything that doesn't need to survive component unmount

**When to escalate:**
- Multiple distant components need the same data
- State needs to persist across route changes
- State needs to sync with a server

## Derived / Computed State

State that is calculated from other state. Never store derived state separately — compute it.

```
// BAD: storing derived state (gets out of sync)
items = [...]
itemCount = items.length        // redundant, can drift
filteredItems = items.filter()  // redundant, can drift

// GOOD: compute derived values
items = [...]
// Compute when needed:
itemCount = items.length
filteredItems = items.filter(i => i.active)
```

| Framework | Mechanism |
|-----------|-----------|
| React | `useMemo`, computed during render |
| Svelte | `$derived` rune |
| Vue | `computed()` |
| Angular | `computed()` signal |
| Vanilla | Getter functions |

**Key rule:** If a value can be computed from existing state, never store it as separate state.

## Lifting State Up

When two sibling components need the same state, move it to their closest common parent.

```
// Before: duplicated state
ComponentA (has its own "selectedId")
ComponentB (has its own "selectedId")

// After: lifted state
Parent (owns "selectedId", passes it down)
  ComponentA (receives selectedId via props)
  ComponentB (receives selectedId via props)
```

**When to lift:**
- Two+ components need to read the same value
- A change in one component should reflect in another
- Components need to stay synchronized

**When NOT to lift (use context or store instead):**
- Lifting would require passing through 3+ intermediate components
- Many unrelated components need the same data

## Server State

Data that lives on the server and is cached locally. This is fundamentally different from client state.

**Server state characteristics:**
- Has a remote source of truth
- Can become stale
- May be shared across users
- Needs loading/error/success states
- Needs caching, deduplication, and background refresh

**Libraries:** TanStack Query (React, Vue, Svelte, Angular, Solid), SWR (React), Apollo Client (GraphQL). These handle request deduplication, caching, background refetch, optimistic updates, pagination, and retry.

**Rule:** If data comes from an API, use a server state library. Don't store API responses in a global store.

## State Machines

Model complex state transitions as explicit states with allowed transitions. Prevents impossible states.

```
// Without state machine — bug-prone
isLoading = true
isError = false
isSuccess = false
// What if isLoading AND isError are both true? Impossible but possible in code.

// With state machine — impossible states are impossible
state = 'idle' | 'loading' | 'success' | 'error'
// Can only be in ONE state at a time
```

### Common UI State Machines

**Fetch lifecycle:**
```
idle -> loading -> success
                -> error -> loading (retry)
```

**Modal:**
```
closed -> opening -> open -> closing -> closed
```

**Multi-step form:**
```
step1 -> step2 -> step3 -> review -> submitting -> success
                                                 -> error
```

**When to use a state machine:**
- More than 3 boolean flags controlling the same feature
- Complex transitions with preconditions
- Bugs from impossible state combinations
- Features that follow a clear workflow

**Libraries:** XState (comprehensive), Zag.js (UI-focused), or hand-rolled switch statements for simple cases.

## Optimistic Updates

Update the UI immediately, sync with the server in the background, rollback on failure.

```
// Pseudocode
function toggleLike(postId) {
  // 1. Optimistic update — UI changes instantly
  cache.update(postId, post => ({ ...post, liked: !post.liked }));

  // 2. Server sync — fire and forget
  try {
    await api.toggleLike(postId);
  } catch {
    // 3. Rollback on failure
    cache.update(postId, post => ({ ...post, liked: !post.liked }));
    showError('Failed to update');
  }
}
```

**Rules for optimistic updates:**
- Action should succeed >95% of the time
- Rollback must be possible and obvious
- Don't use for actions affecting other users' data
- Show subtle indication that sync is pending (if long)
- Good candidates: likes, bookmarks, read status, local settings
- Bad candidates: payments, deleting shared resources, permission changes

## Global State Managers

Libraries: Zustand/Jotai/Redux Toolkit (React), Pinia (Vue), built-in stores (Svelte), NgRx/Signals (Angular).

**When you need one:** Auth state, feature flags, shopping cart, multi-step wizard state, real-time data (WebSockets).

**When you DON'T:** Server data (use TanStack Query/SWR), form state, transient UI state (modals/tooltips), URL-dependent state (use router).

## Additional Resources

- [state-reference.md](state-reference.md) — Detailed patterns for URL state management, real-time state with WebSockets, state persistence, debugging state issues, migration strategies

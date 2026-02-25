# State Management — Detailed Reference

## URL State Management

URL state is the most shareable and bookmarkable form of state. Use it for anything a user might want to share or return to.

**What belongs in the URL:**
- Current page/route
- Search query and filters
- Sort order
- Pagination (page number)
- Selected tab
- Modal/dialog open state (debatable — use for shareable modals)

**What does NOT belong in the URL:**
- Form input values (until submitted)
- Loading states
- Authentication tokens
- Transient UI state (hover, focus)

### URL State Patterns

```
// Search with filters
/products?q=keyboard&category=electronics&sort=price-asc&page=2

// Selected item
/projects/123/tasks/456

// Tab selection
/settings?tab=security
```

**Sync URL with state:**
- On state change, update URL (pushState or replaceState)
- On URL change (browser back/forward), update state
- Use `replaceState` for changes that shouldn't create history entries (filters)
- Use `pushState` for navigation changes

## Real-Time State (WebSockets)

For data that changes frequently from external sources.

### Connection Lifecycle

```
disconnected -> connecting -> connected -> reconnecting -> connected
                                        -> disconnected (after max retries)
```

### Real-Time State Patterns

**Pattern 1: Event-Driven Updates**
```
// Server sends events, client applies them to local state
ws.onmessage = (event) => {
  const { type, payload } = JSON.parse(event.data);
  switch (type) {
    case 'item.created': addItem(payload); break;
    case 'item.updated': updateItem(payload); break;
    case 'item.deleted': removeItem(payload.id); break;
  }
};
```

**Pattern 2: Full State Sync**
```
// Server periodically sends complete state snapshot
ws.onmessage = (event) => {
  const fullState = JSON.parse(event.data);
  replaceState(fullState);
};
```

**Pattern 3: Hybrid (Snapshots + Deltas)**
```
// Initial: full state snapshot
// Subsequent: incremental deltas
// Periodic: full re-sync to correct drift
```

### Reconnection Strategy

```javascript
// Exponential backoff with jitter
function getReconnectDelay(attempt) {
  const base = Math.min(1000 * Math.pow(2, attempt), 30000); // max 30s
  const jitter = base * 0.5 * Math.random();
  return base + jitter;
}
```

## State Persistence

### When to Persist State

| Data | Storage | Why |
|------|---------|-----|
| Auth tokens | httpOnly cookies (server-set) | Security |
| User preferences | localStorage | Survives sessions |
| Form drafts | sessionStorage or IndexedDB | Recovery |
| Shopping cart | localStorage | Cross-session |
| Search history | localStorage | Convenience |
| Cached API data | Memory (TanStack Query cache) | Performance |

### Persistence Patterns

**Hydration pattern:**
1. On app start, read persisted state from storage
2. Merge with any server-provided state
3. Use merged state as initial value
4. Subscribe to state changes, persist on every update (debounced)

```javascript
// Pseudocode: persist + hydrate
function createPersistedStore(key, defaultValue) {
  // Hydrate from storage
  const stored = localStorage.getItem(key);
  const initial = stored ? JSON.parse(stored) : defaultValue;

  const store = createStore(initial);

  // Persist on changes (debounced)
  store.subscribe(debounce((state) => {
    localStorage.setItem(key, JSON.stringify(state));
  }, 500));

  return store;
}
```

**Storage size limits:**
- localStorage: ~5-10MB per origin
- sessionStorage: ~5-10MB per origin
- IndexedDB: much larger (hundreds of MB)
- Cookies: 4KB per cookie

## Debugging State Issues

### Common State Bugs

**1. Stale Closure**
A callback captures an old value of state because it was created before the state updated. Solution: use refs or ensure closures always access current state.

**2. Race Condition**
Two async operations complete out of order. The slower response overwrites the faster one.

```javascript
// Bug: fast response overwrites slow response
search("abc");  // returns 50 results (slow)
search("abcd"); // returns 3 results (fast)
// "abc" finishes after "abcd" — shows 50 results for "abcd" query

// Fix: track request identity
let currentRequestId = 0;

async function search(query) {
  const requestId = ++currentRequestId;
  const results = await api.search(query);
  if (requestId === currentRequestId) {
    setResults(results); // only apply if still the latest request
  }
}
```

**3. Derived State Drift**
Storing computed values as separate state that gets out of sync. Solution: always compute derived values.

**4. Unnecessary Re-Renders**
Creating new object/array references on every render.

```javascript
// Bug: new array created every render
<List items={items.filter(i => i.active)} />

// Fix: memoize the computation
const activeItems = useMemo(() => items.filter(i => i.active), [items]);
<List items={activeItems} />
```

### Debugging Tools

| Tool | What it shows |
|------|---------------|
| React DevTools | Component tree, props, state, profiler |
| Vue DevTools | Component tree, Pinia stores, routes |
| Svelte DevTools | Component tree, state |
| Redux DevTools | Action log, state diff, time travel |
| TanStack Query DevTools | Cache entries, fetch status, stale time |
| Browser DevTools Network tab | API requests, timing, payload |

## State Architecture Decision Tree

```
Is it from the server?
  YES -> Use server state library (TanStack Query, SWR)
  NO  -> Continue...

Does it belong in the URL?
  YES -> Use URL/router state
  NO  -> Continue...

Is it used by only one component?
  YES -> Use local component state
  NO  -> Continue...

Is it used by nearby components (parent/child)?
  YES -> Lift state to common parent
  NO  -> Continue...

Is it used across many distant components?
  YES -> Is it frequently changing?
    YES -> Use a state manager (Zustand, Pinia, etc.)
    NO  -> Use context/injection (theme, auth, locale)
```

## Migration Strategies

### From Global Store to Server State

When you have API data stored in Redux/Zustand that should be in TanStack Query:

1. Identify all API-fetched data in the global store
2. Create query hooks/composables for each endpoint
3. Replace store reads with query hooks
4. Remove fetch actions/thunks from the global store
5. Delete the now-empty store slices

### From Prop Drilling to Context

1. Identify props passed through 3+ levels without being used
2. Create a context provider at the appropriate level
3. Replace intermediate prop forwarding with context consumption
4. Remove the unused props from intermediate components

### From Class Components to Hooks/Composition

This is framework-specific but the principle is the same:
1. Extract state logic into reusable hooks/composables
2. Replace lifecycle methods with equivalent hooks
3. Test that behavior is preserved
4. Remove the old class implementation

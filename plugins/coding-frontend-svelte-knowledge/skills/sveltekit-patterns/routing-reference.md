# SvelteKit 2 — Routing Reference

## Dynamic Routes

```
src/routes/
├── blog/[slug]/          → /blog/my-post       (params.slug = 'my-post')
├── shop/[...path]/       → /shop/a/b/c         (params.path = 'a/b/c', catch-all)
├── [[optional]]/         → / or /value          (optional param)
└── (group)/[id=uuid]/   → /some-uuid           (param matcher)
```

### Param Matchers

Create `src/params/uuid.ts` to validate params:

```typescript
// src/params/uuid.ts
import type { ParamMatcher } from '@sveltejs/kit';

export const match: ParamMatcher = (param) => {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(param);
};
```

```
src/routes/users/[id=uuid]/   → only matches valid UUID paths
```

### Accessing Route Parameters

```typescript
// In load function
export const load: PageServerLoad = async ({ params, url }) => {
  params.slug;          // route param value
  url.searchParams;     // query string params
  url.pathname;         // current path
};
```

```svelte
<!-- In component -->
<script>
  import { page } from '$app/state';  // Svelte 5: use $app/state, not $app/stores
</script>

<p>Current slug: {page.params.slug}</p>
<p>Current path: {page.url.pathname}</p>
```

## Layout Hierarchy

```
src/routes/
├── +layout.svelte          [A] root layout
├── +page.svelte            → A wraps page
├── about/
│   └── +page.svelte        → A wraps page
├── blog/
│   ├── +layout.svelte      [B] blog layout
│   ├── +page.svelte        → A wraps B wraps page
│   └── [slug]/
│       └── +page.svelte    → A wraps B wraps page
├── (marketing)/
│   ├── +layout.svelte      [C] marketing layout
│   └── landing/
│       └── +page.svelte    → A wraps C wraps page
└── admin/
    ├── +layout.svelte      [D] admin layout
    └── dashboard/
        ├── +layout@.svelte [E] reset layout (breaks to root A)
        └── +page.svelte    → A wraps E wraps page (D is skipped)
```

### Layout Reset / Breaking

```
+layout@.svelte         → resets to root layout
+layout@(group).svelte  → resets to the named group's layout
+page@.svelte           → this specific page uses root layout only
+page@(group).svelte    → this specific page uses group layout only
```

## Route Load Data Hierarchy

Child pages can access parent layout load data:

```typescript
// src/routes/+layout.server.ts
export const load: LayoutServerLoad = async ({ cookies }) => {
  const user = await getUserFromSession(cookies.get('session'));
  return { user };
};
```

```typescript
// src/routes/blog/+page.server.ts
export const load: PageServerLoad = async ({ parent }) => {
  const { user } = await parent(); // access layout data
  if (!user) redirect(302, '/login');

  const posts = await db.getPosts({ authorId: user.id });
  return { posts };
};
```

## $page State (Svelte 5 / SvelteKit 2)

In Svelte 5, use `$app/state` instead of `$app/stores`:

```svelte
<script>
  import { page, navigating, updated } from '$app/state';
  // page, navigating, updated are reactive — no $ prefix needed in Svelte 5
</script>

<p>Path: {page.url.pathname}</p>
<p>Params: {JSON.stringify(page.params)}</p>
<p>Status: {page.status}</p>

{#if navigating}
  <LoadingBar />
{/if}
```

**page object properties:**
```typescript
page.url          // URL object
page.params       // route parameters
page.route        // { id: string } — route ID like '/blog/[slug]'
page.status       // HTTP status code
page.error        // error if page errored
page.data         // merged data from all load functions
page.form         // form action result
page.state        // history state (from goto/pushState)
```

## Error Handling

```svelte
<!-- src/routes/+error.svelte — nearest error boundary -->
<script>
  import { page } from '$app/state';
</script>

<h1>{page.status}: {page.error?.message}</h1>
```

```typescript
// In load function
import { error, redirect } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ params }) => {
  const post = await db.getPost(params.id);

  if (!post) {
    error(404, { message: 'Post not found' }); // throws — nearest +error.svelte renders
  }

  if (!post.published) {
    redirect(302, '/'); // throws — redirects
  }

  return { post };
};
```

## Navigation Utilities

```typescript
import {
  goto,
  back,
  forward,
  preloadData,
  preloadCode,
  pushState,
  replaceState,
  afterNavigate,
  beforeNavigate,
  onNavigate
} from '$app/navigation';

// Programmatic navigation
await goto('/dashboard');
await goto('/items?page=2', { replaceState: true, noScroll: true });

// History manipulation (shallow routing)
pushState('/items/123', { selectedItem: 123 }); // update URL without navigation

// Lifecycle hooks (inside component)
afterNavigate(({ from, to, type }) => {
  // Runs after every navigation
  analytics.track(to.url.pathname);
});

beforeNavigate(({ from, to, type, cancel }) => {
  if (hasUnsavedChanges) {
    cancel(); // prevent navigation
  }
});
```

## Locals — Server-Side Request Context

```typescript
// src/app.d.ts — augment the App namespace
declare global {
  namespace App {
    interface Locals {
      user: User | null;
      session: Session | null;
    }
    interface PageData {
      user?: User; // data available on all pages
    }
    interface Error {
      message: string;
      errorId?: string;
    }
  }
}
```

```typescript
// src/hooks.server.ts — populate locals
export const handle: Handle = async ({ event, resolve }) => {
  event.locals.user = await getUserFromCookies(event.cookies);
  event.locals.session = await getSession(event.cookies);
  return resolve(event);
};
```

```typescript
// +page.server.ts — access locals in load functions
export const load: PageServerLoad = async ({ locals }) => {
  if (!locals.user) redirect(302, '/login');
  return { user: locals.user };
};
```

## View Transitions with SvelteKit

```typescript
// src/hooks.client.ts — enable view transitions on navigation
import { onNavigate } from '$app/navigation';

onNavigate((navigation) => {
  if (!document.startViewTransition) return;

  return new Promise((resolve) => {
    document.startViewTransition(async () => {
      resolve();
      await navigation.complete;
    });
  });
});
```

```css
/* Apply view-transition-name to elements for matched transitions */
.post-card {
  view-transition-name: var(--post-id); /* must be unique per element */
}
```

## Shallow Routing (SvelteKit 2)

For UI state that should be URL-addressable but shouldn't trigger full navigation:

```svelte
<script>
  import { pushState, replaceState } from '$app/navigation';
  import { page } from '$app/state';

  function openModal(itemId: string) {
    // Update URL without navigation
    pushState(`/items/${itemId}`, { modal: itemId });
  }

  // Read state from page.state
  $derived let modalId = page.state.modal;
</script>

{#if modalId}
  <Modal id={modalId} onclose={() => history.back()} />
{/if}
```

## SvelteKit with Service Workers

```typescript
// src/service-worker.ts
import { build, files, version } from '$service-worker';

const CACHE = `cache-${version}`;

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll([...build, ...files]))
  );
});
```

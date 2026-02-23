---
name: coding-frontend-svelte-knowledge:sveltekit-patterns
description: "SvelteKit 2 routing, data loading, form actions, streaming SSR, hooks, adapters, and prerendering patterns — complete reference for building full-stack SvelteKit applications."
---

# SvelteKit 2 Patterns Quick Reference

SvelteKit is the official meta-framework for Svelte. It provides file-based routing, server-side rendering, data loading, form actions, and deployment adapters.

## File Conventions

| File | Purpose | Runs On |
|------|---------|---------|
| `+page.svelte` | Page UI component | Client (CSR nav) + Server (initial) |
| `+page.ts` | Universal load function | Both client and server |
| `+page.server.ts` | Server-only load + form actions | Server only |
| `+layout.svelte` | Layout wrapper (wraps child routes) | Both |
| `+layout.ts` | Layout universal load | Both |
| `+layout.server.ts` | Layout server load | Server only |
| `+server.ts` | API route (GET/POST/etc. handlers) | Server only |
| `+error.svelte` | Error boundary UI | Both |
| `+loading.svelte` | Loading UI during navigation | Client only |

## Routing — File System Structure

```
src/routes/
├── +page.svelte              → /
├── +layout.svelte            → root layout (wraps all routes)
├── about/
│   └── +page.svelte          → /about
├── blog/
│   ├── +page.svelte          → /blog
│   └── [slug]/
│       └── +page.svelte      → /blog/:slug
├── (marketing)/              → route group — no URL segment
│   ├── +layout.svelte        → layout only for routes in group
│   ├── landing/
│   │   └── +page.svelte      → /landing (not /(marketing)/landing)
│   └── pricing/
│       └── +page.svelte      → /pricing
├── admin/
│   ├── +layout.svelte        → admin layout
│   └── dashboard/
│       ├── +layout@.svelte   → layout break — resets to root layout
│       └── +page.svelte      → /admin/dashboard (uses root layout only)
└── api/
    └── users/
        └── +server.ts        → /api/users (REST endpoint)
```

**Route groups** `(name)` — group routes without adding URL segments. Use for separate layouts (marketing vs app vs admin).

**Layout breaking** `+layout@.svelte` or `+layout@(group).svelte` — breaks out of ancestor layout, resetting to root or a named group layout.

## Load Functions

```typescript
// +page.server.ts — runs ONLY on server
// Access: cookies, env vars, DB, private APIs
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, cookies, fetch, locals }) => {
  const session = cookies.get('session');
  if (!session) redirect(302, '/login');

  const post = await db.getPost(params.slug);
  if (!post) error(404, 'Post not found');

  return { post }; // available as data.post in +page.svelte
};
```

```typescript
// +page.ts — runs on server AND client
// Use for: public API calls, no sensitive data
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, fetch, data }) => {
  const post = await fetch(`/api/posts/${params.slug}`).then(r => r.json());
  return { post };
};
```

```svelte
<!-- +page.svelte — receives load data via data prop -->
<script>
  import type { PageData } from './$types';
  let { data }: { data: PageData } = $props();
</script>
<h1>{data.post.title}</h1>
```

## Streaming SSR with Promises

```typescript
// +page.server.ts
export const load: PageServerLoad = async ({ params }) => {
  return {
    // Awaited before streaming — fast, critical data
    post: await db.getPost(params.slug),

    // NOT awaited — streams in after initial HTML
    comments: db.getComments(params.slug),  // returns Promise
    related: fetch('/api/related').then(r => r.json())
  };
};
```

```svelte
<!-- +page.svelte -->
<script>
  let { data } = $props();
</script>

<article>{data.post.body}</article>

<!-- Svelte 5 await blocks for streamed data -->
{#await data.comments}
  <p>Loading comments...</p>
{:then comments}
  {#each comments as comment}
    <Comment {comment} />
  {/each}
{:catch error}
  <p>Failed to load comments</p>
{/await}
```

## Form Actions

```typescript
// +page.server.ts
import type { Actions } from './$types';
import { fail } from '@sveltejs/kit';

export const actions: Actions = {
  // default action — invoked when no ?/action specified
  default: async ({ request, cookies }) => {
    const data = await request.formData();
    const email = data.get('email') as string;

    if (!email?.includes('@')) {
      return fail(422, { email, error: 'Invalid email' });
    }

    await db.subscribe(email);
    return { success: true };
  },

  // Named actions — invoked via action="?/create"
  create: async ({ request, locals }) => {
    // ...
  },

  delete: async ({ request }) => {
    // ...
  }
};
```

```svelte
<!-- +page.svelte — progressive enhancement with use:enhance -->
<script>
  import { enhance } from '$app/forms';
  import type { ActionData, PageData } from './$types';

  let { data, form }: { data: PageData; form: ActionData } = $props();
  let submitting = $state(false);
</script>

<form
  method="POST"
  action="?/create"
  use:enhance={({ formElement, formData, action, cancel }) => {
    submitting = true;
    // Return callback for after submission
    return async ({ result, update }) => {
      submitting = false;
      // result.type: 'success' | 'failure' | 'redirect' | 'error'
      await update(); // re-run load functions and update page
    };
  }}
>
  <input name="email" type="email" />
  {#if form?.error}
    <p class="error">{form.error}</p>
  {/if}
  <button disabled={submitting}>Subscribe</button>
</form>
```

## API Routes (+server.ts)

```typescript
// src/routes/api/posts/+server.ts
import type { RequestHandler } from './$types';
import { json } from '@sveltejs/kit';

export const GET: RequestHandler = async ({ url, locals }) => {
  const page = Number(url.searchParams.get('page') ?? 1);
  const posts = await db.getPosts({ page });
  return json(posts);
};

export const POST: RequestHandler = async ({ request, locals }) => {
  if (!locals.user) return new Response('Unauthorized', { status: 401 });

  const body = await request.json();
  const post = await db.createPost({ ...body, authorId: locals.user.id });
  return json(post, { status: 201 });
};
```

## Hooks (src/hooks.server.ts)

```typescript
import type { Handle, HandleError, HandleFetch } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';

// handle — intercept every request
const auth: Handle = async ({ event, resolve }) => {
  const session = event.cookies.get('session');
  event.locals.user = session ? await getUser(session) : null;
  return resolve(event);
};

const cors: Handle = async ({ event, resolve }) => {
  if (event.url.pathname.startsWith('/api/')) {
    const response = await resolve(event);
    response.headers.set('Access-Control-Allow-Origin', '*');
    return response;
  }
  return resolve(event);
};

// Combine multiple handle hooks
export const handle = sequence(auth, cors);

// handleError — called when an unexpected error occurs
export const handleError: HandleError = async ({ error, event, status, message }) => {
  console.error(error);
  return { message: 'An unexpected error occurred' };
};

// handleFetch — intercept fetch calls in load functions
export const handleFetch: HandleFetch = async ({ request, fetch, event }) => {
  // Rewrite internal API calls to bypass network
  if (request.url.startsWith('https://myapp.com/api/')) {
    const url = request.url.replace('https://myapp.com', '');
    return fetch(new Request(url, request));
  }
  return fetch(request);
};
```

## Invalidation and Revalidation

```typescript
// Programmatic invalidation — re-run load functions
import { invalidate, invalidateAll, goto } from '$app/navigation';

// Invalidate specific dependency
await invalidate('/api/posts');         // re-run loads that called fetch('/api/posts')
await invalidate('app:session');        // re-run loads that called depends('app:session')
await invalidateAll();                  // re-run ALL load functions on current page
```

```typescript
// Load function declaring a dependency
export const load: PageLoad = async ({ depends, fetch }) => {
  depends('app:user');                  // invalidate('app:user') re-runs this
  const user = await fetch('/api/me').then(r => r.json());
  return { user };
};
```

## Adapters

| Adapter | Use Case | Install |
|---------|----------|---------|
| `@sveltejs/adapter-auto` | Detects Vercel, Netlify, Cloudflare automatically | Default |
| `@sveltejs/adapter-node` | Node.js server (Docker, VPS) | npm i -D @sveltejs/adapter-node |
| `@sveltejs/adapter-static` | Pure static site / SPA (Tauri, GitHub Pages) | npm i -D @sveltejs/adapter-static |
| `@sveltejs/adapter-vercel` | Vercel (edge functions, ISR) | npm i -D @sveltejs/adapter-vercel |
| `@sveltejs/adapter-cloudflare` | Cloudflare Workers/Pages | npm i -D @sveltejs/adapter-cloudflare |

```javascript
// svelte.config.js — static adapter (for Tauri/SPA)
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({
      fallback: 'index.html',     // SPA mode — serve index.html for all paths
      pages: 'build',             // output directory
      assets: 'build'
    })
  }
};
```

## Preloading and Prerendering

```typescript
// Prerender a route at build time
export const prerender = true;       // in +page.ts or +page.server.ts
export const prerender = false;      // disable for dynamic content
export const ssr = false;            // client-only rendering
export const csr = false;            // server-only, no JS hydration

// Preload on hover (in +layout.svelte)
import { preloadData, preloadCode } from '$app/navigation';
```

```svelte
<!-- data-sveltekit-preload-data — preload on hover/tap -->
<a href="/about" data-sveltekit-preload-data="hover">About</a>

<!-- data-sveltekit-preload-code — preload JS only -->
<a href="/heavy-page" data-sveltekit-preload-code="viewport">Heavy Page</a>
```

## Additional Resources

- [routing-reference.md](routing-reference.md) — Dynamic routes, catch-all routes, params matchers, route layout hierarchy, error handling patterns
- [data-patterns.md](data-patterns.md) — Parent load data access, `$page` store, `$navigating`, cookies, locals, session patterns, TypeScript types from `$types`

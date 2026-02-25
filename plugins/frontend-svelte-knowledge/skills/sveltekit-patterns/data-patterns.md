# SvelteKit 2 — Data Loading Patterns

## Universal vs Server Load Functions

| Feature | +page.ts (Universal) | +page.server.ts (Server-only) |
|---------|---------------------|-------------------------------|
| Runs on | Server (initial) + Client (navigation) | Server only |
| Access to cookies | No (use parent data) | Yes |
| Access to locals | No | Yes |
| Can use private env vars | No | Yes |
| Can access DB directly | No (security risk) | Yes |
| fetch() behavior | Uses browser fetch / Node fetch | SvelteKit-enhanced fetch |
| Form actions | No | Yes (export const actions) |
| Can return non-serializable | Yes (functions, classes) | No (must be serializable) |

### When to Use Which

- **+page.server.ts**: Authentication, database queries, private API keys, form handling, cookies
- **+page.ts**: Public API calls, client-side caching, returning non-serializable values
- **+layout.server.ts**: Session data, user profile, global app state needed everywhere
- **+layout.ts**: Shared non-sensitive data, configuration

## Combining Server and Universal Load

When both `+page.server.ts` and `+page.ts` exist:

```typescript
// +page.server.ts
export const load: PageServerLoad = async ({ cookies }) => {
  return {
    user: await getUserFromSession(cookies.get('session')),
    serverTime: new Date().toISOString()
  };
};
```

```typescript
// +page.ts — receives server load data via `data` param
export const load: PageLoad = async ({ data, fetch }) => {
  // data = result from +page.server.ts
  const posts = await fetch(`/api/posts?userId=${data.user.id}`).then(r => r.json());
  return {
    ...data,  // spread server data
    posts     // add client-fetched data
  };
};
```

## Cookies and Session Management

```typescript
// Setting cookies
export const actions: Actions = {
  login: async ({ request, cookies }) => {
    const { email, password } = Object.fromEntries(await request.formData());
    const user = await authenticate(email as string, password as string);

    if (!user) return fail(401, { error: 'Invalid credentials' });

    cookies.set('session', createSession(user), {
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7 // 1 week
    });

    redirect(302, '/dashboard');
  }
};
```

## Environment Variables

```typescript
// $env/static/private — build-time, server-only
import { DATABASE_URL, JWT_SECRET } from '$env/static/private';

// $env/static/public — build-time, safe to expose
import { PUBLIC_SENTRY_DSN } from '$env/static/public';

// $env/dynamic/private — runtime, server-only
import { env } from '$env/dynamic/private';
const dbUrl = env.DATABASE_URL;

// $env/dynamic/public — runtime, safe to expose
import { env } from '$env/dynamic/public';
const analyticsId = env.PUBLIC_ANALYTICS_ID;
```

## Handling Load Errors

```typescript
// +page.server.ts
import { error, redirect, fail } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ params }) => {
  try {
    const post = await db.getPost(params.id);
    if (!post) error(404, 'Not found');
    return { post };
  } catch (e) {
    if (e instanceof SvelteKitError) throw e; // re-throw SvelteKit errors
    console.error(e);
    error(500, 'Internal server error');
  }
};
```

## TypeScript Types from $types

SvelteKit generates types for every route. Import from `./$types`:

```typescript
import type {
  PageLoad,          // universal load function
  PageServerLoad,    // server load function
  LayoutLoad,        // layout universal load
  LayoutServerLoad,  // layout server load
  PageData,          // data returned by load, used in +page.svelte
  LayoutData,        // data from layout load
  ActionData,        // form action result
  Actions,           // form actions object type
  RequestHandler     // +server.ts handler type
} from './$types';
```

```svelte
<!-- Typed page component -->
<script>
  import type { PageData, ActionData } from './$types';

  let { data, form }: { data: PageData; form: ActionData } = $props();
</script>
```

## Depends — Custom Invalidation Keys

```typescript
// +page.ts — declare custom dependency
export const load: PageLoad = async ({ depends, fetch }) => {
  depends('app:cart');  // allows invalidate('app:cart') to re-run this load

  const cart = await fetch('/api/cart').then(r => r.json());
  return { cart };
};
```

```svelte
<script>
  import { invalidate } from '$app/navigation';

  async function addToCart(productId: string) {
    await fetch('/api/cart', { method: 'POST', body: JSON.stringify({ productId }) });
    await invalidate('app:cart'); // triggers re-run of any load that called depends('app:cart')
  }
</script>
```

## Parent Data in Load Functions

```typescript
// Child load can access parent layout data
export const load: PageServerLoad = async ({ parent, params }) => {
  const { user } = await parent(); // blocks until parent load resolves

  // Use parent data
  const posts = await db.getPostsByUser(user.id);
  return { posts };
};
```

**Caution:** Calling `parent()` makes the child load wait for the parent. For independent data, avoid calling `parent()` until actually needed.

## Server-Sent Events / Streaming

```typescript
// +server.ts — streaming endpoint
export const GET: RequestHandler = async ({ request }) => {
  const stream = new ReadableStream({
    async start(controller) {
      for (let i = 0; i < 10; i++) {
        controller.enqueue(`data: ${JSON.stringify({ count: i })}\n\n`);
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      controller.close();
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache'
    }
  });
};
```

```svelte
<!-- Client: consume SSE -->
<script>
  let messages = $state<string[]>([]);

  $effect(() => {
    const source = new EventSource('/api/stream');
    source.onmessage = (e) => {
      messages = [...messages, JSON.parse(e.data)];
    };
    return () => source.close();
  });
</script>
```

## Optimistic UI with Form Actions

```svelte
<script>
  import { enhance } from '$app/forms';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  let todos = $state(data.todos);

  function createOptimisticTodo(text: string): Todo {
    return { id: crypto.randomUUID(), text, done: false, optimistic: true };
  }
</script>

<form
  method="POST"
  action="?/addTodo"
  use:enhance={({ formData }) => {
    const text = formData.get('text') as string;
    const optimistic = createOptimisticTodo(text);
    todos = [...todos, optimistic];

    return async ({ result, update }) => {
      if (result.type === 'success') {
        await update(); // refresh from server
      } else {
        // Rollback
        todos = todos.filter(t => !t.optimistic);
      }
    };
  }}
>
  <input name="text" />
  <button>Add</button>
</form>
```

## SvelteKit Config Reference

```javascript
// svelte.config.js
export default {
  kit: {
    adapter: adapter(),

    // Custom alias
    alias: {
      $components: 'src/lib/components',
      $server: 'src/lib/server'
    },

    // CSRF protection
    csrf: { checkOrigin: true },

    // Path prefix for deployment
    paths: {
      base: '/app',    // sets base path for links
      assets: ''
    },

    // Prerendering
    prerender: {
      handleHttpError: 'warn',  // or 'fail' or function
      concurrency: 4
    },

    // Output directory
    outDir: '.svelte-kit'
  }
};
```

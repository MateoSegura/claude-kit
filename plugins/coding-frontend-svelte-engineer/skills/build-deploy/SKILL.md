---
name: coding-frontend-svelte-engineer:build-deploy
description: "Build configuration and deployment reference for SvelteKit across all targets: web (SPA, SSR, static, hybrid, PWA) and desktop (Tauri 2, Electron). Covers adapter selection, Vite configuration, TypeScript setup, environment variables, Tauri IPC, and CI/CD patterns. Load this when configuring builds, setting up new projects, selecting adapters, or integrating with desktop frameworks."
user-invocable: false
---

# Build & Deploy — SvelteKit Configuration Reference

Quick reference for adapter selection, config essentials, and environment variables. See [reference.md](reference.md) for complete per-target deployment configs, Tauri 2 deep dive, Electron setup, and CI/CD patterns.

## Adapter Selection Guide

| Deployment Target | Adapter | Package |
|-------------------|---------|---------|
| Vercel | `@sveltejs/adapter-vercel` | Auto-detected by adapter-auto |
| Cloudflare Pages/Workers | `@sveltejs/adapter-cloudflare` | Auto-detected by adapter-auto |
| Netlify | `@sveltejs/adapter-netlify` | Auto-detected by adapter-auto |
| Node.js server | `@sveltejs/adapter-node` | Explicit install required |
| Static site (pure SSG) | `@sveltejs/adapter-static` | Explicit install required |
| Docker/self-hosted | `@sveltejs/adapter-node` | Explicit install required |
| Tauri 2 desktop | `@sveltejs/adapter-static` | SPA mode (`fallback: '200.html'`) |
| Electron desktop | `@sveltejs/adapter-static` | SPA mode (`fallback: '200.html'`) |
| Unknown/auto | `@sveltejs/adapter-auto` | Installed by default |

## svelte.config.js Essentials

```javascript
import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
export default {
  preprocess: vitePreprocess(),

  kit: {
    adapter: adapter(),

    alias: {
      $components: 'src/lib/components',
      $server: 'src/lib/server',
      $utils: 'src/lib/utils',
    },

    // Security: CSP headers
    csp: {
      mode: 'auto',
      directives: {
        'script-src': ['self'],
        'style-src': ['self', 'unsafe-inline'],
      }
    }
  }
};
```

## Environment Variables

SvelteKit has four env modules based on privacy and timing:

| Module | Access | Timing | Use For |
|--------|--------|--------|---------|
| `$env/static/private` | Server only | Build time | API keys, DB URLs (build-time constants) |
| `$env/static/public` | Client + server | Build time | Public API URLs, feature flags |
| `$env/dynamic/private` | Server only | Runtime | Secrets that change without rebuild |
| `$env/dynamic/public` | Client + server | Runtime | Config that changes without rebuild |

```typescript
// Server-only secret (build-time)
import { DATABASE_URL } from '$env/static/private';

// Public config (build-time)
import { PUBLIC_API_BASE } from '$env/static/public';

// Runtime server secret (useful in Docker)
import { env } from '$env/dynamic/private';
const secret = env.MY_RUNTIME_SECRET;
```

**Rule**: Never import `$env/static/private` or `$env/dynamic/private` in `+page.svelte`, `+page.ts`, or any client-accessible file. Only use in `+page.server.ts`, `+layout.server.ts`, `+server.ts`, and server-only `$lib/server/` modules.

## TypeScript Configuration

```json
// tsconfig.json
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "paths": {
      "$lib": ["src/lib"],
      "$lib/*": ["src/lib/*"]
    }
  }
}
```

```typescript
// src/app.d.ts — Augment SvelteKit types
declare global {
  namespace App {
    interface Error {
      code?: string;  // Custom error codes
    }
    interface Locals {
      user: User | null;  // Set in hooks.server.ts
    }
    interface PageData {
      // Common page data properties
    }
    interface Platform {
      // Adapter-specific (e.g., Cloudflare bindings)
      env?: {
        MY_KV: KVNamespace;
      };
    }
  }
}

export {};
```

## Tauri 2 Integration Overview

```
SvelteKit (SPA) → adapter-static → Tauri WebView → Rust backend
```

1. Set `ssr = false` in root `+layout.ts`
2. Use `@sveltejs/adapter-static` with `fallback: '200.html'`
3. Set `devUrl` in `tauri.conf.json` to SvelteKit dev server port
4. Import `@tauri-apps/api` only inside `browser` guard or `onMount`

```typescript
// src/routes/+layout.ts
export const ssr = false;
export const prerender = false;
```

```javascript
// tauri.conf.json (excerpt)
{
  "build": {
    "devUrl": "http://localhost:5173",
    "frontendDist": "../build"
  },
  "app": {
    "windows": [{
      "title": "My App",
      "width": 1200,
      "height": 800
    }]
  }
}
```

```svelte
<!-- Tauri IPC call -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  let result = $state<string>('');

  onMount(async () => {
    if (!browser) return;
    const { invoke } = await import('@tauri-apps/api/core');
    result = await invoke<string>('my_command', { name: 'world' });
  });
</script>
```

See [reference.md](reference.md) for complete Tauri 2 setup including Rust command definitions, event system, auto-updater, and system tray.

## Vite Configuration Essentials

```typescript
// vite.config.ts
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],

  // Define global constants (replaces at build time)
  define: {
    '__APP_VERSION__': JSON.stringify(process.env.npm_package_version),
  },

  // Pre-bundle these dependencies
  optimizeDeps: {
    include: ['@sveltejs/kit', 'svelte'],
  },

  server: {
    port: 5173,
    // Proxy API calls during development
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        rewrite: (path) => path.replace(/^\/api/, ''),
      }
    }
  }
});
```

## Additional Resources

- [reference.md](reference.md) — Complete per-target deployment configs (SPA, SSR, static, hybrid, PWA), Tauri 2 complete setup (Rust commands, events, auto-updater, system tray, multi-window), Electron IPC patterns, CI/CD with GitHub Actions, Docker configs for adapter-node

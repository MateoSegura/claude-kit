# Build & Deploy Reference — Complete Target Configurations

## SPA Mode (Client-Side Only)

Use for: Electron, Tauri, apps that cannot do SSR, or when you need full client-side navigation without server.

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({
      fallback: '200.html',  // Required for SPA routing in web hosts
      precompress: false,    // Let host handle compression
    })
  }
};
```

```typescript
// src/routes/+layout.ts — disable SSR for entire app
export const ssr = false;
export const prerender = false;
```

## SSR Mode (Server-Side Rendering)

### adapter-node

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-node';

export default {
  kit: {
    adapter: adapter({
      out: 'build',
    })
  }
};
```

```dockerfile
# Dockerfile for adapter-node
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=builder /app/build ./build
COPY --from=builder /app/package*.json ./
RUN npm ci --production
EXPOSE 3000
ENV PORT=3000
CMD ["node", "build"]
```

### adapter-vercel

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-vercel';

export default {
  kit: {
    adapter: adapter({
      runtime: 'nodejs22.x',
      split: true,           // Separate function per route for cold start optimization
    })
  }
};
```

```typescript
// Per-route config in +page.server.ts
export const config = {
  // Edge runtime (faster cold start, global distribution)
  runtime: 'edge',
};

// Or ISR
export const config = {
  isr: {
    expiration: 60,                          // Revalidate every 60 seconds
    bypassToken: process.env.BYPASS_TOKEN,   // On-demand revalidation
    allowQuery: ['sort', 'filter'],          // Cache different query combinations
  }
};
```

### adapter-cloudflare

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-cloudflare';

export default {
  kit: {
    adapter: adapter({
      routes: {
        include: ['/*'],
        exclude: ['<all>'],  // Static assets served by Cloudflare CDN directly
      }
    })
  }
};
```

```toml
# wrangler.toml
name = "my-sveltekit-app"
compatibility_date = "2024-01-01"
compatibility_flags = ["nodejs_compat"]
pages_build_output_dir = ".svelte-kit/cloudflare"

[[kv_namespaces]]
binding = "MY_KV"
id = "your-kv-namespace-id"
```

```typescript
// src/app.d.ts
declare global {
  namespace App {
    interface Platform {
      env: {
        MY_KV: KVNamespace;
        MY_D1: D1Database;
        MY_R2: R2Bucket;
      };
      context: ExecutionContext;
    }
  }
}
```

## Static Site Generation (SSG)

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: undefined,  // No fallback = strict SSG
      precompress: true,    // Generate .gz and .br files
      strict: true,         // Error if any route not prerenderable
    }),
    prerender: {
      crawl: true,
      entries: ['*'],
      handleHttpError: ({ path, referrer, message }) => {
        // Ignore 404s for known dynamic paths
        if (path.startsWith('/api/')) return;
        throw new Error(message);
      }
    }
  }
};
```

## Hybrid Mode (Per-Route Config)

Mix SSR, prerendered, and CSR routes in one app:

```typescript
// src/routes/blog/[slug]/+page.ts — prerender blog posts
export const prerender = true;

// src/routes/dashboard/+page.ts — SSR (default, no config needed)

// src/routes/editor/+page.ts — CSR only (no SSR needed for heavy editor)
export const ssr = false;
```

## PWA Setup

```typescript
// vite.config.ts with vite-plugin-pwa
import { sveltekit } from '@sveltejs/kit/vite';
import { VitePWA } from 'vite-plugin-pwa';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [
    sveltekit(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,webp,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.example\.com\//,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: { maxEntries: 100, maxAgeSeconds: 300 },
            }
          }
        ]
      },
      manifest: {
        name: 'My SvelteKit App',
        short_name: 'MyApp',
        theme_color: '#1a56db',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ]
      }
    })
  ]
});
```

## Tauri 2 Complete Setup

### Project Structure

```
my-app/
├── src/                      # SvelteKit frontend
│   └── routes/
├── src-tauri/                # Rust backend
│   ├── src/
│   │   ├── main.rs
│   │   ├── lib.rs
│   │   └── commands.rs       # IPC command handlers
│   ├── Cargo.toml
│   └── tauri.conf.json
├── svelte.config.js
└── package.json
```

### svelte.config.js for Tauri

```javascript
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({ fallback: '200.html' }),
  }
};
```

### tauri.conf.json

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "My App",
  "version": "0.1.0",
  "identifier": "com.example.myapp",
  "build": {
    "frontendDist": "../build",
    "devUrl": "http://localhost:5173",
    "beforeDevCommand": "pnpm dev",
    "beforeBuildCommand": "pnpm build"
  },
  "app": {
    "windows": [{
      "title": "My App",
      "width": 1200,
      "height": 800,
      "resizable": true,
      "fullscreen": false
    }],
    "security": {
      "csp": "default-src 'self'; img-src 'self' asset: https://asset.localhost"
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": ["icons/32x32.png", "icons/128x128.png", "icons/128x128@2x.png", "icons/icon.icns", "icons/icon.ico"]
  }
}
```

### Rust IPC Commands (src-tauri/src/commands.rs)

```rust
use tauri::State;
use std::sync::Mutex;

pub struct AppState {
    pub counter: Mutex<u32>,
}

// Simple command returning a value
#[tauri::command]
pub async fn greet(name: &str) -> Result<String, String> {
    Ok(format!("Hello, {}!", name))
}

// Command with app state
#[tauri::command]
pub fn increment_counter(state: State<AppState>) -> u32 {
    let mut counter = state.counter.lock().unwrap();
    *counter += 1;
    *counter
}

// Async command with error handling
#[tauri::command]
pub async fn read_file(path: String) -> Result<String, String> {
    tokio::fs::read_to_string(&path)
        .await
        .map_err(|e| e.to_string())
}
```

```rust
// src-tauri/src/lib.rs
mod commands;
use commands::{greet, increment_counter, read_file};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(commands::AppState { counter: Default::default() })
        .invoke_handler(tauri::generate_handler![
            greet,
            increment_counter,
            read_file,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Svelte IPC Invocation (Tauri 2)

```typescript
// src/lib/tauri.ts — typed IPC wrapper
import { invoke } from '@tauri-apps/api/core';
import { browser } from '$app/environment';

// Typed wrapper that only runs in browser (Tauri WebView)
export async function tauriInvoke<T>(
  command: string,
  args?: Record<string, unknown>
): Promise<T> {
  if (!browser) throw new Error('Tauri commands only available in browser');
  return invoke<T>(command, args);
}
```

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { tauriInvoke } from '$lib/tauri.ts';

  let greeting = $state('');
  let count = $state(0);

  onMount(async () => {
    greeting = await tauriInvoke<string>('greet', { name: 'World' });
  });

  async function increment() {
    count = await tauriInvoke<number>('increment_counter');
  }
</script>
```

### Tauri Events (Bidirectional)

```typescript
// Frontend: listen for Rust events
import { listen } from '@tauri-apps/api/event';

const unlisten = await listen<string>('download-progress', (event) => {
  console.log('Progress:', event.payload);
});

// Cleanup
onDestroy(() => unlisten());
```

```rust
// Rust: emit event to frontend
use tauri::{AppHandle, Emitter};

#[tauri::command]
pub async fn start_download(app: AppHandle, url: String) -> Result<(), String> {
    // ... download logic ...
    app.emit("download-progress", "50%").map_err(|e| e.to_string())
}
```

## Electron Integration

### Setup

```bash
pnpm add -D electron electron-builder concurrently wait-on
pnpm add @electron-toolkit/preload @electron-toolkit/utils
```

```javascript
// svelte.config.js — same as Tauri: SPA mode
import adapter from '@sveltejs/adapter-static';
export default {
  kit: { adapter: adapter({ fallback: '200.html' }) }
};
```

### Main Process (electron/main.ts)

```typescript
import { app, BrowserWindow, ipcMain } from 'electron';
import { join } from 'path';

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      contextIsolation: true,    // Security: required
      nodeIntegration: false,    // Security: do not enable
    }
  });

  if (process.env.NODE_ENV === 'development') {
    win.loadURL('http://localhost:5173');
  } else {
    win.loadFile(join(__dirname, '../build/200.html'));
  }
}

// IPC handler
ipcMain.handle('read-file', async (event, path: string) => {
  const { readFile } = await import('fs/promises');
  return readFile(path, 'utf-8');
});

app.whenReady().then(createWindow);
```

### Preload Script (electron/preload.ts)

```typescript
import { contextBridge, ipcRenderer } from 'electron';

// Expose only what the renderer needs — no full node access
contextBridge.exposeInMainWorld('electron', {
  readFile: (path: string) => ipcRenderer.invoke('read-file', path),
  platform: process.platform,
});
```

### Renderer (Svelte) Usage

```svelte
<script lang="ts">
  declare global {
    interface Window {
      electron: {
        readFile: (path: string) => Promise<string>;
        platform: string;
      };
    }
  }

  import { browser } from '$app/environment';

  async function openFile() {
    if (!browser || !window.electron) return;
    const content = await window.electron.readFile('/path/to/file.txt');
    console.log(content);
  }
</script>
```

## CI/CD — GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Type check
        run: pnpm svelte-check

      - name: Lint
        run: pnpm lint

      - name: Build
        run: pnpm build
        env:
          PUBLIC_API_BASE: ${{ vars.PUBLIC_API_BASE }}

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build
          path: build/
          retention-days: 7
```

## Package.json Scripts

```json
{
  "scripts": {
    "dev": "vite dev",
    "build": "vite build",
    "preview": "vite preview",
    "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
    "check:watch": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json --watch",
    "lint": "prettier --check . && eslint .",
    "format": "prettier --write .",
    "test": "vitest run",
    "test:ui": "vitest --ui",
    "test:e2e": "playwright test",
    "analyze": "ANALYZE=true pnpm build"
  }
}
```

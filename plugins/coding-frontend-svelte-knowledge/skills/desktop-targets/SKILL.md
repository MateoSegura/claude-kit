---
name: coding-frontend-svelte-knowledge:desktop-targets
description: "Tauri 2 and Electron integration with SvelteKit: adapter-static SPA configuration, Tauri IPC invoke patterns, Rust commands, Electron with electron-vite, desktop-specific OS features, cross-platform CI, and binary size comparison."
---

# Desktop Targets Quick Reference

## Tauri 2 vs Electron Comparison

| Aspect | Tauri 2 | Electron |
|--------|---------|---------|
| Binary size | ~3–8 MB | ~150–200 MB |
| RAM usage | ~30–80 MB | ~100–200 MB |
| Backend language | Rust | Node.js |
| WebView | OS native (WebKit/Edge/WebKitGTK) | Chromium (bundled) |
| Rendering consistency | Platform-specific (test on each OS) | Identical cross-platform |
| Plugin ecosystem | Growing (tauri-apps plugins) | Large (npm) |
| Startup time | Faster (native binary) | Slower (V8 startup) |
| IPC mechanism | Rust commands via invoke() | contextBridge / ipcRenderer |
| Auto-updater | Built-in | electron-updater |

**Choose Tauri:** Security-sensitive apps, low memory requirement, system utilities, small installers.

**Choose Electron:** Need Node.js ecosystem, complex OS integration, team already knows Node/JS, CSS rendering consistency critical.

## Tauri 2 — SvelteKit Configuration

### 1. Install and configure adapter-static

```bash
npm install --save-dev @sveltejs/adapter-static
npm install --save-dev @tauri-apps/cli@^2
```

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      fallback: 'index.html',  // SPA mode — all routes served from index.html
      pages: 'build',
      assets: 'build',
      precompress: false,
      strict: true
    })
  }
};
```

```typescript
// src/routes/+layout.ts — disable SSR globally
export const ssr = false;
// SPA mode: load functions run in webview, can access Tauri APIs
```

### 2. Tauri project structure

```
my-app/
├── src/                     # SvelteKit source
├── src-tauri/               # Tauri Rust backend
│   ├── src/
│   │   ├── main.rs
│   │   └── lib.rs           # Tauri commands live here
│   ├── Cargo.toml
│   └── tauri.conf.json
├── svelte.config.js
├── vite.config.ts
└── package.json
```

### 3. tauri.conf.json

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "My App",
  "version": "0.1.0",
  "identifier": "com.mycompany.myapp",
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../build"
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": ["icons/32x32.png", "icons/128x128.png", "icons/icon.icns", "icons/icon.ico"]
  },
  "app": {
    "windows": [{
      "title": "My App",
      "width": 1200,
      "height": 800,
      "minWidth": 800,
      "minHeight": 600,
      "resizable": true,
      "fullscreen": false
    }]
  },
  "security": {
    "csp": "default-src 'self'; img-src 'self' asset: https://asset.localhost;"
  }
}
```

## Tauri IPC — Calling Rust from Svelte

### Define Rust command

```rust
// src-tauri/src/lib.rs
use tauri::AppHandle;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn read_config(app: AppHandle) -> Result<String, String> {
    let config_path = app.path().app_config_dir()
        .map_err(|e| e.to_string())?
        .join("config.json");

    std::fs::read_to_string(&config_path)
        .map_err(|e| format!("Failed to read config: {}", e))
}

#[tauri::command]
async fn save_file(path: String, content: String) -> Result<(), String> {
    std::fs::write(&path, &content)
        .map_err(|e| format!("Failed to write file: {}", e))
}

// Register commands in builder
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![greet, read_config, save_file])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Call from SvelteKit

```svelte
<script>
  import { invoke } from '@tauri-apps/api/core';

  let message = $state('');
  let config = $state<string | null>(null);

  async function greet() {
    // Types match Rust function signature
    message = await invoke<string>('greet', { name: 'World' });
  }

  async function loadConfig() {
    try {
      const raw = await invoke<string>('read_config');
      config = JSON.parse(raw);
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  }

  async function saveContent(path: string, content: string) {
    await invoke<void>('save_file', { path, content });
  }
</script>

<button onclick={greet}>Greet from Rust</button>
<p>{message}</p>
```

### Tauri Events (Rust → Svelte)

```rust
// Emit events from Rust
use tauri::{AppHandle, Emitter};

#[tauri::command]
async fn start_processing(app: AppHandle) {
    for i in 0..100 {
        app.emit("progress", i).unwrap();
        tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
    }
    app.emit("processing-done", ()).unwrap();
}
```

```svelte
<script>
  import { listen } from '@tauri-apps/api/event';
  import { onDestroy } from 'svelte';

  let progress = $state(0);

  const unlisten = listen<number>('progress', (event) => {
    progress = event.payload;
  });

  onDestroy(async () => {
    (await unlisten)(); // cleanup listener
  });
</script>

<progress value={progress} max={100} />
```

## Tauri — Desktop-Specific Features

### File System Access

```bash
# Cargo.toml — add filesystem plugin
[dependencies]
tauri-plugin-fs = "2"
```

```svelte
<script>
  import { open, save } from '@tauri-apps/plugin-dialog';
  import { readTextFile, writeTextFile } from '@tauri-apps/plugin-fs';

  async function openFile() {
    const selected = await open({
      multiple: false,
      filters: [{ name: 'Text', extensions: ['txt', 'md'] }]
    });
    if (selected) {
      const content = await readTextFile(selected as string);
      text = content;
    }
  }

  async function saveFile() {
    const path = await save({
      filters: [{ name: 'Text', extensions: ['txt'] }]
    });
    if (path) {
      await writeTextFile(path, text);
    }
  }
</script>
```

### System Tray

```rust
// src-tauri/src/lib.rs
use tauri::{
    menu::{MenuBuilder, MenuItemBuilder},
    tray::{MouseButton, TrayIconBuilder, TrayIconEvent},
};

fn setup_tray(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let show = MenuItemBuilder::new("Show").id("show").build(app)?;
    let quit = MenuItemBuilder::new("Quit").id("quit").build(app)?;
    let menu = MenuBuilder::new(app).items(&[&show, &quit]).build()?;

    TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&menu)
        .on_menu_event(|app, event| match event.id.as_ref() {
            "show" => { let _ = app.get_webview_window("main").unwrap().show(); }
            "quit" => { app.exit(0); }
            _ => {}
        })
        .build(app)?;

    Ok(())
}
```

### Native Menus

```rust
use tauri::menu::{MenuBuilder, MenuItemBuilder, SubmenuBuilder};

fn setup_menu(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let file_menu = SubmenuBuilder::new(app, "File")
        .item(&MenuItemBuilder::new("New").id("new").build(app)?)
        .item(&MenuItemBuilder::new("Open").id("open").build(app)?)
        .separator()
        .item(&MenuItemBuilder::new("Quit").id("quit").build(app)?)
        .build()?;

    let menu = MenuBuilder::new(app).items(&[&file_menu]).build()?;
    app.set_menu(menu)?;

    Ok(())
}
```

## Electron with electron-vite

```bash
npm create electron-vite@latest my-app -- --template svelte-ts
cd my-app && npm install
```

### SvelteKit SPA mode with Electron

Electron requires static files — use SvelteKit in SPA mode:

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({ fallback: 'index.html' })
  }
};
```

```typescript
// electron/main.ts
import { app, BrowserWindow, ipcMain } from 'electron';
import { join } from 'path';

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false // never enable
    }
  });

  if (process.env.NODE_ENV === 'development') {
    win.loadURL('http://localhost:5173');
  } else {
    win.loadFile(join(__dirname, '../build/index.html'));
  }
}
```

### Secure IPC (contextBridge)

```typescript
// electron/preload.ts — expose limited API via contextBridge
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  openFile: () => ipcRenderer.invoke('dialog:open-file'),
  saveFile: (content: string) => ipcRenderer.invoke('fs:save-file', content),
  onUpdate: (callback: (v: string) => void) => {
    ipcRenderer.on('app:update', (_, v) => callback(v));
  }
});
```

```svelte
<!-- SvelteKit component — access via window.electronAPI -->
<script>
  // Type declaration
  declare global {
    interface Window {
      electronAPI: {
        openFile: () => Promise<string | null>;
        saveFile: (content: string) => Promise<void>;
      };
    }
  }

  async function openFile() {
    // Only runs in Electron — check if API exists first
    if (window.electronAPI) {
      const content = await window.electronAPI.openFile();
      text = content ?? text;
    }
  }
</script>
```

## Cross-Platform CI (GitHub Actions)

```yaml
# .github/workflows/build.yml
name: Build

on:
  push:
    tags: ['v*']

jobs:
  build-tauri:
    strategy:
      matrix:
        platform:
          - os: ubuntu-22.04
            target: x86_64-unknown-linux-gnu
          - os: macos-latest
            target: aarch64-apple-darwin
          - os: windows-latest
            target: x86_64-pc-windows-msvc

    runs-on: ${{ matrix.platform.os }}

    steps:
      - uses: actions/checkout@v4

      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.platform.target }}

      - name: Install Linux dependencies
        if: matrix.platform.os == 'ubuntu-22.04'
        run: |
          sudo apt-get update
          sudo apt-get install -y libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - run: npm ci

      - name: Build Tauri app
        uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}
        with:
          tagName: ${{ github.ref_name }}
          releaseName: 'Release ${{ github.ref_name }}'
          args: --target ${{ matrix.platform.target }}
```

## Desktop Development Checklist

- [ ] SvelteKit configured with `adapter-static` and `fallback: 'index.html'`
- [ ] `ssr = false` in root `+layout.ts`
- [ ] Tauri APIs only called client-side (wrapped in `if (browser)` from `$app/environment` if needed)
- [ ] File system operations use Tauri plugins, not web File API
- [ ] Window management (minimize, maximize, close) uses Tauri window API
- [ ] Auto-updater configured for production builds
- [ ] Code signing configured for macOS (notarization) and Windows (EV cert)
- [ ] App icon provided in all required sizes
- [ ] Keyboard shortcuts match platform conventions (Cmd vs Ctrl)

## Additional Resources

- [tauri-plugins-reference.md](tauri-plugins-reference.md) — Full list of official Tauri 2 plugins: fs, dialog, notification, shell, http, store, window-state, clipboard, global-shortcut, deep-link; integration patterns and permissions configuration
- For USB/serial/HID communication, see the **usb-serial-hid** skill
- For Bluetooth Low Energy, see the **ble-communication** skill
- For LAN/network device discovery, see the **lan-discovery** skill
- For audio and MIDI devices, see the **audio-midi-devices** skill
- For hardware abstraction patterns and IoT protocols, see the **hardware-abstraction** skill

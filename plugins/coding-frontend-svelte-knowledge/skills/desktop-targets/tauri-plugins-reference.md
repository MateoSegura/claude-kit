# Tauri 2 — Plugins Reference

## Official Tauri 2 Plugin Catalog

All official plugins live in `@tauri-apps/plugin-*`. Install via npm and add to `Cargo.toml`.

| Plugin | npm Package | Cargo Crate | Purpose |
|--------|------------|-------------|---------|
| File System | `@tauri-apps/plugin-fs` | `tauri-plugin-fs` | Read/write files |
| Dialog | `@tauri-apps/plugin-dialog` | `tauri-plugin-dialog` | Open/save file dialogs, message boxes |
| Notification | `@tauri-apps/plugin-notification` | `tauri-plugin-notification` | System notifications |
| Shell | `@tauri-apps/plugin-shell` | `tauri-plugin-shell` | Open external URLs, spawn processes |
| HTTP Client | `@tauri-apps/plugin-http` | `tauri-plugin-http` | Bypass CORS restrictions |
| Store | `@tauri-apps/plugin-store` | `tauri-plugin-store` | Persistent key-value storage |
| Window State | `@tauri-apps/plugin-window-state` | `tauri-plugin-window-state` | Persist window size/position |
| Clipboard | `@tauri-apps/plugin-clipboard-manager` | `tauri-plugin-clipboard-manager` | Clipboard read/write |
| Global Shortcut | `@tauri-apps/plugin-global-shortcut` | `tauri-plugin-global-shortcut` | App-wide keyboard shortcuts |
| Deep Link | `@tauri-apps/plugin-deep-link` | `tauri-plugin-deep-link` | Custom URL scheme handling |
| Updater | `@tauri-apps/plugin-updater` | `tauri-plugin-updater` | Auto-updater |
| Positioner | `@tauri-apps/plugin-positioner` | `tauri-plugin-positioner` | Window positioning helpers |
| Log | `@tauri-apps/plugin-log` | `tauri-plugin-log` | File-based logging |
| Stronghold | `@tauri-apps/plugin-stronghold` | `tauri-plugin-stronghold` | Encrypted secret storage |
| Biometric | `@tauri-apps/plugin-biometric` | `tauri-plugin-biometric` | Fingerprint/Face ID auth |

## Plugin Setup Pattern

```toml
# src-tauri/Cargo.toml
[dependencies]
tauri-plugin-fs = "2"
tauri-plugin-dialog = "2"
tauri-plugin-store = "2"
```

```rust
// src-tauri/src/lib.rs
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .invoke_handler(tauri::generate_handler![my_command])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

## Permissions Configuration

Tauri 2 uses a permissions system — capabilities define what the app can do:

```json
// src-tauri/capabilities/default.json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Default app capabilities",
  "platforms": ["linux", "macOS", "windows"],
  "windows": ["main"],
  "permissions": [
    "core:default",
    "fs:allow-read-text-file",
    "fs:allow-write-text-file",
    "fs:allow-app-read",
    "fs:allow-app-write",
    "dialog:allow-open",
    "dialog:allow-save",
    "dialog:allow-message",
    "shell:allow-open",
    "notification:allow-notify",
    "store:allow-get",
    "store:allow-set",
    "store:allow-save"
  ]
}
```

## File System Plugin

```svelte
<script>
  import {
    readTextFile,
    readBinaryFile,
    writeTextFile,
    writeBinaryFile,
    readDir,
    mkdir,
    remove,
    exists,
    copyFile,
    rename
  } from '@tauri-apps/plugin-fs';

  import {
    appDataDir,
    appConfigDir,
    appLocalDataDir,
    homeDir,
    downloadDir,
    documentsDir
  } from '@tauri-apps/api/path';

  async function loadUserConfig() {
    const dir = await appConfigDir();
    const configPath = `${dir}/config.json`;

    if (await exists(configPath)) {
      const content = await readTextFile(configPath);
      return JSON.parse(content);
    }
    return null;
  }

  async function saveUserConfig(config: object) {
    const dir = await appConfigDir();
    await mkdir(dir, { recursive: true });
    await writeTextFile(`${dir}/config.json`, JSON.stringify(config, null, 2));
  }
</script>
```

## Dialog Plugin

```svelte
<script>
  import { open, save, message, ask, confirm } from '@tauri-apps/plugin-dialog';

  async function pickFiles() {
    const selected = await open({
      multiple: true,
      directory: false,
      filters: [{
        name: 'Images',
        extensions: ['png', 'jpg', 'jpeg', 'gif', 'webp']
      }]
    });
    // Returns string | string[] | null
    return Array.isArray(selected) ? selected : selected ? [selected] : [];
  }

  async function pickFolder() {
    return await open({ directory: true, multiple: false });
  }

  async function saveAs(content: string) {
    const path = await save({
      defaultPath: 'document.txt',
      filters: [{ name: 'Text', extensions: ['txt', 'md'] }]
    });
    if (path) {
      await writeTextFile(path, content);
    }
  }

  async function confirmDelete() {
    return await confirm('Delete this item? This cannot be undone.', {
      title: 'Confirm Delete',
      kind: 'warning',
      okLabel: 'Delete',
      cancelLabel: 'Cancel'
    });
  }
</script>
```

## Store Plugin (Persistent Key-Value)

```svelte
<script>
  import { Store } from '@tauri-apps/plugin-store';

  const store = new Store('settings.json');

  async function loadSettings() {
    await store.load();
    const theme = await store.get<string>('theme') ?? 'system';
    const fontSize = await store.get<number>('fontSize') ?? 14;
    return { theme, fontSize };
  }

  async function saveSettings(settings: { theme: string; fontSize: number }) {
    await store.set('theme', settings.theme);
    await store.set('fontSize', settings.fontSize);
    await store.save(); // persist to disk
  }
</script>
```

## Shell Plugin (Open External URLs)

```svelte
<script>
  import { open } from '@tauri-apps/plugin-shell';

  // Open in default browser
  async function openDocs() {
    await open('https://tauri.app');
  }

  // Open in default email client
  async function openEmail() {
    await open('mailto:support@example.com');
  }

  // Open file in default app
  async function openFile(path: string) {
    await open(path);
  }
</script>
```

## Window State Plugin

```rust
// src-tauri/src/lib.rs — saves window position/size between sessions
use tauri_plugin_window_state::{AppHandleExt, StateFlags};

pub fn run() {
    tauri::Builder::default()
        .plugin(
            tauri_plugin_window_state::Builder::default()
                .with_state_flags(StateFlags::all())  // size, position, maximized
                .build()
        )
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

## Global Shortcut Plugin

```svelte
<script>
  import { register, unregister, isRegistered } from '@tauri-apps/plugin-global-shortcut';
  import { onDestroy } from 'svelte';

  async function setupShortcuts() {
    // Register Cmd+Shift+P (macOS) / Ctrl+Shift+P (Windows/Linux)
    await register('CommandOrControl+Shift+P', () => {
      openCommandPalette();
    });

    // Platform-specific
    await register('CommandOrControl+Option+I', () => {
      toggleDevTools();
    });
  }

  onDestroy(async () => {
    await unregister('CommandOrControl+Shift+P');
  });
</script>
```

## Clipboard Plugin

```svelte
<script>
  import { readText, writeText, readImage, writeImage } from '@tauri-apps/plugin-clipboard-manager';

  async function copyToClipboard(text: string) {
    await writeText(text);
  }

  async function pasteFromClipboard(): Promise<string> {
    return await readText();
  }
</script>
```

## Auto-Updater Plugin

```typescript
// src/lib/updater.ts
import { check } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';
import { ask } from '@tauri-apps/plugin-dialog';

export async function checkForUpdates() {
  const update = await check();

  if (update) {
    const yes = await ask(
      `Update ${update.version} is available.\n\nRelease notes:\n${update.body}`,
      { title: 'Update Available', kind: 'info', okLabel: 'Update Now' }
    );

    if (yes) {
      let downloaded = 0;
      await update.downloadAndInstall((event) => {
        if (event.event === 'Progress') {
          downloaded = event.data.chunkLength;
        }
      });
      await relaunch();
    }
  }
}
```

```json
// tauri.conf.json — updater configuration
{
  "plugins": {
    "updater": {
      "pubkey": "YOUR_PUBLIC_KEY_HERE",
      "endpoints": [
        "https://releases.myapp.com/{{target}}/{{arch}}/{{current_version}}"
      ]
    }
  }
}
```

## Notification Plugin

```svelte
<script>
  import { sendNotification, requestPermission, isPermissionGranted } from '@tauri-apps/plugin-notification';

  async function notify(title: string, body: string) {
    let permissionGranted = await isPermissionGranted();

    if (!permissionGranted) {
      const permission = await requestPermission();
      permissionGranted = permission === 'granted';
    }

    if (permissionGranted) {
      await sendNotification({
        title,
        body,
        icon: 'icons/icon.png',
        sound: 'default'
      });
    }
  }
</script>
```

## Deep Link Plugin

```json
// tauri.conf.json — register URL scheme
{
  "plugins": {
    "deep-link": {
      "desktop": {
        "schemes": ["myapp"]
      }
    }
  }
}
```

```rust
// src-tauri/src/lib.rs
use tauri_plugin_deep_link::DeepLinkExt;

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_deep_link::init())
        .setup(|app| {
            app.deep_link().on_open_url(|event| {
                // Handle myapp://... URLs
                println!("Deep link: {:?}", event.urls());
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

## Desktop-Specific SvelteKit Guards

```typescript
// Guard Tauri-specific code from SSR and browser builds
import { browser } from '$app/environment';

export const isTauri = browser && '__TAURI_INTERNALS__' in window;

// Use in components
async function openFile() {
  if (!isTauri) {
    // Fallback for browser/Electron
    const [fileHandle] = await window.showOpenFilePicker();
    return await fileHandle.getFile();
  }

  // Tauri-specific
  const { open } = await import('@tauri-apps/plugin-dialog');
  return await open({ multiple: false });
}
```

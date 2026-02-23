---
name: coding-frontend-svelte-knowledge:ble-communication
description: "Bluetooth Low Energy communication from Tauri apps: BLE scanning and device discovery, GATT service/characteristic model, btleplug crate for direct Rust BLE, tauri-plugin-blec community plugin, device pairing and bonding, characteristic read/write/notify, and cross-platform permissions."
user-invocable: true
---

# BLE Communication Quick Reference

## Section 1 — BLE Fundamentals

| Concept | Description |
|---------|-------------|
| **GAP** | Generic Access Profile — governs advertising (peripheral broadcasts) and scanning (central discovers) |
| **GATT** | Generic Attribute Profile — governs service/characteristic data exchange after connection |
| **Central** | Device that scans and initiates connections (your Tauri app) |
| **Peripheral** | Device that advertises and accepts connections (sensor, wearable, etc.) |
| **Service** | Logical grouping of related characteristics; identified by UUID |
| **Characteristic** | Individual data value within a service; supports read/write/notify operations |
| **Descriptor** | Metadata about a characteristic (e.g., CCCD to enable notifications) |
| **UUID** | 16-bit (Bluetooth SIG standard, e.g. `0x180D`) or 128-bit (custom vendor UUID) |
| **MTU** | Maximum Transmission Unit — negotiated on connect; default 23 bytes, negotiate up to 512 |
| **Connection interval** | How often central and peripheral exchange packets; shorter = faster, more power |
| **RSSI** | Received Signal Strength Indicator — negative dBm; closer to 0 = stronger signal |

### UUID Formats

```rust
use uuid::{uuid, Uuid};

// 16-bit standard UUID (Bluetooth SIG assigned)
const HEART_RATE_SERVICE: Uuid = uuid!("0000180d-0000-1000-8000-00805f9b34fb");
const BATTERY_SERVICE:    Uuid = uuid!("0000180f-0000-1000-8000-00805f9b34fb");
const HEART_RATE_MEAS:    Uuid = uuid!("00002a37-0000-1000-8000-00805f9b34fb");

// Custom 128-bit UUID (generate with uuidgen)
const MY_SERVICE:     Uuid = uuid!("12345678-1234-1234-1234-1234567890ab");
const MY_CHAR_NOTIFY: Uuid = uuid!("12345678-1234-1234-1234-1234567890ac");
```

---

## Section 2 — Crate Decision: btleplug vs tauri-plugin-blec

| Aspect | btleplug | tauri-plugin-blec |
|--------|----------|-------------------|
| Integration | Direct Rust crate | Tauri plugin (wraps btleplug internally) |
| Android support | No | Yes |
| JavaScript API | None (Rust only) | Yes (`@mnlphlp/plugin-blec`) |
| Permissions setup | Manual per-platform | Handled by plugin capabilities system |
| Maturity | Mature, widely used | Community plugin, active development |
| Fine-grained control | Full API access | Higher-level API |

**Recommendation:** Use `tauri-plugin-blec` for Tauri apps — it gives you a JS API, handles Android, and integrates with Tauri's capabilities/permissions system. Use `btleplug` directly only when you need low-level control unavailable through the plugin (custom GATT descriptor access, scan filter details, multiple adapter management).

---

## Section 3 — BLE Scanning Patterns (btleplug)

```toml
# src-tauri/Cargo.toml
[dependencies]
btleplug = "0.11"
tokio = { version = "1", features = ["full"] }
uuid = { version = "1", features = ["v4"] }
```

```rust
// src-tauri/src/lib.rs
use btleplug::api::{Central, CentralEvent, Manager as _, Peripheral as _, ScanFilter};
use btleplug::platform::{Adapter, Manager, Peripheral};
use futures::stream::StreamExt;
use tauri::{AppHandle, Emitter};
use uuid::Uuid;

// Scan for all devices (no filter)
#[tauri::command]
pub async fn start_scan(app: AppHandle) -> Result<(), String> {
    let manager = Manager::new().await.map_err(|e| e.to_string())?;
    let adapters = manager.adapters().await.map_err(|e| e.to_string())?;
    let adapter = adapters.into_iter().next().ok_or("No BLE adapter found")?;

    // Scan with no filter — discovers all advertising devices
    adapter.start_scan(ScanFilter::default()).await.map_err(|e| e.to_string())?;

    let mut events = adapter.events().await.map_err(|e| e.to_string())?;

    tokio::spawn(async move {
        while let Some(event) = events.next().await {
            if let CentralEvent::DeviceDiscovered(id) = event {
                if let Ok(peripheral) = adapter.peripheral(&id).await {
                    if let Ok(Some(props)) = peripheral.properties().await {
                        let device_info = serde_json::json!({
                            "id": id.to_string(),
                            "name": props.local_name.unwrap_or_default(),
                            "rssi": props.rssi,
                            "services": props.services.iter().map(|u| u.to_string()).collect::<Vec<_>>(),
                        });
                        let _ = app.emit("ble-device-discovered", device_info);
                    }
                }
            }
        }
    });

    Ok(())
}

#[tauri::command]
pub async fn stop_scan(state: tauri::State<'_, BleState>) -> Result<(), String> {
    let guard = state.adapter.lock().await;
    if let Some(adapter) = guard.as_ref() {
        adapter.stop_scan().await.map_err(|e| e.to_string())?;
    }
    Ok(())
}
```

### Scan Filters

```rust
use btleplug::api::ScanFilter;

// Filter by service UUID — only returns peripherals advertising this service
let filter = ScanFilter {
    services: vec![HEART_RATE_SERVICE],
};
adapter.start_scan(filter).await?;

// Name prefix and manufacturer data filtering must be done manually
// after receiving DeviceDiscovered events, by inspecting peripheral.properties()
// — btleplug's ScanFilter only supports service UUID filtering natively.
```

### Deduplication by Peripheral ID

```rust
use std::collections::HashSet;
use btleplug::api::BDAddr;

let mut seen: HashSet<String> = HashSet::new();

while let Some(event) = events.next().await {
    if let CentralEvent::DeviceDiscovered(id) | CentralEvent::DeviceUpdated(id) = event {
        let key = id.to_string();
        if seen.insert(key.clone()) {
            // First time we see this peripheral — emit to frontend
            // DeviceUpdated fires when RSSI or advertising data changes;
            // use seen set to decide if you want to re-emit or just update RSSI
        }
    }
}
```

---

## Section 4 — GATT Interaction Patterns

```rust
use btleplug::api::{Characteristic, Peripheral as _, WriteType};

// Discover all services and characteristics on a connected peripheral
async fn explore_peripheral(peripheral: &Peripheral) -> Result<(), btleplug::Error> {
    peripheral.discover_services().await?;
    for service in peripheral.services() {
        println!("Service: {}", service.uuid);
        for char in &service.characteristics {
            println!("  Characteristic: {} — {:?}", char.uuid, char.properties);
        }
    }
    Ok(())
}

// Read a characteristic value
async fn read_battery(peripheral: &Peripheral) -> Result<u8, String> {
    let chars = peripheral.characteristics();
    let battery_char = chars.iter()
        .find(|c| c.uuid == BATTERY_LEVEL_CHAR)
        .ok_or("Battery characteristic not found")?;

    let data = peripheral.read(battery_char).await.map_err(|e| e.to_string())?;
    Ok(data[0]) // Battery level is a single byte 0–100
}

// Write with response (ACKed by peripheral)
async fn write_with_response(peripheral: &Peripheral, char: &Characteristic, value: &[u8]) -> Result<(), String> {
    peripheral.write(char, value, WriteType::WithResponse)
        .await.map_err(|e| e.to_string())
}

// Write without response (fire and forget, faster)
async fn write_no_response(peripheral: &Peripheral, char: &Characteristic, value: &[u8]) -> Result<(), String> {
    peripheral.write(char, value, WriteType::WithoutResponse)
        .await.map_err(|e| e.to_string())
}

// Subscribe to notifications
async fn subscribe_notifications(peripheral: &Peripheral, app: AppHandle) -> Result<(), String> {
    let chars = peripheral.characteristics();
    let notify_char = chars.iter()
        .find(|c| c.uuid == MY_CHAR_NOTIFY)
        .ok_or("Notify characteristic not found")?;

    peripheral.subscribe(notify_char).await.map_err(|e| e.to_string())?;

    let mut notifications = peripheral.notifications().await.map_err(|e| e.to_string())?;
    tokio::spawn(async move {
        while let Some(notif) = notifications.next().await {
            // Parse little-endian i16 temperature value (value / 100.0 = °C)
            let temp = if notif.value.len() >= 2 {
                let raw = i16::from_le_bytes([notif.value[0], notif.value[1]]);
                raw as f32 / 100.0
            } else { 0.0 };

            let _ = app.emit("ble-notification", serde_json::json!({
                "char": notif.uuid.to_string(),
                "raw": notif.value,
                "temperature_c": temp,
            }));
        }
    });
    Ok(())
}
```

### Common GATT Service UUIDs

| Service | UUID (16-bit) | Key Characteristics |
|---------|--------------|---------------------|
| Heart Rate | `0x180D` | Heart Rate Measurement `0x2A37` |
| Battery | `0x180F` | Battery Level `0x2A19` |
| Device Information | `0x180A` | Manufacturer `0x2A29`, Model `0x2A24` |
| Generic Access | `0x1800` | Device Name `0x2A00` |
| Generic Attribute | `0x1801` | Service Changed `0x2A05` |

---

## Section 5 — Device Connection Management

```rust
use std::{collections::HashMap, sync::Arc, time::Duration};
use tokio::sync::Mutex;
use btleplug::platform::Peripheral;

pub struct BleManager {
    adapter: Option<Adapter>,
    connected: HashMap<String, Peripheral>,
}

#[tauri::command]
pub async fn connect_device(
    peripheral_id: String,
    state: tauri::State<'_, BleState>,
) -> Result<(), String> {
    let guard = state.manager.lock().await;
    let peripheral = guard.adapter.as_ref()
        .ok_or("No adapter")?
        .peripheral(&peripheral_id.parse().map_err(|e: uuid::Error| e.to_string())?)
        .await.map_err(|e| e.to_string())?;

    // Connection with timeout
    tokio::time::timeout(
        Duration::from_secs(10),
        peripheral.connect()
    ).await
        .map_err(|_| "Connection timed out".to_string())?
        .map_err(|e| e.to_string())?;

    Ok(())
}

// Auto-reconnect on unexpected disconnect
async fn watch_connection(peripheral: Peripheral, app: AppHandle) {
    let mut events = match peripheral.events().await {
        Ok(e) => e,
        Err(_) => return,
    };
    while let Some(event) = events.next().await {
        if let btleplug::api::PeripheralEvent::Disconnected = event {
            app.emit("ble-disconnected", peripheral.id().to_string()).ok();
            // Attempt reconnect with exponential backoff
            for delay in [1, 2, 4, 8] {
                tokio::time::sleep(Duration::from_secs(delay)).await;
                if peripheral.connect().await.is_ok() {
                    app.emit("ble-reconnected", peripheral.id().to_string()).ok();
                    break;
                }
            }
        }
    }
}
```

---

## Section 6 — Tauri Integration

```rust
// State type — wrap BleManager in Arc<Mutex<>> for Tauri managed state
pub struct BleState {
    pub manager: Arc<Mutex<BleManager>>,
}

// Register in builder
pub fn run() {
    tauri::Builder::default()
        .manage(BleState {
            manager: Arc::new(Mutex::new(BleManager {
                adapter: None,
                connected: HashMap::new(),
            }))
        })
        .invoke_handler(tauri::generate_handler![
            start_scan,
            stop_scan,
            connect_device,
            disconnect_device,
            read_characteristic,
            write_characteristic,
        ])
        .on_window_event(|window, event| {
            // Cleanup on app exit: disconnect all peripherals
            if let tauri::WindowEvent::Destroyed = event {
                // spawn cleanup task
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

```svelte
<!-- BLE device list in Svelte -->
<script>
  import { listen } from '@tauri-apps/api/event';
  import { invoke } from '@tauri-apps/api/core';
  import { onDestroy } from 'svelte';

  let devices = $state([]);
  let scanning = $state(false);

  const unlisten = listen('ble-device-discovered', (event) => {
    const dev = event.payload;
    // Deduplicate by id
    if (!devices.find(d => d.id === dev.id)) {
      devices = [...devices, dev];
    }
  });

  async function startScan() {
    devices = [];
    scanning = true;
    await invoke('start_scan');
  }

  async function connect(id) {
    await invoke('connect_device', { peripheralId: id });
  }

  onDestroy(async () => { (await unlisten)(); });
</script>

<button onclick={startScan} disabled={scanning}>Scan</button>
{#each devices as device}
  <div>
    <span>{device.name || 'Unknown'}</span>
    <span>RSSI: {device.rssi} dBm</span>
    <button onclick={() => connect(device.id)}>Connect</button>
  </div>
{/each}
```

---

## Section 7 — Cross-Platform BLE Permissions

### macOS

Add to `src-tauri/Info.plist` (or via tauri.conf.json `bundle.macOS.infoPlist`):

```xml
<key>NSBluetoothAlwaysUsageDescription</key>
<string>This app uses Bluetooth to communicate with nearby devices.</string>
```

No special entitlements needed for desktop Bluetooth access on macOS (only required for iOS/iPad).

### Linux

BlueZ is the Linux BLE stack (via D-Bus). The user running the app must either:

- Be in the `bluetooth` group: `sudo usermod -aG bluetooth $USER` (requires re-login)
- Or have polkit rules granting access without group membership

btleplug uses BlueZ's D-Bus API directly — no extra system packages needed if BlueZ is installed (standard on Ubuntu/Fedora).

### Windows

Add a Bluetooth capability to `src-tauri/capabilities/default.json`:

```json
{
  "identifier": "default",
  "description": "Default app capabilities",
  "permissions": ["core:default"],
  "windows": ["main"],
  "platforms": ["windows"]
}
```

Windows Bluetooth requires the app to declare the `bluetooth` device capability in its app manifest. btleplug on Windows uses the WinRT Bluetooth API which requires Windows 10 1703+ (Build 15063).

---

## Additional Resources

- [ble-reference.md](ble-reference.md) — Complete btleplug and tauri-plugin-blec code examples, Svelte BLE scanner component, common BLE protocol parsing, error handling patterns, and testing strategies

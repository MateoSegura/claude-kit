# BLE Communication — Complete Reference

## Section 1 — btleplug Complete Example

Full async Rust example: manager setup, scan, connect, service discovery, read/write/notify.

```toml
# src-tauri/Cargo.toml
[dependencies]
btleplug = "0.11"
tokio = { version = "1", features = ["full"] }
uuid = { version = "1", features = ["v4"] }
futures = "0.3"
serde_json = "1"
```

```rust
use btleplug::api::{
    Central, CentralEvent, Manager as _, Peripheral as _,
    ScanFilter, WriteType,
};
use btleplug::platform::{Adapter, Manager, Peripheral};
use futures::stream::StreamExt;
use std::time::Duration;
use uuid::{uuid, Uuid};

const HEART_RATE_SERVICE: Uuid = uuid!("0000180d-0000-1000-8000-00805f9b34fb");
const HEART_RATE_MEAS:    Uuid = uuid!("00002a37-0000-1000-8000-00805f9b34fb");
const BATTERY_SERVICE:    Uuid = uuid!("0000180f-0000-1000-8000-00805f9b34fb");
const BATTERY_LEVEL:      Uuid = uuid!("00002a19-0000-1000-8000-00805f9b34fb");

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 1. Create manager and get first adapter
    let manager = Manager::new().await?;
    let adapters = manager.adapters().await?;
    let adapter: Adapter = adapters.into_iter().next()
        .ok_or("No BLE adapter found")?;

    println!("Using adapter: {:?}", adapter.adapter_info().await);

    // 2. Start scan — filter by Heart Rate service UUID
    adapter.start_scan(ScanFilter {
        services: vec![HEART_RATE_SERVICE],
    }).await?;

    // 3. Listen for discovered devices
    let mut events = adapter.events().await?;
    let mut target: Option<Peripheral> = None;

    tokio::time::timeout(Duration::from_secs(10), async {
        while let Some(event) = events.next().await {
            match event {
                CentralEvent::DeviceDiscovered(id) => {
                    let peripheral = adapter.peripheral(&id).await?;
                    let props = peripheral.properties().await?;
                    if let Some(p) = props {
                        println!("Found: {} ({:?}) RSSI: {:?}",
                            p.local_name.as_deref().unwrap_or("unknown"),
                            id,
                            p.rssi
                        );
                        target = Some(peripheral);
                        break;
                    }
                }
                _ => {}
            }
            Ok::<_, btleplug::Error>(())
        }
        Ok(())
    }).await??;

    adapter.stop_scan().await?;

    // 4. Connect
    let peripheral = target.ok_or("No device found")?;
    println!("Connecting...");
    peripheral.connect().await?;
    println!("Connected.");

    // 5. Discover services
    peripheral.discover_services().await?;

    for service in peripheral.services() {
        println!("Service: {}", service.uuid);
        for c in &service.characteristics {
            println!("  Characteristic: {} props={:?}", c.uuid, c.properties);
        }
    }

    // 6. Find and read Heart Rate Measurement characteristic
    let chars = peripheral.characteristics();

    let hr_char = chars.iter()
        .find(|c| c.uuid == HEART_RATE_MEAS)
        .ok_or("Heart Rate Measurement characteristic not found")?;

    // Subscribe to notifications
    peripheral.subscribe(hr_char).await?;
    let mut notifications = peripheral.notifications().await?;

    println!("Listening for heart rate notifications (Ctrl+C to stop)...");
    while let Some(notif) = notifications.next().await {
        if notif.uuid == HEART_RATE_MEAS {
            // Heart Rate Measurement format (Bluetooth spec):
            // Byte 0: flags (bit 0 = 0 means HR is uint8, 1 means uint16)
            // Byte 1 (or 1-2): heart rate value
            let flags = notif.value[0];
            let hr = if flags & 0x01 == 0 {
                notif.value[1] as u16
            } else {
                u16::from_le_bytes([notif.value[1], notif.value[2]])
            };
            println!("Heart rate: {} BPM", hr);
        }
    }

    peripheral.disconnect().await?;
    Ok(())
}
```

---

## Section 2 — tauri-plugin-blec Complete Example

### Installation

```bash
# Rust
cargo add tauri-plugin-blec

# JavaScript
npm install @mnlphlp/plugin-blec
```

### Rust: register plugin in Tauri builder

```rust
// src-tauri/src/lib.rs
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_blec::init())  // register BLE plugin
        .invoke_handler(tauri::generate_handler![])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Capabilities: `src-tauri/capabilities/default.json`

```json
{
  "identifier": "default",
  "description": "Default capabilities",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "blec:default"
  ]
}
```

### JavaScript API

```typescript
// src/lib/ble.svelte.ts
import {
  scan,
  connect,
  disconnect,
  read,
  write,
  startNotifications,
  stopNotifications,
  type BleDevice,
} from '@mnlphlp/plugin-blec';

// Scan for devices (returns array of BleDevice)
export async function scanDevices(timeoutMs = 5000): Promise<BleDevice[]> {
  return await scan(timeoutMs);
}

// Connect by device address
export async function connectDevice(address: string): Promise<void> {
  await connect(address);
}

// Read a characteristic (returns Uint8Array)
export async function readCharacteristic(
  serviceUuid: string,
  charUuid: string
): Promise<Uint8Array> {
  return await read(serviceUuid, charUuid);
}

// Write a characteristic
export async function writeCharacteristic(
  serviceUuid: string,
  charUuid: string,
  value: Uint8Array
): Promise<void> {
  await write(serviceUuid, charUuid, value);
}

// Subscribe to notifications — callback called on each notification
export async function subscribeToNotifications(
  serviceUuid: string,
  charUuid: string,
  callback: (value: Uint8Array) => void
): Promise<() => Promise<void>> {
  await startNotifications(serviceUuid, charUuid, callback);
  return () => stopNotifications(serviceUuid, charUuid);
}
```

---

## Section 3 — Wrapping btleplug in Tauri Commands

Full BleManager struct approach for production Tauri apps:

```rust
// src-tauri/src/ble/manager.rs
use btleplug::api::{Central, CentralEvent, Manager as _, Peripheral as _, ScanFilter, WriteType};
use btleplug::platform::{Adapter, Manager, Peripheral};
use futures::StreamExt;
use std::collections::HashMap;
use std::sync::Arc;
use tauri::{AppHandle, Emitter};
use tokio::sync::Mutex;
use uuid::Uuid;

pub struct BleManager {
    adapter: Option<Adapter>,
    peripherals: HashMap<String, Peripheral>,
}

impl BleManager {
    pub fn new() -> Self {
        Self { adapter: None, peripherals: HashMap::new() }
    }

    pub async fn init(&mut self) -> Result<(), String> {
        let manager = Manager::new().await.map_err(|e| e.to_string())?;
        let adapters = manager.adapters().await.map_err(|e| e.to_string())?;
        self.adapter = Some(adapters.into_iter().next().ok_or("No BLE adapter")?);
        Ok(())
    }
}

pub type BleState = Arc<Mutex<BleManager>>;

// Tauri command: scan and emit events to frontend
#[tauri::command]
pub async fn ble_start_scan(
    app: AppHandle,
    state: tauri::State<'_, BleState>,
) -> Result<(), String> {
    let mut guard = state.lock().await;
    if guard.adapter.is_none() {
        guard.init().await?;
    }
    let adapter = guard.adapter.as_ref().unwrap().clone();
    drop(guard); // release lock before spawning

    adapter.start_scan(ScanFilter::default()).await.map_err(|e| e.to_string())?;

    let app_clone = app.clone();
    tokio::spawn(async move {
        let Ok(mut events) = adapter.events().await else { return };
        while let Some(event) = events.next().await {
            match event {
                CentralEvent::DeviceDiscovered(id) | CentralEvent::DeviceUpdated(id) => {
                    if let Ok(p) = adapter.peripheral(&id).await {
                        if let Ok(Some(props)) = p.properties().await {
                            let _ = app_clone.emit("ble-scan-result", serde_json::json!({
                                "id": id.to_string(),
                                "name": props.local_name,
                                "rssi": props.rssi,
                                "services": props.services.iter().map(|u| u.to_string()).collect::<Vec<_>>(),
                            }));
                        }
                    }
                }
                _ => {}
            }
        }
    });

    Ok(())
}

#[tauri::command]
pub async fn ble_connect(
    peripheral_id: String,
    app: AppHandle,
    state: tauri::State<'_, BleState>,
) -> Result<(), String> {
    let guard = state.lock().await;
    let adapter = guard.adapter.as_ref().ok_or("BLE not initialized")?;
    let id = peripheral_id.parse().map_err(|_| "Invalid peripheral ID")?;
    let peripheral = adapter.peripheral(&id).await.map_err(|e| e.to_string())?;
    drop(guard);

    tokio::time::timeout(
        std::time::Duration::from_secs(10),
        peripheral.connect()
    ).await
        .map_err(|_| "Connection timeout")?
        .map_err(|e| e.to_string())?;

    state.lock().await.peripherals.insert(peripheral_id.clone(), peripheral);
    app.emit("ble-connected", &peripheral_id).ok();
    Ok(())
}

#[tauri::command]
pub async fn ble_disconnect(
    peripheral_id: String,
    app: AppHandle,
    state: tauri::State<'_, BleState>,
) -> Result<(), String> {
    let mut guard = state.lock().await;
    if let Some(p) = guard.peripherals.remove(&peripheral_id) {
        p.disconnect().await.map_err(|e| e.to_string())?;
        app.emit("ble-disconnected", &peripheral_id).ok();
    }
    Ok(())
}

#[tauri::command]
pub async fn ble_read(
    peripheral_id: String,
    service_uuid: String,
    char_uuid: String,
    state: tauri::State<'_, BleState>,
) -> Result<Vec<u8>, String> {
    let guard = state.lock().await;
    let peripheral = guard.peripherals.get(&peripheral_id).ok_or("Device not connected")?;
    let service_uuid: Uuid = service_uuid.parse().map_err(|_| "Invalid service UUID")?;
    let char_uuid: Uuid = char_uuid.parse().map_err(|_| "Invalid characteristic UUID")?;

    let chars = peripheral.characteristics();
    let characteristic = chars.iter()
        .find(|c| c.uuid == char_uuid)
        .ok_or("Characteristic not found")?;

    peripheral.read(characteristic).await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn ble_write(
    peripheral_id: String,
    char_uuid: String,
    value: Vec<u8>,
    with_response: bool,
    state: tauri::State<'_, BleState>,
) -> Result<(), String> {
    let guard = state.lock().await;
    let peripheral = guard.peripherals.get(&peripheral_id).ok_or("Device not connected")?;
    let char_uuid: Uuid = char_uuid.parse().map_err(|_| "Invalid characteristic UUID")?;

    let chars = peripheral.characteristics();
    let characteristic = chars.iter()
        .find(|c| c.uuid == char_uuid)
        .ok_or("Characteristic not found")?;

    let write_type = if with_response { WriteType::WithResponse } else { WriteType::WithoutResponse };
    peripheral.write(characteristic, &value, write_type).await.map_err(|e| e.to_string())
}
```

---

## Section 4 — Svelte BLE Device Scanner Component

```svelte
<!-- src/lib/BleScanner.svelte -->
<script lang="ts">
  import { listen } from '@tauri-apps/api/event';
  import { invoke } from '@tauri-apps/api/core';
  import { onDestroy } from 'svelte';

  interface BleDevice {
    id: string;
    name: string | null;
    rssi: number | null;
    services: string[];
  }

  interface Notification {
    char: string;
    raw: number[];
    temperature_c?: number;
  }

  let devices = $state<BleDevice[]>([]);
  let scanning = $state(false);
  let connectedId = $state<string | null>(null);
  let notifications = $state<Notification[]>([]);
  let error = $state<string | null>(null);

  // rssiToStrength: map dBm to signal bars label
  function rssiLabel(rssi: number | null): string {
    if (rssi == null) return 'Unknown';
    if (rssi >= -60) return 'Strong';
    if (rssi >= -75) return 'Good';
    if (rssi >= -90) return 'Weak';
    return 'Very weak';
  }

  const unlistenScan = listen<BleDevice>('ble-scan-result', (event) => {
    const dev = event.payload;
    if (!devices.find(d => d.id === dev.id)) {
      devices = [...devices, dev];
    }
  });

  const unlistenNotif = listen<Notification>('ble-notification', (event) => {
    notifications = [event.payload, ...notifications.slice(0, 49)]; // keep last 50
  });

  const unlistenDisconnect = listen<string>('ble-disconnected', (event) => {
    if (event.payload === connectedId) {
      connectedId = null;
      error = 'Device disconnected unexpectedly';
    }
  });

  async function startScan() {
    devices = [];
    error = null;
    scanning = true;
    try {
      await invoke('ble_start_scan');
      // Auto-stop after 10 seconds
      setTimeout(async () => {
        scanning = false;
        await invoke('ble_stop_scan').catch(() => {});
      }, 10_000);
    } catch (e) {
      error = String(e);
      scanning = false;
    }
  }

  async function connectDevice(id: string) {
    error = null;
    try {
      await invoke('ble_connect', { peripheralId: id });
      connectedId = id;
    } catch (e) {
      error = String(e);
    }
  }

  async function disconnectDevice() {
    if (!connectedId) return;
    await invoke('ble_disconnect', { peripheralId: connectedId }).catch(() => {});
    connectedId = null;
  }

  onDestroy(async () => {
    (await unlistenScan)();
    (await unlistenNotif)();
    (await unlistenDisconnect)();
  });
</script>

<div class="ble-scanner">
  {#if error}
    <p class="error">{error}</p>
  {/if}

  <div class="controls">
    <button onclick={startScan} disabled={scanning}>
      {scanning ? 'Scanning...' : 'Scan for Devices'}
    </button>
    {#if connectedId}
      <button onclick={disconnectDevice}>Disconnect</button>
    {/if}
  </div>

  <ul class="device-list">
    {#each devices as device (device.id)}
      <li class:connected={device.id === connectedId}>
        <span class="name">{device.name ?? 'Unknown Device'}</span>
        <span class="rssi" title="{device.rssi} dBm">{rssiLabel(device.rssi)}</span>
        {#if device.id !== connectedId}
          <button onclick={() => connectDevice(device.id)}>Connect</button>
        {:else}
          <span class="badge">Connected</span>
        {/if}
      </li>
    {/each}
  </ul>

  {#if notifications.length > 0}
    <section class="notifications">
      <h3>Live Notifications</h3>
      {#each notifications as notif (notif)}
        <div class="notif">
          <span class="char">{notif.char.slice(0, 8)}...</span>
          {#if notif.temperature_c != null}
            <span class="value">{notif.temperature_c.toFixed(1)} °C</span>
          {:else}
            <span class="value">[{notif.raw.join(', ')}]</span>
          {/if}
        </div>
      {/each}
    </section>
  {/if}
</div>
```

---

## Section 5 — Common BLE Protocol Parsing

### Heart Rate Service (0x180D)

```rust
// Characteristic 0x2A37 — Heart Rate Measurement
// Byte 0: flags
//   bit 0: HR format (0=uint8, 1=uint16)
//   bit 3-4: energy expended status
//   bit 5: RR interval present
fn parse_heart_rate(data: &[u8]) -> Option<u16> {
    if data.is_empty() { return None; }
    let flags = data[0];
    if flags & 0x01 == 0 {
        data.get(1).map(|&b| b as u16)
    } else {
        if data.len() < 3 { return None; }
        Some(u16::from_le_bytes([data[1], data[2]]))
    }
}
```

### Battery Service (0x180F)

```rust
// Characteristic 0x2A19 — Battery Level (single byte, 0–100%)
fn parse_battery_level(data: &[u8]) -> Option<u8> {
    data.first().copied()
}
```

### Custom Temperature Characteristic (vendor UUID)

```rust
// Custom encoding: i16 little-endian, value / 100.0 = temperature in °C
// e.g., [0x94, 0x08] = 0x0894 = 2196 → 21.96 °C
fn parse_temperature_celsius(data: &[u8]) -> Option<f32> {
    if data.len() < 2 { return None; }
    let raw = i16::from_le_bytes([data[0], data[1]]);
    Some(raw as f32 / 100.0)
}

// From Svelte: decode a Uint8Array notification value
function parseTemperature(raw: number[]): number | null {
  if (raw.length < 2) return null;
  const view = new DataView(new Uint8Array(raw).buffer);
  return view.getInt16(0, true) / 100.0; // little-endian
}
```

### Multi-byte Encoding/Decoding Pattern

```typescript
// Encoding a value to write (e.g., set target temperature 22.50 °C)
function encodeTemperature(celsius: number): Uint8Array {
  const raw = Math.round(celsius * 100);
  const buf = new ArrayBuffer(2);
  new DataView(buf).setInt16(0, raw, true); // little-endian
  return new Uint8Array(buf);
}

// Writing encoded value
await invoke('ble_write', {
  peripheralId: id,
  charUuid: '12345678-1234-1234-1234-1234567890ac',
  value: Array.from(encodeTemperature(22.5)),
  withResponse: true,
});
```

---

## Section 6 — Error Handling

| Error scenario | Cause | Handling strategy |
|----------------|-------|-------------------|
| `No BLE adapter found` | Bluetooth hardware absent or disabled | Check adapter presence, surface actionable message to user |
| Connection timeout | Device out of range, or too slow to respond | `tokio::time::timeout` with 10–30s limit, retry with backoff |
| `Characteristic not found` | `discover_services()` not called, or wrong UUID | Always call `discover_services()` before accessing characteristics |
| Write failed | Characteristic has no write property, or device busy | Check `characteristic.properties` before writing; retry once |
| Notification stream dropped | Peripheral disconnected mid-stream | `while let Some(n) = stream.next().await` exits cleanly; handle by reconnect |
| `Device not connected` | App state out of sync | Guard all operations with `peripherals.contains_key()` check |
| `BlueZ permission denied` (Linux) | User not in `bluetooth` group | Show OS-specific setup instructions in UI |

```rust
// Guard pattern: check connection state before every operation
#[tauri::command]
pub async fn ble_read_safe(
    peripheral_id: String,
    char_uuid: String,
    state: tauri::State<'_, BleState>,
) -> Result<Vec<u8>, String> {
    let guard = state.lock().await;
    let peripheral = guard.peripherals.get(&peripheral_id)
        .ok_or_else(|| format!("Device {} is not connected", peripheral_id))?;

    if !peripheral.is_connected().await.unwrap_or(false) {
        return Err(format!("Device {} disconnected unexpectedly", peripheral_id));
    }

    // proceed with read...
    drop(guard);
    Ok(vec![])
}
```

---

## Section 7 — Testing BLE Code

### Mock Adapter Pattern for Unit Tests

btleplug's API is trait-based — implement `Peripheral` and `Central` traits for a mock:

```rust
// tests/mock_peripheral.rs
use btleplug::api::{Characteristic, Peripheral as _, Properties, Service};
use btleplug::platform::PeripheralId;
use std::collections::BTreeSet;

// Use btleplug's mock support or build a simple stub
// For unit tests, prefer testing the parsing logic independently:

#[test]
fn test_parse_heart_rate_uint8() {
    let data = vec![0x00, 75]; // flags=0 (uint8 format), HR=75
    assert_eq!(parse_heart_rate(&data), Some(75));
}

#[test]
fn test_parse_heart_rate_uint16() {
    let data = vec![0x01, 0x96, 0x00]; // flags=1 (uint16 format), HR=150
    assert_eq!(parse_heart_rate(&data), Some(150));
}

#[test]
fn test_parse_temperature() {
    let data = vec![0x94, 0x08]; // 0x0894 = 2196 → 21.96 °C
    let temp = parse_temperature_celsius(&data).unwrap();
    assert!((temp - 21.96).abs() < 0.001);
}
```

### Integration Testing Strategies

- **Simulator**: Use nRF Connect (iOS/Android) or LightBlue to simulate a BLE peripheral. Run your app and verify scan/connect/read flow against the simulator.
- **Known hardware**: Test with a cheap development board (nRF52840 DK, ESP32 with BLE) running a known GATT service (e.g., Battery Service). These are deterministic and cheap.
- **CI skipping**: Gate BLE integration tests behind a feature flag or environment variable (`RUN_BLE_TESTS=1`) since CI machines lack Bluetooth adapters. Mark these tests `#[ignore]` unless the flag is set.

```rust
#[test]
#[ignore = "requires real BLE hardware"]
async fn test_connect_and_read_battery() {
    // integration test with real device
}
```

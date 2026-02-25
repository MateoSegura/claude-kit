---
name: frontend-svelte-knowledge:hardware-abstraction
description: "Cross-cutting hardware abstraction patterns for Tauri apps: trait-based device abstraction, wrapping hardware crates in Tauri commands, async device-to-frontend data streaming, IoT protocol patterns (command/response, firmware upload, sensor telemetry), device state machines with exponential backoff reconnection, Svelte 5 device management UI components, error recovery strategies, and cross-platform USB/BLE/Audio/MIDI permission requirements."
user-invocable: true
---

# Hardware Abstraction Quick Reference

Hardware access in Tauri lives entirely in Rust. The frontend calls `invoke()` as with any command — crate and protocol choices are invisible to Svelte. This skill covers the architectural patterns that span USB, BLE, MIDI, and other device types.

## Section 1 — Tauri Hardware Command Architecture

### Trait-Based Device Abstraction

```rust
// src-tauri/src/device.rs
use async_trait::async_trait;

#[async_trait]
pub trait DeviceConnection: Send + Sync {
    async fn connect(&mut self) -> Result<(), DeviceError>;
    async fn disconnect(&mut self) -> Result<(), DeviceError>;
    async fn send(&mut self, data: &[u8]) -> Result<(), DeviceError>;
    async fn receive(&mut self) -> Result<Vec<u8>, DeviceError>;
    fn device_info(&self) -> DeviceInfo;
}

#[derive(Clone, serde::Serialize)]
pub struct DeviceInfo {
    pub id: String,
    pub name: String,
    pub device_type: DeviceType,
    pub firmware_version: Option<String>,
}

#[derive(Clone, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DeviceType { Serial, Ble, Usb, Hid, Midi }
```

### Wrapping Device Handles in Tauri State

Use `Arc<Mutex<Option<T>>>` so commands can hold an open device across calls:

```rust
pub struct DeviceState {
    pub serial: Arc<Mutex<Option<Box<dyn DeviceConnection>>>>,
    pub ble:    Arc<Mutex<Option<Box<dyn DeviceConnection>>>>,
}

#[tauri::command]
pub async fn connect_device(
    device_type: DeviceType,
    path: String,
    state: State<'_, DeviceState>,
) -> Result<DeviceInfo, String> {
    match device_type {
        DeviceType::Serial => {
            let mut guard = state.serial.lock().await;
            let mut device = SerialDevice::new(&path);
            device.connect().await.map_err(|e| e.to_string())?;
            let info = device.device_info();
            *guard = Some(Box::new(device));
            Ok(info)
        }
        DeviceType::Ble => { /* similar pattern */ Err("todo".into()) }
        _ => Err(format!("Unsupported device type")),
    }
}

pub fn run() {
    tauri::Builder::default()
        .manage(DeviceState {
            serial: Arc::new(Mutex::new(None)),
            ble:    Arc::new(Mutex::new(None)),
        })
        .invoke_handler(tauri::generate_handler![connect_device, disconnect_device, send_command])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Type-Safe Error Handling

```rust
// src-tauri/src/error.rs
use thiserror::Error;

#[derive(Error, Debug, serde::Serialize)]
pub enum DeviceError {
    #[error("Device not connected")]         NotConnected,
    #[error("Timeout after {0}ms")]          Timeout(u64),
    #[error("Protocol error: {0}")]          Protocol(String),
    #[error("Device disconnected")]          Disconnected,
    #[error("Permission denied: {0}")]       Permission(String),
    #[error(transparent)] Io(#[from] std::io::Error),
}
```

---

## Section 2 — Async Device Streams

```rust
// Bounded channel — backpressure: drop oldest on overflow
const CHANNEL_CAPACITY: usize = 1000;

pub fn start_device_stream(app: AppHandle, mut device: impl DeviceConnection + 'static) {
    let (tx, mut rx) = mpsc::channel::<Vec<u8>>(CHANNEL_CAPACITY);

    // Reader task: device → channel
    tauri::async_runtime::spawn(async move {
        loop {
            match device.receive().await {
                Ok(data) => { let _ = tx.try_send(data); } // drop if full
                Err(e)   => { app.emit("device-error", e.to_string()).ok(); break; }
            }
        }
    });

    // Emitter task: batch samples, emit at ~30fps (don't flood frontend)
    let app2 = app.clone();
    tauri::async_runtime::spawn(async move {
        let mut batch: Vec<Vec<u8>> = Vec::new();
        let mut interval = tokio::time::interval(Duration::from_millis(33));
        loop {
            tokio::select! {
                _ = interval.tick() => {
                    if !batch.is_empty() {
                        app2.emit("device-data", &batch).ok();
                        batch.clear();
                    }
                }
                data = rx.recv() => match data {
                    Some(d) => batch.push(d),
                    None    => break,
                }
            }
        }
    });
}
```

Svelte consumer keeps a ring buffer and auto-scrolls:

```svelte
<script>
  let samples = $state([]);
  const unlisten = listen('device-data', (event) => {
    samples = [...samples.slice(-500), ...event.payload]; // keep last 500
  });
  onDestroy(async () => { (await unlisten)(); });
</script>
```

---

## Section 3 — IoT Protocol Patterns

### Command/Response over Serial (Framed Protocol)

```
Frame: STX (0x02) + length (u16 BE) + payload + checksum (XOR) + ETX (0x03)
On NAK: retry up to N times. On timeout: return Err(DeviceError::Timeout).
```

```rust
const STX: u8 = 0x02; const ETX: u8 = 0x03; const NAK: u8 = 0x15; const ACK: u8 = 0x06;

fn build_frame(payload: &[u8]) -> Vec<u8> {
    let checksum = payload.iter().fold(0u8, |acc, &b| acc ^ b);
    let mut frame = vec![STX];
    frame.extend_from_slice(&(payload.len() as u16).to_be_bytes());
    frame.extend_from_slice(payload);
    frame.push(checksum);
    frame.push(ETX);
    frame
}
```

### Firmware Upload with Progress Events

```rust
#[tauri::command]
pub async fn upload_firmware(
    firmware_path: String, app: AppHandle, state: State<'_, DeviceState>,
) -> Result<(), String> {
    let firmware = std::fs::read(&firmware_path).map_err(|e| e.to_string())?;
    let total_chunks = (firmware.len() + 255) / 256;
    let mut guard = state.serial.lock().await;
    let device = guard.as_mut().ok_or("Device not connected")?;

    for (i, chunk) in firmware.chunks(256).enumerate() {
        let mut payload = vec![0x10u8]; // CMD_CHUNK
        payload.extend_from_slice(&(i as u32).to_be_bytes());
        payload.push(chunk.len() as u8);
        payload.extend_from_slice(chunk);

        device.send(&payload).await.map_err(|e| e.to_string())?;
        let resp = device.receive().await.map_err(|e| e.to_string())?;
        if resp.first() != Some(&ACK) { return Err(format!("NAK on chunk {}", i)); }

        app.emit("firmware-progress", serde_json::json!({
            "chunk": i + 1, "total": total_chunks,
            "percent": ((i + 1) * 100) / total_chunks,
        })).ok();
    }
    Ok(())
}
```

### Sensor Telemetry (Polling with Threshold)

```rust
tauri::async_runtime::spawn(async move {
    let mut ticker = tokio::time::interval(Duration::from_millis(poll_ms));
    let mut last_value: Option<f32> = None;
    loop {
        ticker.tick().await;
        let mut guard = device_arc.lock().await;
        if let Some(device) = guard.as_mut() {
            if let Ok(data) = device.receive().await {
                let value = parse_sensor_value(&data);
                let changed = last_value.map_or(true, |lv| (value - lv).abs() > threshold);
                if changed {
                    app.emit("sensor-reading", serde_json::json!({
                        "timestamp": unix_ms(), "value": value,
                    })).ok();
                    last_value = Some(value);
                }
            }
        }
    }
});
```

---

## Section 4 — Device State Machine

```rust
#[derive(Clone, Debug, serde::Serialize)]
#[serde(tag = "status", content = "data")]
pub enum ConnectionState {
    Disconnected,
    Connecting,
    Connected(DeviceInfo),
    Reconnecting { attempt: u32 },
    Error(String),
}

impl DeviceStateMachine {
    fn transition(&mut self, new_state: ConnectionState) {
        self.state = new_state.clone();
        self.app.emit("device-state", &new_state).ok(); // always notify frontend
    }

    pub async fn reconnect_with_backoff(
        &mut self, device: &mut impl DeviceConnection, max_attempts: u32,
    ) -> Result<(), DeviceError> {
        for attempt in 1..=max_attempts {
            self.transition(ConnectionState::Reconnecting { attempt });
            let delay = (1u64 << (attempt - 1)).min(30); // 1s, 2s, 4s, 8s… max 30s
            tokio::time::sleep(Duration::from_secs(delay)).await;

            match device.connect().await {
                Ok(()) => {
                    self.transition(ConnectionState::Connected(device.device_info()));
                    return Ok(());
                }
                Err(_) if attempt < max_attempts => continue,
                Err(e) => {
                    self.transition(ConnectionState::Error(
                        format!("Failed after {} attempts: {}", max_attempts, e)
                    ));
                    return Err(DeviceError::Protocol(e.to_string()));
                }
            }
        }
        unreachable!()
    }
}
```

---

## Section 5 — Svelte Device Management UI

### DeviceConnectionStatus Component

```svelte
<script>
  let connectionState = $state({ status: 'Disconnected' });
  listen('device-state', (e) => { connectionState = e.payload; });

  let indicatorColor = $derived(() => ({
    Connected:    'bg-green-500',
    Connecting:   'bg-yellow-400 animate-pulse',
    Reconnecting: 'bg-orange-400 animate-pulse',
    Error:        'bg-red-500',
  }[connectionState.status] ?? 'bg-gray-400'));

  let statusLabel = $derived(() =>
    connectionState.status === 'Reconnecting'
      ? `Reconnecting (attempt ${connectionState.data?.attempt})`
      : connectionState.status === 'Connected'
        ? `Connected: ${connectionState.data?.name}`
        : connectionState.status
  );
</script>
<div class="flex items-center gap-2">
  <span class="w-3 h-3 rounded-full {indicatorColor()}"></span>
  <span class="text-sm">{statusLabel()}</span>
</div>
```

### DeviceDashboard Layout (Sidebar + Main Panel)

```svelte
<!-- Sidebar: scan → device list → connect. Main panel: DataStream -->
<div class="flex h-screen">
  <aside class="w-64 border-r flex flex-col">
    <div class="p-3 border-b">
      <DeviceConnectionStatus />
      <button onclick={() => invoke('scan_devices').then(r => devices = r)} class="mt-2 w-full">
        Scan Devices
      </button>
    </div>
    <ul class="flex-1 overflow-y-auto">
      {#each devices as device}
        <li class="p-3 cursor-pointer hover:bg-gray-100"
            onclick={() => invoke('connect_device', { deviceType: device.type, path: device.id })}>
          <div class="font-medium">{device.name}</div>
          <div class="text-xs text-gray-500">{device.type}</div>
        </li>
      {/each}
    </ul>
  </aside>
  <main class="flex-1">
    <DataStream />   <!-- real-time data, auto-scroll, pause button -->
  </main>
</div>
```

---

## Section 6 — Error Recovery Patterns

### Disconnect Detection

```rust
fn is_disconnect_error(e: &std::io::Error) -> bool {
    matches!(e.kind(),
        ErrorKind::BrokenPipe | ErrorKind::ConnectionReset
        | ErrorKind::ConnectionAborted | ErrorKind::UnexpectedEof
    )
}
```

### Svelte Stale Data Indicator

```svelte
<script>
  let lastReading = $state(null);
  let isStale = $state(false);
  let staleTimer;

  listen('sensor-reading', (e) => {
    lastReading = e.payload;
    isStale = false;
    clearTimeout(staleTimer);
    staleTimer = setTimeout(() => { isStale = true; }, 5000); // stale after 5s
  });
  listen('device-disconnected', () => { isStale = true; });
</script>

{#if lastReading}
  <div class:opacity-50={isStale}>
    {#if isStale}<span class="text-yellow-600">[stale] </span>{/if}
    Value: {lastReading.value}
  </div>
{/if}
```

---

## Section 7 — Cross-Platform Permission Matrix

| Hardware Type | Linux | macOS | Windows |
|--------------|-------|-------|---------|
| **USB Serial** | udev rule + `dialout` group | No entitlement (driver auto-installs for FTDI/CH340/CP210x) | Manufacturer driver (Win10+ auto-installs common chips) |
| **USB Raw (nusb/rusb)** | udev rule `MODE="0666"` | No entitlement for direct distribution | WinUSB driver via Zadig |
| **BLE** | `bluetooth` group; BlueZ required | `NSBluetoothAlwaysUsageDescription` in Info.plist | `bluetooth` device capability in app manifest; Win10 1703+ |
| **Audio Input** | PulseAudio/PipeWire (user by default) | `NSMicrophoneUsageDescription` in Info.plist | App manifest `microphone` device capability |
| **Audio Output** | PulseAudio/PipeWire (user by default) | No entitlement | No special entry |
| **MIDI** | `audio` group; `alsa-seq` module | CoreMIDI — no entitlement | No special entry |
| **Network Listen** | `CAP_NET_BIND_SERVICE` for ports <1024 | App Sandbox: `com.apple.security.network.server` | No special entry |
| **Network Connect** | No setup needed | App Sandbox: `com.apple.security.network.client` | No special entry |

```bash
# Linux: USB serial
sudo usermod -aG dialout $USER
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", MODE="0666", GROUP="dialout"' \
  | sudo tee /etc/udev/rules.d/99-device.rules
sudo udevadm control --reload-rules && sudo udevadm trigger

# Linux: BLE
sudo usermod -aG bluetooth $USER  # then log out/in
```

```xml
<!-- macOS: src-tauri/Info.plist — add for BLE or Audio Input -->
<key>NSBluetoothAlwaysUsageDescription</key>
<string>This app uses Bluetooth to communicate with nearby devices.</string>
<key>NSMicrophoneUsageDescription</key>
<string>This app uses the microphone for audio device input.</string>
```

```xml
<!-- Windows: src-tauri/src/main.manifest -->
<Package><Capabilities>
  <DeviceCapability Name="bluetooth" />
  <DeviceCapability Name="microphone" />
</Capabilities></Package>
```

---

## Additional Resources

- [hardware-patterns-reference.md](hardware-patterns-reference.md) — Complete implementations: full DeviceConnection trait for serial and BLE, complete streaming pipeline, full firmware upload flow with Svelte progress component, sensor dashboard with Canvas 2D chart, device discovery page, full cross-platform permission setup scripts, CI/CD configuration, and anti-patterns catalog

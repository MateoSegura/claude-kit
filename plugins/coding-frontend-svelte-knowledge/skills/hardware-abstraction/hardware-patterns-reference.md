# Hardware Abstraction — Complete Patterns Reference

Companion to `SKILL.md`. Each section provides complete, copy-paste-ready implementations.

---

## Section 1 — Complete DeviceConnection Trait Implementations

### Cargo.toml

```toml
[dependencies]
async-trait    = "0.1"
serialport     = "4"
tokio-serial   = "5"
btleplug       = "0.11"
tokio          = { version = "1", features = ["full"] }
thiserror      = "1"
serde          = { version = "1", features = ["derive"] }
serde_json     = "1"
uuid           = { version = "1", features = ["v4"] }
crc32fast      = "1"
```

### SerialDevice Implementation

```rust
// src-tauri/src/serial_device.rs
pub struct SerialDevice {
    path: String, baud_rate: u32,
    port: Mutex<Option<Box<dyn serialport::SerialPort + Send>>>,
}

#[async_trait]
impl DeviceConnection for SerialDevice {
    async fn connect(&mut self) -> Result<(), DeviceError> {
        let port = serialport::new(&self.path, self.baud_rate)
            .timeout(Duration::from_millis(500)).open()
            .map_err(|e| DeviceError::Protocol(e.to_string()))?;
        *self.port.lock().unwrap() = Some(port);
        Ok(())
    }

    async fn disconnect(&mut self) -> Result<(), DeviceError> {
        *self.port.lock().unwrap() = None; // drop closes port
        Ok(())
    }

    async fn send(&mut self, data: &[u8]) -> Result<(), DeviceError> {
        use std::io::Write;
        let mut g = self.port.lock().unwrap();
        let port = g.as_mut().ok_or(DeviceError::NotConnected)?;
        port.write_all(data).map_err(|e| if is_disconnect_io(&e) { DeviceError::Disconnected } else { DeviceError::Io(e) })
    }

    async fn receive(&mut self) -> Result<Vec<u8>, DeviceError> {
        use std::io::Read;
        let mut g = self.port.lock().unwrap();
        let port = g.as_mut().ok_or(DeviceError::NotConnected)?;
        let mut buf = vec![0u8; 256];
        match port.read(&mut buf) {
            Ok(n) => { buf.truncate(n); Ok(buf) }
            Err(e) if e.kind() == std::io::ErrorKind::TimedOut => Ok(vec![]),
            Err(e) if is_disconnect_io(&e) => Err(DeviceError::Disconnected),
            Err(e) => Err(DeviceError::Io(e)),
        }
    }

    fn device_info(&self) -> DeviceInfo {
        DeviceInfo { id: self.path.clone(), name: format!("Serial({})", self.path),
            device_type: DeviceType::Serial, firmware_version: None }
    }
}

fn is_disconnect_io(e: &std::io::Error) -> bool {
    use std::io::ErrorKind::*;
    matches!(e.kind(), BrokenPipe | ConnectionReset | ConnectionAborted | UnexpectedEof)
}
```

### Enum Dispatch in Tauri Commands

```rust
#[tauri::command]
pub async fn send_command(device_type: DeviceType, payload: Vec<u8>,
    state: State<'_, DeviceState>) -> Result<Vec<u8>, String> {
    let guard_result = match device_type {
        DeviceType::Serial => { let mut g = state.serial.lock().await;
            let d = g.as_mut().ok_or("Not connected")?;
            d.send(&payload).await.map_err(|e| e.to_string())?;
            d.receive().await.map_err(|e| e.to_string()) }
        DeviceType::Ble => { let mut g = state.ble.lock().await;
            let d = g.as_mut().ok_or("Not connected")?;
            d.send(&payload).await.map_err(|e| e.to_string())?;
            d.receive().await.map_err(|e| e.to_string()) }
        _ => Err("Unsupported".into()),
    };
    guard_result
}
```

---

## Section 2 — Complete Async Streaming Pipeline

```
device reader task → tokio::mpsc::channel(1000) → emitter task (30fps batch) → Svelte $state
```

```rust
// src-tauri/src/streaming.rs
pub struct StreamHandle { pub stop_tx: tokio::sync::oneshot::Sender<()> }

pub fn start_streaming(app: AppHandle, mut device: impl DeviceConnection + 'static) -> StreamHandle {
    let (data_tx, mut data_rx) = mpsc::channel::<Vec<u8>>(1000);
    let (stop_tx, mut stop_rx) = tokio::sync::oneshot::channel::<()>();

    // Task 1: device → channel (bounded, try_send drops on backpressure)
    let app1 = app.clone();
    tauri::async_runtime::spawn(async move {
        loop {
            tokio::select! {
                _ = &mut stop_rx => break,
                result = device.receive() => match result {
                    Ok(data) if !data.is_empty() => { let _ = data_tx.try_send(data); }
                    Ok(_) => {}
                    Err(DeviceError::Disconnected) => { app1.emit("device-disconnected", ()).ok(); break; }
                    Err(e) => { app1.emit("device-error", e.to_string()).ok(); break; }
                }
            }
        }
    });

    // Task 2: batch + emit at ~30fps
    tauri::async_runtime::spawn(async move {
        let mut batch: Vec<serde_json::Value> = Vec::new();
        let mut ticker = tokio::time::interval(Duration::from_millis(33));
        loop {
            tokio::select! {
                _ = ticker.tick() => {
                    if !batch.is_empty() { app.emit("device-data", &batch).ok(); batch.clear(); }
                }
                data = data_rx.recv() => match data {
                    Some(bytes) => batch.push(serde_json::json!({ "raw": bytes })),
                    None => break,
                }
            }
        }
    });

    StreamHandle { stop_tx }
}
```

```svelte
<script>
  let samples = $state([]);
  let streaming = $state(false);
  let unlisten;

  async function startStream() {
    unlisten = await listen('device-data', (e) => {
      samples = [...samples.slice(-1000), ...e.payload]; // ring buffer
    });
    await invoke('start_stream');
    streaming = true;
  }

  async function stopStream() {
    await invoke('stop_stream'); streaming = false;
    if (unlisten) unlisten();
  }
  onDestroy(() => { if (unlisten) unlisten(); });
</script>
<button onclick={streaming ? stopStream : startStream}>{streaming ? 'Stop' : 'Start'} Stream</button>
<p>{samples.length} samples</p>
```

---

## Section 3 — Complete Firmware Upload Flow

```rust
// Rust: chunked upload (256B/chunk), ACK per chunk, retry on NAK, CRC32 final verify
#[tauri::command]
pub async fn upload_firmware(firmware_path: String, app: AppHandle,
    state: State<'_, DeviceState>) -> Result<(), String> {
    const CHUNK_SIZE: usize = 256;
    let firmware = tokio::fs::read(&firmware_path).await.map_err(|e| e.to_string())?;
    let total_chunks = (firmware.len() + CHUNK_SIZE - 1) / CHUNK_SIZE;
    let mut crc = crc32fast::Hasher::new();
    let mut guard = state.serial.lock().await;
    let device = guard.as_mut().ok_or("Device not connected")?;

    device.send(&[0x01, 0x00]).await.map_err(|e| e.to_string())?; // CMD_START
    let _ = device.receive().await.map_err(|e| e.to_string())?;   // wait ACK

    for (i, chunk) in firmware.chunks(CHUNK_SIZE).enumerate() {
        crc.update(chunk);
        let mut payload = vec![0x10u8]; // CMD_CHUNK
        payload.extend_from_slice(&(i as u32).to_be_bytes());
        payload.push(chunk.len() as u8);
        payload.extend_from_slice(chunk);

        for attempt in 0..3u8 {
            device.send(&payload).await.map_err(|e| e.to_string())?;
            let resp = device.receive().await.map_err(|e| e.to_string())?;
            if resp.first() == Some(&0x06u8) { break; }           // ACK
            if attempt == 2 { return Err(format!("NAK chunk {}", i)); }
        }

        app.emit("firmware-progress", serde_json::json!({
            "chunk": i+1, "total": total_chunks,
            "percent": ((i+1)*100)/total_chunks,
        })).map_err(|e| e.to_string())?;
    }

    // Final CRC32 verification
    let mut verify = vec![0x11u8]; // CMD_VERIFY
    verify.extend_from_slice(&crc.finalize().to_be_bytes());
    device.send(&verify).await.map_err(|e| e.to_string())?;
    let resp = device.receive().await.map_err(|e| e.to_string())?;
    if resp.first() != Some(&0x06u8) { return Err("CRC verification failed".into()); }
    app.emit("firmware-complete", ()).ok();
    Ok(())
}
```

```svelte
<!-- FirmwareUpload.svelte — progress bar, ETA, cancel -->
<script>
  import { invoke } from '@tauri-apps/api/core';
  import { listen } from '@tauri-apps/api/event';
  import { open } from '@tauri-apps/plugin-dialog';

  let progress = $state(null); // { chunk, total, percent }
  let uploading = $state(false);
  let startTime = 0;

  let etaSeconds = $derived(() => {
    if (!progress || progress.percent <= 0) return null;
    const rate = progress.percent / ((Date.now() - startTime) / 1000);
    return rate > 0 ? Math.round((100 - progress.percent) / rate) : null;
  });

  async function pickAndUpload() {
    const path = await open({ filters: [{ name: 'Firmware', extensions: ['bin', 'hex'] }] });
    if (!path) return;
    uploading = true; startTime = Date.now();
    await listen('firmware-progress', (e) => { progress = e.payload; });
    await listen('firmware-complete', () => { uploading = false; });
    try {
      await invoke('upload_firmware', { firmwarePath: path });
    } catch (e) { alert(`Upload failed: ${e}`); uploading = false; }
  }
</script>

{#if uploading && progress}
  <div class="space-y-2">
    <progress value={progress.percent} max={100} class="w-full"></progress>
    <div class="flex justify-between text-sm">
      <span>{progress.percent}% — chunk {progress.chunk}/{progress.total}</span>
      {#if etaSeconds()}<span>~{etaSeconds()}s remaining</span>{/if}
    </div>
    <button onclick={() => invoke('cancel_firmware_upload').then(() => { uploading = false; })}>Cancel</button>
  </div>
{:else}
  <button onclick={pickAndUpload} disabled={uploading}>Upload Firmware</button>
{/if}
```

---

## Section 4 — Complete Sensor Dashboard

```rust
// Rust: ring buffer for sensor readings, configurable polling, CSV export
const RING_BUFFER_SIZE: usize = 6000; // 5 min at 20Hz

pub struct SensorState { pub readings: Arc<Mutex<VecDeque<SensorReading>>> }

#[derive(serde::Serialize, Clone)]
pub struct SensorReading { pub timestamp: u64, pub temperature: f32, pub humidity: f32, pub pressure: f32 }

#[tauri::command]
pub async fn start_sensor(interval_ms: u64, app: AppHandle,
    sensor_state: State<'_, SensorState>, device_state: State<'_, DeviceState>,
) -> Result<(), String> {
    let (readings_arc, device_arc) = (sensor_state.readings.clone(), device_state.serial.clone());
    tauri::async_runtime::spawn(async move {
        let mut ticker = tokio::time::interval(Duration::from_millis(interval_ms));
        loop {
            ticker.tick().await;
            let mut guard = device_arc.lock().await;
            if let Some(device) = guard.as_mut() {
                if let Ok(data) = device.receive().await {
                    let reading = parse_sensor_packet(&data);
                    let mut buf = readings_arc.lock().await;
                    if buf.len() >= RING_BUFFER_SIZE { buf.pop_front(); }
                    buf.push_back(reading.clone());
                    app.emit("sensor-reading", &reading).ok();
                }
            }
        }
    });
    Ok(())
}

#[tauri::command]
pub async fn export_sensor_csv(sensor_state: State<'_, SensorState>) -> Result<String, String> {
    let buf = sensor_state.readings.lock().await;
    let mut csv = "timestamp,temperature,humidity,pressure\n".to_string();
    for r in buf.iter() {
        csv.push_str(&format!("{},{:.2},{:.2},{:.2}\n", r.timestamp, r.temperature, r.humidity, r.pressure));
    }
    Ok(csv)
}
```

```svelte
<!-- SensorDashboard.svelte — Canvas 2D line chart, auto-scaling Y axis, 5-min time window -->
<script>
  const WINDOW_MS = 5 * 60 * 1000;
  let readings = $state([]);
  let canvas;

  listen('sensor-reading', (e) => {
    readings = [...readings.filter(r => r.timestamp > Date.now() - WINDOW_MS), e.payload];
    if (canvas && readings.length >= 2) {
      const ctx = canvas.getContext('2d'), { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);
      const temps = readings.map(r => r.temperature);
      const minT = Math.min(...temps), range = (Math.max(...temps) - minT) || 1;
      const oldest = readings[0].timestamp, xSpan = (readings.at(-1).timestamp - oldest) || 1;
      ctx.strokeStyle = '#3b82f6'; ctx.lineWidth = 1.5; ctx.beginPath();
      readings.forEach((r, i) => {
        const x = ((r.timestamp - oldest) / xSpan) * width;
        const y = height - ((r.temperature - minT) / range) * (height - 20) - 10;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.stroke();
    }
  });

  async function exportCsv() {
    const csv = await invoke('export_sensor_csv');
    const path = await save({ filters: [{ name: 'CSV', extensions: ['csv'] }] });
    if (path) await writeTextFile(path, csv);
  }
</script>
<div class="flex flex-col h-full p-4 gap-4">
  <div class="flex justify-between">
    <h2 class="font-semibold">Sensor (last 5 min)</h2>
    <button onclick={exportCsv}>Export CSV</button>
  </div>
  <canvas bind:this={canvas} width={800} height={300} class="border rounded"></canvas>
  {#if readings.length}
    {@const last = readings.at(-1)}
    <div class="grid grid-cols-3 gap-4 text-center">
      <div>{last.temperature.toFixed(1)}°C</div>
      <div>{last.humidity.toFixed(1)}%</div>
      <div>{last.pressure.toFixed(0)} hPa</div>
    </div>
  {/if}
</div>
```

---

## Section 5 — Device Discovery and Management Page

Discovery page pattern: scan → deduplicated device cards with RSSI bars → connect → detail panel → recent devices (Tauri store plugin).

```svelte
<script>
  import { invoke } from '@tauri-apps/api/core';
  import { listen } from '@tauri-apps/api/event';
  import { load } from '@tauri-apps/plugin-store';
  import { onMount } from 'svelte';

  let discovered = $state([]), connected = $state(null), recentDevices = $state([]), scanning = $state(false);

  onMount(async () => {
    recentDevices = (await (await load('device-store.json')).get('recent')) ?? [];
    await listen('ble-device-discovered', (e) => {
      if (!discovered.find(d => d.id === e.payload.id)) discovered = [...discovered, e.payload];
    });
  });

  async function scan() {
    discovered = []; scanning = true;
    await invoke('start_scan');
    setTimeout(async () => { await invoke('stop_scan'); scanning = false; }, 10_000);
  }

  async function connectDevice(device) {
    await invoke('connect_device', { deviceType: device.type, path: device.id });
    connected = device;
    const store = await load('device-store.json');
    const recent = [device, ...recentDevices.filter(d => d.id !== device.id)].slice(0, 5);
    await store.set('recent', recent); await store.save();
    recentDevices = recent;
  }

  const rssiToPercent = (r) => Math.max(0, Math.min(100, ((r + 100) / 60) * 100));
</script>

<div class="p-4 space-y-4">
  <button onclick={scan} disabled={scanning}>{scanning ? 'Scanning…' : 'Scan'}</button>
  <div class="grid grid-cols-2 gap-3">
    {#each discovered as d}
      <div class="border rounded p-3 flex justify-between items-center">
        <div>
          <div class="font-medium">{d.name || 'Unknown'}</div>
          {#if d.rssi}
            <!-- 4-bar RSSI indicator -->
            <div class="flex gap-0.5 mt-1">
              {#each [25,50,75,100] as t}
                <div class="w-1 rounded" class:bg-blue-500={rssiToPercent(d.rssi)>=t}
                     class:bg-gray-300={rssiToPercent(d.rssi)<t} style="height:{t*.1+4}px"></div>
              {/each}
            </div>
          {/if}
        </div>
        <button onclick={() => connectDevice(d)}>Connect</button>
      </div>
    {/each}
  </div>
  {#if connected}
    <div class="border rounded p-4">
      <div class="flex justify-between">
        <span>{connected.name}</span>
        <button onclick={() => invoke('disconnect_device',{deviceType:connected.type}).then(()=>connected=null)}>Disconnect</button>
      </div>
    </div>
  {/if}
  {#if recentDevices.length}
    <div><h3 class="font-medium mb-1">Recent</h3>
      {#each recentDevices as d}
        <div class="flex justify-between text-sm">
          <span>{d.name} ({d.type})</span>
          <button onclick={() => connectDevice(d)} class="text-blue-500">Reconnect</button>
        </div>
      {/each}
    </div>
  {/if}
</div>
```

---

## Section 6 — Complete Cross-Platform Permission Setup

### Linux: udev Rules + Install Script

```bash
# /etc/udev/rules.d/99-myapp.rules
SUBSYSTEM=="tty",    ATTRS{idVendor}=="10c4", MODE="0666", GROUP="dialout", TAG+="uaccess"  # CP210x
SUBSYSTEM=="tty",    ATTRS{idVendor}=="0403", MODE="0666", GROUP="dialout", TAG+="uaccess"  # FTDI
SUBSYSTEM=="tty",    ATTRS{idVendor}=="1a86", MODE="0666", GROUP="dialout", TAG+="uaccess"  # CH340
SUBSYSTEM=="usb",    ATTRS{idVendor}=="1234", ATTRS{idProduct}=="5678", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1234", MODE="0666", GROUP="plugdev"
```

```bash
#!/usr/bin/env bash
# install-permissions.sh
set -e
sudo cp 99-myapp.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
sudo usermod -aG dialout "$USER"   # serial
sudo usermod -aG plugdev "$USER"   # USB raw + HID
sudo usermod -aG bluetooth "$USER" # BLE
sudo usermod -aG audio "$USER"     # MIDI/audio
echo "Log out and back in for group changes to take effect."
```

### macOS: Info.plist Usage Descriptions

```xml
<!-- src-tauri/Info.plist — add entries for each permission you need -->
<plist version="1.0"><dict>
  <key>NSBluetoothAlwaysUsageDescription</key>
  <string>This app uses Bluetooth to communicate with nearby hardware devices.</string>
  <key>NSMicrophoneUsageDescription</key>
  <string>This app uses the microphone for audio device input.</string>
  <key>NSLocalNetworkUsageDescription</key>
  <string>This app uses local networking to discover devices on your network.</string>
</dict></plist>
```

For App Sandbox builds add entitlements (`com.apple.security.device.bluetooth`, `com.apple.security.device.audio-input`, `com.apple.security.network.client`).

### Windows: App Manifest

```xml
<!-- src-tauri/src/main.manifest -->
<Package><Capabilities>
  <DeviceCapability Name="bluetooth" />
  <DeviceCapability Name="microphone" />
</Capabilities></Package>
```

### CI/CD

```yaml
# GitHub Actions: Linux build requires system libraries for BLE and USB
- name: Install Linux deps
  if: runner.os == 'Linux'
  run: |
    sudo apt-get update && sudo apt-get install -y \
      libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev \
      libdbus-1-dev libssl-dev pkg-config libudev-dev bluez
    # libudev-dev: needed by serialport and nusb
    # bluez: BlueZ headers needed by btleplug
# macOS: code signing secrets passed to tauri-action (APPLE_CERTIFICATE, APPLE_SIGNING_IDENTITY, etc.)
# Windows: add DeviceCapabilities to the manifest before building
```

---

## Section 7 — Anti-Patterns

**1. Blocking the async runtime with sync hardware calls**

```rust
// WRONG — blocking_lock + sync I/O blocks Tauri's runtime thread
fn read_sensor(state: State<DeviceState>) -> Vec<u8> { state.serial.blocking_lock()... }

// RIGHT — async throughout
async fn read_sensor(state: State<'_, DeviceState>) -> Result<Vec<u8>, String> {
    state.serial.lock().await.as_mut().ok_or("Not connected")?.receive().await.map_err(|e| e.to_string())
}
```

**2. Not cleaning up on app exit** — use `on_window_event` to drop device handles:

```rust
.on_window_event(|window, event| {
    if let tauri::WindowEvent::Destroyed = event {
        let state = window.app_handle().state::<DeviceState>();
        tauri::async_runtime::block_on(async {
            *state.serial.lock().await = None;   // drops port handle
            *state.ble.lock().await = None;
        });
    }
})
```

**3. Flooding frontend with unthrottled events** — always batch at 30fps (see Section 2). Never emit on every byte.

**4. Storing device handles in `lazy_static`** — use `tauri::Builder::manage()` instead. `lazy_static` bypasses Tauri's lifecycle and ownership model.

**5. Ignoring platform permissions in production** — test with a non-developer user account. The app works in dev (developer has full system access) but fails packaged (missing `dialout` group, BLE permission denied). Add udev rules to your installer.

**6. Using `unwrap()` on hardware operations** — hardware disconnects are normal events, not bugs. Always use `?` / `map_err` and propagate errors to the frontend:

```rust
// WRONG — panics when device disconnects mid-session
let data = device.receive().await.unwrap();

// RIGHT
let data = device.receive().await.map_err(|e| e.to_string())?;
```

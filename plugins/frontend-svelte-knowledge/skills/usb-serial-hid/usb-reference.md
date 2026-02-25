# USB / Serial / HID — Complete Code Reference

Detailed examples and patterns for USB communication from Tauri Rust backends. All examples assume Tauri 2 with Svelte 5 frontend.

---

## Section 1 — Complete Serial Port Example

### Cargo.toml

```toml
[dependencies]
serialport = "4"
serde = { version = "1", features = ["derive"] }
tauri = { version = "2", features = [] }
```

### Port Config Struct

```rust
// src-tauri/src/serial.rs
use serde::{Deserialize, Serialize};
use serialport::SerialPort;
use std::sync::Mutex;
use std::time::Duration;

#[derive(Debug, Deserialize)]
pub struct PortConfig {
    pub path: String,
    pub baud_rate: u32,
    pub data_bits: u8,   // 5, 6, 7, 8
    pub parity: String,  // "none", "odd", "even"
    pub stop_bits: u8,   // 1, 2
    pub timeout_ms: u64,
}

pub struct SerialState(pub Mutex<Option<Box<dyn SerialPort + Send>>>);
```

### Rust Commands with Full Error Handling

```rust
// src-tauri/src/serial.rs (continued)
use tauri::State;

#[tauri::command]
pub fn serial_open(state: State<SerialState>, config: PortConfig) -> Result<(), String> {
    let data_bits = match config.data_bits {
        5 => serialport::DataBits::Five,
        6 => serialport::DataBits::Six,
        7 => serialport::DataBits::Seven,
        _ => serialport::DataBits::Eight,
    };
    let parity = match config.parity.as_str() {
        "odd" => serialport::Parity::Odd,
        "even" => serialport::Parity::Even,
        _ => serialport::Parity::None,
    };
    let stop_bits = match config.stop_bits {
        2 => serialport::StopBits::Two,
        _ => serialport::StopBits::One,
    };

    let port = serialport::new(&config.path, config.baud_rate)
        .data_bits(data_bits)
        .parity(parity)
        .stop_bits(stop_bits)
        .flow_control(serialport::FlowControl::None)
        .timeout(Duration::from_millis(config.timeout_ms))
        .open()
        .map_err(|e| match e.kind() {
            serialport::ErrorKind::NoDevice => format!("Port {} not found", config.path),
            serialport::ErrorKind::PermissionDenied => {
                format!("Permission denied on {}. On Linux, add udev rule or join 'dialout' group", config.path)
            }
            _ => e.to_string(),
        })?;

    let mut guard = state.0.lock().unwrap();
    *guard = Some(port);
    Ok(())
}

#[tauri::command]
pub fn serial_write(state: State<SerialState>, data: Vec<u8>) -> Result<usize, String> {
    use std::io::Write;
    let mut guard = state.0.lock().unwrap();
    let port = guard.as_mut().ok_or("Serial port not connected")?;
    port.write(&data).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn serial_read(state: State<SerialState>, max_bytes: usize) -> Result<Vec<u8>, String> {
    use std::io::Read;
    let mut guard = state.0.lock().unwrap();
    let port = guard.as_mut().ok_or("Serial port not connected")?;
    let mut buf = vec![0u8; max_bytes];
    match port.read(&mut buf) {
        Ok(n) => { buf.truncate(n); Ok(buf) }
        Err(e) if e.kind() == std::io::ErrorKind::TimedOut => Ok(vec![]), // timeout = no data
        Err(e) => Err(e.to_string()),
    }
}

#[tauri::command]
pub fn serial_close(state: State<SerialState>) {
    let mut guard = state.0.lock().unwrap();
    *guard = None;
}

#[tauri::command]
pub fn serial_list_ports() -> Result<Vec<String>, String> {
    serialport::available_ports()
        .map_err(|e| e.to_string())
        .map(|ports| ports.into_iter().map(|p| p.port_name).collect())
}
```

### Register in lib.rs

```rust
// src-tauri/src/lib.rs
mod serial;
use serial::SerialState;
use std::sync::Mutex;

pub fn run() {
    tauri::Builder::default()
        .manage(SerialState(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![
            serial::serial_open,
            serial::serial_write,
            serial::serial_read,
            serial::serial_close,
            serial::serial_list_ports,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Svelte Component

```svelte
<!-- src/lib/SerialTerminal.svelte -->
<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';

  let ports = $state<string[]>([]);
  let selectedPort = $state('');
  let connected = $state(false);
  let log = $state<string[]>([]);
  let inputText = $state('');

  async function refreshPorts() {
    ports = await invoke<string[]>('serial_list_ports');
  }

  async function connect() {
    try {
      await invoke('serial_open', {
        config: {
          path: selectedPort,
          baudRate: 115200,
          dataBits: 8,
          parity: 'none',
          stopBits: 1,
          timeoutMs: 500,
        }
      });
      connected = true;
      log = [...log, `Connected to ${selectedPort}`];
    } catch (err) {
      log = [...log, `Error: ${err}`];
    }
  }

  async function disconnect() {
    await invoke('serial_close');
    connected = false;
    log = [...log, 'Disconnected'];
  }

  async function send() {
    const bytes = new TextEncoder().encode(inputText + '\n');
    await invoke('serial_write', { data: Array.from(bytes) });
    log = [...log, `> ${inputText}`];
    inputText = '';
  }

  async function poll() {
    if (!connected) return;
    const data = await invoke<number[]>('serial_read', { maxBytes: 256 });
    if (data.length > 0) {
      const text = new TextDecoder().decode(new Uint8Array(data));
      log = [...log, `< ${text.trim()}`];
    }
  }

  $effect(() => {
    refreshPorts();
    const id = setInterval(poll, 100);
    return () => clearInterval(id);
  });
</script>

<select bind:value={selectedPort}>
  {#each ports as port}
    <option value={port}>{port}</option>
  {/each}
</select>

{#if connected}
  <button onclick={disconnect}>Disconnect</button>
  <input bind:value={inputText} onkeydown={(e) => e.key === 'Enter' && send()} />
  <button onclick={send}>Send</button>
{:else}
  <button onclick={connect} disabled={!selectedPort}>Connect</button>
{/if}

<div class="log">
  {#each log as line}
    <div>{line}</div>
  {/each}
</div>
```

---

## Section 2 — Complete nusb Example

### Cargo.toml

```toml
[dependencies]
nusb = "0.1"
futures-lite = "2"
serde = { version = "1", features = ["derive"] }
```

### Enumerate, Open, Transfer

```rust
// src-tauri/src/usb.rs
use nusb::transfer::RequestBuffer;
use serde::Serialize;
use tauri::State;
use std::sync::Mutex;

#[derive(Serialize)]
pub struct UsbDeviceInfo {
    vendor_id: u16,
    product_id: u16,
    manufacturer: String,
    product: String,
}

pub struct UsbState(pub Mutex<Option<(nusb::Device, nusb::Interface)>>);

#[tauri::command]
pub fn usb_list_devices() -> Result<Vec<UsbDeviceInfo>, String> {
    let devices: Vec<UsbDeviceInfo> = nusb::list_devices()
        .map_err(|e| e.to_string())?
        .map(|d| UsbDeviceInfo {
            vendor_id: d.vendor_id(),
            product_id: d.product_id(),
            manufacturer: d.manufacturer_string().unwrap_or("").to_string(),
            product: d.product_string().unwrap_or("").to_string(),
        })
        .collect();
    Ok(devices)
}

#[tauri::command]
pub fn usb_open(
    state: State<UsbState>,
    vendor_id: u16,
    product_id: u16,
    interface_number: u8,
) -> Result<(), String> {
    let device_info = nusb::list_devices()
        .map_err(|e| e.to_string())?
        .find(|d| d.vendor_id() == vendor_id && d.product_id() == product_id)
        .ok_or_else(|| format!("Device {:04x}:{:04x} not found", vendor_id, product_id))?;

    let device = device_info.open().map_err(|e| e.to_string())?;
    let interface = device
        .claim_interface(interface_number)
        .map_err(|e| e.to_string())?;

    let mut guard = state.0.lock().unwrap();
    *guard = Some((device, interface));
    Ok(())
}

// Async bulk transfer — OUT then IN
#[tauri::command]
pub async fn usb_bulk_transfer(
    state: State<'_, UsbState>,
    endpoint_out: u8,
    endpoint_in: u8,
    data: Vec<u8>,
    read_len: usize,
) -> Result<Vec<u8>, String> {
    let guard = state.0.lock().unwrap();
    let (_, interface) = guard.as_ref().ok_or("USB device not open")?;

    // OUT
    let result = interface.bulk_out(endpoint_out, data).await;
    result.status.map_err(|e| e.to_string())?;

    // IN
    let buf = RequestBuffer::new(read_len);
    let result = interface.bulk_in(endpoint_in, buf).await;
    result.status.map_err(|e| e.to_string())?;
    Ok(result.data)
}

#[tauri::command]
pub fn usb_close(state: State<UsbState>) {
    let mut guard = state.0.lock().unwrap();
    *guard = None;
}
```

### Register in lib.rs

```rust
use usb::UsbState;

pub fn run() {
    tauri::Builder::default()
        .manage(UsbState(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![
            usb::usb_list_devices,
            usb::usb_open,
            usb::usb_bulk_transfer,
            usb::usb_close,
        ])
        // ...
}
```

---

## Section 3 — Complete HID Example

```rust
// src-tauri/src/hid.rs
use hidapi::HidApi;
use serde::Serialize;

#[derive(Serialize)]
pub struct HidDeviceInfo {
    vendor_id: u16,
    product_id: u16,
    manufacturer: String,
    product: String,
    usage_page: u16,
    usage: u16,
}

#[tauri::command]
pub fn hid_list_devices() -> Result<Vec<HidDeviceInfo>, String> {
    let api = HidApi::new().map_err(|e| e.to_string())?;
    let devices = api.device_list()
        .map(|d| HidDeviceInfo {
            vendor_id: d.vendor_id(),
            product_id: d.product_id(),
            manufacturer: d.manufacturer_string().unwrap_or("").to_string(),
            product: d.product_string().unwrap_or("").to_string(),
            usage_page: d.usage_page(),
            usage: d.usage(),
        })
        .collect();
    Ok(devices)
}

#[tauri::command]
pub fn hid_send_output_report(
    vendor_id: u16,
    product_id: u16,
    report_id: u8,
    data: Vec<u8>,
) -> Result<(), String> {
    let api = HidApi::new().map_err(|e| e.to_string())?;
    let device = api.open(vendor_id, product_id).map_err(|e| e.to_string())?;

    // First byte is report ID (0 for single-report devices)
    let mut report = vec![report_id];
    report.extend_from_slice(&data);
    device.write(&report).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub fn hid_read_input_report(
    vendor_id: u16,
    product_id: u16,
    timeout_ms: i32,
) -> Result<Vec<u8>, String> {
    let api = HidApi::new().map_err(|e| e.to_string())?;
    let device = api.open(vendor_id, product_id).map_err(|e| e.to_string())?;

    let mut buf = [0u8; 64];
    match device.read_timeout(&mut buf, timeout_ms) {
        Ok(0) => Ok(vec![]),  // timeout
        Ok(n) => Ok(buf[..n].to_vec()),
        Err(e) => Err(e.to_string()),
    }
}

#[tauri::command]
pub fn hid_set_feature_report(
    vendor_id: u16,
    product_id: u16,
    report_id: u8,
    data: Vec<u8>,
) -> Result<(), String> {
    let api = HidApi::new().map_err(|e| e.to_string())?;
    let device = api.open(vendor_id, product_id).map_err(|e| e.to_string())?;
    let mut report = vec![report_id];
    report.extend_from_slice(&data);
    device.send_feature_report(&report).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn hid_get_feature_report(
    vendor_id: u16,
    product_id: u16,
    report_id: u8,
) -> Result<Vec<u8>, String> {
    let api = HidApi::new().map_err(|e| e.to_string())?;
    let device = api.open(vendor_id, product_id).map_err(|e| e.to_string())?;
    let mut buf = vec![0u8; 65]; // report ID byte + 64 data bytes
    buf[0] = report_id;
    let n = device.get_feature_report(&mut buf).map_err(|e| e.to_string())?;
    Ok(buf[1..n].to_vec()) // strip report ID byte
}
```

---

## Section 4 — tauri-plugin-serialplugin

### Installation

```bash
# Adds to Cargo.toml and package.json automatically
cargo tauri add serialplugin
```

Or manually:

```toml
# src-tauri/Cargo.toml
[dependencies]
tauri-plugin-serialplugin = "2"
```

```bash
npm install @tauri-apps/plugin-serialplugin
```

### Rust Setup

```rust
// src-tauri/src/lib.rs
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_serialplugin::init())
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Capabilities Permission

```json
// src-tauri/capabilities/default.json
{
  "permissions": [
    "core:default",
    "serialplugin:allow-available-ports",
    "serialplugin:allow-open",
    "serialplugin:allow-write",
    "serialplugin:allow-read",
    "serialplugin:allow-close",
    "serialplugin:allow-cancel-read"
  ]
}
```

### JavaScript API

```typescript
import {
  available_ports,
  open,
  close,
  write,
  read,
  cancelRead,
} from '@tauri-apps/plugin-serialplugin';

// List available ports
const ports = await available_ports(); // { '/dev/ttyUSB0': { type: 'UsbPort', usbInfo: {...} } }

// Open
await open('/dev/ttyUSB0', {
  baudRate: 115200,
  dataBits: 8,
  flowControl: 'None',
  parity: 'None',
  stopBits: 1,
  timeout: 200,
});

// Write string
await write('/dev/ttyUSB0', 'hello\n');

// Read (resolves when data arrives or timeout)
const data = await read('/dev/ttyUSB0', {
  timeout: 1000,
  size: 128,
});

// Close
await close('/dev/ttyUSB0');
```

---

## Section 5 — Device Lifecycle Management

### Rust Struct Holding State

```rust
// src-tauri/src/device.rs
use serialport::SerialPort;
use std::sync::Mutex;
use tauri::{AppHandle, Emitter, Manager, State};

pub struct DeviceState {
    pub port: Mutex<Option<Box<dyn SerialPort + Send>>>,
    pub port_path: Mutex<Option<String>>,
}

#[tauri::command]
pub fn device_connect(
    state: State<DeviceState>,
    app: AppHandle,
    path: String,
) -> Result<(), String> {
    let port = serialport::new(&path, 115_200)
        .timeout(std::time::Duration::from_millis(500))
        .open()
        .map_err(|e| e.to_string())?;

    *state.port.lock().unwrap() = Some(port);
    *state.port_path.lock().unwrap() = Some(path.clone());
    app.emit("device-connected", &path).ok();
    Ok(())
}

#[tauri::command]
pub fn device_disconnect(state: State<DeviceState>, app: AppHandle) {
    *state.port.lock().unwrap() = None;
    *state.port_path.lock().unwrap() = None;
    app.emit("device-disconnected", ()).ok();
}
```

### Reconnection Strategy

```rust
use std::{sync::Arc, sync::Mutex, thread, time::Duration};

pub fn start_reconnect_task(
    port_path: Arc<Mutex<Option<String>>>,
    port: Arc<Mutex<Option<Box<dyn SerialPort + Send>>>>,
    app: AppHandle,
) {
    thread::spawn(move || {
        loop {
            thread::sleep(Duration::from_secs(2));

            let path = {
                let guard = port_path.lock().unwrap();
                match guard.as_deref() {
                    Some(p) => p.to_string(),
                    None => continue, // not configured — skip
                }
            };

            let already_connected = port.lock().unwrap().is_some();
            if already_connected { continue; }

            match serialport::new(&path, 115_200)
                .timeout(Duration::from_millis(500))
                .open()
            {
                Ok(p) => {
                    *port.lock().unwrap() = Some(p);
                    app.emit("device-reconnected", &path).ok();
                }
                Err(_) => {} // still disconnected
            }
        }
    });
}
```

### Cleanup on Exit

```rust
// src-tauri/src/lib.rs
pub fn run() {
    tauri::Builder::default()
        .manage(DeviceState {
            port: Mutex::new(None),
            port_path: Mutex::new(None),
        })
        .build(tauri::generate_context!())
        .expect("error building app")
        .run(|app, event| {
            if let tauri::RunEvent::ExitRequested { .. } = event {
                // Close device before exit
                let state = app.state::<DeviceState>();
                *state.port.lock().unwrap() = None;
            }
        });
}
```

---

## Section 6 — Linux udev Rules Template

```
# /etc/udev/rules.d/99-myapp-usb.rules
#
# Replace ATTRS{idVendor} and ATTRS{idProduct} with your device's VID/PID.
# Find values with: lsusb
# Or: udevadm info --name=/dev/ttyUSB0 --attribute-walk | grep idVendor
#
# Serial/USB adapters — common chips
# CP210x (Silicon Labs)
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", MODE="0666", GROUP="dialout", TAG+="uaccess"
# FTDI FT232
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", MODE="0666", GROUP="dialout", TAG+="uaccess"
# CH340/CH341
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", GROUP="dialout", TAG+="uaccess"
# Prolific PL2303
SUBSYSTEM=="tty", ATTRS{idVendor}=="067b", MODE="0666", GROUP="dialout", TAG+="uaccess"

# Raw USB device — custom VID/PID
SUBSYSTEM=="usb", ATTRS{idVendor}=="1234", ATTRS{idProduct}=="5678", MODE="0666", GROUP="plugdev", TAG+="uaccess"

# HID device (usually not needed — HID class allows user access by default)
# KERNEL=="hidraw*", ATTRS{idVendor}=="1234", ATTRS{idProduct}=="5678", MODE="0666"
```

### Installation

```bash
# Install the rules file
sudo cp 99-myapp-usb.rules /etc/udev/rules.d/

# Reload udev and re-trigger for already-connected devices
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add user to dialout group (serial) and plugdev group (raw USB)
sudo usermod -aG dialout "$USER"
sudo usermod -aG plugdev "$USER"

# Log out and back in, or run:
newgrp dialout
```

### Debugging Permissions

```bash
# See which device node a USB device got
lsusb  # find Bus and Device numbers
ls -la /dev/ttyUSB* /dev/ttyACM*  # serial ports
ls -la /dev/hidraw*                 # HID raw devices
ls -la /dev/bus/usb/BUS/DEVICE     # raw USB

# Check which udev rules matched
udevadm test $(udevadm info --query=path --name=/dev/ttyUSB0) 2>&1 | grep -E "(MODE|GROUP|TAG)"
```

---

## Section 7 — Common Error Patterns and Recovery

### Permission Denied

```rust
Err(e) if e.kind() == serialport::ErrorKind::PermissionDenied => {
    // Linux: user not in dialout group, or missing udev rule
    // macOS: should not occur for standard serial/USB
    // Windows: device in use by another process, or driver conflict
    Err("Permission denied. On Linux: add udev rule or join 'dialout' group.".to_string())
}
```

### Device Busy

```rust
// Another process has the port open (common on Linux)
Err(e) if e.to_string().contains("busy") || e.to_string().contains("EBUSY") => {
    Err("Device is busy — another process may have it open.".to_string())
}
```

### Device Disconnected Mid-Transfer

```rust
// Detect in blocking serial read
Err(e) if e.kind() == std::io::ErrorKind::BrokenPipe
       || e.kind() == std::io::ErrorKind::UnexpectedEof => {
    // Device was unplugged; close and attempt reconnect
    *state.port.lock().unwrap() = None;
    app.emit("device-disconnected", ()).ok();
    Err("Device disconnected".to_string())
}
```

For nusb (async transfers), a disconnected device surfaces as a `TransferError`:

```rust
let result = interface.bulk_in(endpoint_in, buf).await;
match result.status {
    Ok(_) => { /* process result.data */ }
    Err(nusb::transfer::TransferError::Disconnected) => {
        // device removed during transfer
    }
    Err(e) => { /* other error */ }
}
```

### Timeout Handling

```rust
// serialport: timeout is set at open time — read returns TimedOut
Err(e) if e.kind() == std::io::ErrorKind::TimedOut => {
    Ok(vec![]) // no data within timeout window — not an error
}

// nusb: set transfer timeout via submit options (if needed)
// For most cases, rely on the timeout configured on the interface
```

### Port Not Found

```rust
// Check port existence before opening — useful for UI polling
#[tauri::command]
fn is_port_available(path: String) -> bool {
    serialport::available_ports()
        .map(|ports| ports.iter().any(|p| p.port_name == path))
        .unwrap_or(false)
}
```

### Svelte-Side Error Handling

```svelte
<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';

  let error = $state<string | null>(null);

  async function connect(path: string) {
    try {
      error = null;
      await invoke('serial_open', { config: { path, baudRate: 115200, /* ... */ } });
    } catch (err) {
      // Tauri propagates the Rust Err(String) as an exception
      error = String(err);
    }
  }
</script>

{#if error}
  <p class="error">{error}</p>
{/if}
```

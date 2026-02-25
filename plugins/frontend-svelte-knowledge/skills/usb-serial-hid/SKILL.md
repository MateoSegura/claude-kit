---
name: frontend-svelte-knowledge:usb-serial-hid
description: "USB communication from Tauri Rust backends: serial port communication (serialport crate, tokio-serial for async), raw USB access (nusb pure-Rust preferred over rusb/libusb), HID devices (hidapi crate), and tauri-plugin-serialplugin as a ready-made serial alternative. Covers Tauri command wrapping, device state management, and cross-platform access rules."
user-invocable: true
---

# USB / Serial / HID Quick Reference

USB peripherals from a Tauri app are accessed entirely in Rust. The frontend calls `invoke()` as with any other Tauri command — the choice of crate is invisible to Svelte.

## Section 1 — Crate Decision Table

### Serial Port Crates

| Crate | Async | When to Use |
|-------|-------|-------------|
| `serialport` | Blocking only | Simplest API; polling or spawning a thread is fine |
| `serial2` | Blocking only | Slightly lower-level; good when you want POSIX termios control |
| `tokio-serial` | async (Tokio) | Use when already on Tokio and you need non-blocking reads |
| `tauri-plugin-serialplugin` | async, managed | Drop-in for Tauri; JS API included; best choice when you don't need raw control |

**Rule of thumb:** use `tauri-plugin-serialplugin` when the serial use case is straightforward (open/read/write/close). Drop to `serialport` or `tokio-serial` when you need custom framing, flow control, or tight integration with other async logic.

### Raw USB Crates

| Crate | Backend | When to Use |
|-------|---------|-------------|
| `nusb` | Pure Rust | **Preferred** — no C deps, async-native, cross-platform |
| `rusb` | libusb wrapper | Use only if nusb is missing a feature you need |
| `libusb` (sys) | C FFI | Avoid — use rusb/nusb instead |

**nusb is the modern choice.** It ships with no C dependencies, works on stable Rust, and has first-class async transfer support via its `TransferFuture` API.

### HID Crates

| Crate | Notes |
|-------|-------|
| `hidapi` | Wraps OS HID stack (HIDAPI C lib). Enumeration, input/output/feature reports. |
| `nusb` | Can also talk to HID interfaces via raw USB — use when you need direct control |

---

## Section 2 — Serial Port Patterns

### Cargo.toml

```toml
[dependencies]
serialport = "4"
# OR for async:
tokio-serial = "5"
tokio = { version = "1", features = ["full"] }
```

### Port Enumeration

```rust
use serialport::available_ports;

#[tauri::command]
fn list_serial_ports() -> Result<Vec<String>, String> {
    let ports = available_ports().map_err(|e| e.to_string())?;
    Ok(ports.iter().map(|p| p.port_name.clone()).collect())
}
```

### Open with Config

```rust
use serialport::SerialPort;
use std::time::Duration;

fn open_port(path: &str) -> Result<Box<dyn SerialPort>, String> {
    serialport::new(path, 115_200)
        .data_bits(serialport::DataBits::Eight)
        .parity(serialport::Parity::None)
        .stop_bits(serialport::StopBits::One)
        .flow_control(serialport::FlowControl::None)
        .timeout(Duration::from_millis(500))
        .open()
        .map_err(|e| e.to_string())
}
```

### Blocking Read / Write

```rust
use std::io::{Read, Write};

#[tauri::command]
fn serial_write(port_name: String, data: Vec<u8>) -> Result<(), String> {
    let mut port = open_port(&port_name)?;
    port.write_all(&data).map_err(|e| e.to_string())
}

#[tauri::command]
fn serial_read(port_name: String, max_bytes: usize) -> Result<Vec<u8>, String> {
    let mut port = open_port(&port_name)?;
    let mut buf = vec![0u8; max_bytes];
    let n = port.read(&mut buf).map_err(|e| e.to_string())?;
    buf.truncate(n);
    Ok(buf)
}
```

### Async Read with tokio-serial

```rust
use tokio_serial::SerialPortBuilderExt;
use tokio::io::AsyncReadExt;

#[tauri::command]
async fn async_serial_read(port_name: String) -> Result<Vec<u8>, String> {
    let mut port = tokio_serial::new(&port_name, 115_200)
        .open_native_async()
        .map_err(|e| e.to_string())?;

    let mut buf = vec![0u8; 256];
    let n = port.read(&mut buf).await.map_err(|e| e.to_string())?;
    buf.truncate(n);
    Ok(buf)
}
```

### Reconnection on Disconnect

```rust
use std::{thread, time::Duration};

fn read_with_reconnect(port_name: &str) {
    loop {
        match open_port(port_name) {
            Ok(mut port) => {
                let mut buf = [0u8; 64];
                loop {
                    match port.read(&mut buf) {
                        Ok(n) if n > 0 => { /* process buf[..n] */ }
                        Ok(_) => {} // zero bytes — timeout, retry
                        Err(e) => {
                            eprintln!("Port error: {e} — reconnecting");
                            break; // exit inner loop, retry open
                        }
                    }
                }
            }
            Err(e) => eprintln!("Cannot open port: {e}"),
        }
        thread::sleep(Duration::from_secs(2));
    }
}
```

---

## Section 3 — Raw USB Patterns (nusb)

### Cargo.toml

```toml
[dependencies]
nusb = "0.1"
futures-lite = "2"  # for block_on in sync contexts
```

### Enumerate Devices by VID/PID

```rust
use nusb::DeviceInfo;

#[tauri::command]
fn find_usb_device(vendor_id: u16, product_id: u16) -> Result<String, String> {
    let device = nusb::list_devices()
        .map_err(|e| e.to_string())?
        .find(|d| d.vendor_id() == vendor_id && d.product_id() == product_id)
        .ok_or_else(|| format!("Device {:04x}:{:04x} not found", vendor_id, product_id))?;

    Ok(format!(
        "{} — {}",
        device.manufacturer_string().unwrap_or("Unknown"),
        device.product_string().unwrap_or("Unknown")
    ))
}
```

### Bulk Transfer

```rust
use nusb::transfer::RequestBuffer;

#[tauri::command]
async fn usb_bulk_transfer(
    vendor_id: u16,
    product_id: u16,
    endpoint_out: u8,
    endpoint_in: u8,
    data: Vec<u8>,
) -> Result<Vec<u8>, String> {
    let device_info = nusb::list_devices()
        .map_err(|e| e.to_string())?
        .find(|d| d.vendor_id() == vendor_id && d.product_id() == product_id)
        .ok_or("Device not found")?;

    let device = device_info.open().map_err(|e| e.to_string())?;
    let interface = device.claim_interface(0).map_err(|e| e.to_string())?;

    // OUT transfer
    let result = interface.bulk_out(endpoint_out, data).await;
    result.status.map_err(|e| e.to_string())?;

    // IN transfer
    let buf = RequestBuffer::new(512);
    let result = interface.bulk_in(endpoint_in, buf).await;
    result.status.map_err(|e| e.to_string())?;
    Ok(result.data)
}
```

### Interrupt Transfer

```rust
use nusb::transfer::RequestBuffer;

async fn usb_interrupt_read(interface: &nusb::Interface, endpoint: u8) -> Result<Vec<u8>, String> {
    let buf = RequestBuffer::new(64);
    let result = interface.interrupt_in(endpoint, buf).await;
    result.status.map_err(|e| e.to_string())?;
    Ok(result.data)
}
```

### Control Transfer

```rust
use nusb::transfer::{ControlIn, ControlOut, ControlType, Recipient};

async fn send_control(device: &nusb::Device) -> Result<(), String> {
    let result = device
        .control_out(ControlOut {
            control_type: ControlType::Vendor,
            recipient: Recipient::Device,
            request: 0x01,
            value: 0x0000,
            index: 0x0000,
            data: &[0xAB, 0xCD],
        })
        .await;
    result.status.map_err(|e| e.to_string())
}
```

---

## Section 4 — HID Device Patterns

### Cargo.toml

```toml
[dependencies]
hidapi = "2"
```

### Enumerate HID Devices

```rust
use hidapi::HidApi;

#[tauri::command]
fn list_hid_devices() -> Result<Vec<String>, String> {
    let api = HidApi::new().map_err(|e| e.to_string())?;
    let devices: Vec<String> = api
        .device_list()
        .map(|d| format!(
            "{:04x}:{:04x} — {} {}",
            d.vendor_id(),
            d.product_id(),
            d.manufacturer_string().unwrap_or(""),
            d.product_string().unwrap_or("")
        ))
        .collect();
    Ok(devices)
}
```

### Open and Communicate

```rust
#[tauri::command]
fn hid_send_receive(
    vendor_id: u16,
    product_id: u16,
    report: Vec<u8>,
) -> Result<Vec<u8>, String> {
    let api = HidApi::new().map_err(|e| e.to_string())?;
    let device = api.open(vendor_id, product_id).map_err(|e| e.to_string())?;

    // Output report (report ID 0 for single-report devices)
    device.write(&report).map_err(|e| e.to_string())?;

    // Input report with 100 ms timeout
    let mut buf = [0u8; 64];
    let n = device.read_timeout(&mut buf, 100).map_err(|e| e.to_string())?;
    Ok(buf[..n].to_vec())
}

#[tauri::command]
fn hid_feature_report(
    vendor_id: u16,
    product_id: u16,
    report_id: u8,
    data: Vec<u8>,
) -> Result<Vec<u8>, String> {
    let api = HidApi::new().map_err(|e| e.to_string())?;
    let device = api.open(vendor_id, product_id).map_err(|e| e.to_string())?;

    // Send feature report
    let mut report = vec![report_id];
    report.extend_from_slice(&data);
    device.send_feature_report(&report).map_err(|e| e.to_string())?;

    // Get feature report
    let mut buf = vec![report_id, 0u8; 65];
    device.get_feature_report(&mut buf).map_err(|e| e.to_string())?;
    Ok(buf[1..].to_vec()) // strip report ID
}
```

---

## Section 5 — Tauri Integration

### Managed Device State

Use `tauri::State<Mutex<Option<T>>>` to hold an open device handle across commands:

```rust
use std::sync::Mutex;
use serialport::SerialPort;
use tauri::State;

pub struct SerialState(Mutex<Option<Box<dyn SerialPort + Send>>>);

#[tauri::command]
fn connect(state: State<SerialState>, port: String) -> Result<(), String> {
    let mut guard = state.0.lock().unwrap();
    let port = serialport::new(&port, 115_200)
        .timeout(std::time::Duration::from_millis(500))
        .open()
        .map_err(|e| e.to_string())?;
    *guard = Some(port);
    Ok(())
}

#[tauri::command]
fn disconnect(state: State<SerialState>) {
    let mut guard = state.0.lock().unwrap();
    *guard = None; // drop closes the port
}

#[tauri::command]
fn write_bytes(state: State<SerialState>, data: Vec<u8>) -> Result<(), String> {
    use std::io::Write;
    let mut guard = state.0.lock().unwrap();
    let port = guard.as_mut().ok_or("Not connected")?;
    port.write_all(&data).map_err(|e| e.to_string())
}

// Register in lib.rs
pub fn run() {
    tauri::Builder::default()
        .manage(SerialState(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![connect, disconnect, write_bytes])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### tauri-plugin-serialplugin (Ready-Made Alternative)

```bash
cargo tauri add serialplugin
```

```typescript
// Svelte component — JS API included
import { open, close, write, read, available_ports } from '@tauri-apps/plugin-serialplugin';

const ports = await available_ports();
await open({ path: ports[0], baudRate: 115200 });
await write({ path: ports[0], value: 'hello\n' });
const data = await read({ path: ports[0], timeout: 1000, size: 64 });
await close(ports[0]);
```

Requires capability permission: `"serialplugin:allow-open"`, `"serialplugin:allow-write"`, `"serialplugin:allow-read"`, `"serialplugin:allow-close"`, `"serialplugin:allow-available-ports"`.

---

## Section 6 — Cross-Platform Notes

### Linux — udev Rules

Without udev rules, serial and USB devices require root. Add a rules file:

```
# /etc/udev/rules.d/99-myapp.rules
# Grant access to USB serial adapters (CP210x, FTDI, CH340, etc.)
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", MODE="0666", GROUP="dialout"
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", MODE="0666", GROUP="dialout"
# Raw USB by VID/PID
SUBSYSTEM=="usb", ATTRS{idVendor}=="1234", ATTRS{idProduct}=="5678", MODE="0666"
```

```bash
sudo cp 99-myapp.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
# User must be in the dialout group for serial
sudo usermod -aG dialout $USER  # log out / in to take effect
```

### macOS

No special entitlements needed for USB or serial in Tauri. USB serial adapters (FTDI, CH340, CP210x) need their kernel extension or DriverKit driver. Native HID works without any entitlement. For App Store distribution, USB entitlements are required but Tauri apps are typically direct-distribution.

### Windows — Driver Requirements

| Device type | Required driver | Tool |
|-------------|-----------------|------|
| USB Serial (FTDI/CH340/CP210x) | Manufacturer driver | Installed automatically on Win 10+ for common chips |
| Raw USB with nusb/rusb | WinUSB | Use Zadig to replace the default driver |
| HID | None | HID class driver built into Windows |

WinUSB installation via Zadig: download from `zadig.akeo.ie`, select device, choose WinUSB, click Install. Warning: replacing HID driver breaks HID access — only do this for non-HID devices.

---

## Additional Resources

- [usb-reference.md](usb-reference.md) — Complete code examples: full serial Tauri command + Svelte component, complete nusb enumerate/transfer example, full HID example, tauri-plugin-serialplugin setup, device lifecycle management, Linux udev template, common error patterns

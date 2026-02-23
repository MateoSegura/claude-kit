# LAN Discovery — Complete Code Reference

Complete working examples for LAN networking in Tauri apps. Each section is self-contained.

---

## Section 1: Complete TCP Client — JSON Commands with Reconnect

Full Tauri command that connects to a device, sends JSON commands with length-prefix framing, reads responses, and reconnects on failure.

```rust
// src-tauri/src/tcp_client.rs
use serde::{Deserialize, Serialize};
use std::time::Duration;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;
use tokio::time::timeout;

#[derive(Serialize, Deserialize, Debug)]
pub struct DeviceCommand {
    pub id: u32,
    pub method: String,
    pub params: serde_json::Value,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct DeviceResponse {
    pub id: u32,
    pub result: Option<serde_json::Value>,
    pub error: Option<String>,
}

/// Sends a JSON command to a device using length-prefix framing.
/// Retries connection up to `retries` times before failing.
#[tauri::command]
pub async fn device_command(
    host: String,
    port: u16,
    method: String,
    params: serde_json::Value,
    retries: Option<u32>,
) -> Result<DeviceResponse, String> {
    let max_retries = retries.unwrap_or(3);
    let addr = format!("{}:{}", host, port);
    let cmd = DeviceCommand { id: 1, method, params };
    let payload = serde_json::to_vec(&cmd).map_err(|e| e.to_string())?;

    for attempt in 0..=max_retries {
        match try_send_command(&addr, &payload).await {
            Ok(resp) => return Ok(resp),
            Err(e) if attempt < max_retries => {
                eprintln!("Attempt {} failed: {}. Retrying...", attempt + 1, e);
                tokio::time::sleep(Duration::from_millis(500 * (attempt as u64 + 1))).await;
            }
            Err(e) => return Err(e),
        }
    }
    unreachable!()
}

async fn try_send_command(addr: &str, payload: &[u8]) -> Result<DeviceResponse, String> {
    // Connect with 3-second timeout
    let stream = timeout(
        Duration::from_secs(3),
        TcpStream::connect(addr),
    )
    .await
    .map_err(|_| format!("Connection timeout to {}", addr))?
    .map_err(|e| format!("Connection refused: {}", e))?;

    let (mut reader, mut writer) = stream.into_split();

    // Write: [4-byte length][payload]
    let len_bytes = (payload.len() as u32).to_be_bytes();
    writer.write_all(&len_bytes).await.map_err(|e| e.to_string())?;
    writer.write_all(payload).await.map_err(|e| e.to_string())?;
    writer.flush().await.map_err(|e| e.to_string())?;

    // Read response with 5-second timeout
    let response = timeout(Duration::from_secs(5), async {
        let mut len_buf = [0u8; 4];
        reader.read_exact(&mut len_buf).await?;
        let resp_len = u32::from_be_bytes(len_buf) as usize;

        // Guard against absurdly large responses
        if resp_len > 1_048_576 {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "Response too large",
            ));
        }

        let mut resp_buf = vec![0u8; resp_len];
        reader.read_exact(&mut resp_buf).await?;
        Ok(resp_buf)
    })
    .await
    .map_err(|_| "Response timeout".to_string())?
    .map_err(|e: std::io::Error| e.to_string())?;

    serde_json::from_slice(&response).map_err(|e| e.to_string())
}
```

---

## Section 2: Complete UDP Broadcast Discovery

Send a discovery broadcast, collect responses, parse device info, and display in Svelte.

```rust
// src-tauri/src/udp_discovery.rs
use serde::{Deserialize, Serialize};
use std::net::Ipv4Addr;
use tokio::net::UdpSocket;
use tokio::time::{timeout, Duration};

const DISCOVERY_PORT: u16 = 54321;
const DISCOVERY_TIMEOUT_MS: u64 = 2000;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DiscoveredDevice {
    pub ip: String,
    pub name: String,
    pub device_type: String,
    pub tcp_port: u16,
    pub capabilities: Vec<String>,
}

#[tauri::command]
pub async fn scan_local_network() -> Result<Vec<DiscoveredDevice>, String> {
    let socket = UdpSocket::bind("0.0.0.0:0")
        .await
        .map_err(|e| format!("Bind error: {}", e))?;

    socket.set_broadcast(true).map_err(|e| e.to_string())?;

    // Send discovery to broadcast address
    let packet = serde_json::json!({
        "type": "discover",
        "app": "myapp",
        "version": "1.0"
    });
    let packet_bytes = serde_json::to_vec(&packet).unwrap();

    socket
        .send_to(&packet_bytes, format!("255.255.255.255:{}", DISCOVERY_PORT))
        .await
        .map_err(|e| format!("Send error: {}", e))?;

    // Collect responses within timeout
    let mut devices = Vec::new();
    let mut buf = [0u8; 2048];

    let collect_fut = async {
        loop {
            match socket.recv_from(&mut buf).await {
                Ok((len, peer_addr)) => {
                    // Skip our own broadcast (if we happen to be listening)
                    if let Ok(json) = serde_json::from_slice::<serde_json::Value>(&buf[..len]) {
                        if json.get("type").and_then(|t| t.as_str()) == Some("discover") {
                            continue; // skip discovery packets
                        }
                        let device = DiscoveredDevice {
                            ip: peer_addr.ip().to_string(),
                            name: json["name"].as_str().unwrap_or("Unknown").to_string(),
                            device_type: json["type"].as_str().unwrap_or("unknown").to_string(),
                            tcp_port: json["port"].as_u64().unwrap_or(0) as u16,
                            capabilities: json["capabilities"]
                                .as_array()
                                .map(|a| a.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect())
                                .unwrap_or_default(),
                        };
                        devices.push(device);
                    }
                }
                Err(_) => break,
            }
        }
    };

    let _ = timeout(Duration::from_millis(DISCOVERY_TIMEOUT_MS), collect_fut).await;
    Ok(devices)
}
```

```svelte
<!-- src/lib/components/DeviceScanner.svelte -->
<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';

  interface Device {
    ip: string;
    name: string;
    device_type: string;
    tcp_port: number;
    capabilities: string[];
  }

  let devices = $state<Device[]>([]);
  let scanning = $state(false);
  let error = $state<string | null>(null);

  async function scan() {
    scanning = true;
    error = null;
    try {
      devices = await invoke<Device[]>('scan_local_network');
    } catch (e) {
      error = String(e);
    } finally {
      scanning = false;
    }
  }
</script>

<div class="scanner">
  <button onclick={scan} disabled={scanning}>
    {scanning ? 'Scanning...' : 'Scan Network'}
  </button>

  {#if error}
    <p class="error">{error}</p>
  {/if}

  <ul>
    {#each devices as device (device.ip)}
      <li>
        <strong>{device.name}</strong> — {device.ip}:{device.tcp_port}
        <span class="type">{device.device_type}</span>
        {#if device.capabilities.length}
          <small>{device.capabilities.join(', ')}</small>
        {/if}
      </li>
    {/each}
  </ul>
</div>
```

---

## Section 3: Complete mDNS Service Discovery

Full mDNS service registration and browsing using `mdns-sd`.

```rust
// src-tauri/src/mdns.rs
use mdns_sd::{ServiceDaemon, ServiceEvent, ServiceInfo};
use serde::Serialize;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Emitter, State};

#[derive(Clone, Serialize)]
pub struct MdnsDevice {
    pub fullname: String,
    pub ip: String,
    pub port: u16,
    pub txt_records: HashMap<String, String>,
}

pub struct MdnsState {
    pub daemon: Arc<Mutex<Option<ServiceDaemon>>>,
}

impl MdnsState {
    pub fn new() -> Self {
        MdnsState {
            daemon: Arc::new(Mutex::new(None)),
        }
    }
}

/// Start mDNS browsing — call from app setup, runs indefinitely
pub async fn start_mdns_browse(app: AppHandle, mdns_state: State<'_, MdnsState>) {
    let daemon = ServiceDaemon::new().expect("Failed to create mDNS daemon");

    let receiver = daemon
        .browse("_myapp._tcp.local.")
        .expect("Failed to browse mDNS");

    // Store daemon in state so it stays alive
    *mdns_state.daemon.lock().unwrap() = Some(daemon);

    // Process events in a thread (mdns-sd uses synchronous channels)
    let app_clone = app.clone();
    tokio::task::spawn_blocking(move || {
        while let Ok(event) = receiver.recv() {
            match event {
                ServiceEvent::ServiceResolved(info) => {
                    let ip = info
                        .get_addresses()
                        .iter()
                        .find(|a| a.is_ipv4())
                        .map(|a| a.to_string())
                        .unwrap_or_default();

                    let txt_records: HashMap<String, String> = info
                        .get_properties()
                        .iter()
                        .map(|p| (p.key().to_string(), p.val_str().to_string()))
                        .collect();

                    let device = MdnsDevice {
                        fullname: info.get_fullname().to_string(),
                        ip,
                        port: info.get_port(),
                        txt_records,
                    };

                    app_clone.emit("mdns-device-found", &device).ok();
                }
                ServiceEvent::ServiceRemoved(_, fullname) => {
                    app_clone.emit("mdns-device-lost", fullname).ok();
                }
                ServiceEvent::SearchStopped(_) => break,
                _ => {}
            }
        }
    });
}

/// Register this app as an mDNS service so peers can find us
#[tauri::command]
pub fn register_mdns_service(
    port: u16,
    instance_name: String,
    state: State<'_, MdnsState>,
) -> Result<(), String> {
    let daemon_guard = state.daemon.lock().unwrap();
    let daemon = daemon_guard.as_ref().ok_or("mDNS daemon not started")?;

    let mut props = HashMap::new();
    props.insert("version".to_string(), "1.0".to_string());
    props.insert("platform".to_string(), "tauri".to_string());

    // Get local hostname (mdns-sd resolves to current machine's hostname)
    let hostname = hostname::get()
        .ok()
        .and_then(|h| h.into_string().ok())
        .unwrap_or_else(|| "localhost".to_string());

    let service = ServiceInfo::new(
        "_myapp._tcp.local.",
        &instance_name,
        &format!("{}.local.", hostname),
        (), // empty IP — mdns-sd will use the actual interface IP
        port,
        Some(props),
    )
    .map_err(|e| e.to_string())?;

    daemon.register(service).map_err(|e| e.to_string())
}
```

---

## Section 4: WebSocket from Rust (tokio-tungstenite)

Connect to a device WebSocket endpoint, handle binary/text messages, ping/pong keep-alive, reconnect on close.

```rust
// src-tauri/src/ws_client.rs
use futures_util::{SinkExt, StreamExt};
use std::time::Duration;
use tauri::{AppHandle, Emitter};
use tokio::time::interval;
use tokio_tungstenite::{connect_async, tungstenite::Message};

#[tauri::command]
pub async fn connect_device_ws(
    app: AppHandle,
    device_id: String,
    url: String,
) -> Result<(), String> {
    tauri::async_runtime::spawn(async move {
        let mut reconnect_delay = Duration::from_secs(1);

        loop {
            match connect_async(&url).await {
                Ok((ws_stream, _response)) => {
                    reconnect_delay = Duration::from_secs(1); // reset on success
                    app.emit("ws-connected", &device_id).ok();

                    let (mut sink, mut stream) = ws_stream.split();

                    // Ping every 15 seconds to keep connection alive
                    let mut ping_ticker = interval(Duration::from_secs(15));
                    let device_id_clone = device_id.clone();
                    let app_clone = app.clone();

                    loop {
                        tokio::select! {
                            msg = stream.next() => {
                                match msg {
                                    Some(Ok(Message::Text(text))) => {
                                        app_clone.emit("ws-message", serde_json::json!({
                                            "device_id": &device_id_clone,
                                            "type": "text",
                                            "data": text
                                        })).ok();
                                    }
                                    Some(Ok(Message::Binary(bin))) => {
                                        // Binary data — emit as base64 for easy Svelte handling
                                        use base64::Engine;
                                        let b64 = base64::engine::general_purpose::STANDARD.encode(&bin);
                                        app_clone.emit("ws-message", serde_json::json!({
                                            "device_id": &device_id_clone,
                                            "type": "binary",
                                            "data": b64
                                        })).ok();
                                    }
                                    Some(Ok(Message::Pong(_))) => {} // keep-alive ack
                                    Some(Ok(Message::Close(_))) | None => {
                                        break; // connection closed
                                    }
                                    Some(Err(e)) => {
                                        eprintln!("WebSocket error: {}", e);
                                        break;
                                    }
                                    _ => {}
                                }
                            }
                            _ = ping_ticker.tick() => {
                                if sink.send(Message::Ping(vec![])).await.is_err() {
                                    break;
                                }
                            }
                        }
                    }

                    app.emit("ws-disconnected", &device_id).ok();
                }
                Err(e) => {
                    eprintln!("WebSocket connect failed: {}", e);
                }
            }

            // Reconnect with exponential backoff (max 30s)
            tokio::time::sleep(reconnect_delay).await;
            reconnect_delay = (reconnect_delay * 2).min(Duration::from_secs(30));
        }
    });
    Ok(())
}
```

---

## Section 5: Svelte Network Device Browser Component

Real-time device list with Tauri event listeners, connection status indicators, command input, and response display.

```svelte
<!-- src/lib/components/NetworkDeviceBrowser.svelte -->
<script lang="ts">
  import { listen } from '@tauri-apps/api/event';
  import { invoke } from '@tauri-apps/api/core';
  import { onDestroy } from 'svelte';

  interface Device {
    fullname: string;
    ip: string;
    port: number;
    txt_records: Record<string, string>;
    status: 'online' | 'offline' | 'connecting';
    lastSeen: number;
  }

  let devices = $state<Map<string, Device>>(new Map());
  let selectedId = $state<string | null>(null);
  let commandInput = $state('{"method":"ping","params":{}}');
  let response = $state<string | null>(null);
  let sending = $state(false);

  // Subscribe to mDNS discovery events
  const unlistenFound = listen<Device>('mdns-device-found', (event) => {
    const dev = { ...event.payload, status: 'online' as const, lastSeen: Date.now() };
    devices = new Map(devices.set(dev.fullname, dev));
  });

  const unlistenLost = listen<string>('mdns-device-lost', (event) => {
    const id = event.payload;
    const existing = devices.get(id);
    if (existing) {
      devices = new Map(devices.set(id, { ...existing, status: 'offline' }));
    }
  });

  const unlistenStatus = listen<{ id: string; status: string }>('device-status', (event) => {
    const { id, status } = event.payload;
    const existing = devices.get(id);
    if (existing) {
      devices = new Map(devices.set(id, {
        ...existing,
        status: status as Device['status'],
      }));
    }
  });

  async function sendCommand() {
    if (!selectedId) return;
    const device = devices.get(selectedId);
    if (!device) return;

    sending = true;
    response = null;
    try {
      const cmd = JSON.parse(commandInput);
      const result = await invoke('device_command', {
        host: device.ip,
        port: device.port,
        method: cmd.method,
        params: cmd.params ?? {},
      });
      response = JSON.stringify(result, null, 2);
    } catch (e) {
      response = `Error: ${String(e)}`;
    } finally {
      sending = false;
    }
  }

  onDestroy(async () => {
    (await unlistenFound)();
    (await unlistenLost)();
    (await unlistenStatus)();
  });

  function statusColor(status: Device['status']) {
    return { online: '#22c55e', offline: '#ef4444', connecting: '#eab308' }[status];
  }
</script>

<div class="network-browser">
  <h2>Local Network Devices</h2>

  <ul class="device-list">
    {#each [...devices.values()] as device (device.fullname)}
      <li
        class="device-item"
        class:selected={selectedId === device.fullname}
        onclick={() => selectedId = device.fullname}
      >
        <span
          class="status-dot"
          style="background: {statusColor(device.status)}"
          title={device.status}
        ></span>
        <span class="device-name">{device.fullname.split('.')[0]}</span>
        <span class="device-addr">{device.ip}:{device.port}</span>
      </li>
    {:else}
      <li class="empty">No devices found. Make sure mDNS browsing is active.</li>
    {/each}
  </ul>

  {#if selectedId}
    <div class="command-panel">
      <h3>Send Command</h3>
      <textarea
        bind:value={commandInput}
        rows={4}
        placeholder='{"method":"ping","params":{}}'
      ></textarea>
      <button onclick={sendCommand} disabled={sending}>
        {sending ? 'Sending...' : 'Send'}
      </button>

      {#if response}
        <pre class="response">{response}</pre>
      {/if}
    </div>
  {/if}
</div>

<style>
  .device-list { list-style: none; padding: 0; margin: 0; }
  .device-item {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.5rem; cursor: pointer; border-radius: 4px;
  }
  .device-item:hover { background: var(--surface-2, #f5f5f5); }
  .device-item.selected { background: var(--surface-3, #e8e8e8); }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .device-addr { margin-left: auto; color: var(--text-muted, #888); font-size: 0.85em; }
  .response { background: #1e1e1e; color: #d4d4d4; padding: 1rem; border-radius: 4px; overflow-x: auto; }
</style>
```

---

## Section 6: Multi-Connection Manager

Rust struct managing multiple TCP connections by device ID, broadcast, route, and health monitoring.

```rust
// src-tauri/src/connection_manager.rs
use serde::Serialize;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;
use tokio::sync::Mutex;
use tokio::time::{interval, Duration};
use tauri::{AppHandle, Emitter};

#[derive(Serialize, Clone)]
pub struct ConnectionStatus {
    pub device_id: String,
    pub connected: bool,
    pub error: Option<String>,
}

pub struct MultiConnectionManager {
    connections: Arc<Mutex<HashMap<String, TcpStream>>>,
    app: AppHandle,
}

impl MultiConnectionManager {
    pub fn new(app: AppHandle) -> Self {
        Self {
            connections: Arc::new(Mutex::new(HashMap::new())),
            app,
        }
    }

    pub async fn add_connection(&self, device_id: String, host: &str, port: u16) -> Result<(), String> {
        let stream = TcpStream::connect(format!("{}:{}", host, port))
            .await
            .map_err(|e| e.to_string())?;

        self.connections.lock().await.insert(device_id.clone(), stream);

        self.app.emit("connection-changed", ConnectionStatus {
            device_id,
            connected: true,
            error: None,
        }).ok();

        Ok(())
    }

    pub async fn remove_connection(&self, device_id: &str) {
        self.connections.lock().await.remove(device_id);
        self.app.emit("connection-changed", ConnectionStatus {
            device_id: device_id.to_string(),
            connected: false,
            error: None,
        }).ok();
    }

    /// Send a message to a specific device
    pub async fn send_to(&self, device_id: &str, payload: &[u8]) -> Result<(), String> {
        let mut connections = self.connections.lock().await;
        let stream = connections.get_mut(device_id).ok_or("Device not connected")?;

        let len = (payload.len() as u32).to_be_bytes();
        stream.write_all(&len).await.map_err(|e| e.to_string())?;
        stream.write_all(payload).await.map_err(|e| e.to_string())?;
        stream.flush().await.map_err(|e| e.to_string())
    }

    /// Broadcast a message to all connected devices
    pub async fn broadcast(&self, payload: &[u8]) {
        let mut connections = self.connections.lock().await;
        let len = (payload.len() as u32).to_be_bytes();

        let mut failed = Vec::new();
        for (id, stream) in connections.iter_mut() {
            let ok = stream.write_all(&len).await.is_ok()
                && stream.write_all(payload).await.is_ok()
                && stream.flush().await.is_ok();
            if !ok {
                failed.push(id.clone());
            }
        }
        drop(connections);

        // Remove failed connections
        for id in failed {
            self.remove_connection(&id).await;
        }
    }

    /// Ping all connections to check health (run as background task)
    pub async fn run_health_monitor(manager: Arc<Self>) {
        let mut ticker = interval(Duration::from_secs(15));
        let ping = {
            let payload = b"ping";
            let mut v = Vec::with_capacity(8);
            v.extend_from_slice(&(payload.len() as u32).to_be_bytes());
            v.extend_from_slice(payload);
            v
        };

        loop {
            ticker.tick().await;
            manager.broadcast(&ping).await;
        }
    }
}

// Tauri commands wrapping the manager
#[tauri::command]
pub async fn connect_to_device(
    id: String,
    host: String,
    port: u16,
    manager: tauri::State<'_, Arc<MultiConnectionManager>>,
) -> Result<(), String> {
    manager.add_connection(id, &host, port).await
}

#[tauri::command]
pub async fn disconnect_device(
    id: String,
    manager: tauri::State<'_, Arc<MultiConnectionManager>>,
) {
    manager.remove_connection(&id).await;
}

#[tauri::command]
pub async fn send_to_device(
    id: String,
    payload: String,
    manager: tauri::State<'_, Arc<MultiConnectionManager>>,
) -> Result<(), String> {
    manager.send_to(&id, payload.as_bytes()).await
}
```

---

## Section 7: Error Patterns

Common network errors and how to handle them in Tauri commands.

```rust
use std::io::ErrorKind;
use tokio::net::TcpStream;

pub fn classify_io_error(e: &std::io::Error) -> &'static str {
    match e.kind() {
        ErrorKind::ConnectionRefused => "connection_refused",
        ErrorKind::TimedOut => "timeout",
        ErrorKind::NetworkUnreachable | ErrorKind::HostUnreachable => "network_unreachable",
        ErrorKind::AddrInUse => "address_already_in_use",
        ErrorKind::ConnectionReset | ErrorKind::BrokenPipe => "connection_lost",
        ErrorKind::PermissionDenied => "permission_denied",
        _ => "unknown_error",
    }
}

/// Handle each error type appropriately:
///
/// - ConnectionRefused: Device is offline or not listening. Show "offline" status.
///   Retry with exponential backoff up to 3 attempts.
///
/// - TimedOut: Network path exists but device not responding. Could be firewall.
///   Show "connecting..." status, retry once.
///
/// - NetworkUnreachable: No route to host — WiFi disconnected or subnet mismatch.
///   Check network interface. Emit "network-unavailable" event to frontend.
///
/// - AddrInUse: Port already bound (another instance running, or port held by OS).
///   Try the next available port or wait 60s for TIME_WAIT to expire.
///
/// - ConnectionReset / BrokenPipe: Remote closed connection unexpectedly.
///   Re-establish from scratch — don't reuse the old socket.

#[tauri::command]
pub async fn resilient_connect(host: String, port: u16) -> Result<String, String> {
    match TcpStream::connect(format!("{}:{}", host, port)).await {
        Ok(_) => Ok("connected".to_string()),
        Err(e) => {
            let kind = classify_io_error(&e);
            Err(serde_json::json!({
                "error_kind": kind,
                "message": e.to_string(),
                "advice": match kind {
                    "connection_refused" => "Device is offline. Check if the app is running on the target.",
                    "timeout" => "Device not responding. Check firewall rules.",
                    "network_unreachable" => "No network path. Check WiFi/LAN connection.",
                    "address_already_in_use" => "Port already in use. Try a different port.",
                    _ => "Unexpected network error."
                }
            }).to_string())
        }
    }
}

// Svelte: handle network-unavailable event
//
// listen('network-unavailable', () => {
//   showToast('Lost network connection. Discovery paused.', 'warning');
// });
//
// Network interface change recovery:
// tauri::async_runtime::spawn(async move {
//   // Watch for network changes — restart mDNS daemon when interface changes
//   // mdns-sd daemon handles interface changes internally on most platforms
//   // For UDP sockets: close and rebind to 0.0.0.0:0 after network reconnect
// });
```

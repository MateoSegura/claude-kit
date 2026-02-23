---
name: coding-frontend-svelte-knowledge:lan-discovery
description: "LAN and local network communication from Tauri Rust backends: async TCP/UDP sockets with tokio::net, mDNS/DNS-SD service discovery and advertisement with mdns-sd, multicast group management with socket2, local network device discovery patterns, and WebSocket from Rust with tokio-tungstenite."
user-invocable: true
---

# LAN Discovery — Tauri Rust Networking Quick Reference

For Tauri apps that need to discover and communicate with devices on the local network (printers, cameras, IoT devices, peer apps, etc.). All networking runs on the Rust side — the Svelte frontend receives results via Tauri events and commands.

## Section 1: Crate Decision Table

| Crate | Purpose | When to Use |
|-------|---------|------------|
| `tokio::net` | Async TCP (`TcpStream`, `TcpListener`) and UDP (`UdpSocket`) | All standard TCP/UDP networking — the default choice |
| `mdns-sd` | mDNS service discovery + advertisement (DNS-SD) | Find devices by service type, advertise your own app on LAN |
| `tokio-tungstenite` | Async WebSocket client/server on top of tokio | Connect to a device that exposes a WebSocket endpoint |
| `socket2` | Advanced socket options (join multicast, set TTL, broadcast, reuse) | Multicast groups, broadcast sockets, raw socket control |
| `serde_json` | JSON serialization for wire messages | All JSON-based messaging protocols |

```toml
# src-tauri/Cargo.toml
[dependencies]
tokio = { version = "1", features = ["full"] }
mdns-sd = "0.11"
tokio-tungstenite = "0.24"
socket2 = { version = "0.5", features = ["all"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

**Decision guide:**
- Device speaks a custom protocol over TCP? Use `tokio::net::TcpStream` with length-prefix framing.
- Need to find nearby devices without knowing their IP? Use `mdns-sd` for service advertisement/browsing.
- Broadcast "is anyone there?" and collect replies? Use `UdpSocket` with `255.255.255.255` broadcast.
- Need multicast (group messaging, not broadcast to all)? Use `socket2` to join the multicast group.
- Device exposes WebSocket? Use `tokio-tungstenite`.

---

## Section 2: TCP Communication

### Async TCP client in Tauri command

```rust
use tokio::net::TcpStream;
use tokio::io::{AsyncReadExt, AsyncWriteExt};

#[tauri::command]
pub async fn tcp_send_command(
    host: String,
    port: u16,
    message: String,
) -> Result<String, String> {
    let addr = format!("{}:{}", host, port);
    let mut stream = TcpStream::connect(&addr)
        .await
        .map_err(|e| format!("Connect failed: {e}"))?;

    // Length-prefix framing: write 4-byte big-endian length, then payload
    let payload = message.as_bytes();
    let len = (payload.len() as u32).to_be_bytes();
    stream.write_all(&len).await.map_err(|e| e.to_string())?;
    stream.write_all(payload).await.map_err(|e| e.to_string())?;

    // Read response (same framing)
    let mut len_buf = [0u8; 4];
    stream.read_exact(&mut len_buf).await.map_err(|e| e.to_string())?;
    let resp_len = u32::from_be_bytes(len_buf) as usize;

    let mut resp_buf = vec![0u8; resp_len];
    stream.read_exact(&mut resp_buf).await.map_err(|e| e.to_string())?;

    String::from_utf8(resp_buf).map_err(|e| e.to_string())
}
```

### TCP framing protocols

| Protocol | Description | Use When |
|---------|-------------|----------|
| Length-prefix | 4-byte big-endian length before each message | Binary or JSON, variable-length messages |
| Newline-delimited JSON | Each JSON object ends with `\n` | Human-readable, simple devices |
| Fixed-size frames | Each message is exactly N bytes | Known device protocol with fixed format |
| HTTP-style | `Content-Length` header then body | REST-like protocols |

### Newline-delimited JSON (JSON Lines)

```rust
use tokio::io::{AsyncBufReadExt, BufReader};

#[tauri::command]
pub async fn tcp_json_rpc(host: String, port: u16, cmd: serde_json::Value) -> Result<serde_json::Value, String> {
    let stream = TcpStream::connect(format!("{}:{}", host, port))
        .await
        .map_err(|e| e.to_string())?;
    let (reader, mut writer) = stream.into_split();
    let mut reader = BufReader::new(reader);

    // Write JSON line
    let mut line = serde_json::to_string(&cmd).map_err(|e| e.to_string())?;
    line.push('\n');
    writer.write_all(line.as_bytes()).await.map_err(|e| e.to_string())?;

    // Read response line
    let mut response = String::new();
    reader.read_line(&mut response).await.map_err(|e| e.to_string())?;
    serde_json::from_str(&response).map_err(|e| e.to_string())
}
```

### Keep-alive with tokio interval

```rust
use tokio::time::{interval, Duration};

// Run as background task — see Section 6 for spawn pattern
async fn keepalive_loop(mut stream: TcpStream) {
    let mut ticker = interval(Duration::from_secs(30));
    loop {
        ticker.tick().await;
        let ping = b"\x00\x00\x00\x04ping";  // length-prefixed "ping"
        if stream.write_all(ping).await.is_err() {
            break; // connection lost
        }
    }
}
```

---

## Section 3: UDP Communication

### Broadcast discovery — send to 255.255.255.255, collect replies

```rust
use tokio::net::UdpSocket;
use tokio::time::{timeout, Duration};

const DISCOVERY_PORT: u16 = 54321;

#[tauri::command]
pub async fn udp_discover_devices() -> Result<Vec<String>, String> {
    let socket = UdpSocket::bind("0.0.0.0:0").await.map_err(|e| e.to_string())?;
    socket.set_broadcast(true).map_err(|e| e.to_string())?;

    // Send discovery packet
    let packet = b"{\"type\":\"discover\",\"app\":\"myapp\"}";
    socket.send_to(packet, format!("255.255.255.255:{DISCOVERY_PORT}"))
        .await
        .map_err(|e| e.to_string())?;

    // Collect responses with 2-second timeout
    let mut devices = Vec::new();
    let mut buf = [0u8; 1024];

    let collect = async {
        loop {
            match socket.recv_from(&mut buf).await {
                Ok((len, addr)) => {
                    if let Ok(text) = std::str::from_utf8(&buf[..len]) {
                        devices.push(format!("{}: {}", addr.ip(), text));
                    }
                }
                Err(_) => break,
            }
        }
    };

    // Stop collecting after 2 seconds
    let _ = timeout(Duration::from_secs(2), collect).await;
    Ok(devices)
}
```

### Multicast group management (socket2)

```rust
use socket2::{Domain, Protocol, Socket, Type};
use std::net::{Ipv4Addr, SocketAddrV4};

fn create_multicast_socket(multicast_addr: Ipv4Addr, port: u16) -> std::io::Result<std::net::UdpSocket> {
    let socket = Socket::new(Domain::IPV4, Type::DGRAM, Some(Protocol::UDP))?;

    socket.set_reuse_address(true)?;
    socket.bind(&SocketAddrV4::new(Ipv4Addr::UNSPECIFIED, port).into())?;

    // Join multicast group on all interfaces
    socket.join_multicast_v4(&multicast_addr, &Ipv4Addr::UNSPECIFIED)?;
    socket.set_multicast_loop_v4(false)?;  // don't receive own packets
    socket.set_multicast_ttl_v4(1)?;       // LAN only (TTL 1)

    Ok(socket.into())
}
```

### Datagram size limits

- Practical limit: **1400 bytes** (stays under Ethernet MTU of 1500 minus headers)
- Theoretical UDP max: 65507 bytes, but fragmentation and packet loss risk increases above 1400
- For discovery packets: keep under 512 bytes — routers/switches handle these reliably
- For larger payloads: use UDP to discover, then establish TCP for the actual transfer

---

## Section 4: mDNS/DNS-SD

mDNS allows devices on the same LAN to discover each other by service type without a central DNS server. Devices broadcast their services as `_servicetype._tcp.local.`.

### Register your app as a service (advertise)

```rust
use mdns_sd::{ServiceDaemon, ServiceInfo};
use std::collections::HashMap;

fn start_mdns_service(port: u16) -> Result<ServiceDaemon, String> {
    let mdns = ServiceDaemon::new().map_err(|e| e.to_string())?;

    let mut properties = HashMap::new();
    properties.insert("version".to_string(), "1.0".to_string());
    properties.insert("platform".to_string(), "tauri".to_string());

    let service = ServiceInfo::new(
        "_myapp._tcp.local.",   // service type
        "MyApp-Device-1",       // instance name (must be unique on LAN)
        "hostname.local.",      // hostname
        "192.168.1.100",        // IP address — use actual interface IP
        port,
        Some(properties),
    )
    .map_err(|e| e.to_string())?;

    mdns.register(service).map_err(|e| e.to_string())?;
    Ok(mdns) // keep alive — dropping daemon unregisters the service
}
```

### Browse for services (discover devices)

```rust
use mdns_sd::{ServiceDaemon, ServiceEvent};
use tauri::{AppHandle, Emitter};

pub async fn browse_mdns(app: AppHandle) -> Result<(), String> {
    let mdns = ServiceDaemon::new().map_err(|e| e.to_string())?;
    let receiver = mdns.browse("_myapp._tcp.local.").map_err(|e| e.to_string())?;

    while let Ok(event) = receiver.recv() {
        match event {
            ServiceEvent::ServiceResolved(info) => {
                // Found a device — emit to frontend
                let device = serde_json::json!({
                    "name": info.get_fullname(),
                    "ip": info.get_addresses().iter().next().map(|a| a.to_string()),
                    "port": info.get_port(),
                    "properties": info.get_properties()
                        .iter()
                        .map(|p| (p.key().to_string(), p.val_str().to_string()))
                        .collect::<std::collections::HashMap<_,_>>()
                });
                app.emit("mdns-device-found", device).ok();
            }
            ServiceEvent::ServiceRemoved(_, fullname) => {
                app.emit("mdns-device-lost", fullname).ok();
            }
            _ => {}
        }
    }
    Ok(())
}
```

### mDNS daemon lifecycle

- One `ServiceDaemon` per app — create once, share via Tauri state
- Dropping the daemon stops all browsing and unregisters all services
- `browse()` returns a channel receiver — can be polled async or in a thread
- Multiple `browse()` calls on the same daemon are fine — each gets its own channel

---

## Section 5: Device Discovery Patterns

### Combined discovery: mDNS + UDP broadcast

```rust
use tauri::{AppHandle, Emitter};

#[derive(Clone, serde::Serialize)]
pub struct DeviceInfo {
    pub id: String,
    pub name: String,
    pub ip: String,
    pub port: u16,
    pub device_type: String,
    pub capabilities: Vec<String>,
    pub last_seen: u64, // Unix timestamp ms
}
```

Recommended flow:
1. Start mDNS browse on app launch — passive, catches any device that advertises
2. Fire UDP broadcast on user-triggered "scan" — active, catches devices not using mDNS
3. Merge results by device ID (from a TXT record or response field)
4. Track `last_seen` timestamp — devices not heard from in 30s are marked offline

### Online/offline status tracking

```rust
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::time::{interval, Duration};

fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_millis() as u64
}

// Heartbeat check — run in background task (see Section 6)
async fn check_device_health(app: AppHandle, devices: Arc<Mutex<HashMap<String, DeviceInfo>>>) {
    let mut ticker = interval(Duration::from_secs(10));
    loop {
        ticker.tick().await;
        let now = now_ms();
        let mut map = devices.lock().unwrap();
        for (id, device) in map.iter_mut() {
            let age_ms = now - device.last_seen;
            let status = if age_ms < 30_000 { "online" } else { "offline" };
            app.emit("device-status", serde_json::json!({"id": id, "status": status})).ok();
        }
    }
}
```

---

## Section 6: Tauri Integration

### Long-running background tasks

```rust
use tauri::Manager;

pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let app_handle = app.handle().clone();

            // Spawn background mDNS browse — runs for app lifetime
            tauri::async_runtime::spawn(async move {
                if let Err(e) = browse_mdns(app_handle).await {
                    eprintln!("mDNS browse error: {e}");
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            tcp_send_command,
            udp_discover_devices,
        ])
        .run(tauri::generate_context!())
        .expect("error running tauri");
}
```

### Managing connections in Tauri state

```rust
use std::collections::HashMap;
use std::sync::Mutex;
use tokio::net::TcpStream;

pub struct ConnectionManager(pub Mutex<HashMap<String, TcpStream>>);

// Register in builder:
// .manage(ConnectionManager(Mutex::new(HashMap::new())))

#[tauri::command]
pub async fn connect_device(
    id: String,
    host: String,
    port: u16,
    state: tauri::State<'_, ConnectionManager>,
) -> Result<(), String> {
    let stream = TcpStream::connect(format!("{}:{}", host, port))
        .await
        .map_err(|e| e.to_string())?;
    state.0.lock().unwrap().insert(id, stream);
    Ok(())
}
```

### Forwarding discovered devices to frontend

```rust
// In any async context with AppHandle:
app.emit("device-discovered", &device_info).ok();
app.emit("device-lost", &device_id).ok();
app.emit("device-status-changed", serde_json::json!({"id": id, "online": true})).ok();
```

```svelte
<!-- Svelte side — listen for events -->
<script>
  import { listen } from '@tauri-apps/api/event';
  import { onDestroy } from 'svelte';

  let devices = $state([]);

  const unlisten = listen('device-discovered', (event) => {
    const dev = event.payload;
    devices = [...devices.filter(d => d.id !== dev.id), dev];
  });

  const unlistenLost = listen('device-lost', (event) => {
    devices = devices.filter(d => d.id !== event.payload);
  });

  onDestroy(async () => {
    (await unlisten)();
    (await unlistenLost)();
  });
</script>
```

---

## Section 7: Cross-Platform Network Notes

### Windows

- **Windows Defender Firewall prompt**: On first TCP `listen()` or UDP bind to a non-loopback address, Windows shows a firewall dialog. The app needs to handle the "blocked" case gracefully.
- Accept the prompt or pre-configure with `netsh advfirewall firewall` in the installer.
- UDP broadcast (`255.255.255.255`) usually works without a firewall rule.

### macOS

- **App Sandbox entitlements** — required in `src-tauri/entitlements.mac.plist`:

```xml
<key>com.apple.security.network.client</key>
<true/>
<key>com.apple.security.network.server</key>
<true/>
```

- **Sonoma (macOS 14+) local network permission**: The OS shows a dialog "MyApp would like to find devices on your local network." This fires when the app first accesses multicast or mDNS. Add `NSLocalNetworkUsageDescription` to `Info.plist`:

```xml
<key>NSLocalNetworkUsageDescription</key>
<string>MyApp discovers other instances of the app running on your local network.</string>
```

- **mDNS on macOS**: `mdns-sd` uses the standard multicast groups that macOS allows. No special entitlement needed beyond `network.client`.

### Linux

- No special permissions for user-space networking (TCP, UDP, mDNS multicast).
- If the app needs raw sockets or ICMP (ping), it needs `CAP_NET_RAW` or run as root — avoid this.
- Firewall (ufw/iptables): users may need to open ports if they have restrictive firewall rules.

---

## Additional Resources

- [lan-reference.md](lan-reference.md) — Complete working code examples: TCP client with reconnect, UDP broadcast discovery, full mDNS service registration/browse, WebSocket from Rust, Svelte device browser component, multi-connection manager, and error handling patterns

---
name: core-embedded:comm-protocols
description: "Embedded communication protocols — SPI, I2C, UART, CAN bus, BLE concepts, and constrained-device networking (CoAP, MQTT-SN, LwM2M)"
user-invocable: false
---

# Communication Protocols Quick Reference

## Protocol Selection Guide

| Protocol | Speed | Distance | Wires | Topology | Best For |
|----------|-------|----------|-------|----------|----------|
| SPI | 1-100+ MHz | < 1 m | 4+ | Star | High-speed peripherals (flash, display, ADC) |
| I2C | 100-3400 kHz | < 1 m | 2 | Bus | Sensors, EEPROMs, low-pin-count devices |
| UART | 9600-3M baud | < 15 m | 2-3 | Point-to-point | Debug console, GPS, modems |
| CAN | 125K-1M bps | < 40 m (1M) | 2 | Bus | Automotive, industrial, multi-node |
| BLE | 1-2 Mbps | < 100 m | Radio | Star/mesh | Wearables, sensors, mobile connectivity |

## SPI (Serial Peripheral Interface)

4-wire interface: SCLK (clock), MOSI (data out), MISO (data in), CS (chip select, active low). One CS per peripheral.

**Modes**: Defined by CPOL (clock idle level) and CPHA (data sample edge). Mode 0 (CPOL=0, CPHA=0, sample on rising) is most common. Always check peripheral datasheet.

**Best practices**: Assert CS before clock, deassert after. Use DMA for large transfers. Keep traces short at high speeds. Watch CS setup/hold timing.

## I2C (Inter-Integrated Circuit)

2-wire bus (SDA data, SCL clock), both open-drain with pull-ups. Multiple devices share the bus, each with a unique 7-bit address (0x08-0x77). Speeds: Standard (100 kHz), Fast (400 kHz), Fast Plus (1 MHz).

**Transaction**: START, address+R/W, ACK, data bytes, STOP. Use repeated START for atomic register reads.

**Best practices**: Pull-ups 2.2-10k (speed-dependent). Bus capacitance < 400 pF. Implement bus recovery (toggle SCL 9x if SDA stuck). Scan for devices before assuming connectivity.

## UART (Universal Asynchronous Receiver-Transmitter)

Point-to-point: TX crosses to RX. Frame: start bit, 8 data bits, optional parity, 1-2 stop bits. Common baud rates: 9600, 115200. Both sides must match exactly (2-3% mismatch causes errors).

**Flow control**: None (simplest), Hardware RTS/CTS (most reliable), Software XON/XOFF (cannot use with binary data).

**Best practices**: Use DMA or interrupt-driven RX (never poll). Implement framing protocol for binary data (sync, length, CRC). Consider RS-485 for multi-drop or long-distance.

## CAN Bus

Differential two-wire bus (CAN_H, CAN_L) with built-in arbitration, error detection, and multi-master capability. Frames carry 11 or 29-bit IDs and 0-8 bytes data (CAN FD: up to 64 bytes). Lower ID wins arbitration (higher priority). Messages are broadcast; nodes filter by ID.

**Best practices**: Assign IDs by priority (lower = more urgent). Terminate both bus ends with 120 ohm. Respect length limits (40m at 1 Mbps, 500m at 125 kbps). Monitor error counters for bus health.

## BLE (Bluetooth Low Energy)

### GAP Roles

| Role | Description |
|------|-------------|
| Broadcaster | Sends advertising packets only (beacon) |
| Observer | Scans for advertisements only |
| Peripheral | Advertises, accepts connections, acts as GATT server |
| Central | Scans, initiates connections, acts as GATT client |

### GATT Data Model

Hierarchical: Profile -> Service (UUID) -> Characteristic (UUID) -> Value + Descriptors. The CCCD descriptor enables notifications/indications.

### Key Parameters

- **Advertising interval**: 20 ms - 10.24 s (longer = less power, slower discovery)
- **Connection interval**: 7.5 ms - 4 s (longer = less power)
- **Slave latency**: 0-499 events (peripheral can skip events when idle)

**Power tips**: Maximize connection interval, use slave latency, batch data, prefer non-connectable advertising for beacons.

## Constrained-Device Networking

IoT protocol stack: Link (802.15.4, BLE, LoRa) -> Network (IPv6/6LoWPAN) -> Transport (UDP preferred) -> Application (CoAP, MQTT-SN, LwM2M).

- **CoAP**: REST-like over UDP, 4-byte header, confirmable messages for reliability, Observe for push, DTLS for security
- **MQTT-SN**: MQTT over UDP, numeric topic IDs, sleeping client support, QoS -1 fire-and-forget
- **LwM2M**: Device management on CoAP, standard object model, built-in FOTA support

| Criterion | CoAP | MQTT-SN | LwM2M | HTTP |
|-----------|------|---------|-------|------|
| Header overhead | 4 bytes | 2 bytes | 4 bytes | 200+ bytes |
| RAM required | 2-5 KB | 2-5 KB | 5-15 KB | 10-30 KB |
| Best for | REST APIs | Pub/sub | Fleet mgmt | Cloud APIs |

## Additional Resources

- For detailed protocol timing diagrams, error handling, and advanced configuration, see [protocols-reference.md](protocols-reference.md)

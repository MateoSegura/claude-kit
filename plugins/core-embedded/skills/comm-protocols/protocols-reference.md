# Communication Protocols — Complete Reference

## SPI Advanced Topics

### Multi-Slave Configuration

```
Controller
  SCLK ──┬──────┬──────┬──
  MOSI ──┬┤─────┬┤─────┬┤──
  MISO ──┼┤─────┼┤─────┼┤──  (active-low CS selects one at a time)
  CS0  ──┘      │      │
  CS1  ─────────┘      │
  CS2  ─────────────────┘
```

Rules:
- Only assert one CS at a time
- Deassert all CS before asserting a different one
- Some peripherals need CS deasserted between transactions (check datasheet)
- Share SCLK/MOSI/MISO but use separate CS per peripheral

### SPI Timing Parameters

```
           CS assert
               |
    ___________V_________
CS  ‾‾‾|                |‾‾‾‾‾‾
       |                |
       |<-- t_su_cs --->|  CS setup time before first clock
       |                |
CLK ___/‾\_/‾\_/‾\_/‾\__|___
       |  |  |  |  |  |
MOSI  X|D7|D6|D5|D4|D3|X
       |                |<-- t_hd_cs -->|  CS hold time after last clock
```

Important timing values (check datasheet):
- `t_su_cs`: CS setup time before first clock edge (typically 10-100 ns)
- `t_hd_cs`: CS hold time after last clock edge (typically 10-100 ns)
- `t_clk`: Minimum clock period (determines max frequency)
- `t_su_data`: Data setup time before sampling edge
- `t_hd_data`: Data hold time after sampling edge

### SPI DMA Best Practices

```c
/* Full-duplex SPI with DMA (pseudo-code) */

/* TX DMA: memory → SPI TX register */
dma_configure(DMA_TX, &tx_buffer, &SPI->DR, length, MEM_TO_PERIPH);

/* RX DMA: SPI RX register → memory */
dma_configure(DMA_RX, &SPI->DR, &rx_buffer, length, PERIPH_TO_MEM);

/* Start RX DMA first (ready to receive before TX starts) */
dma_start(DMA_RX);
dma_start(DMA_TX);

/* Wait for completion */
dma_wait_complete(DMA_RX);
```

Key: start RX DMA before TX DMA to avoid missing received bytes.

## I2C Advanced Topics

### Multi-Master Arbitration

If two masters start simultaneously:
1. Both drive SDA and monitor the bus
2. If a master sends HIGH but reads LOW, it loses arbitration
3. Losing master immediately releases the bus
4. Winning master continues unaware

### Bus Recovery Sequence

When a slave holds SDA low (e.g., after interrupted transfer):

```c
void i2c_bus_recovery(void) {
    /* Configure SCL as GPIO output, SDA as GPIO input */
    gpio_set_output(SCL_PIN);
    gpio_set_input(SDA_PIN);

    /* Toggle SCL up to 9 times */
    for (int i = 0; i < 9; i++) {
        if (gpio_read(SDA_PIN) == 1) break;  /* SDA released */
        gpio_write(SCL_PIN, 1);
        delay_us(5);
        gpio_write(SCL_PIN, 0);
        delay_us(5);
    }

    /* Generate STOP condition */
    gpio_write(SDA_PIN, 0);
    gpio_write(SCL_PIN, 1);
    delay_us(5);
    gpio_write(SDA_PIN, 1);  /* SDA rising while SCL high = STOP */

    /* Reconfigure pins for I2C peripheral */
    i2c_pin_init();
}
```

### I2C Address Scanner

```c
void i2c_scan(void) {
    for (uint8_t addr = 0x08; addr < 0x78; addr++) {
        /* Send START + address + R/W, check for ACK */
        if (i2c_probe(addr) == 0) {
            printf("Device found at 0x%02X\n", addr);
        }
    }
}
```

### Pull-Up Resistor Selection

```
R_pullup = V_dd / I_sink_max    (minimum, for speed)
R_pullup = t_rise / (0.8473 * C_bus)  (maximum, for timing)

Typical values:
  Standard mode (100 kHz): 4.7k - 10k ohm
  Fast mode (400 kHz):     2.2k - 4.7k ohm
  Fast mode+ (1 MHz):      1k - 2.2k ohm

Bus capacitance estimate:
  Each device: 5-10 pF
  PCB trace:   1-2 pF per cm
  Connector:   5-10 pF
```

## UART Advanced Topics

### Framing Protocol Design

For reliable binary communication over UART:

```
+------+--------+------+------+------+------+------+
| SYNC | LENGTH | CMD  | SEQ  | DATA | CRC  | END  |
| 0xA5 | 1 byte | 1 B  | 1 B  | N B  | 2 B  | 0x5A |
+------+--------+------+------+------+------+------+
```

```c
struct frame {
    uint8_t sync;       /* 0xA5 start marker */
    uint8_t length;     /* Total frame length */
    uint8_t command;    /* Command ID */
    uint8_t sequence;   /* Sequence number for ack/retry */
    uint8_t data[];     /* Variable payload */
    /* uint16_t crc;    -- follows data */
    /* uint8_t end;     -- 0x5A end marker */
};
```

### UART State Machine Parser

```c
typedef enum {
    PARSE_SYNC,
    PARSE_LENGTH,
    PARSE_PAYLOAD,
    PARSE_CRC,
} parse_state_t;

static parse_state_t state = PARSE_SYNC;
static uint8_t frame_buf[MAX_FRAME];
static uint8_t frame_idx;
static uint8_t expected_len;

void uart_rx_byte(uint8_t byte) {
    switch (state) {
    case PARSE_SYNC:
        if (byte == 0xA5) {
            frame_idx = 0;
            frame_buf[frame_idx++] = byte;
            state = PARSE_LENGTH;
        }
        break;
    case PARSE_LENGTH:
        expected_len = byte;
        frame_buf[frame_idx++] = byte;
        if (expected_len > MAX_FRAME || expected_len < MIN_FRAME) {
            state = PARSE_SYNC;  /* Invalid length */
        } else {
            state = PARSE_PAYLOAD;
        }
        break;
    case PARSE_PAYLOAD:
        frame_buf[frame_idx++] = byte;
        if (frame_idx >= expected_len) {
            if (verify_crc(frame_buf, expected_len)) {
                process_frame(frame_buf, expected_len);
            }
            state = PARSE_SYNC;
        }
        break;
    }
}
```

### RS-485 Half-Duplex

```
Node A          RS-485 Bus          Node B
  TX/RX ─────── A (+) ─────────── TX/RX
  DE/RE ─────── B (-) ─────────── DE/RE
                 |
               120 ohm (termination)
```

```c
/* TX: enable driver, send data, disable driver */
void rs485_transmit(uint8_t *data, size_t len) {
    gpio_set(DE_PIN, 1);     /* Enable driver (DE) */
    gpio_set(RE_PIN, 1);     /* Disable receiver (RE, active low) */
    uart_send(data, len);
    uart_wait_tx_complete();
    gpio_set(DE_PIN, 0);     /* Disable driver */
    gpio_set(RE_PIN, 0);     /* Enable receiver */
}
```

## CAN Bus Advanced Topics

### Message Priority and ID Allocation

| ID Range | Priority | Usage |
|----------|----------|-------|
| 0x000-0x0FF | Highest | Safety-critical (emergency stop, fault) |
| 0x100-0x1FF | High | Real-time control (motor commands, sensor data) |
| 0x200-0x3FF | Medium | Status and telemetry |
| 0x400-0x5FF | Low | Configuration and diagnostics |
| 0x600-0x7FF | Lowest | Node management, heartbeat |

### Error Handling

CAN nodes maintain error counters:

```
Transmit Error Counter (TEC):
  +8 on transmit error
  -1 on successful transmit

Receive Error Counter (REC):
  +1 to +8 on receive error (depends on type)
  -1 on successful receive

State transitions:
  Error Active  (TEC < 128, REC < 128) → normal operation
  Error Passive (TEC >= 128 or REC >= 128) → can still send, with restrictions
  Bus Off       (TEC >= 256) → disconnected, must recover
```

### CAN FD (Flexible Data Rate)

Extensions over classic CAN:

| Feature | Classic CAN | CAN FD |
|---------|-------------|--------|
| Data payload | 0-8 bytes | 0-64 bytes |
| Bit rate (arbitration) | Up to 1 Mbps | Up to 1 Mbps |
| Bit rate (data) | Same | Up to 8 Mbps |
| CRC | 15-bit | 17-bit or 21-bit |

## BLE Advanced Topics

### Advertising Optimization

```
Non-connectable, non-scannable (beacon):
  Lowest power, broadcast only, 3 channels
  Interval: 100 ms - 10.24 s

Connectable, undirected:
  Most common, allows central to connect
  Interval: 20 ms - 10.24 s
  Power: moderate (listening for connection requests)

Directed advertising:
  Targets specific central, fastest connection
  High-duty: 3.75 ms interval, max 1.28 s duration
  Low-duty: normal interval range
```

### Connection Parameter Negotiation

After connection, peripheral can request parameter update:

```c
/* Request parameters (pseudo-code) */
struct conn_params {
    uint16_t min_interval;   /* In units of 1.25 ms */
    uint16_t max_interval;   /* 7.5 ms to 4 s */
    uint16_t slave_latency;  /* 0 to 499 */
    uint16_t sup_timeout;    /* In units of 10 ms, 100 ms to 32 s */
};

/* Low power profile: 1s interval, skip 4 events */
struct conn_params low_power = {
    .min_interval = 800,    /* 1000 ms */
    .max_interval = 800,
    .slave_latency = 4,     /* Can skip 4 events */
    .sup_timeout = 600,     /* 6 s supervision timeout */
};

/* Low latency profile: 15ms interval, no skipping */
struct conn_params low_latency = {
    .min_interval = 12,     /* 15 ms */
    .max_interval = 12,
    .slave_latency = 0,
    .sup_timeout = 200,     /* 2 s */
};
```

### GATT Database Design

```
Service: Environmental Sensing (0x181A)
├── Characteristic: Temperature (0x2A6E)
│   ├── Properties: Read, Notify
│   ├── Value: int16_t (0.01 C resolution)
│   └── CCCD: Client Characteristic Configuration
├── Characteristic: Humidity (0x2A6F)
│   ├── Properties: Read, Notify
│   ├── Value: uint16_t (0.01% resolution)
│   └── CCCD
└── Characteristic: Pressure (0x2A6D)
    ├── Properties: Read
    └── Value: uint32_t (0.1 Pa resolution)

Custom Service: Device Control (128-bit UUID)
├── Characteristic: Command (write)
├── Characteristic: Status (read, notify)
└── Characteristic: Config (read, write)
```

### BLE Security

| Level | Name | Protection |
|-------|------|-----------|
| 1 | No security | No encryption, no authentication |
| 2 | Unauthenticated | Encryption (Just Works pairing) |
| 3 | Authenticated | Encryption + MITM protection (passkey/OOB) |
| 4 | Authenticated LE Secure | LESC with numeric comparison or OOB |

## Constrained Networking Details

### CoAP Message Format

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Ver| T |  TKL  |     Code      |         Message ID            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   Token (if any, TKL bytes) ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   Options (if any) ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|1 1 1 1 1 1 1 1|    Payload (if any) ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- 4-byte fixed header (vs HTTP minimum ~200 bytes)
- Token: 0-8 bytes for request/response matching
- Type: CON (confirmable), NON (non-confirmable), ACK, RST

### CoAP Observe Pattern

Server push for resource monitoring:

```
Client                      Server
  |--- GET /temp (Observe:0) --->|   Register observer
  |<-- 2.05 Content (22.5 C) ---|   Immediate response
  |                              |   ... time passes ...
  |<-- 2.05 Content (23.0 C) ---|   Push notification
  |<-- 2.05 Content (22.8 C) ---|   Push notification
  |--- RST ---------------------->|   Cancel observation
```

### LwM2M Object Model

Standard objects for device management:

| Object | ID | Description |
|--------|----|-------------|
| LwM2M Security | 0 | Bootstrap/server credentials |
| LwM2M Server | 1 | Server registration settings |
| Access Control | 2 | Per-object access rights |
| Device | 3 | Manufacturer, model, serial, battery |
| Connectivity | 4 | Network bearer information |
| Firmware Update | 5 | FOTA management |
| Location | 6 | GPS coordinates |
| Temperature | 3303 | Temperature sensor |
| Humidity | 3304 | Humidity sensor |
| Accelerometer | 3313 | Accelerometer |

### 6LoWPAN Header Compression

IPv6 header compression for IEEE 802.15.4:

```
Full IPv6 header:     40 bytes
6LoWPAN compressed:   2-7 bytes (typical)

Compression ratio:    80-95% header reduction
```

Techniques:
- Elide fields derivable from link-layer (addresses)
- Compress common traffic class and flow label values
- Context-based address compression for known prefixes

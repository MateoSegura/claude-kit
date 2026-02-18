---
name: networking-protocols
description: Zephyr networking protocols — BLE, MQTT, CoAP, HTTP, sockets API, TLS/DTLS configuration and secure communication patterns
user-invocable: false
---

# Networking Protocols Quick Reference

## Protocol Selection Guide

| Protocol | Use Case | Transport | Overhead | Security |
|----------|----------|-----------|----------|----------|
| **BLE** | Low-power sensors, wearables | BLE radio | Low | BLE Security Manager |
| **MQTT** | IoT telemetry, pub/sub | TCP | Medium | TLS 1.2/1.3 |
| **CoAP** | Constrained devices, REST-like | UDP | Low | DTLS 1.2 |
| **HTTP** | Web APIs, cloud services | TCP | High | TLS 1.2/1.3 |
| **Sockets** | Custom protocols | TCP/UDP | Minimal | TLS/DTLS optional |

## BLE Quick Start

### Minimal Peripheral

```c
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/gap.h>

static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
    BT_DATA_BYTES(BT_DATA_UUID16_ALL, BT_UUID_16_ENCODE(BT_UUID_DIS_VAL)),
};

void main(void) {
    int err = bt_enable(NULL);
    if (err) {
        printk("BLE init failed: %d\n", err);
        return;
    }

    err = bt_le_adv_start(BT_LE_ADV_CONN_NAME, ad, ARRAY_SIZE(ad), NULL, 0);
    if (err) {
        printk("Advertising failed: %d\n", err);
    }
}
```

**Kconfig:**

```kconfig
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
CONFIG_BT_DEVICE_NAME="MyDevice"
```

### GATT Service

```c
#include <zephyr/bluetooth/gatt.h>

static uint8_t sensor_value = 0;

static ssize_t read_sensor(struct bt_conn *conn, const struct bt_gatt_attr *attr,
                           void *buf, uint16_t len, uint16_t offset)
{
    return bt_gatt_attr_read(conn, attr, buf, len, offset, &sensor_value, sizeof(sensor_value));
}

BT_GATT_SERVICE_DEFINE(sensor_svc,
    BT_GATT_PRIMARY_SERVICE(BT_UUID_DECLARE_16(0x1234)),
    BT_GATT_CHARACTERISTIC(BT_UUID_DECLARE_16(0x5678),
                           BT_GATT_CHRC_READ | BT_GATT_CHRC_NOTIFY,
                           BT_GATT_PERM_READ, read_sensor, NULL, NULL),
);
```

## MQTT Quick Start

```c
#include <zephyr/net/mqtt.h>
#include <zephyr/net/socket.h>

static struct mqtt_client client;
static struct sockaddr_storage broker;
static uint8_t rx_buffer[256];
static uint8_t tx_buffer[256];

void mqtt_event_handler(struct mqtt_client *c, const struct mqtt_evt *evt)
{
    switch (evt->type) {
    case MQTT_EVT_CONNACK:
        printk("Connected to broker\n");
        break;
    case MQTT_EVT_PUBLISH:
        printk("Received: %.*s\n", evt->param.publish.message.payload.len,
               evt->param.publish.message.payload.data);
        break;
    default:
        break;
    }
}

void init_mqtt(void)
{
    struct sockaddr_in *broker4 = (struct sockaddr_in *)&broker;
    broker4->sin_family = AF_INET;
    broker4->sin_port = htons(1883);
    inet_pton(AF_INET, "192.168.1.100", &broker4->sin_addr);

    mqtt_client_init(&client);
    client.broker = &broker;
    client.evt_cb = mqtt_event_handler;
    client.client_id.utf8 = "zephyr_client";
    client.client_id.size = strlen("zephyr_client");
    client.rx_buf = rx_buffer;
    client.rx_buf_size = sizeof(rx_buffer);
    client.tx_buf = tx_buffer;
    client.tx_buf_size = sizeof(tx_buffer);

    mqtt_connect(&client);
}
```

**Kconfig:**

```kconfig
CONFIG_NETWORKING=y
CONFIG_NET_SOCKETS=y
CONFIG_MQTT_LIB=y
```

## CoAP Quick Start

```c
#include <zephyr/net/coap.h>

static struct coap_resource resources[] = {
    { .path = COAP_WELL_KNOWN_CORE_PATH,
      .get = well_known_core_get },
    { .path = (const char * const[]){ "sensor", NULL },
      .get = sensor_get },
};

static int sensor_get(struct coap_resource *resource,
                      struct coap_packet *request,
                      struct sockaddr *addr, socklen_t addr_len)
{
    struct coap_packet response;
    uint8_t payload[32];
    int r;

    r = coap_packet_init(&response, data, sizeof(data),
                         COAP_VERSION_1, COAP_TYPE_ACK,
                         COAP_TOKEN_MAX_LEN, coap_header_get_token(request),
                         COAP_RESPONSE_CODE_CONTENT,
                         coap_header_get_id(request));
    if (r < 0) return r;

    r = snprintf(payload, sizeof(payload), "value=%d", sensor_value);
    r = coap_packet_append_payload_marker(&response);
    r = coap_packet_append_payload(&response, payload, r);

    return sendto(sock, response.data, response.offset, 0, addr, addr_len);
}
```

**Kconfig:**

```kconfig
CONFIG_COAP=y
CONFIG_NET_UDP=y
```

## Sockets API

### TCP Client

```c
#include <zephyr/net/socket.h>

int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

struct sockaddr_in addr;
addr.sin_family = AF_INET;
addr.sin_port = htons(8080);
inet_pton(AF_INET, "192.168.1.100", &addr.sin_addr);

if (connect(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
    printk("Connect failed\n");
    close(sock);
    return;
}

const char *msg = "Hello";
send(sock, msg, strlen(msg), 0);

char buf[128];
ssize_t len = recv(sock, buf, sizeof(buf), 0);

close(sock);
```

### UDP Server

```c
int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

struct sockaddr_in addr;
addr.sin_family = AF_INET;
addr.sin_port = htons(1234);
addr.sin_addr.s_addr = INADDR_ANY;

bind(sock, (struct sockaddr *)&addr, sizeof(addr));

while (1) {
    char buf[512];
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);

    ssize_t len = recvfrom(sock, buf, sizeof(buf), 0,
                           (struct sockaddr *)&client_addr, &client_len);
    if (len > 0) {
        sendto(sock, buf, len, 0,
               (struct sockaddr *)&client_addr, client_len);
    }
}
```

## TLS/DTLS Configuration

### TLS over TCP

```c
#include <zephyr/net/tls_credentials.h>

/* Register certificate */
static const unsigned char ca_cert[] = {
    #include "ca_cert.pem.inc"
};

void init_tls(void)
{
    tls_credential_add(CA_CERTIFICATE_TAG, TLS_CREDENTIAL_CA_CERTIFICATE,
                       ca_cert, sizeof(ca_cert));
}

/* Create TLS socket */
int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TLS_1_2);

int sec_tag_list[] = { CA_CERTIFICATE_TAG };
setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST, sec_tag_list, sizeof(sec_tag_list));

/* Optional: set hostname for SNI */
setsockopt(sock, SOL_TLS, TLS_HOSTNAME, "example.com", strlen("example.com"));

/* Connect and use as normal TCP socket */
connect(sock, (struct sockaddr *)&addr, sizeof(addr));
```

**Kconfig:**

```kconfig
CONFIG_NET_SOCKETS_SOCKOPT_TLS=y
CONFIG_MBEDTLS=y
CONFIG_MBEDTLS_TLS_VERSION_1_2=y
CONFIG_MBEDTLS_KEY_EXCHANGE_RSA_ENABLED=y
CONFIG_MBEDTLS_CIPHER_AES_ENABLED=y
```

### DTLS over UDP

```c
int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_DTLS_1_2);

int sec_tag_list[] = { PSK_TAG };
setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST, sec_tag_list, sizeof(sec_tag_list));

/* Use as normal UDP socket */
sendto(sock, data, len, 0, (struct sockaddr *)&addr, sizeof(addr));
```

## Protocol Comparison

### Message Size

- **BLE:** 20-244 bytes per packet (ATT MTU dependent)
- **CoAP:** Optimized for small payloads (< 1280 bytes typical)
- **MQTT:** No inherent limit (protocol overhead ~2-10 bytes)
- **HTTP:** No limit (header overhead 200-500 bytes typical)

### Power Consumption

1. **BLE** — Lowest (µA idle, mA active bursts)
2. **CoAP/UDP** — Low (no connection overhead)
3. **MQTT** — Medium (persistent TCP connection)
4. **HTTP** — Highest (TCP + TLS handshake per request)

### Reliability

- **TCP (MQTT, HTTP)** — Guaranteed delivery, ordering
- **UDP (CoAP)** — Best effort, confirmable mode adds retries
- **BLE** — Link-layer retries, connection-oriented

## Additional resources

- For complete protocol API reference, configuration options, and advanced patterns, see [protocol-reference.md](protocol-reference.md)
- For TLS/DTLS certificate management, PSA Crypto integration, and security best practices, see [tls-best-practices.md](tls-best-practices.md)

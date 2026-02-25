# Networking Protocol API — Complete Reference

## BLE API

### Initialization and Advertising

```c
int bt_enable(bt_ready_cb_t cb);
```

**Parameters:**
- `cb` — Callback when BLE stack ready (can be NULL for synchronous init)

**Returns:** `0` on success, negative errno otherwise.

```c
int bt_le_adv_start(const struct bt_le_adv_param *param,
                    const struct bt_data *ad, size_t ad_len,
                    const struct bt_data *sd, size_t sd_len);
```

**Parameters:**
- `param` — Advertising parameters (or use `BT_LE_ADV_CONN_NAME` preset)
- `ad` — Advertising data array
- `ad_len` — Number of AD elements
- `sd` — Scan response data (optional)
- `sd_len` — Number of scan response elements

**Returns:** `0` on success.

### Advertising Data Construction

```c
#define BT_DATA(_type, _data, _data_len) \
    { .type = (_type), .data_len = (_data_len), .data = (_data) }

#define BT_DATA_BYTES(_type, _bytes...) \
    BT_DATA(_type, ((uint8_t []) { _bytes }), sizeof((uint8_t []) { _bytes }))
```

**Common types:**
- `BT_DATA_FLAGS` — Flags (typically `BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR`)
- `BT_DATA_UUID16_ALL` — Complete list of 16-bit UUIDs
- `BT_DATA_UUID128_ALL` — Complete list of 128-bit UUIDs
- `BT_DATA_NAME_COMPLETE` — Complete local name
- `BT_DATA_NAME_SHORTENED` — Shortened local name
- `BT_DATA_MANUFACTURER_DATA` — Manufacturer-specific data

### GATT Service Definition

```c
BT_GATT_SERVICE_DEFINE(service_name,
    BT_GATT_PRIMARY_SERVICE(uuid),
    BT_GATT_CHARACTERISTIC(uuid, properties, permissions, read_cb, write_cb, value),
    BT_GATT_CCC(ccc_cfg_changed, permissions),
);
```

**Characteristic properties:**
- `BT_GATT_CHRC_READ` — Readable
- `BT_GATT_CHRC_WRITE` — Writable
- `BT_GATT_CHRC_WRITE_WITHOUT_RESP` — Write without response
- `BT_GATT_CHRC_NOTIFY` — Notifications
- `BT_GATT_CHRC_INDICATE` — Indications

**Permissions:**
- `BT_GATT_PERM_READ` — Read allowed
- `BT_GATT_PERM_WRITE` — Write allowed
- `BT_GATT_PERM_READ_ENCRYPT` — Require encryption for read
- `BT_GATT_PERM_WRITE_ENCRYPT` — Require encryption for write

### GATT Notifications

```c
int bt_gatt_notify(struct bt_conn *conn, const struct bt_gatt_attr *attr,
                   const void *data, uint16_t len);
```

**Parameters:**
- `conn` — Connection (or NULL for all connections)
- `attr` — Characteristic attribute
- `data` — Notification payload
- `len` — Payload length

**Returns:** `0` on success, negative errno otherwise.

### Connection Callbacks

```c
static void connected(struct bt_conn *conn, uint8_t err)
{
    if (err) {
        printk("Connection failed: %u\n", err);
        return;
    }
    printk("Connected\n");
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
    printk("Disconnected: %u\n", reason);
}

BT_CONN_CB_DEFINE(conn_callbacks) = {
    .connected = connected,
    .disconnected = disconnected,
};
```

## MQTT API

### Client Initialization

```c
void mqtt_client_init(struct mqtt_client *client);
```

Initializes client structure to default values.

### Connection

```c
int mqtt_connect(struct mqtt_client *client);
```

**Prerequisites:**
- `client->broker` — Broker address
- `client->client_id` — Client identifier
- `client->evt_cb` — Event callback
- `client->rx_buf` / `client->rx_buf_size` — Receive buffer
- `client->tx_buf` / `client->tx_buf_size` — Transmit buffer

**Returns:** `0` on success (asynchronous, wait for `MQTT_EVT_CONNACK`).

### Publishing

```c
int mqtt_publish(struct mqtt_client *client, const struct mqtt_publish_param *param);
```

**Structure:**

```c
struct mqtt_publish_param {
    struct mqtt_topic topic;           /* Topic */
    struct mqtt_binstr message;        /* Payload */
    uint16_t message_id;               /* Message ID (auto if 0) */
    enum mqtt_qos qos;                 /* QoS level */
    uint8_t retain_flag;               /* Retain flag */
};
```

**QoS levels:**
- `MQTT_QOS_0_AT_MOST_ONCE` — Fire and forget
- `MQTT_QOS_1_AT_LEAST_ONCE` — Acknowledged
- `MQTT_QOS_2_EXACTLY_ONCE` — Assured delivery

### Subscribing

```c
int mqtt_subscribe(struct mqtt_client *client, const struct mqtt_subscription_list *param);
```

**Structure:**

```c
struct mqtt_subscription_list {
    struct mqtt_topic *list;  /* Array of topics */
    uint16_t list_count;      /* Number of topics */
    uint16_t message_id;      /* Message ID (auto if 0) */
};
```

### Event Handling

```c
void event_handler(struct mqtt_client *client, const struct mqtt_evt *evt)
{
    switch (evt->type) {
    case MQTT_EVT_CONNACK:
        if (evt->result == 0) {
            /* Connected */
        }
        break;
    case MQTT_EVT_PUBLISH:
        /* Received message */
        printk("Topic: %.*s\n", evt->param.publish.message.topic.topic.size,
               evt->param.publish.message.topic.topic.utf8);
        printk("Payload: %.*s\n", evt->param.publish.message.payload.len,
               evt->param.publish.message.payload.data);
        mqtt_publish_qos1_ack(client, &evt->param.publish.message);
        break;
    case MQTT_EVT_DISCONNECT:
        /* Disconnected */
        break;
    }
}
```

### Keep-Alive

```c
int mqtt_live(struct mqtt_client *client);
```

Call periodically (at least every keep-alive interval) to maintain connection.

### Disconnection

```c
int mqtt_disconnect(struct mqtt_client *client);
```

## CoAP API

### Packet Initialization

```c
int coap_packet_init(struct coap_packet *cpkt, uint8_t *data, uint16_t max_len,
                     uint8_t ver, uint8_t type, uint8_t tkl, const uint8_t *token,
                     uint8_t code, uint16_t id);
```

**Type:**
- `COAP_TYPE_CON` — Confirmable
- `COAP_TYPE_NON_CON` — Non-confirmable
- `COAP_TYPE_ACK` — Acknowledgement
- `COAP_TYPE_RESET` — Reset

**Code:** Use `COAP_METHOD_*` for requests, `COAP_RESPONSE_CODE_*` for responses.

### Request Methods

- `COAP_METHOD_GET` — 0.01
- `COAP_METHOD_POST` — 0.02
- `COAP_METHOD_PUT` — 0.03
- `COAP_METHOD_DELETE` — 0.04

### Response Codes

- `COAP_RESPONSE_CODE_OK` — 2.00
- `COAP_RESPONSE_CODE_CREATED` — 2.01
- `COAP_RESPONSE_CODE_CHANGED` — 2.04
- `COAP_RESPONSE_CODE_CONTENT` — 2.05
- `COAP_RESPONSE_CODE_BAD_REQUEST` — 4.00
- `COAP_RESPONSE_CODE_NOT_FOUND` — 4.04

### Adding Options

```c
int coap_packet_append_option(struct coap_packet *cpkt, uint16_t code,
                               const uint8_t *value, uint16_t len);
```

**Common options:**
- `COAP_OPTION_URI_PATH` — URI path segment
- `COAP_OPTION_CONTENT_FORMAT` — Content type
- `COAP_OPTION_OBSERVE` — Observe registration

### Adding Payload

```c
int coap_packet_append_payload_marker(struct coap_packet *cpkt);
int coap_packet_append_payload(struct coap_packet *cpkt, const uint8_t *payload, uint16_t len);
```

Always call `append_payload_marker` before `append_payload`.

### Resource Definition

```c
static int resource_get(struct coap_resource *resource,
                        struct coap_packet *request,
                        struct sockaddr *addr, socklen_t addr_len)
{
    /* Build and send response */
}

static const char * const paths[] = { "sensor", "temp", NULL };

static struct coap_resource resources[] = {
    { .path = paths, .get = resource_get },
};
```

### Observing Resources

```c
int coap_register_observer(struct coap_resource *resource,
                            const struct coap_packet *request,
                            const struct sockaddr *addr);
```

## HTTP Client API

### Request Structure

```c
struct http_request {
    const char *method;             /* "GET", "POST", etc. */
    const char *url;                /* Full URL */
    const char *host;               /* Host header */
    const char *protocol;           /* "HTTP/1.1" */
    const char **header_fields;     /* Optional headers */
    const char *payload;            /* Request body */
    size_t payload_len;             /* Body length */
    http_response_cb_t response;    /* Response callback */
    http_payload_cb_t recv;         /* Payload callback */
};
```

### Sending Request

```c
int http_client_req(int sock, struct http_request *req, int32_t timeout,
                    void *user_data);
```

**Parameters:**
- `sock` — Connected TCP socket
- `req` — Request parameters
- `timeout` — Timeout in milliseconds
- `user_data` — Passed to callbacks

**Returns:** `0` on success.

### Response Callback

```c
void response_cb(struct http_response *rsp, enum http_final_call final_data,
                 void *user_data)
{
    if (final_data == HTTP_DATA_MORE) {
        printk("Partial data: %.*s\n", rsp->data_len, rsp->recv_buf);
    } else if (final_data == HTTP_DATA_FINAL) {
        printk("Final data: %.*s\n", rsp->data_len, rsp->recv_buf);
        printk("HTTP status: %d\n", rsp->http_status_code);
    }
}
```

## Sockets API

### Socket Creation

```c
int socket(int family, int type, int proto);
```

**Family:**
- `AF_INET` — IPv4
- `AF_INET6` — IPv6

**Type:**
- `SOCK_STREAM` — TCP
- `SOCK_DGRAM` — UDP

**Proto:**
- `IPPROTO_TCP` / `IPPROTO_UDP` — Standard
- `IPPROTO_TLS_1_2` / `IPPROTO_DTLS_1_2` — Secure

### Socket Options

```c
int setsockopt(int sock, int level, int optname, const void *optval, socklen_t optlen);
int getsockopt(int sock, int level, int optname, void *optval, socklen_t *optlen);
```

**Common options:**

```c
/* Receive timeout */
struct timeval tv = { .tv_sec = 5, .tv_usec = 0 };
setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

/* Reuse address */
int enable = 1;
setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &enable, sizeof(enable));

/* Non-blocking */
int flags = fcntl(sock, F_GETFL, 0);
fcntl(sock, F_SETFL, flags | O_NONBLOCK);
```

### TLS Socket Options

```c
/* Security tag list */
int sec_tag_list[] = { CA_CERTIFICATE_TAG };
setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST, sec_tag_list, sizeof(sec_tag_list));

/* Hostname for SNI */
setsockopt(sock, SOL_TLS, TLS_HOSTNAME, hostname, strlen(hostname));

/* Peer verification */
int peer_verify = TLS_PEER_VERIFY_REQUIRED;
setsockopt(sock, SOL_TLS, TLS_PEER_VERIFY, &peer_verify, sizeof(peer_verify));

/* DTLS handshake timeout */
int timeout_ms = 10000;
setsockopt(sock, SOL_TLS, TLS_DTLS_HANDSHAKE_TIMEO, &timeout_ms, sizeof(timeout_ms));
```

### DNS Resolution

```c
int getaddrinfo(const char *host, const char *service,
                const struct addrinfo *hints, struct addrinfo **res);
void freeaddrinfo(struct addrinfo *res);
```

**Example:**

```c
struct addrinfo hints = {
    .ai_family = AF_INET,
    .ai_socktype = SOCK_STREAM,
};
struct addrinfo *result;

if (getaddrinfo("example.com", "80", &hints, &result) == 0) {
    struct sockaddr_in *addr = (struct sockaddr_in *)result->ai_addr;
    /* Use addr */
    freeaddrinfo(result);
}
```

### Poll for Multiple Sockets

```c
int poll(struct pollfd *fds, int nfds, int timeout);
```

**Structure:**

```c
struct pollfd {
    int fd;         /* Socket */
    short events;   /* POLLIN, POLLOUT, POLLERR */
    short revents;  /* Returned events */
};
```

**Example:**

```c
struct pollfd fds[] = {
    { .fd = sock1, .events = POLLIN },
    { .fd = sock2, .events = POLLIN },
};

int ret = poll(fds, ARRAY_SIZE(fds), 5000);  /* 5 second timeout */
if (ret > 0) {
    if (fds[0].revents & POLLIN) {
        recv(sock1, buf, sizeof(buf), 0);
    }
    if (fds[1].revents & POLLIN) {
        recv(sock2, buf, sizeof(buf), 0);
    }
}
```

## TLS Credentials API

### Adding Credentials

```c
int tls_credential_add(sec_tag_t tag, enum tls_credential_type type,
                       const void *cred, size_t credlen);
```

**Types:**
- `TLS_CREDENTIAL_CA_CERTIFICATE` — CA certificate (PEM or DER)
- `TLS_CREDENTIAL_SERVER_CERTIFICATE` — Server certificate
- `TLS_CREDENTIAL_PRIVATE_KEY` — Private key
- `TLS_CREDENTIAL_PSK` — Pre-shared key
- `TLS_CREDENTIAL_PSK_ID` — PSK identity

**Example:**

```c
static const unsigned char ca_cert[] = {
    #include "ca_cert.pem.inc"
};

tls_credential_add(CA_TAG, TLS_CREDENTIAL_CA_CERTIFICATE,
                   ca_cert, sizeof(ca_cert));
```

### Deleting Credentials

```c
int tls_credential_delete(sec_tag_t tag, enum tls_credential_type type);
```

### Retrieving Credentials

```c
int tls_credential_get(sec_tag_t tag, enum tls_credential_type type,
                       void *cred, size_t *credlen);
```

## Network Configuration

### DHCP

```c
#include <zephyr/net/dhcpv4.h>

void dhcp_handler(struct net_mgmt_event_callback *cb, uint32_t mgmt_event,
                  struct net_if *iface)
{
    if (mgmt_event == NET_EVENT_IPV4_DHCP_BOUND) {
        /* DHCP lease acquired */
    }
}

struct net_if *iface = net_if_get_default();
net_dhcpv4_start(iface);
```

### Static IP

```c
#include <zephyr/net/net_if.h>

struct net_if *iface = net_if_get_default();
struct in_addr addr, netmask, gw;

inet_pton(AF_INET, "192.168.1.100", &addr);
inet_pton(AF_INET, "255.255.255.0", &netmask);
inet_pton(AF_INET, "192.168.1.1", &gw);

net_if_ipv4_addr_add(iface, &addr, NET_ADDR_MANUAL, 0);
net_if_ipv4_set_netmask(iface, &netmask);
net_if_ipv4_set_gw(iface, &gw);
```

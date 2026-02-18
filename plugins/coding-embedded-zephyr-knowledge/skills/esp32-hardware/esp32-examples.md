# ESP32 Examples

## WiFi STA (ESP32-C3)

```c
#include <zephyr/net/wifi_mgmt.h>

struct wifi_connect_req_params params = {
    .ssid = "MyWiFi",
    .ssid_length = 6,
    .psk = "password",
    .psk_length = 8,
    .security = WIFI_SECURITY_TYPE_PSK,
};

struct net_if *iface = net_if_get_default();
net_mgmt(NET_REQUEST_WIFI_CONNECT, iface, &params, sizeof(params));
```

## BLE + WiFi Coexistence (ESP32-S3)

```kconfig
CONFIG_BT=y
CONFIG_WIFI=y
CONFIG_ESP32_WIFI_BT_COEXIST=y
```

## Deep Sleep with RTC Wakeup

```c
RTC_DATA_ATTR static int count = 0;

void main(void) {
    count++;
    printk("Wakeup %d\n", count);
    
    esp_sleep_enable_timer_wakeup(5 * 1000000);
    esp_deep_sleep_start();
}
```
